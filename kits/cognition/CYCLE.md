# The cognitive cycle: procedure for the caretaker agent

This is what your caretaker agent (the agent that looks after the whole system's learning, whatever you call it) does when it is started in **cycle mode**. The hook in [`README.md`](README.md) starts it in the background every few hours, inside a normal session, so it runs on the subscription. You can also start it by hand: "Mode: cycle".

A single lesson is reviewed when it is born (P05, the learning packet and the independent judge). The cycle looks at the whole body of learned rules at once: it measures whether learning works, weights, judges whether the rules that were used actually helped, reviews the ones that hurt, takes in new lessons, detects lessons nobody wrote down, curates where each rule lives, reflects, and reports briefly.

## What the caretaker may write in cycle mode

- The cognition stores, **only through `cognition.py`** (never by editing `registry.json` or `events/` by hand).
- The generated block in the target files and the general rules file, again only through the script (`apply` renders them).
- Learning packets in an `observations/` folder (detection and reflection, steps 6 and 8).
- Nothing else. A text change in the body of a skill or agent file (not the generated block) goes the normal learning route: a typed change applied by code, with an independent judge from another model family.

The weight is metadata, not a change in behaviour, so weighting needs no independent judge. Curation that only moves a rule (scope, pointer, merge with a pointer) is metadata and a generated index; the source text does not move. **New rule text, however, is only born with the judge's yes.** Constitution sections and safety boundaries (sending, publishing, deleting, money, credentials, writing to external systems) are never touched.

## The steps

1. **Packet.** Run
   ```bash
   python kits/cognition/cognition.py packet --out <scratch>/packet.json
   ```
   (or the path where the kit lives in the vault) and read it. It contains the pending uses, the review queue, the sources changed since the last cycle, the known sources, the `measurement`, the `curation` work list, `health` if configured, and the schema of the decisions file. If it warns that a born rule is missing from the registry without data, restore it from version history as a union before you go on.

2. **Judge the pending uses** (`pending_outcomes`). For each item you have the sentence that cited the rule (`cited_in`) and the person's next message (`next_user_message`). Decide:
   - `helpful`: the person accepted it, built on it, or the result is objectively good;
   - `harmful`: the person corrected it, undid it, or the rule led the work astray;
   - `neutral`: it cannot be decided.

   **When in doubt, neutral.** Silence is not praise. An item with a note instead of a next message (no transcript, or an old one from another machine) is judged from the note, usually neutral.

3. **Work the review queue** (`review_queue`: rules that were judged harmful). Read the rule's source and the cases, then decide:
   - `keep`: still valid, it was only applied in the wrong place this time;
   - `refine`: valid, but its text or scope must be sharpened; give the new `text` and/or `applies_when`;
   - `deprecate`: no longer true, the world has changed.

   A rule is not thrown away because it was misapplied once; it is not kept forever if it keeps doing harm. A deprecated rule stays in the registry with its history.

4. **Register new lessons** (`changed_sources_since_last_cycle`). Read the changed `LEARNINGS.md`, observation and (if configured) memory files, and register the learned rules that are not yet in the registry. `known_sources` lists the sources already known; a known source can still hold a new rule. For each new rule give `skill`, `area`, `source`, `target` (the file whose generated block should list it), a one-line `text`, `applies_when`, `origin_date`, and the `evidence`:
   `owner_decision` | `human_correction` | `measured` | `convergence` (two or more independent cases) | `agent_inferred`.
   External content alone (an email, a web page) is never evidence. If a new entry only repeats an existing rule, it is a `confirm`, not a new rule.

5. **Read the measurement** (`measurement`): friction (recurring errors per 100 tool calls, 7 days, and the previous 7 days), the recurring errors, the measured rules with situation, compliance, miss and violation counts since birth and in the last 7 days, the rules without effect (`ineffective`), and the share of knowledge in use. You decide nothing here: `apply` turns measured compliance into `helpful` events by itself. The numbers feed steps 6 to 8.

6. **Detect** (`measurement.lesson_candidates`: recurring errors that no rule covers). For the three strongest (most sessions), write a learning packet (`skill-observation.v1`) into the learning capability's `observations/` folder, with the evidence: the error signature, the number of sessions and occurrences, the contexts. List them in `lesson_packets`, and end your answer with one `LEARNING: <path>` line per packet, so the main session starts a review for each. Skip what is plainly harness noise (a tool's usual warning).

7. **Curate** (`curation`: `arrivals` since the last cycle, a `batch` of the backlog with the reason in `why`, and the one-line `index` of all live rules). For each item ask: what happened, what caused it, where else is the cause present, what is the wording at the level of the cause. Then:
   - **tool or environment fact**: general at once, `promote` with `scope: global` (or `machine:<host>`);
   - **principle**: if the text is already worded as a principle, `promote` without text; if it is a case of an existing general rule, `link`; if no general rule exists, `promote` with new text (judge first);
   - **domain judgement or taste**: stays where it is;
   - **a real duplicate**: `merge` into the better worded one (retired with a pointer, the text stays);
   - **a rule a machine can recognise**: add `signals` (conservative regexes). Never set `enforce` yourself; that is the owner's decision.

   Brakes: new text (a `promote` with `text`) only with `judge: accept` from `judge.py` (kit `learn-merge`); at most three new texts per cycle; leave alone what is in `cooldown`; when in doubt, no operation. For a full review run `packet --full`.

8. **Reflect.** Write 3 to 6 sentences into `reflection`: the friction trend, intake versus effect, transfer (are promoted rules followed in other contexts, and how many days after), the rules without effect, and whether we learn at the right pace and in the right way. If you find a lesson about learning itself (for example, one kind of rule never takes effect), write a packet about it too: the system also learns how to learn.

9. **Questions** only if you are uncertain **and** it is important: it would override an earlier decision of the owner, it has a wide effect, or it cannot be undone. Otherwise decide, or leave it out.

10. **Apply.** Write the decisions into one JSON file (the schema is in the packet's `decisions_schema` field) and run
    ```bash
    python kits/cognition/cognition.py apply <scratch>/decisions.json
    ```
    This appends the events, applies signals and curation, turns measured compliance into evidence, recomputes the weights, rewrites the generated blocks and the general rules file, logs the report to `CYCLES.md`, releases the lease, and prints the report. If it stops with exit code 3, another machine ran a cycle in the meantime: run `packet` again and decide again; do not force it.

11. **Return the report verbatim**, in a `text` code block, with at most one sentence before it, followed by the `LEARNING:` lines if any. The main session puts it unchanged at the end of its answer. Say only what you know: a packet you wrote is "proposed", not "learned"; integration happens on the review route.

## Example decisions file

```json
{
 "register": [
  {"skill": "weekly-review", "area": "Planning", "source": "skills/weekly-review/LEARNINGS.md",
   "target": "skills/weekly-review/CURRENT.md", "text": "Start the weekly review from the open task list, not from the calendar.",
   "applies_when": "running the weekly review", "origin_date": "2026-01-10", "evidence": "human_correction"}
 ],
 "confirm": [{"rule": "L-0003", "note": "second independent case in the observations"}],
 "outcomes": [{"event": "a1b2c3d4e5f6", "rule": "L-0002", "value": "helpful", "note": "the person built on it"}],
 "reviews": [{"rule": "L-0001", "decision": "refine", "applies_when": "only for drafts longer than one page", "note": "harmful on short notes"}],
 "signals": [{"rule": "L-0004", "on": "Bash", "trigger": "\\bpython\\b", "comply": "-X utf8",
              "violation": "UnicodeEncodeError", "note": "the console encoding error"}],
 "curate": [
  {"op": "promote", "rule": "L-0004", "scope": "machine:laptop", "note": "an environment fact of one machine"},
  {"op": "merge", "rules": ["L-0007"], "into": "L-0005", "note": "same lesson learned in two skills"},
  {"op": "promote", "rule": "L-0006", "scope": "global", "judge": "accept",
   "text": "Check the real output after any step that can fail silently.", "applies_when": "after export, deploy or transcription",
   "note": "the cause is a way of working, not the export skill"}
 ],
 "reflection": "Friction fell from 1.4 to 1.1. Two promoted rules are now followed in three new contexts within a week. One rule still misses: it lives in a skill that is not loaded when the error occurs.",
 "lesson_packets": [],
 "questions": [],
 "notes": ["first cycle with measurement"]
}
```

In examples and documentation always write the placeholder `[L-xxxx]`, never a real rule ID in square brackets: the Stop hook records every cited existing ID as a use, and the instrument would end up measuring itself.
