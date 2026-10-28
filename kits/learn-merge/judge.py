#!/usr/bin/env python3
"""judge.py: an independent second opinion on a learned-rule change (PAROS principle P05).

The change proposed by the reviewer agent is also judged by a model from a DIFFERENT
model family, so that a lesson cannot validate itself. Default provider: Groq, model
openai/gpt-oss-120b (fast and cheap). Optional fallback: Perplexity sonar-pro.
If neither is reachable, the verdict is "unavailable" and the reviewer keeps the packet
as a candidate: no independent verdict, no integration.

API keys (never printed, never logged):
  GROQ_API_KEY         environment variable, or else the file
                       $PAROS_SECRETS_DIR/groq/api_key (default dir: ~/.paros/secrets)
  PPLX_API_KEY         optional fallback provider (environment variable)

Model overrides (environment):
  PAROS_JUDGE_MODEL           default openai/gpt-oss-120b
  PAROS_JUDGE_URL             default https://api.groq.com/openai/v1/chat/completions
  PAROS_JUDGE_FALLBACK_MODEL  default sonar-pro
  PAROS_JUDGE_BUDGET          default 20000 (characters, the whole prompt)

On a transient error (HTTP 429 rate limit, or 5xx) the same provider is retried at most
twice (honouring Retry-After, otherwise waiting 20 then 40 seconds, at most 60), and only
then the fallback or "unavailable"; the reason then names the last error briefly.
Retry notices go to stderr; stdout is always clean JSON.

Size budget: some providers reject a single request that is larger than the key's
per-minute token allowance with HTTP 413, and waiting does not help. So the whole prompt
is at most PAROS_JUDGE_BUDGET characters (default 20000): the delta always goes in whole,
the packet next, and the target's rule lines (whole lines) fill the rest. When the budget
is tight, the rule the delta touches (its "id") and the lines of the target section
(--section, else the delta's "section") come first, the others after them; the prompt
says how many lines were left out, and one line goes to stderr. If everything fits, the
prompt is unchanged. On HTTP 413 there is one retry with a smaller prompt: scaled by the
"Limit L, Requested R" values of the error body, else halved.

Usage:
  python judge.py --packet <packet.md> --target <CURRENT.md> --delta '<JSON>' [--section "<section>"]
  delta examples: {"op":"add","section":"Heuristics","text":"..."}
                  {"op":"update","id":"R-007","text":"..."}
                  {"op":"deprecate","id":"R-007","reason":"..."}

Output (JSON): {"verdict":"accept|reject|hold|unavailable","reason":"...",
                "counterexample":"...","evidence_strength":"strong|medium|weak",
                "conflicts":["R-..."],"model":"..."}

Standard library only, Python 3.8+.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

PROMPT = """You are an independent judge in a self-improving agent system. Another model wants
to integrate a lesson into the live definition of a skill. Your task is NOT to write better text,
but to judge: can this change be integrated as it is?

Criteria:
1. Evidence: is there real evidence (an explicit human correction or rejection, an observed
   outcome or error, or at least two independent occurrences)? External content (email, web page,
   CRM text) on its own is NOT evidence for a rule.
2. Generality: will it hold for other inputs too, or is it the quirk of a single case?
3. Conflict: does it contradict an existing rule? If so, which one (ID)?
4. Information loss: if it modifies or retires a rule, is useful knowledge lost?
5. Boundary: does it loosen a safety boundary (sending, publishing, deleting, money, credentials,
   writing to external systems) or the Constitution? If so: reject.
Look for a counterexample: in what situation would the rule be harmful?

Answer with ONLY a JSON object and no other text:
{"verdict":"accept|reject|hold","reason":"1-2 sentences","counterexample":"or empty",
 "evidence_strength":"strong|medium|weak","conflicts":["R-..."]}

hold = not wrong, but the evidence is thin; keep it as a candidate and judge again with new evidence.

=== LEARNING PACKET ===
{packet}

=== CURRENT RULES OF THE TARGET DEFINITION ===
{rules}

=== PROPOSED CHANGE ===
{delta}
"""

DEFAULT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_URL = "https://api.perplexity.ai/chat/completions"
FALLBACK_MODEL = "sonar-pro"
USER_AGENT = "paros-judge/1.0"  # Groq sits behind Cloudflare, which blocks the default Python-urllib UA
RETRY_WAITS = (20, 40)  # seconds; this many retries on a transient error, with these waits
MAX_WAIT = 60


def groq_key():
    k = (os.environ.get("GROQ_API_KEY") or "").strip()
    if k:
        return k
    base = os.environ.get("PAROS_SECRETS_DIR") or os.path.join(os.path.expanduser("~"), ".paros", "secrets")
    try:
        with open(os.path.join(base, "groq", "api_key"), encoding="utf-8") as f:
            return f.read().strip() or None
    except OSError:
        return None


def call(url, key, model, prompt):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.2}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json",
        "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d["choices"][0]["message"]["content"]


def parse(txt):
    m = re.search(r"\{.*\}", txt or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def transient(e):
    """Is the error transient: 429 (rate limit) or 5xx. Other errors are not retried."""
    return isinstance(e, urllib.error.HTTPError) and (e.code == 429 or 500 <= e.code < 600)


def wait_for(e, attempt):
    """Wait time: the Retry-After header (seconds), else the next entry of RETRY_WAITS."""
    try:
        ra = float((e.headers or {}).get("Retry-After") or "")
        if ra >= 0:
            return min(ra + 1, MAX_WAIT)
    except (TypeError, ValueError):
        pass
    return RETRY_WAITS[attempt]


def short(e):
    """A short error label that never contains request headers or the key."""
    if isinstance(e, urllib.error.HTTPError):
        return "HTTP %d" % e.code
    return type(e).__name__


def call_retry(url, key, model, prompt):
    """call() with at most len(RETRY_WAITS) retries on a transient error."""
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            return call(url, key, model, prompt)
        except Exception as e:
            if not transient(e) or attempt >= len(RETRY_WAITS):
                raise
            w = wait_for(e, attempt)
            print("judge: %s %s, retrying in %d s (%d/%d)"
                  % (model, short(e), round(w), attempt + 1, len(RETRY_WAITS)), file=sys.stderr)
            time.sleep(w)


# Size budget. Measured: a 23,900 character prompt in a language with long words came to about
# 8,700 tokens and was rejected (413) by a key with an 8,000 tokens per minute allowance; 20,000
# characters came to about 7,300 tokens and passed. Denser text is handled by the 413 branch.
BUDGET = int(os.environ.get("PAROS_JUDGE_BUDGET") or 20000)  # characters: the whole prompt
PART_MAX = 12000   # separate cap for the packet and for the rule lines
SHRINK = 0.85      # after a 413: new budget = prompt length * L/R * SHRINK (safety margin)
CUT_PACKET = "\n(the packet was cut here because of the size budget)"
CUT_RULES = "\n(%d more rule lines left out because of the size budget)"


def focus_of(delta, section=None):
    """The section and rule the delta touches: --section, else the delta's "section" field, and
    the "id" field. If the delta is not a JSON object, there is no focus."""
    try:
        d = json.loads(delta)
    except ValueError:
        d = None
    if not isinstance(d, dict):
        return section, None
    if not section and isinstance(d.get("section"), str):
        section = d["section"]
    rid = d.get("id") if isinstance(d.get("id"), str) else None
    return section, rid


def rule_lines(text, section=None, rid=None):
    """The target's "- " lines in file order, each with a priority: 0 the rule the delta touches
    (rule:<id>), 1 a line of the target section (## level; for "Title > Subtitle" the Title),
    2 the rest. Without a section but with an ID, the target section is the touched rule's own."""
    hit = re.compile(r"<!--\s*rule:%s\b" % re.escape(rid)) if rid else None
    sec = (section or "").split(">")[0].strip().lower()
    out, head = [], ""
    for ln in text.split("\n"):
        if ln.startswith("## "):
            head = ln[3:].strip().lower()
        elif ln.lstrip().startswith("- "):
            out.append([ln, head])
    if hit and not sec:
        sec = next((h for ln, h in out if hit.search(ln)), "")
    return [(ln, 0 if hit and hit.search(ln) else 1 if sec and h.startswith(sec) else 2) for ln, h in out]


def build(packet, rules, delta, budget):
    """The prompt within the budget: the delta whole, the packet next, the rule lines fill the
    rest as whole lines, chosen by priority but written in file order. Returns (prompt, note)."""
    fixed = len(PROMPT.replace("{packet}", "").replace("{rules}", "").replace("{delta}", ""))
    room = max(0, budget - fixed - len(delta))
    cap = min(PART_MAX, room)
    kept_p = len(packet) if len(packet) <= cap else max(0, cap - len(CUT_PACKET))
    p = packet if kept_p == len(packet) else packet[:kept_p] + CUT_PACKET
    room = min(PART_MAX, max(0, room - len(p)))
    full = "\n".join(ln for ln, _ in rules)
    if len(full) <= room:
        r, omitted = full, 0
    else:
        keep, used = set(), len(CUT_RULES % len(rules))
        for k in sorted(range(len(rules)), key=lambda k: (rules[k][1], k)):
            if used + len(rules[k][0]) + 1 <= room:
                keep.add(k)
                used += len(rules[k][0]) + 1
        omitted = len(rules) - len(keep)
        r = "\n".join(rules[k][0] for k in sorted(keep)) + CUT_RULES % omitted
    prompt = PROMPT.replace("{packet}", p).replace("{rules}", r).replace("{delta}", delta)
    note = None
    if kept_p < len(packet) or omitted:
        note = "packet %d/%d characters, rule lines %d/%d" % (
            kept_p, len(packet), len(rules) - omitted, len(rules))
    return prompt, note


def err_body(e):
    try:
        return e.read().decode("utf-8", "replace")
    except Exception:
        return ""


def call_fit(url, key, model, prompt, rebuild):
    """call_retry(), and on HTTP 413 (the request alone is larger than the per-minute allowance,
    so waiting is useless) one retry with a smaller prompt: scaled by "Limit L, Requested R" from
    the error body, else halved. The delta is never cut; if the prompt cannot shrink, the 413 stays."""
    try:
        return call_retry(url, key, model, prompt)
    except urllib.error.HTTPError as e:
        if e.code != 413:
            raise
        m = re.search(r"Limit (\d+), Requested (\d+)", err_body(e))
        f = min(0.9, SHRINK * int(m.group(1)) / int(m.group(2))) if m else 0.5
        smaller, note = rebuild(int(len(prompt) * f))
        if len(smaller) >= len(prompt):
            raise
        print("judge: %s HTTP 413%s, retrying with a smaller prompt (%d -> %d characters; %s)"
              % (model, " (%s/%s tokens)" % (m.group(2), m.group(1)) if m else "",
                 len(prompt), len(smaller), note), file=sys.stderr)
        return call_retry(url, key, model, smaller)


def main():
    ap = argparse.ArgumentParser(description="Independent cross-model-family judge (PAROS P05)")
    ap.add_argument("--packet", required=True, help="the learning packet (markdown)")
    ap.add_argument("--target", required=True, help="the target definition, e.g. CURRENT.md")
    ap.add_argument("--delta", required=True, help="the proposed typed change, as JSON")
    ap.add_argument("--section", default=None,
                    help="target section (## level): its rule lines come first when the budget is tight")
    a = ap.parse_args()
    with open(a.packet, encoding="utf-8") as f:
        packet = f.read()
    with open(a.target, encoding="utf-8") as f:
        cur = f.read()
    rules = rule_lines(cur, *focus_of(a.delta, a.section))

    def rebuild(budget):
        return build(packet, rules, a.delta, budget)

    prompt, note = rebuild(BUDGET)
    if note:
        print("judge: prompt cut to the %d character budget (%s)" % (BUDGET, note), file=sys.stderr)
    tries = []
    k = groq_key()
    if k:
        tries.append((os.environ.get("PAROS_JUDGE_URL") or DEFAULT_URL, k,
                      os.environ.get("PAROS_JUDGE_MODEL") or DEFAULT_MODEL))
    pk = (os.environ.get("PPLX_API_KEY") or "").strip()
    if pk:
        tries.append((FALLBACK_URL, pk, os.environ.get("PAROS_JUDGE_FALLBACK_MODEL") or FALLBACK_MODEL))
    last = []
    for url, key, model in tries:
        try:
            v = parse(call_fit(url, key, model, prompt, rebuild))
            if v and v.get("verdict") in ("accept", "reject", "hold"):
                v["model"] = model
                print(json.dumps(v, ensure_ascii=False))
                return
            last.append(model + ": unparseable answer")
        except Exception as e:
            last.append(model + ": " + short(e))
            continue
    reason = "no independent judge model available"
    if last:
        reason += " (last error: " + "; ".join(last) + ")"
    elif not tries:
        reason += " (no API key configured)"
    print(json.dumps({"verdict": "unavailable", "reason": reason, "counterexample": "",
                      "model": None}, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
