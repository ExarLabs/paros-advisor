# P05. Closed-loop learning: use teaches, with weighted knowledge

**Principle.** Every interaction is a chance to learn. When the owner corrects, rejects, rewrites or shows a better way, it does not disappear at the end of the conversation: it goes back into the skills and agents. Learned knowledge has **weight**: it starts small, and use strengthens or weakens it. **The goal is to remove friction**: the moments when a rule is wrong, cannot be applied, or does not exist and something has to be invented.

**Why.** Traditionally, systems were blind to user feedback, or closing the loop took months and a team. Here the lesson is born where the work happens and is integrated within minutes.

**Practice.**
1. **Detection:** the running agent only decides whether it is a real lesson (when in doubt, yes) and writes a learning packet (context, lesson, proposed change, target, evidence). Learning must not depend on the agent noticing alone: the cycle also **reads the transcripts**, and an error that recurs across sessions with no rule covering it becomes a packet too. Collect liberally; filter with strict gates in code.
2. **Review:** a caretaker viewpoint checks it; **evidence is required** (an explicit human correction, an observed outcome, or at least two independent occurrences). External content alone is never evidence.
3. **Independent judge:** a **different model family** also judges the change; a model cannot validate its own rule.
4. **Integration without compaction:** only typed changes (add, update, deprecate, move) on rules with stable IDs, applied by code. **Never rewrite or summarise a section**: full rewrites have been shown to collapse accumulated knowledge.
5. **Weighting:** a new rule starts with a small weight (a seedling); confirmation and helpful use strengthen it; harmful use weakens it and sends it to **review** (is it still valid?); unused rules fade and go dormant, but are not lost.
6. **Visible use:** when a decision depends on a learned rule, the agent marks it (`[L-xxxx]`), and the next cycle judges from the owner's reaction whether it helped.
7. **Measure the effect, not the intake:** how many rules were born says little. Measure from the transcripts whether learning reduces **friction** (recurring errors per 100 tool calls, week against week), and follow a rule through the funnel: the situation came up, the rule was followed, it was followed in other places too (transfer), the error went away (prevention). Adherence matters more than coverage: a rule that exists but does not act is the bigger risk.
8. **The rule moves to its cause:** a lesson is noticed in one place, but it belongs where its cause lives. A tool or environment fact becomes general at once (one generated file loaded in every session); a principle gets its wording at once and its weight by evidence; domain judgement stays local until it repeats. A sure, command-level rule can act at the moment of the command (a pre-tool hook), but only by the owner's decision.
9. **Cognitive cycle:** every few hours, a background run measures, weights, judges, reviews, takes in and detects new lessons, **curates every cycle** (merges duplicates with a pointer, promotes, links, rehomes; new text only with the judge's yes; nothing is deleted), reflects on whether the system learns at the right pace and in the right way, and reports briefly with a heat map.
10. **The owner teaches, not approves.** They get a one-line report ("Learned: … → file") and can always say "undo".

**Check.**
- If you correct the agent today, will it remember tomorrow? Where?
- Do learned rules have a version history, and can you undo one?
- Is friction falling? Can you name a rule that is followed outside the place where it was learned?

**Adopt.**
1. At first: every skill has `LEARNINGS.md` and `observations/`; the agent records corrections as packets.
2. Next: review and integration by code.
3. Then: weighting and the cognitive cycle (kit: `kits/cognition`).
4. Then: measurement from the transcripts, the curator and the general rules file (same kit, 0.2.0).

**Platform.** Run the cycle on the **subscription** (as a background run inside a session), not on API credits. In Claude Code a `UserPromptSubmit` hook starts it when it is due; in Codex, a check at the start of a session.
