# Kits: optional reference implementations

A kit is a working example of a principle. **Optional,** and never copied blindly: the agent reads it and rebuilds it for the person's vault (or adopts and adapts it). The code is disposable; the principle and its check are what matter.

| Kit | Principle | What it gives | Status |
|---|---|---|---|
| [`search`](search/README.md) | P06 | SQLite FTS5 index of the vault (kept outside it), ranked search on 2 to 4 word stems, a read-only skill | **available** |
| [`cognition`](cognition/README.md) | P05 | weighted learned rules, use marks, the cognitive cycle, a report with a heat map; the effect of learning measured from the transcripts (friction), detection of recurring errors, a curator that moves each rule to its cause, a general rules file; hooks for Claude Code | **available** |
| [`learn-merge`](learn-merge/README.md) | P05 | typed rule changes without compaction (add, update, deprecate, move), version snapshots, a log; an independent judge from another model family | **available** |
| [`health`](health/README.md) | P11 | canary and weighted checks (index, secrets, frontmatter, learning cycle, backup age), alerts on state change into your task list | **available** |
| [`thin-entry`](thin-entry/README.md) | P04 | builds thin `SKILL.md` entries that always run the live definition from your vault, with a version report; version bumps with snapshots; a learning digest across skills | **available** |
| [`secrets`](secrets/README.md) | P07 | secrets inventory without values, per-machine presence, a health check (the encrypted transfer bundle is planned) | **available** |
| `backup` | P10 | encrypted snapshot backup on a schedule, with test restores | planned |
| [`google-workspace`](google-workspace/README.md) | P07, P08 | Sheets, Forms, Drive and Calendar from a script, several accounts, writes are dry runs until applied; the fetch-and-brief pattern | **available** |
| [`activity-ledger`](activity-ledger/README.md) | P01, P11 | a passive "what did I do" log per machine, written by a session-end hook, with a daily journal and a recap | **available** |
| [`reels`](reels/README.md) | P08 | long video to short captioned clips, step by step, with the measured lessons as pitfalls; your brand in `LOCAL.md` | **available** |
| [`view`](view/README.md) | P02 | three levels: no app, a zero-build Node.js view (search, note preview, tasks written back to markdown, live refresh), or a React app on the same API | **available** |
| [`share-gate`](share-gate/README.md) | P00, P07 | blocks publishing when a repository holds entries of your personal deny list (kept outside it), secret-like patterns or private emails; allow list, file names checked, a pre-commit hook | **available** |
| [`mac-power`](mac-power/README.md) | P01, P07 | prezi and agent power modes for a Mac: zsh commands, the Agent Focus helper, a lid watcher, the narrow sudoers rule | **available** |

Every kit will say what works in Claude Code, what works in Codex, and what is platform-independent (Python scripts with no or minimal dependencies).

The diagnosis scanner is already here: [`tools/diagnose.py`](../tools/diagnose.py). Shared skills are in [`skills/`](../skills/README.md).
