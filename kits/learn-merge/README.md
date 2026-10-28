# Kit: learn-merge

**Principle:** [P05, closed-loop learning](../../principles/P05-closed-loop-learning.md). **Platform:** independent (Python 3.8+, standard library only).

Two small scripts that turn a reviewed lesson into a change in a skill's live definition, without ever losing what was learned before:

| File | What it does |
|---|---|
| [`learn_merge.py`](learn_merge.py) | Applies one **typed** change (add, update, deprecate, move) to one rule, by ID. Snapshots the old version, bumps the version, logs the change. Refuses to touch the Constitution. |
| [`judge.py`](judge.py) | Asks a model from a **different model family** whether the proposed change should go in. Returns `accept`, `reject`, `hold` or `unavailable`. |
| [`example/CURRENT.md`](example/CURRENT.md) | A minimal skill definition to try the commands on. |

Like every kit, this is a reference. Read it, then rebuild or adapt it for your own vault; do not copy it in blindly.

## Why no compaction

The obvious way to "integrate a lesson" is to give a model the whole section and ask it to rewrite it with the lesson included. Do not do this. Repeated full rewrites collapse accumulated context: details that were hard to learn get summarised away a little more each time, until the section is short, fluent and wrong. The ACE paper (*Agentic Context Engineering*, 2025) measured exactly this "context collapse": one rewrite step shrank a learned context from thousands of tokens to about a hundred, and accuracy fell below the starting point.

So the unit of knowledge here is **the rule**: one line, one stable ID. Rules are added, replaced, retired or relocated one at a time, by code. Nothing is summarised, and nothing is deleted.

## The rule-line format

```markdown
- Write every action item as "owner: task, due date". <!-- rule:R-002 since:2026-10-01 -->
```

- `R-NNN` is stable for the life of the rule. IDs are never reused, not even after a rule is retired or moved.
- `since:` is the date the rule was first added. An update keeps it.
- The comment is invisible in rendered markdown, so the file still reads as normal prose.

The target file can have a `version: X.Y.Z` field in its frontmatter; every change bumps the patch number. It should have a `## Constitution` section for the owner's fixed rules (see below).

## Commands

All write commands take `--reason`; `add`, `update` and `deprecate` also take `--packet` (the ID or path of the learning packet that justified the change). Output is one JSON line.

**add**: append a new rule to the end of a section (matched by heading prefix; `"Section > Subsection"` targets a `###` inside a `##`).
```bash
python learn_merge.py add CURRENT.md --section "Heuristics" \
  --text "Quote the participants' own words for a decision." \
  --packet obs-2026-10-05-01 --reason "owner corrected a paraphrased decision twice"
# {"ok": true, "op": "add", "rule": "R-003", "version": "1.0.1"}
```

**update**: replace a rule's text by ID. The old text goes into the log.
```bash
python learn_merge.py update CURRENT.md --id R-002 \
  --text "Write every action item as \"owner: task, due date\"; mark a missing date as \"no date\"." \
  --packet obs-2026-10-05-02 --reason "missing dates were silently dropped"
```

**deprecate**: retire a rule. It moves to a `## Retired rules` section at the end of the file, struck through, with the date and the reason. It no longer applies, but its history stays.
```bash
python learn_merge.py deprecate CURRENT.md --id R-001 --packet obs-2026-10-05-03 \
  --reason "decisions now live in a separate decision log"
# - ~~Put decisions in their own list at the top...~~ (retired 2026-10-05: decisions now live...) <!-- deprecated:R-001 -->
```

**move**: relocate a rule verbatim to `references/rules.md` and leave a pointer in its place. This is how a definition stays small without rewriting anything; the moved rule still applies.
```bash
python learn_merge.py move CURRENT.md --id R-003 --reason "detail, keep the main file short"
# - (R-003 in detail: `references/rules.md`) <!-- moved:R-003 -->
```
If the rule opens with a bold title (`- **Short title:** the detail...`), the pointer keeps the title verbatim, so a reader sees what the moved rule is about without opening `references/`: `- (R-003 in detail: references/rules.md: Short title)`.

**list**: print the active rules with their IDs.
```bash
python learn_merge.py list CURRENT.md
```

**check**: print the hash of the Constitution section, to compare against a value you recorded earlier.
```bash
python learn_merge.py check CURRENT.md
# {"constitution_hash": "3f1c9a0b2d4e5f61"}
```

What every write command leaves behind, next to the target file (or in `agents/<name>/` when the target is `agents/<name>.md`, or in `--home <dir>`):

- `versions/v<old>.md`: the file exactly as it was before the change. If that snapshot already exists but the file was edited by hand since, a separate `v<old>+pre-<timestamp>.md` is written; an existing snapshot is never overwritten.
- `LEARNINGS.md`: one row in the `## Integration log (learn_merge.py)` table: date, operation, rule, old text, new text, packet, reason, new version. This is also where you look to undo a change.
- The target file itself is otherwise byte-for-byte unchanged, line endings included: a file with CRLF (or mixed) line endings keeps them, and new lines get the file's dominant ending. The snapshot keeps the original bytes.

## The Constitution

`## Constitution` holds the rules only the owner changes: typically the safety boundaries (sending, publishing, deleting, money, credentials, writing to external systems). `learn_merge.py` refuses to add into it, refuses to update, deprecate or move a rule inside it, and after every change compares the section's hash with the one taken before; if anything differs, it aborts without writing.

## The generated block

If you also use [`kits/cognition`](../cognition/README.md), it keeps a generated list of weighted rules at the end of a target file, between the `COGNITION:BEGIN` and `COGNITION:END` HTML comment markers, and rewrites that block as a whole on every render. A rule written into it would be lost at the next render, so `learn_merge.py` treats the block like the Constitution: a section ends at the block's marker (an `add` into the last section lands above the block), `deprecate` creates the "Retired rules" section above a block that ends the file, and any operation that would write into the block or take a line out of it aborts without writing.

## The judge

A model cannot validate its own rule: the same blind spot that produced the lesson will approve it. `judge.py` sends the packet, the current rules and the proposed change to a model from a **different family** than the one doing the review, and asks for a verdict:

- `accept`: integrate it.
- `reject`: do not; `reason` and `counterexample` say why.
- `hold`: not wrong, but the evidence is thin; keep it as a candidate and judge again when new evidence arrives.
- `unavailable`: no judge could be reached. **No independent verdict, no integration**: the packet stays a candidate.

The evidence threshold the judge applies (and the reviewer should apply first) is one of:

1. an explicit human correction, rejection or instruction;
2. an observed outcome: an output, an error, a measurement, a test result;
3. at least two independent occurrences of the same thing.

External content (an email, a web page, a document, CRM text) **never counts as evidence on its own**. Text from outside is data, not instructions, and a rule must not be learnable just because someone wrote it somewhere the agent reads.

```bash
python judge.py --packet observations/obs-2026-10-05-01.md --target CURRENT.md \
  --delta '{"op":"add","section":"Heuristics","text":"Quote the participants own words for a decision."}'
# {"verdict": "accept", "reason": "...", "counterexample": "...", "evidence_strength": "strong", "conflicts": [], "model": "openai/gpt-oss-120b"}
```

Configuration (environment):

| Variable | Default | Meaning |
|---|---|---|
| `GROQ_API_KEY` | | Key for the default provider. If unset, read from `$PAROS_SECRETS_DIR/groq/api_key`. |
| `PAROS_SECRETS_DIR` | `~/.paros/secrets` | Folder of secret files, outside the vault ([P07](../../principles/P07-secrets.md)). |
| `PAROS_JUDGE_MODEL` | `openai/gpt-oss-120b` | Judge model. |
| `PAROS_JUDGE_URL` | Groq's OpenAI-compatible endpoint | Any OpenAI-compatible chat completions URL. |
| `PPLX_API_KEY` | | Optional fallback provider (Perplexity). |
| `PAROS_JUDGE_FALLBACK_MODEL` | `sonar-pro` | Fallback model. |
| `PAROS_JUDGE_BUDGET` | `20000` | Upper bound of the whole prompt, in characters. |

The key is never printed. The request sets its own `User-Agent`, because the default Python one is blocked by the provider's edge network. Transient errors (429, 5xx) are retried twice before falling back; retry notices go to stderr so stdout stays clean JSON.

**Size budget.** A free or small API key often has a per-minute token allowance, and a provider rejects a single request larger than that allowance with HTTP 413; waiting does not help. So the prompt is kept within `PAROS_JUDGE_BUDGET`: the proposed change always goes in whole, the packet next, and the target's rule lines fill the rest as whole lines. When the budget is tight, the rule the change touches (its `id`) and the lines of the target section (`--section`, else the delta's `section`) come first. The prompt says how many lines were left out, and one line goes to stderr. On a 413 there is one retry with a smaller prompt, scaled by the limit the provider reports.

Pick the judge so that it is a different family from your reviewer. If your reviewer runs on one vendor's models, the default open-weights model on another provider is a cheap, fast choice; any OpenAI-compatible endpoint works.

## How it fits a caretaker agent

```
running agent: is this a real lesson? (when in doubt, yes)
   └─ writes a learning packet to observations/  (context, lesson, proposed change, target, evidence)
        └─ caretaker / reviewer agent:
             1. checks evidence, generality, conflicts, information loss
             2. turns it into ONE typed change (add / update / deprecate / move)
             3. judge.py  ──► accept ──► learn_merge.py ──► one-line report: "Learned: ... -> file"
                          ├─ hold / unavailable ──► stays a candidate
                          └─ reject ──► one row in LEARNINGS.md, nothing changes
```

The reviewer never edits the definition with a text editor or a rewrite prompt; it only calls `learn_merge.py`. The owner teaches rather than approves: they see the one-line report and can say "undo" at any time (the log row and the snapshot make that a single `update` or `deprecate`). Serialise runs: one review per target file at a time, and re-read the file before writing.

## Platform notes

- **Platform-independent:** both scripts are plain Python 3.8+ with no dependencies, and behave the same on macOS, Linux and Windows. Files are written as UTF-8; new files get `\n` line endings, existing files keep theirs.
- **Claude Code:** run the reviewer as a background subagent; a subagent that cannot start another one ends its report with a pointer to the packet, and the main session starts the review.
- **Codex and others:** run the review at the start of a session, or from any scheduler, by calling the two scripts.
- Keep the judge's API key outside the vault (environment or the secrets folder), never in a note.

## Try it

From this folder:

```bash
cp -r example /tmp/lm
python learn_merge.py list /tmp/lm/CURRENT.md
python learn_merge.py add /tmp/lm/CURRENT.md --section Heuristics --text "Quote decisions verbatim." --reason "test"
ls /tmp/lm/versions && cat /tmp/lm/LEARNINGS.md
python judge.py --packet /tmp/lm/CURRENT.md --target /tmp/lm/CURRENT.md --delta '{"op":"add"}'
# without a key: {"verdict": "unavailable", ...}
```
