#!/usr/bin/env python3
"""PAROS cognitive cycle: weighted learned rules, measured effect, curation (kit version 0.2.0).

A deterministic engine, no LLM inside. The thinking work (what is a new lesson,
did a rule help, is it still valid, where does it belong) is done by a caretaker agent
in its cycle mode, inside a normal agent session on the owner's subscription, not on
API credits. This script only keeps records, measures, computes weights and renders views.

Stores (the JSON and markdown are the truth, the rest is derived):
  registry.json          canonical: the learned rules (ID, source, text, scope, signals)
  events/<host>.jsonl    canonical, append-only, one writer per machine: everything
                         that happened to the rules (born, confirm, used, outcome,
                         reviewed, deprecated, revived, curated, data)
  state.json             the history of cycles (only `apply` writes it)
  lease.json             who is running a cycle right now (90 minute lease)
  .base.<host>.json      one writer per machine: the cycle number seen at `packet` time,
                         the optimistic lock of `apply`
  metrics/<host>.jsonl   measurement records written by miner.py (counters, no content)
  weights.json           DERIVED, can be recomputed at any time
  CYCLES.md              the log of cycle reports, for humans

The weight (0..1) is computed from the events, in order:
  born        base by evidence (owner decision 0.40, human correction 0.35,
              measured 0.30, convergence 0.30, agent inference 0.15)
  confirm     w += 0.15 * (1 - w)
  helpful     w += 0.12 * (1 - w)   (also written automatically from measured compliance)
  harmful     w -= 0.30 * w, and the rule goes to review
  neutral     only the exposure grows
  idle        after 60 days without use: x0.95 per month (human-origin rules
              have a 0.15 floor, so they never fall asleep on their own)
  dormant     w < 0.12: left out of the loaded list, but kept in the file

Several machines, one brain. The registry file is synced between machines, and a sync can
overwrite a newer copy with an older one. So:
  1. every machine issues rule IDs from its own range (PAROS_ID_BLOCKS); an unconfigured
     machine gets a block of 100 in the 6000-9999 band, chosen from its host name; the next
     number is the highest already seen in the range + 1, counted from the registry AND the
     event logs, so two machines cannot collide;
  2. the full rule data also travels in its birth (and refine and curated) event, in the
     machine's own single-writer event log; load_registry() restores from there whatever is
     missing from the registry file, and the next save heals the file;
  3. `backfill` writes a `data` event once for older rules that have none;
  4. `packet` records the cycle number it saw; `apply` stops without writing (exit code 3)
     if another cycle has run since, and asks for a new packet.

Configuration (environment):
  PAROS_COGNITION_DIR    where the stores live (default: this script's folder)
  PAROS_VAULT            the vault root (default: detected upwards from the data
                         folder, by a .obsidian, .git or AGENTS.md marker)
  PAROS_LEARNING_ROOTS   folders (relative to the vault, separated by os.pathsep)
                         scanned for changed LEARNINGS.md and observations/*.md;
                         default: the whole vault
  PAROS_MEMORY_DIR       optional: a folder of agent memory files (relative to the
                         vault). If set, changed rule-type memory files go into the
                         packet, and rules targeting a file there are marked in the
                         memory index by an ID prefix on the index line
  PAROS_MEMORY_INDEX     the memory index file name (default MEMORY.md)
  PAROS_GENERAL_RULES    the generated general rules file, relative to the vault
                         (default PAROS/GENERAL_RULES.md); import it from the vault's
                         entry file so it loads in every session
  PAROS_ID_BLOCKS        JSON {"<host>": [low, high], ...}: the rule ID range per machine
                         (or the same JSON in id_blocks.json next to the stores)
  PAROS_GENERAL_HINTS    a regex of tool and environment words; a narrowly placed rule
                         whose text matches two of them is offered to the curator
  PAROS_HEALTH_CHECK     optional: the health kit's health_check.py; `packet` then runs
                         it and the report shows every machine's health state
  PAROS_HEALTH_STATE_DIR where the health kit keeps state.<host>.json (default ~/.paros/health)
  PAROS_CYCLE_DOC        the cycle procedure the hook points to
                         (default kits/cognition/CYCLE.md)
  PAROS_HOST             the machine name (default: the host name)
  miner.py has its own settings (transcript root, context patterns); see its docstring.

Commands:
  due [--hook] [--hours N]   is a cycle due; --hook: UserPromptSubmit hook mode
  stop-hook                  Stop hook: rules cited as [L-xxxx] in the answer get a
                             use event (outcome: pending)
  pretool-hook               PreToolUse hook: a sure, command-level rule (signals.enforce)
                             stops the form to avoid at the moment of the action
  used L-0001 [--outcome helpful|harmful|neutral|pending] [--note ...]
  packet [--out F] [--full]  the caretaker agent's work packet (--full: curate everything)
  apply decisions.json       the caretaker's decisions: events, weights, render, report
  measure [--full] [--json]  read the transcripts and print the learning rate, no cycle
  report                     the current state as a report (no cycle)
  render                     rewrite the generated blocks and the general rules file
  show L-0001 [...]          one rule in full (text, scope, source, links, weight)
  find <words>               search every learned rule, by weight
  backfill                   once per machine: a data event for every rule without one
"""
import argparse
import datetime as dt
import json
import os
import re
import socket
import sys
import uuid
import zlib
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _detect_vault(start):
    for p in [start, *start.parents]:
        if any((p / m).exists() for m in (".obsidian", ".git", "AGENTS.md")):
            return p
    return Path.cwd()


COG = Path(os.environ.get("PAROS_COGNITION_DIR") or Path(__file__).resolve().parent).resolve()
os.environ.setdefault("PAROS_COGNITION_DIR", str(COG))  # miner.py keeps its metrics next to ours
sys.path.insert(0, str(Path(__file__).resolve().parent))
import miner  # noqa: E402  (transcript reader and learning measurement)

VAULT = Path(os.environ["PAROS_VAULT"]).resolve() if os.environ.get("PAROS_VAULT") else _detect_vault(COG)
REGISTRY = COG / "registry.json"
EVENTS = COG / "events"
STATE = COG / "state.json"
LEASE = COG / "lease.json"
WEIGHTS = COG / "weights.json"
CYCLES = COG / "CYCLES.md"
MEMORY_DIR = (VAULT / os.environ["PAROS_MEMORY_DIR"]).resolve() if os.environ.get("PAROS_MEMORY_DIR") else None
MEMORY_INDEX = os.environ.get("PAROS_MEMORY_INDEX", "MEMORY.md")
CYCLE_DOC = os.environ.get("PAROS_CYCLE_DOC", "kits/cognition/CYCLE.md")
GENERAL_REL = (os.environ.get("PAROS_GENERAL_RULES") or "PAROS/GENERAL_RULES.md").replace("\\", "/")
GENERAL = VAULT / GENERAL_REL
HEALTH_SCRIPT = os.environ.get("PAROS_HEALTH_CHECK")
HEALTH_STATE_DIR = Path(os.environ.get("PAROS_HEALTH_STATE_DIR") or (Path.home() / ".paros" / "health")).expanduser()
HEALTH_STALE_HOURS = 12


def learning_roots():
    raw = os.environ.get("PAROS_LEARNING_ROOTS")
    if not raw:
        return [VAULT]
    return [VAULT / r for r in raw.split(os.pathsep) if r.strip()]


DUE_HOURS = 4
LEASE_MIN = 90
COOLDOWN_DAYS = 7          # what the curator touched is not moved again for this many days
CURATE_BATCH = 6           # the curator gets this many backlog items per cycle
BASE = {"owner_decision": 0.40, "human_correction": 0.35, "measured": 0.30,
        "convergence": 0.30, "agent_inferred": 0.15}
HUMAN_ORIGIN = {"owner_decision", "human_correction"}
DORMANT = 0.12
IDLE_DAYS = 60
TIERS = [(0.25, "seedling", "░"), (0.50, "growing", "▒"), (0.75, "strong", "▓"), (1.01, "root", "█")]
CITE = re.compile(r"\[(L-\d{4})\]")
BEGIN = "<!-- COGNITION:BEGIN"
END = "<!-- COGNITION:END -->"
SKIP_PARTS = {"_archive", "_archiv", "versions", ".git", "node_modules", ".obsidian", ".trash"}
RULE_FIELDS = ("skill", "area", "source", "target", "text", "applies_when", "origin_date", "evidence", "registered",
               "history", "signals", "scope", "superseded_by", "instance_of", "generalizes")
CURATED_FIELDS = ("signals", "scope", "superseded_by", "instance_of", "generalizes", "target")


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t=None):
    return (t or now()).isoformat(timespec="seconds")


def parse(ts):
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def host():
    h = os.environ.get("PAROS_HOST") or socket.gethostname().lower().split(".")[0]
    return re.sub(r"[^a-z0-9-]", "-", h.lower()) or "unknown"


def base_path():
    return COG / f".base.{host()}.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def append_event(ev):
    EVENTS.mkdir(parents=True, exist_ok=True)
    ev.setdefault("id", uuid.uuid4().hex[:12])
    ev.setdefault("ts", iso())
    ev.setdefault("host", host())
    with (EVENTS / f"{host()}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def all_events():
    out = []
    for p in sorted(EVENTS.glob("*.jsonl")) if EVENTS.exists() else []:
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    out.sort(key=lambda e: e.get("ts", ""))
    return out


# ---------------------------------------------------------------- registry and IDs

def id_blocks():
    raw = os.environ.get("PAROS_ID_BLOCKS")
    data = None
    if raw:
        try:
            data = json.loads(raw)
        except Exception:
            data = None
    if data is None:
        data = load(COG / "id_blocks.json", {})
    out = {}
    for h, v in (data or {}).items():
        try:
            out[str(h).lower()] = (int(v[0]), int(v[1]))
        except Exception:
            pass
    return out


def id_block(h=None):
    h = h or host()
    blocks = id_blocks()
    if h in blocks:
        return blocks[h]
    lo = 6000 + (zlib.crc32(h.encode()) % 40) * 100
    return lo, lo + 99


def rid_num(rid):
    try:
        return int(str(rid).split("-")[1])
    except Exception:
        return 0


def load_registry(events=None):
    """The registry file plus the rule data travelling in the event logs, as a union (the file
    can be overwritten by a sync; the single-writer event logs cannot)."""
    reg = load(REGISTRY, {"next_id": 1, "rules": {}})
    reg.setdefault("rules", {})
    events = events if events is not None else all_events()
    healed = []
    for e in events:
        d = e.get("data")
        rid = e.get("rule")
        if not d or not rid:
            continue
        if e.get("type") in ("born", "data") and rid not in reg["rules"]:
            reg["rules"][rid] = {k: d.get(k) for k in RULE_FIELDS if d.get(k) is not None}
            healed.append(rid)
        elif e.get("type") == "reviewed" and rid in reg["rules"]:
            for k in ("text", "applies_when"):
                if d.get(k) and reg["rules"][rid].get(k) != d[k]:
                    reg["rules"][rid].setdefault("history", []).append({k: reg["rules"][rid].get(k), "until": e.get("ts")})
                    reg["rules"][rid][k] = d[k]
        elif e.get("type") == "curated" and rid in reg["rules"]:
            for k in CURATED_FIELDS:
                if k in d and reg["rules"][rid].get(k) != d[k]:
                    reg["rules"][rid][k] = d[k]
    ids = [rid_num(r) for r in reg["rules"]] + [rid_num(e.get("rule")) for e in events if e.get("type") == "born"]
    reg["next_id"] = max([reg.get("next_id", 1) - 1] + ids) + 1
    if healed:
        print(f"[cognition] rules missing from the registry file restored from the event logs: {', '.join(sorted(healed))}",
              file=sys.stderr)
    return reg


def missing_without_data(reg, events):
    """Birth events whose rule is missing from the registry and has no data to restore it from."""
    return sorted({e["rule"] for e in events if e.get("type") == "born" and e.get("rule") not in reg["rules"]})


def alloc_id(reg, events):
    lo, hi = id_block()
    seen = [rid_num(r) for r in reg["rules"]] + [rid_num(e.get("rule")) for e in events if e.get("type") == "born"]
    inside = [n for n in seen if lo <= n <= hi]
    n = (max(inside) + 1) if inside else lo
    if n > hi:
        raise SystemExit(f"The ID range of {host()} ({lo}-{hi}) is used up; give it a range in PAROS_ID_BLOCKS.")
    return f"L-{n:04d}"


def tier(w):
    for lim, name, ch in TIERS:
        if w < lim:
            return name, ch
    return TIERS[-1][1], TIERS[-1][2]


# ---------------------------------------------------------------- weights

def compute(registry=None, events=None, at=None):
    registry = registry or load_registry()
    events = events if events is not None else all_events()
    at = at or now()
    state = load(STATE, {})
    since = parse(state["telemetry_since"]) if state.get("telemetry_since") else at
    res = {}
    for rid in registry["rules"]:
        res[rid] = {"w": 0.0, "status": "active", "exposure": 0, "helpful": 0, "harmful": 0,
                    "neutral": 0, "pending": 0, "confirm": 0, "last": None, "review": False}
    resolved = {e["ref"] for e in events if e.get("type") == "outcome" and e.get("ref")}
    for e in events:
        rid = e.get("rule")
        if rid not in res:
            continue
        s, t = res[rid], e.get("type")
        if t == "born":
            s["w"] = BASE.get(registry["rules"][rid].get("evidence"), 0.15)
        elif t == "confirm":
            s["w"] += 0.15 * (1 - s["w"]); s["confirm"] += 1
        elif t == "used":
            s["exposure"] += 1
            if e.get("outcome", "pending") == "pending" and e["id"] not in resolved:
                s["pending"] += 1
            elif e.get("outcome") in ("helpful", "harmful", "neutral"):
                apply_outcome(s, e["outcome"])
        elif t == "outcome":
            apply_outcome(s, e.get("value"))
        elif t == "reviewed":
            s["review"] = False
        elif t == "deprecated":
            s["status"] = "deprecated"
        elif t == "revived":
            s["status"] = "active"; s["w"] = max(s["w"], 0.2)
        if t in ("data", "curated"):
            continue  # bookkeeping, not use: it does not reset the idle clock
        # A birth registered before telemetry started (an inventory of old rules)
        # does not count as activity: otherwise every old rule would look fresh.
        if t != "born" or parse(e["ts"]) >= since:
            s["last"] = e["ts"]
    for rid, s in res.items():
        last = max(parse(s["last"]) if s["last"] else since, since)
        idle = (at - last).days
        if idle > IDLE_DAYS:
            w = s["w"] * 0.95 ** ((idle - IDLE_DAYS) / 30)
            if registry["rules"][rid].get("evidence") in HUMAN_ORIGIN:
                w = max(w, min(s["w"], 0.15))
            s["w"] = w
        s["w"] = round(min(max(s["w"], 0.0), 1.0), 3)
        if s["status"] != "deprecated":
            if s["review"]:
                s["status"] = "review"
            elif s["w"] < DORMANT:
                s["status"] = "dormant"
    return res


def apply_outcome(s, v):
    if v == "helpful":
        s["helpful"] += 1; s["w"] += 0.12 * (1 - s["w"])
    elif v == "harmful":
        s["harmful"] += 1; s["w"] -= 0.30 * s["w"]; s["review"] = True
    elif v == "neutral":
        s["neutral"] += 1


# ---------------------------------------------------------------- hooks

def cmd_due(a):
    state, lease = load(STATE, {}), load(LEASE, {})
    last = parse(state["last_cycle_at"]) if state.get("last_cycle_at") else None
    hours = (now() - last).total_seconds() / 3600 if last else None
    due = hours is None or hours >= a.hours
    leased = lease.get("at") and (now() - parse(lease["at"])).total_seconds() < LEASE_MIN * 60
    if not a.hook:
        print(json.dumps({"due": due, "hours_since": hours, "leased": bool(leased), "lease": lease}, ensure_ascii=False))
        return
    if not due or leased:
        return
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except Exception:
        inp = {}
    save(LEASE, {"host": host(), "session": inp.get("session_id", ""), "at": iso()})
    ago = "never yet" if hours is None else f"{hours:.0f} hours ago"
    msg = (f"PAROS cognitive cycle is due (the last one ran {ago}; this session holds the lease). "
           "While you serve the person's request, start your caretaker agent in cycle mode, in the BACKGROUND, "
           f"with this prompt: \"Mode: cycle. Run the cognitive cycle as described in {CYCLE_DOC} "
           "and return the report verbatim.\" When it comes back, put the report block unchanged at the end "
           "of your answer. Do not ask about it and do not explain it; the owner decided this.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))


def last_assistant_texts(transcript):
    """From the end of the transcript: the assistant texts after the last real user message."""
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 600_000))
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except Exception:
        return []
    out = []
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") == "user" and isinstance(d.get("message", {}).get("content"), str):
            break
        if d.get("type") == "assistant" and not d.get("isSidechain"):
            for c in d.get("message", {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "text":
                    out.append((d.get("uuid", ""), c.get("text", "")))
    return out


def cmd_stop_hook(a):
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    texts = []
    if inp.get("last_assistant_message"):
        texts.append(("last", inp["last_assistant_message"]))
    if inp.get("transcript_path"):
        texts += last_assistant_texts(inp["transcript_path"])
    reg = load_registry()["rules"]
    seen_p = COG / f".seen.{host()}.json"
    seen = load(seen_p, [])
    sid = inp.get("session_id", "")
    for uid, text in texts:
        for rid in sorted(set(CITE.findall(text))):
            key = f"{sid}:{rid}"
            if rid in reg and key not in seen:
                m = re.search(r"[^\n]*\[" + rid + r"\][^\n]*", text)
                append_event({"type": "used", "rule": rid, "outcome": "pending", "session": sid,
                              "transcript": inp.get("transcript_path", ""), "msg": uid,
                              "context": (m.group(0) if m else "")[:300]})
                seen.append(key)
    save(seen_p, seen[-2000:])


def cmd_pretool_hook(a):
    """PreToolUse hook: a sure, command-level learned rule (signals.enforce) acts at the moment of
    the action. If the situation has come up and the command has the form to avoid, it stops the
    call and gives the rule as the reason; the model corrects the command and runs it again.
    Enforcement is the owner's decision per rule, never the curator's."""
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    name, ti = inp.get("tool_name", ""), inp.get("tool_input", {})
    txt = ti.get("command", "") if name == "Bash" and isinstance(ti, dict) else json.dumps(ti, ensure_ascii=False)
    reg = load(REGISTRY, {}).get("rules", {})
    status = load(WEIGHTS, {}).get("rules", {})
    for rid, r in reg.items():
        s = r.get("signals") or {}
        if not s.get("enforce") or status.get(rid, {}).get("status") in ("deprecated", "dormant"):
            continue
        sc = r.get("scope") or ""
        if sc.startswith("machine:") and sc != f"machine:{host()}":
            continue
        try:
            if s.get("on") and not re.fullmatch(s["on"], name):
                continue
            if not s.get("trigger") or not re.search(s["trigger"], txt, re.I | re.S):
                continue
            bad = (s.get("avoid") and re.search(s["avoid"], txt, re.I | re.S)) or \
                  (s.get("comply") and not re.search(s["comply"], txt, re.I | re.S))
        except re.error:
            continue
        if bad:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                     "permissionDecisionReason": f"Learned rule [{rid}]: {r.get('text')} "
                                                                                 "Correct the command accordingly and run it again."}},
                             ensure_ascii=False))
            return


def cmd_used(a):
    reg = load_registry()["rules"]
    if a.rule not in reg:
        sys.exit(f"unknown rule: {a.rule}")
    ev = append_event({"type": "used", "rule": a.rule, "outcome": a.outcome, "note": a.note or ""})
    s = compute()[a.rule]
    print(f"{a.rule}: {a.outcome} recorded, weight now {s['w']:.2f} ({tier(s['w'])[0]}), event {ev['id']}")


# ---------------------------------------------------------------- cycle

NOT_HUMAN = ("<task-notification>", "<local-command-", "<system-reminder>")


def is_human_turn(d):
    """A real message from the person: a text user line, not meta (image, skill or agent
    message), not a notification or hook output."""
    c = d.get("message", {}).get("content")
    return (d.get("type") == "user" and isinstance(c, str) and not d.get("isMeta")
            and not d.get("isSidechain") and not c.lstrip().startswith(NOT_HUMAN))


def next_user_text(transcript, msg_uuid, limit=700, after_ts=None):
    """The person's first message after the citing answer: the basis for judging whether it helped.

    msg_uuid: the uuid of the citing assistant message. If it is "last" or empty (the Stop hook
    recorded it from last_assistant_message), the anchor is the event time (after_ts): the first
    person message later than that. Without an anchor the result is empty, never the first
    message of the session.
    """
    try:
        lines = Path(transcript).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None
    by_time = msg_uuid in ("", "last")
    if by_time and not after_ts:
        return ""
    anchor = parse(after_ts) if by_time else None
    found = False
    for line in lines:
        try:
            d = json.loads(line)
        except Exception:
            continue
        if by_time:
            try:
                found = bool(d.get("timestamp")) and parse(d["timestamp"]) > anchor
            except Exception:
                found = False
        elif not found and d.get("uuid") == msg_uuid:
            found = True
            continue
        if found and is_human_turn(d):
            return d["message"]["content"][:limit]
    return ""


RULE_MEMORY_TYPES = ("feedback", "reference")


def memory_type(p):
    """The `type` field of a memory file's frontmatter (top level or under metadata); empty on error."""
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    m = re.match(r"---\r?\n(.*?)\r?\n---", txt, re.S)
    t = re.search(r"(?m)^[ \t]*type:[ \t]*['\"]?([A-Za-z_-]+)", m.group(1)) if m else None
    return t.group(1).lower() if t else ""


def rel(p):
    try:
        return str(p.relative_to(VAULT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


# ---------------------------------------------------------------- measurement and curation
# The weight used to measure intake (births, an inventory), not effect. The real measure of
# learning is less friction, and rules that carry over to new places. The measurement reads
# the transcripts (miner.py); the curator sorts the arriving rules and a batch of the backlog
# every cycle, without losing anything.

NARROW_GENERAL = re.compile(os.environ.get("PAROS_GENERAL_HINTS") or (
    r"\b(windows|macos|linux|powershell|python|bash|shell|heredoc|git|github|browser|chrome|utf-?8|cp1252|"
    r"encoding|pdf|ffmpeg|curl|json|regex|frontmatter|subagent|hook|mcp|connector|token|timeout|sync|"
    r"junction|symlink|path|venv|pip|npm|node|deploy|api key|secret|user-agent|line ending|crlf)\b"), re.I)


def is_global(r):
    sc = (r.get("scope") or "")
    return sc == "global" or sc.startswith("machine:")


def target_kind(t):
    t = (t or "").replace("\\", "/")
    if not t:
        return "none"
    if t == GENERAL_REL:
        return "general"
    if MEMORY_DIR:
        try:
            if MEMORY_DIR in (VAULT / t).resolve().parents:
                return "memory"
        except Exception:
            pass
    if "/agents/" in "/" + t:
        return "agent"
    if "/capabilities/" in "/" + t:
        return "capability"
    if t.endswith("CURRENT.md") or "/skills/" in "/" + t:
        return "skill"
    return "other"


def curated_recently(events, days=COOLDOWN_DAYS):
    lim = now() - dt.timedelta(days=days)
    return {e["rule"] for e in events if e.get("type") == "curated" and e.get("rule") and parse(e["ts"]) >= lim}


def _toks(s):
    return set(re.findall(r"[^\W\d_]{4,}|\d{4,}", (s or "").lower()))


def duplicate_pairs(reg, w, thr=0.30):
    """Live rule pairs in different files whose word sets overlap (Jaccard >= thr): duplicate suspects."""
    act = [(rid, r) for rid, r in reg["rules"].items() if w.get(rid, {}).get("status") in ("active", "review")]
    T = [(rid, r.get("target", ""), _toks(r.get("text"))) for rid, r in act]
    out = []
    for i in range(len(T)):
        for j in range(i + 1, len(T)):
            a, b = T[i], T[j]
            if a[1] == b[1] or not a[2] or not b[2]:
                continue
            jac = len(a[2] & b[2]) / len(a[2] | b[2])
            if jac >= thr:
                out.append({"rules": [a[0], b[0]], "overlap": round(jac, 2)})
    return sorted(out, key=lambda x: -x["overlap"])


def rule_born_day(r):
    for k in ("registered", "origin_date"):
        v = r.get(k)
        if v:
            try:
                return dt.date.fromisoformat(str(v)[:10])
            except Exception:
                pass
    return None


def measurement(reg, w, recs, at_day=None):
    """The numbers of the learning funnel from the measurement records (miner)."""
    end = at_day or dt.date.today()
    cur, prev = miner.friction(recs, end, 7), miner.friction(recs, end - dt.timedelta(days=7), 7)
    rec = miner.recurring(recs, end)
    sig_rules = {rid: r for rid, r in reg["rules"].items() if r.get("signals") and w.get(rid, {}).get("status") != "deprecated"}
    vio_rx = {}
    for rid, r in sig_rules.items():
        try:
            if r["signals"].get("violation"):
                vio_rx[rid] = re.compile(r["signals"]["violation"], re.I)
        except re.error:
            pass
    for x in rec:
        x["rules"] = [rid for rid, rx in vio_rx.items() if rx.search(x["signature"])]
    rules = {}
    for rid, r in sig_rules.items():
        born = rule_born_day(r)
        after = miner.rule_stats(recs, rid, since=born) if born else miner.rule_stats(recs, rid)
        w7 = end - dt.timedelta(days=6)
        last7 = miner.rule_stats(recs, rid, since=max(w7, born) if born else w7)  # an error before birth does not count
        rules[rid] = {"born": born.isoformat() if born else None, "after_birth": after, "last7": last7,
                      "scope": r.get("scope"), "target": r.get("target")}
    ineffective = [rid for rid, s in rules.items() if s["last7"]["violations"] or s["last7"]["missed"]]
    since30 = now() - dt.timedelta(days=30)
    used30 = set()
    for e in all_events():
        if e.get("rule") and e.get("type") in ("used", "outcome") and parse(e["ts"]) >= since30:
            used30.add(e["rule"])
    for rid, s in rules.items():
        if s["last7"]["complied"] or miner.rule_stats(recs, rid, since=end - dt.timedelta(days=29))["complied"]:
            used30.add(rid)
    active = [rid for rid, s in w.items() if s["status"] in ("active", "review")]
    born7 = [rid for rid, r in reg["rules"].items() if (rule_born_day(r) or dt.date(2000, 1, 1)) >= end - dt.timedelta(days=6)]
    return {"friction": cur, "friction_prev": prev, "recurring": rec[:25],
            "lesson_candidates": [x for x in rec if not x["rules"]][:10],
            "adherence_failures": [x for x in rec if x["rules"]][:10],
            "rules": rules, "ineffective": ineffective,
            "applied_share": round(len(used30 & set(active)) / len(active), 3) if active else 0,
            "applied_30d": len(used30 & set(active)), "active": len(active), "born_7d": len(born7),
            "series": miner.daily_series(recs, end, 28)}


def curation(reg, w, events, last, full=False, meas=None):
    """The curator's work list: the arrivals, and a batch of the backlog in order of importance."""
    cool = curated_recently(events)
    cutoff = parse(last) if last else None
    live = {rid for rid, s in w.items() if s["status"] in ("active", "review")}
    arrivals = [rid for rid in live if cutoff and reg["rules"][rid].get("registered")
                and parse(reg["rules"][rid]["registered"]) > cutoff]
    backlog, seen = [], set(arrivals)

    def push(rid, why):
        if rid in live and rid not in seen and rid not in cool:
            backlog.append({"rule": rid, "why": why}); seen.add(rid)
    for rid in (meas or {}).get("ineffective", []):
        push(rid, "the error still comes after the rule (an adherence or placement failure)")
    for x in (meas or {}).get("adherence_failures", []):
        for rid in x["rules"]:
            push(rid, f"recurring error although a rule covers it: {x['signature'][:60]}")
    for p in duplicate_pairs(reg, w):
        for rid in p["rules"]:
            push(rid, f"duplicate suspect: {' + '.join(p['rules'])} ({p['overlap']})")
    for rid in sorted(live, key=lambda x: -w[x]["w"]):
        r = reg["rules"][rid]
        if is_global(r) or r.get("instance_of"):
            continue
        txt = (r.get("text") or "") + " " + (r.get("applies_when") or "")
        if target_kind(r.get("target")) in ("skill", "capability", "agent", "other") and len(NARROW_GENERAL.findall(txt)) >= 2:
            push(rid, "lives in a narrow place, but its content is about a tool or the environment")
    for rid in sorted(live, key=lambda x: -w[x]["w"]):
        r = reg["rules"][rid]
        if w[rid]["w"] >= 0.5 and target_kind(r.get("target")) in ("skill", "capability", "agent") and not is_global(r):
            push(rid, "a strong rule in a narrow place")
    if full:
        for rid in sorted(live):
            if not reg["rules"][rid].get("scope") and not reg["rules"][rid].get("instance_of"):
                push(rid, "full review")
    batch = backlog if full else backlog[:CURATE_BATCH]
    index = [f"{rid} | {reg['rules'][rid].get('scope') or 'local'} | {target_kind(reg['rules'][rid].get('target'))}:"
             f"{'/'.join((reg['rules'][rid].get('target') or '').split('/')[-2:])} | When: "
             f"{short(reg['rules'][rid].get('applies_when'), 70)} | {short(reg['rules'][rid].get('text'), 150)}"
             for rid in sorted(live)]

    def detail(rid):
        return {"rule": rid, **{k: reg["rules"][rid].get(k) for k in ("text", "applies_when", "target", "skill", "area",
                                                                     "scope", "evidence", "signals", "instance_of")},
                "weight": w[rid]["w"]}
    return {"arrivals": [detail(r) for r in sorted(arrivals)],
            "batch": [{**detail(b["rule"]), "why": b["why"]} for b in batch],
            "backlog_total": len(backlog), "cooldown": sorted(cool), "full": full,
            "index": index}


def cmd_packet(a):
    events = all_events()
    reg = load_registry(events)
    miss = missing_without_data(reg, events)
    if miss:
        print(f"WARNING: there is a birth event, but the rule is missing from the registry and has no data: "
              f"{', '.join(miss)}. Restore it from version history as a union (never by overwriting) before "
              "you run apply.", file=sys.stderr)
    w = compute(reg, events)
    state = load(STATE, {})
    last = state.get("last_cycle_at")
    resolved = {e["ref"] for e in events if e.get("type") == "outcome"}
    pending = []
    for e in events:
        if e.get("type") == "used" and e.get("outcome") == "pending" and e["id"] not in resolved:
            local = e.get("transcript") and Path(e["transcript"]).exists()
            age = (now() - parse(e["ts"])).days
            item = {"event": e["id"], "rule": e["rule"], "rule_text": reg["rules"].get(e["rule"], {}).get("text", ""),
                    "ts": e["ts"], "host": e.get("host"), "cited_in": e.get("context", "")}
            if local:
                item["next_user_message"] = next_user_text(e["transcript"], e.get("msg", ""), after_ts=e.get("ts"))
            elif not e.get("transcript"):
                item["note"] = "no transcript pointer: judge from the citation text and the note"
            elif age > 14:
                item["note"] = "older than 14 days and the transcript is not on this machine: neutral"
            else:
                continue  # another machine will judge it
            pending.append(item)
    review = [{"rule": rid, **reg["rules"][rid], "weight": s["w"], "harmful": s["harmful"],
               "helpful": s["helpful"]} for rid, s in w.items() if s["status"] == "review"]
    changed = []
    cutoff = parse(last).timestamp() if last else 0
    for root in learning_roots():
        if not root.exists():
            continue
        for p in root.rglob("LEARNINGS.md"):
            if SKIP_PARTS & set(p.parts):
                continue
            if p.stat().st_mtime > cutoff:
                changed.append(rel(p))
        for p in root.rglob("observations/*.md"):
            if p.name != "README.md" and not (SKIP_PARTS & set(p.parts)) and p.stat().st_mtime > cutoff:
                changed.append(rel(p))
    known_sources = sorted({r["source"] for r in reg["rules"].values() if r.get("source")})
    if MEMORY_DIR and MEMORY_DIR.exists():
        for p in sorted(MEMORY_DIR.glob("*.md")):
            r = rel(p)
            if p.name == MEMORY_INDEX or p.name.startswith(Path(MEMORY_INDEX).stem + ".") or p.stat().st_mtime <= cutoff:
                continue
            if p.name.startswith("feedback_") or memory_type(p) in RULE_MEMORY_TYPES or r in known_sources:
                changed.append(r)
    try:
        miner.scan(reg["rules"])
        meas = measurement(reg, w, miner.load_records())
    except Exception as e:
        meas = {"error": f"the measurement did not run: {e}"}
    cur = curation(reg, w, events, last, full=getattr(a, "full", False), meas=meas if "error" not in meas else None)
    health = run_health()
    base = {"at": iso(), "cycles": state.get("cycles", 0), "next_id": reg.get("next_id", 1), "last_cycle_at": last}
    save(base_path(), base)
    pkt = {"generated": iso(), "host": host(), "last_cycle_at": last, "cycle_no": state.get("cycles", 0) + 1,
           "base": base, "rule_count": len(reg["rules"]), "pending_outcomes": pending, "review_queue": review,
           "changed_sources_since_last_cycle": sorted(set(changed)), "known_sources": known_sources,
           "measurement": {k: v for k, v in meas.items() if k != "series"}, "curation": cur,
           "decisions_schema": DECISIONS_SCHEMA}
    if health is not None:
        pkt["health"] = health
    out = json.dumps(pkt, ensure_ascii=False, indent=1, default=str)
    if a.out:
        Path(a.out).write_text(out, encoding="utf-8"); print(a.out)
    else:
        print(out)


# ---------------------------------------------------------------- health (optional)
# If the health kit is configured, the cycle is its second, scheduler-independent runner:
# when the scheduler stops, the cycle still checks; when the cycle stops, the health kit's
# cognition check notices. They watch each other.

def run_health():
    if not HEALTH_SCRIPT:
        return None
    script = Path(HEALTH_SCRIPT).expanduser()
    if not script.exists():
        return {"error": f"health check not found: {script}"}
    import subprocess
    try:
        r = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True,
                           encoding="utf-8", errors="ignore", timeout=600)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"error": f"the health check did not run: {e}"}


def health_lines():
    """The last health state of every machine (state.<host>.json), stale ones marked."""
    if not HEALTH_SCRIPT or not HEALTH_STATE_DIR.exists():
        return []
    L = []
    for p in sorted(HEALTH_STATE_DIR.glob("state.*.json")):
        h = p.name[len("state."):-len(".json")]
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            at = dt.datetime.fromisoformat(s["last_run"])
            if at.tzinfo:
                at = at.astimezone().replace(tzinfo=None)
        except Exception:
            L.append(f"  {h}: unreadable state file")
            continue
        age = (dt.datetime.now() - at).total_seconds() / 3600
        checks = s.get("checks", {})

        def sev(c):
            return c.get("weight", c.get("sev", 1))
        bad = [n for n, c in checks.items() if c.get("ok") is False]
        okn = sum(1 for c in checks.values() if c.get("ok"))
        tot = sum(1 for c in checks.values() if c.get("ok") is not None)
        stale = f"   ! the check has not run for {age:.0f} hours" if age > HEALTH_STALE_HOURS else ""
        L.append(f"  {h}: {s.get('status', '?')} {okn}/{tot}  ({str(s['last_run'])[:16].replace('T', ' ')}){stale}")
        for n in sorted(bad, key=lambda n: -sev(checks[n])):
            L.append(f"    {'!' if sev(checks[n]) >= 2 else '·'} {n}: {short(checks[n].get('detail', ''), 90)}")
    return L


DECISIONS_SCHEMA = {
    "register": "[{skill, area, source, target, text, applies_when, origin_date, evidence, confirmations, still_valid, superseded_by}] "
                "new learned rules; evidence: owner_decision|human_correction|measured|convergence|agent_inferred",
    "confirm": "[{rule, note}] a new, independent confirmation of an existing rule",
    "outcomes": "[{event, rule, value: helpful|harmful|neutral, note}] judgements of pending uses",
    "reviews": "[{rule, decision: keep|refine|deprecate, note}] decisions on the review queue (refine: improve the text or scope, "
               "see the text/applies_when fields)",
    "questions": "[text] what to ask the owner (only if uncertain AND important)",
    "notes": "[text] short observations for the report",
    "signals": "[{rule, on, trigger, comply?, avoid?, violation?, enforce?}] signal pattern (regexes) for rules a machine can "
               "recognise; enforce only on a sure, command-level rule and only by the owner's decision (the PreToolUse hook "
               "then stops the form to avoid)",
    "curate": "[{op, ...}] curator operations, lossless: "
              "merge {rules:[...], into, note}: the others merge into `into` (retired with a superseded_by pointer, the text stays); "
              "promote {rule, scope: global|machine:<host>, text?, applies_when?, area?, evidence?, judge, note}: "
              "without text the rule itself becomes general; with text a new general rule worded at the level of the cause is born "
              "(generalizes pointer) and the original stays as its instance (instance_of); new text needs the independent judge's "
              "yes (judge: accept); "
              "link {rule, instance_of, note}: the rule is an instance of an existing general principle "
              "(instance_of may be \"@new:<rule>\" for a rule promoted with new text in the same file); "
              "rehome {rule, target, note}: a new home (the source text does not move); "
              "scope {rule, scope: local|global|machine:<host>, note}",
    "reflection": "text: 3 to 6 sentences at the end of the cycle: are we learning at the right pace and in the right way "
                  "(friction trend, transfer, rules without effect, intake versus effect), and what would we change in the way "
                  "we learn (a lesson about learning itself goes as a packet to the learning capability's observations/)",
    "lesson_packets": "[path] learning packets written in this cycle (a recurring error without a rule); the main session starts "
                      "a review for each",
}


def _curate_event(reg, rid, op, fields, note=""):
    for k, v in fields.items():
        reg["rules"][rid][k] = v
    append_event({"type": "curated", "rule": rid, "op": op, "note": note, "data": dict(fields)})


def apply_signals_and_curation(reg, dec, born, deprecated_now):
    """Signal patterns and curator operations. Nothing is deleted: retirement with a pointer,
    a new home with a pointer, the source text never moves."""
    done = Counter()

    def live(rid):
        return rid in reg["rules"]
    for s in dec.get("signals", []):
        rid = s.get("rule")
        if not live(rid):
            continue
        sig = {k: s[k] for k in ("on", "trigger", "comply", "avoid", "violation", "enforce") if s.get(k) not in (None, "")}
        try:
            for k in ("on", "trigger", "comply", "avoid", "violation"):
                if k in sig:
                    re.compile(sig[k])
        except re.error as e:
            print(f"signal pattern skipped ({rid}): bad regex: {e}", file=sys.stderr)
            continue
        _curate_event(reg, rid, "signals", {"signals": sig}, s.get("note", ""))
        done["signals"] += 1
    order = {"merge": 0, "promote": 1, "link": 2, "rehome": 3, "scope": 4}
    new_of = {}  # a rule generalised in this run -> the ID of the new general rule (for "@new:L-xxxx")
    for c in sorted(dec.get("curate", []), key=lambda c: order.get(c.get("op"), 9)):
        op = c.get("op")
        if isinstance(c.get("instance_of"), str) and c["instance_of"].startswith("@new:"):
            c = {**c, "instance_of": new_of.get(c["instance_of"][5:], "")}
        if op == "merge":
            into = c.get("into")
            if not live(into):
                print(f"merge skipped: the umbrella rule does not exist: {into}", file=sys.stderr)
                continue
            for rid in c.get("rules", []):
                if rid == into or not live(rid):
                    continue
                _curate_event(reg, rid, "merge", {"superseded_by": into}, c.get("note", ""))
                append_event({"type": "deprecated", "rule": rid, "note": f"merged into {into}. {c.get('note', '')}".strip()})
                append_event({"type": "confirm", "rule": into, "note": f"merge: {rid} learned the same"})
                deprecated_now.append(rid)
                done["merge"] += 1
        elif op == "promote":
            rid = c.get("rule")
            scope = c.get("scope") or "global"
            if not live(rid):
                continue
            if c.get("text"):
                if c.get("judge") != "accept":
                    print(f"promote skipped ({rid}): new text needs the independent judge's yes (judge: accept)", file=sys.stderr)
                    continue
                src = reg["rules"][rid]
                nid = alloc_id(reg, all_events())
                reg["next_id"] = max(reg.get("next_id", 1), rid_num(nid) + 1)
                reg["rules"][nid] = {"skill": "general", "area": c.get("area") or src.get("area"), "source": src.get("source"),
                                     "target": GENERAL_REL, "text": c["text"], "applies_when": c.get("applies_when"),
                                     "origin_date": dt.date.today().isoformat(), "evidence": c.get("evidence") or "convergence",
                                     "registered": iso(), "scope": scope, "generalizes": [rid]}
                save(REGISTRY, reg)
                append_event({"type": "born", "rule": nid, "note": f"generalisation of {rid}", "data": reg["rules"][nid]})
                _curate_event(reg, rid, "promote", {"instance_of": nid}, c.get("note", ""))
                born.append(nid)
                new_of[rid] = nid
            else:
                _curate_event(reg, rid, "promote", {"scope": scope}, c.get("note", ""))
            done["promote"] += 1
        elif op == "link":
            rid, gen = c.get("rule"), c.get("instance_of")
            if live(rid) and live(gen) and rid != gen:
                _curate_event(reg, rid, "link", {"instance_of": gen}, c.get("note", ""))
                g = reg["rules"][gen].get("generalizes") or []
                if rid not in g:
                    _curate_event(reg, gen, "link", {"generalizes": g + [rid]}, f"instance: {rid}")
                done["link"] += 1
        elif op == "rehome":
            rid = c.get("rule")
            if live(rid) and c.get("target"):
                _curate_event(reg, rid, "rehome", {"target": c["target"]}, c.get("note", ""))
                done["rehome"] += 1
        elif op == "scope":
            rid = c.get("rule")
            if live(rid) and c.get("scope"):
                _curate_event(reg, rid, "scope", {"scope": None if c["scope"] == "local" else c["scope"]}, c.get("note", ""))
                done["scope"] += 1
    if done:
        save(REGISTRY, reg)
    return dict(done)


def apply_measured_outcomes(reg, state):
    """Measured compliance (by the signal pattern) since birth, cumulative; if the cumulative count
    grew since the last cycle, one 'helpful' event per rule (measured evidence). The cumulative
    counts live in state.json (measured_seen)."""
    recs = miner.load_records()
    seen = state.setdefault("measured_seen", {})
    out = []
    for rid, r in reg["rules"].items():
        s = r.get("signals") or {}
        if not (s.get("comply") or s.get("avoid")):
            continue
        born = rule_born_day(r)
        mine = [x for x in recs if (not born or x["date"] >= born.isoformat()) and x.get("signals", {}).get(rid, {}).get("c")]
        c = sum(x["signals"][rid]["c"] for x in mine)
        if c > seen.get(rid, 0):
            ctx = sorted({x["context"] for x in mine})
            append_event({"type": "outcome", "rule": rid, "value": "helpful", "source": "measured",
                          "note": f"measured compliance since birth: {c}x (+{c - seen.get(rid, 0)}), in {len(ctx)} contexts "
                                  f"({', '.join(ctx[:4])})"})
            out.append({"rule": rid, "complied": c - seen.get(rid, 0), "contexts": ctx})
            seen[rid] = c
    return out


def cmd_apply(a):
    dec = json.loads(Path(a.decisions).read_text(encoding="utf-8"))
    reg = load_registry()
    state = load(STATE, {})
    base = load(base_path(), None)
    if base is not None and base.get("cycles", 0) != state.get("cycles", 0):
        print(f"STOPPED: another cycle wrote since the packet (cycle number {base.get('cycles', 0)} -> "
              f"{state.get('cycles', 0)}, last machine: {state.get('last_cycle_host', '?')}). Nothing was written. "
              "Run packet again and decide again from the new packet.", file=sys.stderr)
        try:
            if load(LEASE, {}).get("host") == host():
                LEASE.unlink()
        except Exception:
            pass
        try:
            base_path().unlink()
        except Exception:
            pass
        sys.exit(3)
    if not state.get("telemetry_since"):
        state["telemetry_since"] = iso()
    save(STATE, state)
    before = load(WEIGHTS, {}).get("rules", {})
    born, deprecated_now = [], []
    by_key = {(r.get("source"), r.get("text")): rid for rid, r in reg["rules"].items()}
    for item in dec.get("register", []):
        key = (item.get("source"), item["text"])
        if key in by_key:
            continue
        rid = alloc_id(reg, all_events())
        reg["next_id"] = max(reg.get("next_id", 1), rid_num(rid) + 1)
        reg["rules"][rid] = {k: item.get(k) for k in
                             ("skill", "area", "source", "target", "text", "applies_when", "origin_date", "evidence")}
        reg["rules"][rid]["registered"] = iso()
        by_key[key] = rid
        save(REGISTRY, reg)
        append_event({"type": "born", "rule": rid, "note": item.get("origin_date") or "", "data": reg["rules"][rid]})
        for _ in range(int(item.get("confirmations") or 0)):
            append_event({"type": "confirm", "rule": rid, "note": "inventory: later confirmation in the source"})
        if item.get("still_valid") is False:
            append_event({"type": "deprecated", "rule": rid, "note": item.get("superseded_by") or "no longer valid per the inventory"})
            deprecated_now.append(rid)
        born.append(rid)
    for c in dec.get("confirm", []):
        if c["rule"] in reg["rules"]:
            append_event({"type": "confirm", "rule": c["rule"], "note": c.get("note", "")})
    for o in dec.get("outcomes", []):
        if o.get("rule") in reg["rules"]:
            append_event({"type": "outcome", "rule": o["rule"], "ref": o.get("event"), "value": o["value"], "note": o.get("note", "")})
    for r in dec.get("reviews", []):
        rid = r["rule"]
        if rid not in reg["rules"]:
            continue
        if r["decision"] == "deprecate":
            append_event({"type": "deprecated", "rule": rid, "note": r.get("note", "")}); deprecated_now.append(rid)
        else:
            if r["decision"] == "refine":
                for k in ("text", "applies_when"):
                    if r.get(k):
                        reg["rules"][rid].setdefault("history", []).append({k: reg["rules"][rid].get(k), "until": iso()})
                        reg["rules"][rid][k] = r[k]
                save(REGISTRY, reg)
            ev = {"type": "reviewed", "rule": rid, "decision": r["decision"], "note": r.get("note", "")}
            if r["decision"] == "refine":
                ev["data"] = {k: reg["rules"][rid].get(k) for k in ("text", "applies_when")}
            append_event(ev)
    save(REGISTRY, reg)
    curated = apply_signals_and_curation(reg, dec, born, deprecated_now)
    if curated.get("signals"):
        try:
            miner.scan(reg["rules"], full=True)  # a new signal pattern: measure the past too, for a baseline
        except Exception as e:
            print(f"the re-measurement did not run: {e}", file=sys.stderr)
    state = load(STATE, {})
    measured = apply_measured_outcomes(reg, state)
    save(STATE, state)
    w = compute(reg)
    snapshot = summarize(reg, w)
    try:
        meas = measurement(reg, w, miner.load_records())
    except Exception as e:
        meas = {"error": str(e)}
    state = load(STATE, {})
    state["cycles"] = state.get("cycles", 0) + 1
    state["last_cycle_at"] = iso()
    state["last_cycle_host"] = host()
    hist = {"n": state["cycles"], "at": state["last_cycle_at"], "host": host(),
            "total": snapshot["active"], "mass": snapshot["mass"], "tiers": snapshot["tiers"]}
    if "error" not in meas:
        hist.update({"friction": meas["friction"]["friction_per100"], "errors100": meas["friction"]["errors_per100"],
                     "applied_share": meas["applied_share"], "measured_rules": len(meas["rules"]),
                     "ineffective": len(meas["ineffective"]), "curated": sum(curated.values())})
    if dec.get("reflection"):
        hist["reflection"] = dec["reflection"]
    state.setdefault("history", []).append(hist)
    save(STATE, state)
    save(WEIGHTS, {"computed": iso(), "rules": {k: {"w": v["w"], "status": v["status"]} for k, v in w.items()}})
    render(reg, w)
    text = report(reg, w, before, state, born=born, deprecated_now=deprecated_now,
                  outcomes=dec.get("outcomes", []), reviews=dec.get("reviews", []),
                  questions=dec.get("questions", []), notes=dec.get("notes", []),
                  meas=meas, curated=curated, measured=measured, reflection=dec.get("reflection"))
    log_cycle(state["cycles"], text)
    for p in (LEASE, base_path()):
        try:
            p.unlink()
        except Exception:
            pass
    print(text)


# ---------------------------------------------------------------- report

def summarize(reg, w):
    tiers = {name: 0 for _, name, _ in TIERS}
    extra = {"review": 0, "dormant": 0, "deprecated": 0}
    mass = 0.0
    for rid, s in w.items():
        if s["status"] in extra:
            extra[s["status"]] += 1
        else:
            tiers[tier(s["w"])[0]] += 1
            mass += s["w"]
    return {"tiers": tiers, **extra, "active": sum(tiers.values()), "mass": round(mass, 2)}


def spark(values):
    if not values:
        return ""
    chars = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    return "".join(chars[3 if hi - lo < 0.05 else int((v - lo) / (hi - lo) * 7)] for v in values)


def learning_block(reg, w, meas, state, curated=None, measured=None, reflection=None):
    """LEARNING RATE: the effect, not the intake. The main metric is friction (recurring errors
    per 100 tool calls)."""
    L = ["", "LEARNING RATE  (the effect, not the intake; source: the transcripts, miner.py)"]
    if not meas or "error" in meas:
        L.append(f"  the measurement did not run: {(meas or {}).get('error', 'no data')}")
        return L
    f, p = meas["friction"], meas["friction_prev"]
    trend = ""
    if f["friction_per100"] is not None and p["friction_per100"] is not None:
        d = f["friction_per100"] - p["friction_per100"]
        trend = "improving" if d < -0.05 else "worsening" if d > 0.05 else "flat"
    L.append(f"  Friction (7 days): {f['friction_per100']} recurring errors / 100 tool calls   "
             f"previous 7 days: {p['friction_per100']}   -> {trend}")
    L.append(f"    {f['tools']} tool calls, {f['sessions']} sessions, all errors {f['errors_per100']} / 100")
    ser = [round(100.0 * rec / tools, 2) for _, tools, rec in meas.get("series", []) if tools >= 20]
    if len(ser) > 2:
        L.append(f"    daily curve (28 days): {spark(ser)}")
    hist = [h.get("friction") for h in state.get("history", []) if h.get("friction") is not None]
    if len(hist) > 1:
        L.append(f"    per cycle: {spark(hist)}  {hist[0]} -> {hist[-1]}")
    L.append(f"  Intake: {meas['born_7d']} new rules in 7 days   Knowledge in use (30 days): "
             f"{meas['applied_30d']}/{meas['active']} ({100 * meas['applied_share']:.0f}%)")
    mr = meas["rules"]
    if mr:
        L.append(f"  Measured rules: {len(mr)} (with a signal pattern)   last 7 days:")
        for rid, s in sorted(mr.items(), key=lambda x: -(x[1]['last7']['situations'] + x[1]['last7']['violations']))[:8]:
            l7, ab = s["last7"], s["after_birth"]
            comp = (f"{l7['complied']}/{l7['complied'] + l7['missed']} followed" if (l7["complied"] + l7["missed"])
                    else f"{l7['situations']} situations")
            L.append(f"    {rid} {comp}, {l7['violations']} violations;  since birth {len(ab['contexts'])} contexts, "
                     f"first followed {ab['first_compliance'] or '-'}  {short(reg['rules'][rid]['text'], 50)}")
    if meas["ineffective"]:
        L.append(f"  Rules without effect (the error or the miss still comes after the rule): {', '.join(meas['ineffective'][:10])}")
    lc = meas.get("lesson_candidates", [])
    if lc:
        L.append(f"  Recurring errors without a rule (lesson candidates, 14 days): {len(lc)}")
        for x in lc[:4]:
            L.append(f"    {x['sessions']} sessions {x['count']}x  {short(x['signature'], 80)}")
    if measured:
        L.append("  Measured application in this cycle: " +
                 ", ".join(f"{m['rule']} {m['complied']}x/{len(m['contexts'])} ctx" for m in measured[:8]))
    if curated:
        L.append("  Curation in this cycle: " + ", ".join(f"{k} {v}" for k, v in sorted(curated.items())))
    if reflection:
        L.append("")
        L.append("REFLECTION ON LEARNING (caretaker)")
        for line in re.split(r"(?<=[.!?])\s+", reflection.strip()):
            if line:
                L.append(f"  {line}")
    return L


def report(reg, w, before=None, state=None, born=(), deprecated_now=(), outcomes=(), reviews=(), questions=(), notes=(),
           meas=None, curated=None, measured=None, reflection=None):
    before = before or {}
    state = state or load(STATE, {})
    sm = summarize(reg, w)
    n = state.get("cycles", 0)
    when = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    L.append(f"PAROS COGNITIVE CYCLE #{n}   {when}   machine: {host()}")
    L.append("=" * 64)
    t = sm["tiers"]
    L.append(f"Live knowledge: {sm['active']} rules, total weight {sm['mass']:.1f}")
    L.append(f"  █ root {t['root']:>3}   ▓ strong {t['strong']:>3}   ▒ growing {t['growing']:>3}   ░ seedling {t['seedling']:>3}")
    L.append(f"  ! review {sm['review']:>3}   · dormant {sm['dormant']:>3}   × retired {sm['deprecated']:>3}")
    hist = state.get("history", [])
    if len(hist) > 1:
        L.append(f"Growth (total weight per cycle): {spark([h['mass'] for h in hist])}  {hist[0]['mass']:.1f} -> {hist[-1]['mass']:.1f}")
    up = [r for r in w if r in before and w[r]["w"] > before[r]["w"] + 0.005]
    down = [r for r in w if r in before and w[r]["w"] < before[r]["w"] - 0.005]
    L.append("")
    L.append(f"This cycle: +{len(born)} new   ↑{len(up)} stronger   ↓{len(down)} weaker   "
             f"{len(list(reviews))} reviews closed   {len(list(deprecated_now))} retired")
    if meas is not None:
        L.extend(learning_block(reg, w, meas, state, curated, measured, reflection))
    L.append("")
    L.append("HEAT MAP  (row = capability, cell = rule, darker = stronger)")
    areas = {}
    for rid, r in reg["rules"].items():
        if w[rid]["status"] == "deprecated":
            continue
        areas.setdefault(r.get("area") or "Other", {}).setdefault(r.get("skill") or "?", []).append(rid)
    for area in sorted(areas, key=lambda k: -sum(len(v) for v in areas[k].values())):
        skills = areas[area]
        aw = [w[x]["w"] for v in skills.values() for x in v]
        L.append(f"{area}  ({len(aw)} rules, mean {sum(aw) / len(aw):.2f})")
        for sk in sorted(skills, key=lambda k: -sum(w[x]["w"] for x in skills[k])):
            ids = sorted(skills[sk], key=lambda x: -w[x]["w"])
            cells = "".join("!" if w[x]["status"] == "review" else "·" if w[x]["status"] == "dormant"
                            else tier(w[x]["w"])[1] for x in ids)
            more = ""
            if len(cells) > 30:
                cells, more = cells[:30], f" +{len(ids) - 30}"
            L.append(f"  {sk[:28]:<28} {cells}{more}")
    act = [r for r in w if w[r]["status"] == "active"]
    top = sorted(act, key=lambda r: -w[r]["w"])[:5]
    L.append("")
    L.append("Strongest rules:")
    for r in top:
        L.append(f"  {r} {w[r]['w']:.2f}  {short(reg['rules'][r]['text'])}")
    if born and len(born) <= 12:
        L.append("Born now:")
        for r in born:
            L.append(f"  {r} {w[r]['w']:.2f}  {short(reg['rules'][r]['text'])}")
    if outcomes:
        L.append("Live use judged:")
        for o in list(outcomes)[:10]:
            mark = {"helpful": "+ helpful", "harmful": "- harmful", "neutral": "= neutral"}.get(o["value"], o["value"])
            L.append(f"  {o['rule']} {mark}: {short(o.get('note', ''), 60)}")
    if up:
        L.append("Stronger: " + ", ".join(f"{r} {before[r]['w']:.2f}->{w[r]['w']:.2f}" for r in up[:8]))
    if down:
        L.append("Weaker:   " + ", ".join(f"{r} {before[r]['w']:.2f}->{w[r]['w']:.2f}" for r in down[:8]))
    rv = [r for r in w if w[r]["status"] == "review"]
    if rv:
        L.append("Waiting for review: " + ", ".join(rv[:10]))
    hl = health_lines()
    if hl:
        L.append("")
        L.append("PAROS HEALTH  (per machine; ! = weight 2 or 3, · = log level)")
        L.extend(hl)
    for q in questions:
        L.append(f"QUESTION FOR THE OWNER: {q}")
    for x in notes:
        L.append(f"Note: {x}")
    L.append("=" * 64)
    L.append("Marking during work: [L-xxxx] = this decision depended on a learned rule.")
    return "\n".join(L)


def short(s, n=70):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def log_cycle(n, text):
    if not CYCLES.exists():
        CYCLES.write_text(
            f"---\ntitle: CYCLES\ndate: {dt.date.today().isoformat()}\nstatus: active\n"
            "description: Append-only log of the PAROS cognitive cycle reports: per cycle the state of the "
            "weighted knowledge, the learning rate, its heat map, and the rules born, strengthened, weakened and retired.\n"
            f"id: {uuid.uuid4()}\ntags: [paros, learning, cognitive-cycle]\n---\n\n"
            "# Cognitive cycles\n\n> Append-only. Written by `cognition.py apply`.\n", encoding="utf-8")
    with CYCLES.open("a", encoding="utf-8") as f:
        f.write(f"\n## Cycle #{n} ({dt.date.today().isoformat()})\n\n```text\n{text}\n```\n")


def cmd_report(a):
    reg = load_registry()
    w = compute(reg)
    try:
        meas = measurement(reg, w, miner.load_records())
    except Exception as e:
        meas = {"error": str(e)}
    print(report(reg, w, load(WEIGHTS, {}).get("rules", {}), meas=meas))


def cmd_measure(a):
    """Read the transcripts (since the last read) and print the learning rate, without a cycle."""
    reg = load_registry()
    w = compute(reg)
    recs = miner.scan(reg["rules"], full=getattr(a, "full", False))
    meas = measurement(reg, w, miner.load_records())
    print(f"read: {len(recs)} new records ({host()})")
    print("\n".join(learning_block(reg, w, meas, load(STATE, {}))))
    if getattr(a, "json", False):
        print(json.dumps({k: v for k, v in meas.items() if k != "series"}, ensure_ascii=False, indent=1, default=str))


def cmd_show(a):
    """One rule in full (text, scope, source, links, weight)."""
    reg = load_registry()
    w = compute(reg)
    for rid in a.rules:
        r = reg["rules"].get(rid)
        if not r:
            print(f"{rid}: no such rule"); continue
        s = w.get(rid, {})
        print(f"{rid}  weight {s.get('w')}  status {s.get('status')}  scope {r.get('scope') or 'local'}")
        for k in ("text", "applies_when", "source", "target", "area", "evidence", "instance_of", "generalizes", "superseded_by"):
            if r.get(k):
                print(f"  {k}: {r[k]}")
        print()


def cmd_find(a):
    """Quick search among all learned rules (text, when, skill, area, source); hits by weight."""
    reg = load_registry()
    w = compute(reg)
    terms = [t.lower() for t in a.terms]
    hits = []
    for rid, r in reg["rules"].items():
        if w.get(rid, {}).get("status") == "deprecated":
            continue
        hay = " ".join(str(r.get(k) or "") for k in ("text", "applies_when", "skill", "area", "source")).lower()
        score = sum(hay.count(t) for t in terms)
        if score and all(t in hay for t in terms[:1]):
            hits.append((score, w[rid]["w"], rid))
    for score, wt, rid in sorted(hits, key=lambda x: (-x[0], -x[1]))[: a.limit]:
        r = reg["rules"][rid]
        print(f"{rid} {wt:.2f}  {short(r.get('applies_when'), 60)} | {short(r.get('text'), 140)}")
    if not hits:
        print("no hits")


# ---------------------------------------------------------------- render

def render(reg, w):
    by_target = {}
    for rid, r in reg["rules"].items():
        if r.get("target"):
            by_target.setdefault(r["target"], []).append(rid)
    memory_ids = {}
    for target, ids in by_target.items():
        if target.replace("\\", "/") == GENERAL_REL:
            continue  # the general rules file is rendered as a whole by render_general()
        p = (VAULT / target).resolve()
        if MEMORY_DIR and MEMORY_DIR in p.parents:
            # Memory files carry no block; the rule ID goes onto the file's index line.
            for rid in ids:
                memory_ids[p.name] = rid
            continue
        if not p.exists() or p.suffix != ".md":
            continue
        live = sorted([x for x in ids if w[x]["status"] in ("active", "review")], key=lambda x: -w[x]["w"])
        sleep = [x for x in ids if w[x]["status"] == "dormant"]
        lines = [f"{BEGIN} (generated: cognition.py render; do not edit by hand) -->",
                 "## Learned rules with weights (cognitive cycle)",
                 "",
                 "If a decision of yours depends on one of these, mark it in the answer like this: `[L-xxxx]`; "
                 "that is how the caretaker learns whether the rule helped. Weight 0..1: in a conflict the higher "
                 "one wins, a seedling (below 0.25) is only a suggestion. The rule text in the body above or in its "
                 "source is authoritative; this list is an index.",
                 ""]
        for x in live:
            r, s = reg["rules"][x], w[x]
            name, ch = tier(s["w"])
            flag = " (under review)" if s["status"] == "review" else ""
            when = f" When: {r['applies_when']}." if r.get("applies_when") else ""
            gen = f" (its general principle: `{r['instance_of']}`)" if r.get("instance_of") else ""
            glob = " (general, loaded in every session)" if is_global(r) else ""
            lines.append(f"- `{x}` {ch} {s['w']:.2f} {name}{flag}: {r['text']}{when}{gen}{glob}")
        if sleep:
            lines.append(f"- Dormant (not applied by default, but kept): {', '.join(sleep)}")
        lines.append(END)
        txt = read_raw(p)
        eol = eol_of(txt)
        block = eol.join(lines)
        new = splice_block(txt, block, eol)
        if new is None:
            print(f"render: skipped, the generated block markers are ambiguous: {target}", file=sys.stderr)
            continue
        if new != txt:
            write_raw(p, new)
    render_general(reg, w)
    idx = MEMORY_DIR / MEMORY_INDEX if MEMORY_DIR else None
    if memory_ids and idx and idx.exists():
        raw = read_raw(idx)
        eol = eol_of(raw)
        out = []
        for line in raw.splitlines():
            m = re.match(r"^- (`L-\d{4}` )?(\[.*?\]\(([^)]+)\).*)$", line)
            if m and m.group(3) in memory_ids:
                line = f"- `{memory_ids[m.group(3)]}` {m.group(2)}"
            out.append(line)
        new = eol.join(out) + eol
        if new != raw:
            write_raw(idx, new)


def render_general(reg, w):
    """The generated file of the general rules (scope global or machine:<host>). The vault's entry
    file imports it, so it loads in every session. The rule moves to its cause: a tool, the
    environment, a way of working. Written only when there is a general rule or the file exists."""
    old = read_raw(GENERAL) if GENERAL.exists() else ""
    # A rule that lives in memory already loads in every session through the memory index:
    # it is not repeated here (token thrift).
    live = [rid for rid, r in reg["rules"].items() if is_global(r) and w.get(rid, {}).get("status") in ("active", "review")
            and target_kind(r.get("target")) != "memory"]
    if not live and not old:
        return
    m = re.search(r"(?m)^id: ([0-9a-f-]{36})", old)
    fid = m.group(1) if m else str(uuid.uuid4())
    d = re.search(r"(?m)^date: (\S+)", old)
    groups = {}
    for rid in live:
        sc = reg["rules"][rid].get("scope")
        groups.setdefault("Everywhere" if sc == "global" else f"Only on this machine: {sc.split(':', 1)[1]}", []).append(rid)
    L = ["---", f"title: {GENERAL.stem}", f"date: {d.group(1) if d else dt.date.today().isoformat()}", "status: active",
         "description: The general learned rules of PAROS (generated by cognition.py render): the tool, environment and "
         "way-of-working rules that apply in every session; the vault's entry file imports this file. The curator places a "
         "rule here when its cause is not tied to one task.",
         f"id: {fid}", "tags: [paros, learning, general-rules, generated]", "---", "",
         "# General learned rules", "",
         "> Generated (`cognition.py render`), do not edit by hand. The rule moves to its cause: what is about a tool, a "
         "machine or a way of working lives here, because it is needed everywhere (rules that live in memory are in the "
         "memory index and are not repeated here). One line per rule: when, and what to do. Full text: "
         "`python cognition.py show L-xxxx`; search all learned rules: `python cognition.py find <words>`. "
         "If a decision of yours depends on one of these, mark it: `[L-xxxx]`.", ""]
    if not live:
        L.append("_No general rule yet; the curator fills this in._")
    for g in sorted(groups, key=lambda k: (k != "Everywhere", k)):
        L += [f"## {g}", ""]
        for rid in sorted(groups[g], key=lambda x: -w[x]["w"]):
            r = reg["rules"][rid]
            txt = r.get("text") or ""
            when = (f"When {short(r['applies_when'].rstrip('.'), 80)}: "
                    if r.get("applies_when") and not re.match(r"(?i)^(when|if)\b", txt) else "")
            L.append(f"- `{rid}` {when}{short(txt, 200)}")
        L.append("")
    eol = eol_of(old) if old else "\n"
    new = eol.join(L)
    if new != old:
        GENERAL.parent.mkdir(parents=True, exist_ok=True)
        write_raw(GENERAL, new)


# A marker counts only at the start of its own line (a marker quoted in text or backticks does not).
BEGIN_LINE = re.compile(r"(?m)^" + re.escape(BEGIN) + r"\b[^\r\n]*(?=\r?$)")
END_LINE = re.compile(r"(?m)^" + re.escape(END) + r"[ \t]*(?=\r?$)")
BLOCK_RE = re.compile(r"(?ms)^" + re.escape(BEGIN) + r"\b[^\r\n]*(?=\r?$).*?^" + re.escape(END) + r"[ \t]*(?=\r?$)")


def read_raw(p):
    """Read without newline translation, so the write can keep the original line ending (CRLF or LF)."""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write_raw(p, txt):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(txt)


def eol_of(txt):
    crlf = txt.count("\r\n")
    return "\r\n" if crlf and crlf * 2 >= txt.count("\n") else "\n"


def splice_block(txt, block, eol):
    """Replace or append the generated block. None if the markers are ambiguous (then nothing is written).

    Only a marker at the start of its own line counts; the BEGIN and END counts must match, and every
    block must hold exactly one `## ` heading (its own generated heading). With several intact blocks,
    each is replaced."""
    nb, ne = len(BEGIN_LINE.findall(txt)), len(END_LINE.findall(txt))
    if nb == 0 and ne == 0:
        return txt.rstrip("\r\n") + eol + eol + block + eol
    blocks = BLOCK_RE.findall(txt)
    if nb != ne or len(blocks) != nb:
        return None
    if any(len(re.findall(r"(?m)^## ", b)) != 1 for b in blocks):
        return None
    return BLOCK_RE.sub(lambda m: block, txt)


def cmd_render(a):
    reg = load_registry()
    render(reg, compute(reg))
    print("render done")


def cmd_backfill(a):
    """Once per machine: a `data` event for every rule that has none yet, into this machine's log."""
    events = all_events()
    reg = load_registry(events)
    have = {e.get("rule") for e in events if e.get("data") and e.get("type") in ("born", "data")}
    n = 0
    for rid, r in sorted(reg["rules"].items()):
        if rid in have:
            continue
        append_event({"type": "data", "rule": rid, "data": {k: r.get(k) for k in RULE_FIELDS if r.get(k) is not None}})
        n += 1
    save(REGISTRY, reg)
    lo, hi = id_block()
    print(f"backfill: data of {n} rules in the event log; registry: {len(reg['rules'])} rules, next_id {reg['next_id']}; "
          f"ID range of {host()}: L-{lo:04d}..L-{hi:04d}")


def main():
    ap = argparse.ArgumentParser(description="PAROS cognitive cycle")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("due"); p.add_argument("--hook", action="store_true"); p.add_argument("--hours", type=float, default=DUE_HOURS)
    sp.add_parser("stop-hook")
    sp.add_parser("pretool-hook")
    p = sp.add_parser("used"); p.add_argument("rule"); p.add_argument("--outcome", default="pending",
                                                                       choices=["helpful", "harmful", "neutral", "pending"]); p.add_argument("--note")
    p = sp.add_parser("packet"); p.add_argument("--out"); p.add_argument("--full", action="store_true",
                                                                          help="curator: the whole body of rules, not one batch")
    p = sp.add_parser("apply"); p.add_argument("decisions")
    p = sp.add_parser("measure"); p.add_argument("--full", action="store_true"); p.add_argument("--json", action="store_true")
    sp.add_parser("report")
    sp.add_parser("render")
    p = sp.add_parser("show"); p.add_argument("rules", nargs="+")
    p = sp.add_parser("find"); p.add_argument("terms", nargs="+"); p.add_argument("--limit", type=int, default=12)
    sp.add_parser("backfill")
    a = ap.parse_args()
    fn = {"due": cmd_due, "stop-hook": cmd_stop_hook, "pretool-hook": cmd_pretool_hook, "used": cmd_used,
          "packet": cmd_packet, "apply": cmd_apply, "measure": cmd_measure, "report": cmd_report, "render": cmd_render,
          "show": cmd_show, "find": cmd_find, "backfill": cmd_backfill}[a.cmd]
    if a.cmd in ("due", "stop-hook", "pretool-hook"):
        try:
            fn(a)
        except Exception:
            pass  # a hook must never block the work; the health check watches the cycle
        return
    fn(a)


if __name__ == "__main__":
    main()
