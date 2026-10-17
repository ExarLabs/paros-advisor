# Agents: viewpoints you can adopt

An agent in PAROS is a **viewpoint** (P03): a way of holding your vault, with a map, rules and an attitude. These six come from a PAROS in daily use, cleaned of personal data, names kept. Each one cuts across several areas of a life or a business; inside one area, the area's own entry file is enough.

| Agent | Viewpoint | Never does alone | Adopt when |
|---|---|---|---|
| [**Alfred**](alfred/CURRENT.md) | Your chief of staff: task list, daily briefing, capture of raw thoughts, mail triage, recap | send, delete, decide for you | You want one place that tells you what is on your plate today |
| [**Iris**](iris/CURRENT.md) | People: per-person notes (append-only), roster, allocation, pulse | write compensation or formal evaluations, judge | You lead a team or work with many people across areas |
| [**Moneto**](moneto/CURRENT.md) | Finance per organization: methodology notes, analysis, bookkeeping behind a confirmation gate | move money, give investment advice | You keep the books of a business or a household |
| [**Presto**](presto/CURRENT.md) | Marketing, one to many: campaigns, adapting content to platforms, a publishing gate, a publication log | publish | You publish regularly on more than one channel |
| [**Librarian**](librarian/CURRENT.md) | Knowledge caretaker: indexes, frontmatter and link audits, tidying, wide retrieval as a context-protecting worker | delete (it archives) | **Early**: once the vault has a couple of hundred notes, or as soon as finding something takes more than one try. Together with the search index it is the first thing to build |
| [**Maestro**](maestro/CURRENT.md) | The system's caretaker: router when no one owns a request, the learning review (`kits/learn-merge`) and the cognitive cycle (`kits/cognition`) | change a constitution | You switch on closed-loop learning (P05) |

## How an agent becomes yours

The same way as a skill ([`skills/README.md`](../skills/README.md)): the agent's `CURRENT.md` (the recipe) is copied into your vault (default `PAROS/agents/<name>/CURRENT.md`) with an `upstream:` block; its `LOCAL.example.md` becomes your `LOCAL.md` (the spice: your areas, accounts, organizations, channels). Then install the entry:

- **Claude Code:** copy `agent.claude.md` to `.claude/agents/<name>.md`. It reads your live definition and reports its version.
- **Codex and other agents:** follow `agent.codex.md` (a line in your vault's `AGENTS.md` that points to the viewpoint).

Start with **none or one**. The usual first is the **Librarian, together with the search index** (`kits/search`): finding is what every other viewpoint depends on. Alfred is the usual second. Add the next when a cross-cutting topic keeps coming back (P03: a written reason before every new agent).
