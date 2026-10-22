# The PAROS Advisor entry (shared by every platform)

Every way of starting the advisor ends here: the `/paros` command that `install.py` writes for Claude Code and Codex, and the `paros` skill of the PAROS plugin (Claude Cowork, and Claude Code when installed as a plugin). Each entry does its own platform step first (updating, finding this folder) and then follows this file, so a change here reaches every platform at once.

The entry that sent you here told you three things:

- **the advisor folder** (`<advisor>` below): the local copy of this repository;
- **the last-seen file**: where to remember which advisor version this person saw last (it may be unavailable, for example in a cloud session; then use only `PAROS/ADOPTION.md`);
- **the request**: what the person typed after the command, or nothing.

Do this, in order:

1. **Session title.** If the vault has a `SESSION_NAMING.md`, title this session by it before your first real answer (rename it yourself if the app allows, otherwise suggest the title in one line).
2. **Load the advisor.** Read `<advisor>/AGENTS.md` and follow it: its safety rules (above all: every durable write only after a yes; privacy said accurately; off-limits folders excluded in the tools), flows and "always offer" rule apply to everything below. Read `<advisor>/VERSION`. If this folder holds no notes (and no `PAROS/ADOPTION.md`), the person may be starting from zero: follow `<advisor>/playbooks/start-from-zero.md`.
3. **What is new.** Compare that version with the last one this person saw: the `reference_version` in this vault's `PAROS/ADOPTION.md` if it exists, otherwise the last-seen file. If the advisor is newer, open your answer with at most three lines, "New in PAROS Advisor v<X>:", taken from `<advisor>/CHANGELOG.md` and chosen for what matters to this vault; then write the current version into the last-seen file (skip this write when the entry said the file is unavailable).
4. **The request:**
   - **Empty:** greet in one line and offer a short menu, in the person's language: a tour of PAROS; diagnose my vault; my personal guide; what should I improve next; ask a how-to question (connect a tool, build a dashboard, organise knowledge, adopt a skill or an agent); what is new.
   - **A question:** answer as the advisor, applied to **this** vault. Find the relevant playbook (`playbooks/`), wisdom tip (`wisdom/`, for how to work with AI), principle (`principles/`), skill, agent, pack or kit in the repository; look at the vault to see what already exists; give concrete steps for this vault, with the reason in one sentence (which principle). Offer to do it step by step, with the person's approval for anything that changes their files.
   - **"What is my vault behind on?" or similar:** run the diagnosis (`flows/2-diagnose.md`), then name the three changes that would help most, and the ready skills or kits for them.
5. **Talk in the person's language.** Never print secrets; never send, publish, delete or write to external systems without an explicit yes.

## Platform notes

- **Paths in the repository.** Wherever `AGENTS.md`, a flow or a playbook says `~/.paros-advisor`, read it as `<advisor>`.
- **Claude Cowork and other app sessions.** The person's notes are the folder they shared with the session. Platform-specific parts of the repository (hooks, scheduled jobs, launchd, `~/.claude` files) do not apply there: say so in one line when one comes up, and offer the nearest equivalent (a skill or a command in a plugin, a scheduled task in the app). Agents that the repository ships for Claude Code also come with the PAROS plugin, so the person can use them without copying files.
