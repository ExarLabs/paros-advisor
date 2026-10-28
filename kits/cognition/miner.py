#!/usr/bin/env python3
"""PAROS transcript reader and learning measurement (kit version 0.2.0).

Deterministic, no LLM, read only. It reads this machine's own agent transcripts
(Claude Code: ~/.claude/projects/**/*.jsonl, the main session and subagents), only the
part written since the last read, and gives the cognitive cycle two things:

1. MEASUREMENT (the learning funnel): tool calls, tool errors by error class, and for the
   rules that carry a signal pattern: situation / compliance / miss / violation counts.
   From these come friction (recurring errors per 100 tool calls), application, transfer
   (is the rule followed in other places too) and prevention (did the error go away).
2. DETECTION: the recurring error classes that show up in several sessions. If no rule
   covers them, they are lesson candidates; if a rule covers them and the error still
   comes, that is an adherence (or placement) failure, and an item for the curator.

Stores (one writer per machine, safe with file sync):
  metrics/<host>.jsonl     append-only records: counters per session x day x context
  .miner.<host>.json       read watermark per transcript file (byte offset)

Privacy: no content is stored, only counters and a normalised error signature (paths,
e-mail addresses, long tokens and numbers replaced).

Signal pattern on a rule (registry.json, field `signals`):
  on         tool name regex (e.g. "Bash", "Read", "mcp__browser__.*"), default ".*"
  trigger    regex on the tool input: the situation has come up
  comply     regex on the input: the right form (optional)
  avoid      regex on the input: the form to avoid (optional)
  violation  regex on the error text: the error the rule prevents (optional)
  enforce    true: the PreToolUse hook stops the form to avoid (only on a sure rule)

Configuration (environment):
  PAROS_COGNITION_DIR      where metrics/ and the watermark live (default: this folder)
  PAROS_TRANSCRIPTS        the transcript root (default ~/.claude/projects)
  PAROS_HOST               the machine name used in file names (default: the host name)
  PAROS_CONTEXT_PATTERNS   a JSON list of regexes, each with one group, that name the
                           context of a day's work from the paths in tool inputs (the most
                           frequent match wins); default: skills/<x>, capabilities/<x>,
                           Areas/<x>, agents/<x>
"""
import datetime as dt
import json
import os
import re
import socket
from collections import Counter, defaultdict
from pathlib import Path

PROJECTS = Path(os.environ.get("PAROS_TRANSCRIPTS") or (Path.home() / ".claude" / "projects"))
COG = Path(os.environ.get("PAROS_COGNITION_DIR") or Path(__file__).resolve().parent).resolve()
METRICS = COG / "metrics"
FIRST_SCAN_DAYS = 75       # the first read looks back this far; older files are skipped
RECUR_DAYS = 14            # a recurring error: seen within this window ...
RECUR_MIN_SESSIONS = 3     # ... in at least this many different sessions
# Harness noise, not a lesson: the person declined a tool, an interrupt, a busy limit.
NOISE = re.compile(r"doesn't want to proceed|user (has )?(rejected|denied)|Request interrupted|"
                   r"tool use was rejected|permission to use .* (was|has been) denied|"
                   r"Concurrent subagent limit", re.I)
_DEFAULT_CONTEXTS = [
    r"skills[/\\]+([\w.-]+)",
    r"capabilities[/\\]+([\w.-]+)",
    r"Areas[/\\]+([^/\\\"'\n;&|<>*]+?)(?=[/\\\"'\n;&|<>*]|$)",
    r"agents[/\\]+([\w.-]+?)(?:\.md)?(?=[/\\\"'\s]|$)",
]


def _context_res():
    raw = os.environ.get("PAROS_CONTEXT_PATTERNS")
    pats = _DEFAULT_CONTEXTS
    if raw:
        try:
            pats = [str(p) for p in json.loads(raw)]
        except Exception:
            pass
    out = []
    for p in pats:
        try:
            out.append(re.compile(p))
        except re.error:
            pass
    return out


CONTEXT_RES = _context_res()


def host():
    h = os.environ.get("PAROS_HOST") or socket.gethostname().lower().split(".")[0]
    return re.sub(r"[^a-z0-9-]", "-", h.lower()) or "unknown"


def _load(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def signature(text):
    """The normalised, content-free signature of an error text (for classification)."""
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False)
    text = re.sub(r"</?tool_use_error>", "", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    if "Traceback (most recent call last)" in text:
        line = next((l for l in reversed(lines) if re.match(r"^[A-Za-z_.]+(Error|Exception|Exit)\b", l)), lines[-1])
    elif re.match(r"^Exit code \d+$", lines[0]) and len(lines) > 1:
        line = "exit: " + lines[1]
    else:
        line = lines[0]
    line = re.sub(r"[A-Za-z]:[\\/][^\s\"'`]*", "<path>", line)
    line = re.sub(r"(?<![\w<])/(?:[^\s\"'`/]+/)+[^\s\"'`]*", "<path>", line)
    line = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<email>", line)
    line = re.sub(r"\b[A-Za-z0-9_-]{24,}\b", "<tok>", line)
    line = re.sub(r"\d+", "N", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line[:100]


def _context(inputs, skills, project):
    if skills:
        return "skill:" + skills[0]
    c = Counter()
    for t in inputs:
        for rx in CONTEXT_RES:
            for m in rx.findall(t):
                c[m if isinstance(m, str) else m[0]] += 1
    if c:
        return c.most_common(1)[0][0].strip()[:40]
    return "project:" + project[-40:]


def compile_signals(rules):
    out = {}
    for rid, r in rules.items():
        s = r.get("signals")
        if not s or not s.get("trigger") and not s.get("violation"):
            continue
        try:
            out[rid] = {k: re.compile(s[k], re.I | re.S) for k in ("on", "trigger", "comply", "avoid", "violation") if s.get(k)}
        except re.error:
            continue
    return out


def _tool_text(name, inp):
    if name == "Bash" and isinstance(inp, dict):
        return str(inp.get("command", ""))
    return json.dumps(inp, ensure_ascii=False)


def scan(rules, state_path=None, write=True, full=False):
    """Process the transcript part written since the last read. Returns the list of records.

    full=True rereads everything in the look-back window (used when a new signal pattern
    arrives, so the past is measured too) and rewrites this machine's metrics file."""
    h = host()
    state_path = state_path or COG / f".miner.{h}.json"
    st = {} if full else _load(state_path, {})
    sigs = compile_signals(rules)
    cutoff = dt.datetime.now().timestamp() - FIRST_SCAN_DAYS * 86400
    agg = {}
    files = sorted(PROJECTS.rglob("*.jsonl")) if PROJECTS.exists() else []
    for f in files:
        key = str(f)
        try:
            size, mtime = f.stat().st_size, f.stat().st_mtime
        except OSError:
            continue
        off = st.get(key, 0)
        if off == 0 and mtime < cutoff:
            st[key] = size
            continue
        if off > size:
            off = 0  # the file was rewritten
        if off == size:
            continue
        with open(f, "rb") as fh:
            fh.seek(off)
            data = fh.read()
        end = data.rfind(b"\n")
        if end < 0:
            continue
        chunk, st[key] = data[: end + 1], off + end + 1
        project = f.relative_to(PROJECTS).parts[0]
        session = f.stem[:8] if f.parent.name != "subagents" else f.parent.parent.name[:8]
        per_day = defaultdict(lambda: {"tools": 0, "errors": 0, "err_sigs": Counter(), "inputs": [], "skills": [],
                                       "signals": defaultdict(lambda: Counter())})
        for raw in chunk.splitlines():
            try:
                r = json.loads(raw)
            except Exception:
                continue
            day = (r.get("timestamp") or "")[:10]
            if not day:
                continue
            c = (r.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            d = per_day[day]
            for it in c:
                if not isinstance(it, dict):
                    continue
                if it.get("type") == "tool_use":
                    name, inp = it.get("name", ""), it.get("input", {})
                    txt = _tool_text(name, inp)
                    d["tools"] += 1
                    if len(d["inputs"]) < 400:
                        d["inputs"].append(txt[:400])
                    if name == "Skill" and isinstance(inp, dict) and inp.get("skill"):
                        d["skills"].append(str(inp["skill"]))
                    for rid, s in sigs.items():
                        if "on" in s and not s["on"].fullmatch(name):
                            continue
                        if "trigger" not in s or not s["trigger"].search(txt):
                            continue
                        cnt = d["signals"][rid]
                        cnt["s"] += 1
                        if "comply" not in s and "avoid" not in s:
                            continue  # only marks the situation, does not measure compliance
                        miss = ("avoid" in s and s["avoid"].search(txt)) or ("comply" in s and not s["comply"].search(txt))
                        cnt["m" if miss else "c"] += 1
                elif it.get("type") == "tool_result" and it.get("is_error"):
                    t = it.get("content")
                    t = t if isinstance(t, str) else json.dumps(t, ensure_ascii=False)
                    if NOISE.search(t[:400]):
                        continue
                    d["errors"] += 1
                    sg = signature(t)
                    if sg:
                        d["err_sigs"][sg] += 1
                    for rid, s in sigs.items():
                        if "violation" in s and s["violation"].search(t[:2000]):
                            d["signals"][rid]["v"] += 1
        for day, d in per_day.items():
            if not d["tools"] and not d["errors"]:
                continue
            ctx = _context(d["inputs"], d["skills"], project)
            k = (session, day, ctx)
            a = agg.setdefault(k, {"date": day, "host": h, "session": session, "project": project[-60:],
                                   "context": ctx, "tools": 0, "errors": 0, "err_sigs": Counter(), "signals": {}})
            a["tools"] += d["tools"]; a["errors"] += d["errors"]; a["err_sigs"].update(d["err_sigs"])
            for rid, cnt in d["signals"].items():
                a["signals"].setdefault(rid, Counter()).update(cnt)
    recs = []
    for a in agg.values():
        a["err_sigs"] = dict(a["err_sigs"])
        a["signals"] = {rid: dict(c) for rid, c in a["signals"].items()}
        recs.append(a)
    if write:
        METRICS.mkdir(parents=True, exist_ok=True)
        # a full reread (new signal pattern) rewrites this machine's metrics file, otherwise append
        with (METRICS / f"{h}.jsonl").open("w" if full else "a", encoding="utf-8") as fh:
            stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            for a in recs:
                fh.write(json.dumps({**a, "scanned": stamp}, ensure_ascii=False) + "\n")
        _save(state_path, st)
    return recs


def load_records():
    """The measurement records of every machine (each machine writes only its own file)."""
    out = []
    if METRICS.exists():
        for p in sorted(METRICS.glob("*.jsonl")):
            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _day(s):
    return dt.date.fromisoformat(s)


def window(recs, end, days):
    lo = end - dt.timedelta(days=days - 1)
    return [r for r in recs if lo <= _day(r["date"]) <= end]


def recurring(recs, end, days=RECUR_DAYS, min_sessions=RECUR_MIN_SESSIONS):
    """Error classes that came up in at least min_sessions different sessions within the window."""
    by = defaultdict(lambda: {"count": 0, "sessions": set(), "contexts": set(), "days": set()})
    for r in window(recs, end, days):
        for sg, n in r.get("err_sigs", {}).items():
            b = by[sg]
            b["count"] += n; b["sessions"].add((r["host"], r["session"])); b["contexts"].add(r["context"]); b["days"].add(r["date"])
    out = []
    for sg, b in by.items():
        if len(b["sessions"]) >= min_sessions:
            out.append({"signature": sg, "count": b["count"], "sessions": len(b["sessions"]),
                        "contexts": sorted(b["contexts"])[:6], "first": min(b["days"]), "last": max(b["days"])})
    out.sort(key=lambda x: (-x["sessions"], -x["count"]))
    return out


def friction(recs, end, days=7):
    """Friction: the recurring errors (seen in at least 3 sessions within 14 days) per 100 tool calls."""
    w = window(recs, end, days)
    tools = sum(r["tools"] for r in w)
    errs = sum(r["errors"] for r in w)
    rec_sigs = {x["signature"] for x in recurring(recs, end)}
    rec = sum(n for r in w for sg, n in r.get("err_sigs", {}).items() if sg in rec_sigs)

    def per(x):
        return round(100.0 * x / tools, 2) if tools else None

    return {"days": days, "end": end.isoformat(), "tools": tools, "errors": errs, "recurring": rec,
            "errors_per100": per(errs), "friction_per100": per(rec), "sessions": len({(r["host"], r["session"]) for r in w})}


def rule_stats(recs, rid, since=None, until=None):
    """Situation, compliance, miss and violation counts of one rule, with the contexts where it
    was followed (transfer) and the first day it was followed."""
    s = Counter(); ctx = set(); sess = set(); first_c = None; viol_days = set()
    for r in recs:
        d = _day(r["date"])
        if since and d < since or until and d > until:
            continue
        c = r.get("signals", {}).get(rid)
        if not c:
            continue
        s.update(c)
        if c.get("c"):
            ctx.add(r["context"]); sess.add((r["host"], r["session"]))
            first_c = min(first_c, d) if first_c else d
        if c.get("v"):
            viol_days.add(r["date"])
    return {"situations": s.get("s", 0), "complied": s.get("c", 0), "missed": s.get("m", 0), "violations": s.get("v", 0),
            "contexts": sorted(ctx), "sessions": len(sess), "first_compliance": first_c.isoformat() if first_c else None,
            "violation_days": sorted(viol_days)}


def daily_series(recs, end, days=28):
    """The daily friction series (recurring errors per 100 tool calls) for the report's curve."""
    rec_sigs = {x["signature"] for x in recurring(recs, end, days=days)}
    out = []
    for i in range(days - 1, -1, -1):
        d = end - dt.timedelta(days=i)
        w = [r for r in recs if r["date"] == d.isoformat()]
        tools = sum(r["tools"] for r in w)
        rec = sum(n for r in w for sg, n in r.get("err_sigs", {}).items() if sg in rec_sigs)
        out.append((d.isoformat(), tools, rec))
    return out
