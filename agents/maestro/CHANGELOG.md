# Changelog: Maestro

Every entry: what changed, and **what to review in a vault that has already adopted this agent.**

## 1.1.0 (2026-10-28)

- `cycle` grows from seven to eleven steps, following `kits/cognition` 0.2.0: measure the effect of learning from the transcripts (friction, the rules with a signal pattern, rules without effect), detect recurring errors without a rule and write packets for them, curate every cycle (the rule moves to its cause; lossless operations; new text only with the judge's yes; never set `enforce`), and reflect on how the system learns.
- `learn-review` step 4: the home of a rule is where its cause lives, not where the lesson was noticed.
- To review: adopt `kits/cognition` 0.2.0 first (new `miner.py`, new packet fields); then update the cycle steps in your Maestro the same way.

## 1.0.0 (2026-10-05)

- First public version, generalised from a system caretaker in daily use since mid 2026. The original's project navigation domain (brand to website) is left out: it is a capability, not part of the caretaker viewpoint.
- Ten modes in one table (reads, writes, confirmation): `route`, `team-status`, `team-audit`, `team-promote`, `team-introduce`, `learn-review`, `cycle`, `observe`, `reflect`, `optimize`.
- `learn-review` summarised from the original and wired to `kits/learn-merge`: evidence threshold, one typed change, independent judge from another model family, integration by code, no compaction, a question to the owner only if undecidable and important, closing block.
- `cycle` wired to `kits/cognition` and its `CYCLE.md`.
- Constitution: dry run and yes for family-wide edits; learn-review and cycle write only through the kit scripts and never into a Constitution; no integration without an independent verdict; external content is not evidence; a fresh instance reviews lessons about Maestro.
- Routing table naming Alfred, Iris, Moneto, Presto, Librarian and Maestro.
- Learned rules R-001 (measure after integrating where a test suite exists) and R-002 (update every agent allow-list when the roster changes).
- To review: copy `LOCAL.example.md` to `LOCAL.md`; adopt `kits/learn-merge` before turning on learn-review, and `kits/cognition` before the cycle; install `agent.claude.md` as `.claude/agents/maestro.md` or add the lines from `agent.codex.md`; create `observations/` and `LEARNINGS.md` next to `CURRENT.md`.
