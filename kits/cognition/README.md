# Kit: cognition (P05, weighted learned rules, measured effect and the cognitive cycle)

A working reference for the last steps of [P05](../../principles/P05-closed-loop-learning.md): learned rules carry a **weight**, the agent marks when a decision depended on one (`[L-xxxx]`), the transcripts are **measured** to see whether learning actually reduces friction, and a background **cognitive cycle** judges whether the rules helped, reviews the ones that hurt, takes in new lessons, **curates** where each rule lives, reflects on how well the system is learning, and reports with a text heat map.

The goal is the same as P05's: remove friction, the moments when a rule is wrong, cannot be applied, or does not exist and something has to be invented.

This kit is optional. Read it, then rebuild or adapt it for the vault; do not copy it blindly.

## The weighting model

Every learned rule has a weight between 0 and 1, computed from its events (never stored by hand).

| Event | Effect |
|---|---|
| **born** | base weight by evidence: owner decision 0.40, human correction 0.35, measured 0.30, convergence (2+ independent cases) 0.30, agent inference 0.15 |
| **confirm** | `w += 0.15 * (1 - w)`: +15% of what remains to 1 |
| **helpful** use | `w += 0.12 * (1 - w)`: +12% of what remains; also written automatically when the transcripts show the rule being followed (see measurement) |
| **harmful** use | `w -= 0.30 * w`: -30%, and the rule goes to **review** |
| **neutral** use | only the exposure count grows |
| **idle** | after 60 days without any event, the weight decays 5% per month; rules of human origin (owner decision, human correction) have a floor, so they never fall asleep on their own |
| **dormant** | below 0.12 the rule is no longer listed as active, but it stays in the file and new evidence brings it back |

| Mark | Tier | Weight | Meaning |
|---|---|---|---|
| ░ | seedling | < 0.25 | new or weak evidence; only a suggestion, yields in a conflict |
| ▒ | growing | 0.25 to 0.50 | there is evidence; it is used |
| ▓ | strong | 0.50 to 0.75 | confirmed several times or proven |
| █ | root | 0.75 and above | a foundation of the system |
| ! | review | | it did harm; the next cycle decides about it |
| · | dormant | < 0.12 | not loaded, but kept |
| × | retired | | no longer valid; its history is kept |

A harmful use does not delete anything: the caretaker decides `keep`, `refine` (sharpen the text or scope) or `deprecate`. One bad application is not a reason to drop a rule; repeated harm is.

## Measurement: is the learning working?

A weight that only grows when rules are born or cited measures **intake**, not **effect**. The kit therefore reads the agent's own transcripts (`miner.py`, read only, no LLM) and counts what happened. It stores counters and a normalised error signature (paths, e-mail addresses, long tokens and numbers replaced), never content.

**The main metric is friction:** recurring errors per 100 tool calls, over 7 days, compared with the previous 7 days. An error is "recurring" when the same signature shows up in at least 3 different sessions within 14 days. One-off errors are noise; recurring ones are what learning should remove.

The **learning funnel** follows a rule from birth to effect:

| Stage | Question | Where it comes from |
|---|---|---|
| **Intake** | how many new rules were born | the registry |
| **Exposure** | did the situation the rule is about come up | the rule's `trigger` pattern matched a tool call |
| **Application** | was the rule followed when it came up | the `comply` or `avoid` pattern on that call |
| **Transfer** | is it followed outside the place it was born, and how many days after birth | the contexts (skill, capability, area) where it was followed |
| **Prevention** | did the error it is about go away | the `violation` pattern on error texts, before and after birth |

The report's **LEARNING RATE** block shows friction and its trend, a daily curve, the share of active rules actually in use in the last 30 days, the measured rules with their last-7-day numbers, the **rules without effect** (the error or the miss still comes after the rule), and the **recurring errors without a rule** (lesson candidates).

### Signal pattern

A rule a machine can recognise gets a `signals` field (regexes, conservative):

| Field | Matches | Meaning |
|---|---|---|
| `on` | tool name (full match) | which tool the rule is about, e.g. `Bash`; default any |
| `trigger` | the tool input | the situation has come up |
| `comply` | the tool input | the right form (optional) |
| `avoid` | the tool input | the form to avoid (optional) |
| `violation` | the error text | the error the rule prevents (optional) |
| `enforce` | | `true`: the PreToolUse hook stops the form to avoid (only by the owner's decision) |

When the measured compliance count of a rule grows from one cycle to the next, `apply` writes one `helpful` outcome with `source: measured`. So the weight also grows from effect, not only from citations. When a new signal pattern arrives, the past is re-measured, so there is a baseline.

### Detection

The recurring errors that no rule covers are **lesson candidates**. The caretaker writes a learning packet for the strongest ones (at most three per cycle), and the normal review route (evidence, independent judge, typed change by code) decides. Learning no longer depends only on the running agent noticing a lesson. A recurring error that a rule *does* cover is an **adherence failure**: the rule exists but does not act, usually because it lives in the wrong place. That goes to the curator.

## The curator: the rule moves to its cause

A lesson is usually noticed in one place (a skill, a capability) while its cause lives somewhere else: a tool, the machine, a way of working. A rule kept where it was noticed only loads there, so it does not act where it is needed. The curator runs **every cycle** and asks four questions of each item: what happened, what caused it, where else is the cause present, and what is the wording at the level of the cause.

| What the rule is about | Where it goes |
|---|---|
| a **tool or environment fact** (a shell, an encoding, a path, an API quirk) | general at once: `promote` with `scope: global` (or `machine:<host>` if it holds on one machine only) |
| a **principle**, a way of working | its wording at once (`promote` without text if it is already worded as a principle; `link` if a general principle already covers it; `promote` with new text if not), its **weight by evidence** |
| **domain judgement or taste** | stays where it is; it moves only after it repeats elsewhere |

Operations, all lossless (nothing is deleted, the source text never moves):

| Op | What it does |
|---|---|
| `merge` | duplicates fold into one umbrella rule: the others are retired with a `superseded_by` pointer, their text stays |
| `promote` | the rule becomes general (`scope`); with new `text`, a new general rule is born at the level of the cause and the original stays as its instance (`instance_of`). **New text needs the independent judge's `accept`.** |
| `link` | the rule is an instance of an existing general principle |
| `rehome` | a new target file for the rule's generated line (the source does not move) |
| `scope` | `local`, `global` or `machine:<host>` |

Brakes: new text only with the judge's yes, at most three new texts per cycle, a 7-day **cooldown** on everything the curator touched, and when in doubt no operation. The packet carries the arrivals since the last cycle plus a **batch** of six backlog items in order of importance (rules without effect, adherence failures, duplicate suspects, tool or environment content in a narrow place, strong rules in a narrow place), and a one-line index of every live rule. `packet --full` hands over the whole backlog for a full review.

### The general rules file

Rules with `scope: global` or `machine:<host>` are rendered into one generated file (`PAROS_GENERAL_RULES`, default `PAROS/GENERAL_RULES.md`). **Import it from the vault's entry file** (for example `@PAROS/GENERAL_RULES.md` in `CLAUDE.md`, or a line in `AGENTS.md` telling the agent to read it), so it is loaded in every session. Never edit it by hand.

**Token thrift.** Every line of this file costs tokens in every session, so: a rule that lives in agent memory (and so already loads through the memory index) is not repeated here; each rule is one compact line ("When ...: do ..."), with no weight table; the full text and the links are one command away (`cognition.py show L-xxxx`, `cognition.py find <words>`).

### Just in time: the PreToolUse hook

Some rules are sure and command-level ("always pass this flag when you run that"). For those, a `PreToolUse` hook checks the rule at the moment of the action: if the situation has come up and the command has the form to avoid, it stops the call and gives the rule as the reason; the model corrects the command and runs it again. Only rules with `signals.enforce: true` are enforced, and **enforcement is the owner's decision**, never the curator's, because a wrong enforced rule blocks work.

## Reflection

At the end of each cycle the caretaker writes 3 to 6 sentences: the friction trend, intake versus effect, transfer (are promoted rules followed in other contexts, and how quickly), rules without effect, and whether the system is learning at the right pace and in the right way. The report prints it under **REFLECTION ON LEARNING**, and it is kept in the cycle history. A lesson about learning itself (for example, one kind of rule never takes effect) becomes a learning packet like any other, so the system also learns how to learn.

## Files

| What | Where | Kind |
|---|---|---|
| The engine | `cognition.py` | deterministic, no LLM, standard library only |
| Transcript reader and measurement | `miner.py` | deterministic, read only, standard library only |
| The cycle procedure | [`CYCLE.md`](CYCLE.md) | what the caretaker agent does in cycle mode |
| Rule registry | `registry.json` | canonical: ID, source, text, scope, evidence, signals, links, text history |
| Events | `events/<host>.jsonl` | canonical, append-only, one writer per machine (safe with file sync) |
| Cycle history | `state.json` | written only by `apply` |
| Lease | `lease.json` | which session is running a cycle (90 minutes) |
| Optimistic lock | `.base.<host>.json` | the cycle number seen at `packet` time |
| Measurement records | `metrics/<host>.jsonl` | one writer per machine; counters only |
| Read watermark | `.miner.<host>.json` | byte offset per transcript file |
| Weights | `weights.json` | derived, can be recomputed at any time |
| Report log | `CYCLES.md` | append-only, for humans |
| General rules | `PAROS/GENERAL_RULES.md` (configurable) | generated; imported by the vault's entry file |
| Generated block | at the end of each target file, between the `COGNITION:BEGIN` and `COGNITION:END` HTML comment markers | the rule list with weights, rewritten by `render` and `apply` |

The data files are created on first use. Keep them in the vault (they sync); keep them out of a public repository.

## Several machines

The stores sync between machines, and a sync can put an older registry over a newer one. Four safeguards, each from a real incident:

1. **ID ranges per machine.** Each machine issues rule IDs from its own range (`PAROS_ID_BLOCKS`, or `id_blocks.json` next to the stores), so two machines can never give the same ID to two different rules. A machine without a configured range gets a block of 100 in the 6000 to 9999 band, chosen from its host name; configure a range as soon as you use more than one machine.
2. **Self-healing registry.** The full rule data also travels in its birth, refine and curation events, in the machine's own single-writer event log. Loading the registry restores whatever is missing from the file, and the next save heals it. `backfill` writes these data events once for older rules.
3. **Optimistic lock.** `packet` records the cycle number it saw; if another machine completed a cycle in between, `apply` writes nothing, releases its lease and exits with code 3. Run `packet` again and decide from the new packet.
4. **Lease.** Only one session at a time runs a cycle (90 minutes).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PAROS_COGNITION_DIR` | the script's folder | where the stores live |
| `PAROS_VAULT` | detected upwards from the data folder (`.obsidian`, `.git` or `AGENTS.md`) | the vault root; rule `source` and `target` paths are relative to it |
| `PAROS_LEARNING_ROOTS` | the whole vault | folders (separated by `:` or `;` per platform) scanned for changed `LEARNINGS.md` and `observations/*.md` |
| `PAROS_MEMORY_DIR` | unset | optional: an agent memory folder. Changed rule-type memory files (`feedback_*` or frontmatter `type: feedback` / `reference`) go into the packet, and a rule that targets a memory file gets its ID as a prefix on that file's line in the memory index instead of a generated block |
| `PAROS_MEMORY_INDEX` | `MEMORY.md` | the memory index file name inside the memory folder |
| `PAROS_GENERAL_RULES` | `PAROS/GENERAL_RULES.md` | the generated general rules file, relative to the vault |
| `PAROS_ID_BLOCKS` | unset | JSON, e.g. `{"laptop": [1, 4999], "desktop": [5001, 5999]}`: the rule ID range per machine (host names as `PAROS_HOST` prints them) |
| `PAROS_GENERAL_HINTS` | a list of common tool and environment words | a regex; a narrowly placed rule whose text matches two of its words is offered to the curator |
| `PAROS_HEALTH_CHECK` | unset | optional: the [health kit](../health/README.md)'s `health_check.py`; the packet then runs it, and the report shows every machine's health |
| `PAROS_HEALTH_STATE_DIR` | `~/.paros/health` | where the health kit keeps `state.<host>.json` |
| `PAROS_CYCLE_DOC` | `kits/cognition/CYCLE.md` | the procedure the hook tells the session to follow |
| `PAROS_HOST` | the machine's host name | the name used for the event file, the lease and the ID range |
| `PAROS_TRANSCRIPTS` | `~/.claude/projects` | (miner) the transcript root |
| `PAROS_CONTEXT_PATTERNS` | `skills/<x>`, `capabilities/<x>`, `Areas/<x>`, `agents/<x>` | (miner) a JSON list of regexes with one group that name the context of a day's work from the paths in tool inputs |

## Commands

```bash
python cognition.py report                                   # current state, with the learning rate, no cycle
python cognition.py measure [--full] [--json]                # read new transcript parts, print the learning rate
python cognition.py used L-0042 --outcome helpful --note "..." # a manual signal
python cognition.py packet --out packet.json [--full]        # the caretaker's work packet (--full: full curation)
python cognition.py apply decisions.json                     # the caretaker's decisions, then the report
python cognition.py show L-0042                              # one rule in full
python cognition.py find encoding windows                    # search all learned rules
python cognition.py render                                   # rewrite the generated blocks and the general rules file
python cognition.py due                                      # is a cycle due (JSON)
python cognition.py backfill                                 # once per machine: data events for older rules
```

The owner can say at any time "L-0042 was good" or "L-0042 was wrong"; the main session records it with `used --outcome`.

The report is plain text: tier counts, a growth sparkline across cycles, what got stronger or weaker, the learning rate, the reflection, the review queue, and a heat map with one row per capability and one cell per rule, darker meaning stronger.

## Hooks

### Claude Code

Three hooks in the vault's `.claude/settings.json` (adjust the path to where the kit lives in the vault). Put them in the user-level settings instead if you want sessions in every repository to measure and learn, not only sessions in the vault.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "python PAROS/cognition/cognition.py due --hook"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "python PAROS/cognition/cognition.py stop-hook"}]}
    ],
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python PAROS/cognition/cognition.py pretool-hook"}]}
    ]
  }
}
```

- `UserPromptSubmit` runs `due --hook`: if no cycle ran in the last 4 hours and no other session holds the lease, it takes the lease and adds context telling the session to start the caretaker agent in cycle mode in the background, following `CYCLE.md`, and to append the report to its answer.
- `Stop` runs `stop-hook`: every existing rule cited as `[L-xxxx]` in the answer becomes a pending use, judged in the next cycle from the person's next message.
- `PreToolUse` runs `pretool-hook`: only rules with `signals.enforce` act, at the moment of the command. Leave this hook out until the owner has decided to enforce a rule.

All hooks swallow every error silently: a hook must never block the work. The health check (P11) is what notices a cycle that has not run for 48 hours.

### Codex

Codex has no equivalent hooks. Put this in the vault's `AGENTS.md`: at the start of a session run `python <kit>/cognition.py due`; if it says `"due": true` and `"leased": false`, run the cycle (as a background task where available) following `CYCLE.md`. Mark rule use with `[L-xxxx]` as usual and record outcomes with `used` when the person reacts, since there is no Stop hook to do it automatically. Point `PAROS_TRANSCRIPTS` at the session logs if your platform keeps them as JSON lines in the same shape; otherwise the measurement stays empty and the rest still works.

## Why it runs on the subscription, inside a session

The cycle is judgement work: reading what the person said next and deciding whether a rule helped, deciding where a rule belongs. That needs a capable model, a few times a day, every day. Run as a scheduled API job it would bill API credits on top of the subscription the owner already pays for, and would need an API key stored for an unattended process (one more secret, see P07). Run as a background agent inside a session the owner has open anyway, it uses the subscription, it has the transcripts at hand, and it reports right where the owner is looking. The cost of this choice: no cycle runs while nobody works, which is fine, because nothing new is learned then either.

## What we learned from AutoHarness

In October 2026 we compared this learning loop, at code level, with [AutoHarness](https://github.com/tigerless-labs/autoharness), an open self-improving skill layer for Claude Code. The two are mirror images: AutoHarness is strong at **collecting** (it catches almost everything and writes short, well-triggered rules behind strict code gates), PAROS is strong at **judging** (it learns only from evidence, an independent judge decides, nothing is lost, and it improves the knowledge people already wrote). The largest gain is to put their input side in front of our judging side. What we took over, and where we deliberately differ:

**Taken over**

- **Automatic detection from transcripts.** Learning that depends on the agent noticing a lesson misses most of them. Objective errors are the strongest signal (tool and test errors show up in most sessions; explicit human corrections in few), so the miner reads errors first.
- **Adherence, not coverage.** The most common real correction concerned a rule that already existed and was ignored. A rule that does not act is a bigger risk than a missing rule, so the curator's first items are rules without effect, and the rule moves to where its cause is.
- **Liberal generator, strict code gates.** When the gates were written into the collecting prompt, the collector collected nothing. Filtering belongs in deterministic code, not in the prompt of the part that gathers.
- **Measure the numerator empirically.** A usage counter that is never checked against reality reports almost every rule as unused. Count from the transcripts what actually happened, and treat a missing citation as a measurement gap, not as proof that the rule is useless.
- **Activity-relative probation.** Age measured in calendar days makes every untouched rule start fading on the same day. Measure age by activity (exposure since birth), and do not punish a rule for a gap in the measurement.
- **Never drop a rule from the index.** A model does not search again for what the index no longer shows. A dormant rule may shorten to its ID and one line, but it stays listed.
- **Honest background reports.** A background run says what it knows: "proposed", not "integrated", unless the code that integrates confirmed it.

**Where PAROS deliberately differs**

- **Evidence threshold.** A rule needs an explicit human correction, an observed outcome or at least two independent occurrences. External content alone is never evidence. A collector's guess is a candidate, not a rule.
- **Independent judge.** A model from a different family judges every new rule text; without its verdict nothing is integrated.
- **No compaction.** No section is rewritten or summarised, and the curator never rewrites a rule's text: merges retire with a pointer, generalisations are new rules with links.
- **Learns into human-written knowledge.** AutoHarness writes only into its own skills; PAROS improves the skills, agents and memory the owner already uses, which is where most of the value is.

## Known limits

- Use marking still matters: a cited rule is judged by the person's reaction; a rule without a signal pattern and without citations earns no credit.
- Transcripts live per machine; a pending use is judged on the machine where it happened (after 14 days elsewhere it is treated as neutral), and each machine measures its own sessions.
- The registry text is a short extract; the authoritative text stays in the source file.
- The idle decay still counts calendar days; activity-relative probation is the direction, not yet the code.
- In documentation and examples always write the placeholder `[L-xxxx]`: the Stop hook records any cited existing ID as a use.
