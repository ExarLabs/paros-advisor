# PAROS Advisor

**Personal Agentic Retrieval Operating System** (say it "PAR-oss").

**An advisor engine for building your own PAROS: a minimal, cognitive operating system that adapts to you.**

This repository is not PAROS itself. PAROS is what grows in *your* vault. This is the advisor that helps you build it: it explains the ideas, diagnoses your vault, writes you a personal guide, helps you adopt principles, skills and agents one step at a time, and answers your questions later (how to connect a new tool, how to turn a routine into a skill, how to work day to day).

PAROS is a way to turn a plain folder of markdown notes (an Obsidian vault, for example) into a personal operating system that AI agents work in: they find things, keep order, learn from every correction you make, and connect your personal knowledge with the tools you share with other people.

The name is the idea:

| Letter | Meaning | What it claims |
|---|---|---|
| **P**ersonal | one person | One PAROS belongs to one person. One writer, private by default. |
| **A**gentic | agents work in it | Not just storage: agents read, search, organise, and learn. |
| **R**etrieval | the mechanism | Knowledge is worth what you can bring back at the right moment. Frontmatter, descriptions and indexes all serve this. |
| **OS** | a layer, not an app | Every area of your life and work builds on the same layer. |

## Three things it does

1. **Ask and diagnose.** Talk to it about your knowledge system. It measures your vault against the principles (a diagnosis from 0 to 3 per principle), tells you what is missing (for example a search index, or a backup), and explains why it matters.
2. **Build.** It sets things up with you, step by step: a search index, sync and backup, connectors to your tools, and a small local web view of your vault (Node.js, no build step, for beginners; React when you want more).
3. **Advise.** Practical wisdom on working with AI, from 28 tips around four human dimensions, adapted to your situation; and playbooks for what people actually do with PAROS.

When it finds a gap in itself, it asks you once whether to report it to the maintainers, in your language, and you can tell it never to ask again. Reports go straight to the maintainers' inbox; you do not need a GitHub account.

## If you are an AI agent reading this

Someone sent you here to set up PAROS for them. Do this:

1. Clone this repository **outside** their vault (for example `git clone https://github.com/ExarLabs/paros-advisor.git ~/paros-advisor`), or `git pull` if it is already there.
2. Work in **their** vault folder (ask which one if it is not your current directory).
3. Read [`AGENTS.md`](AGENTS.md) and follow it. Start with the tour, then offer the diagnosis. The tour and the diagnosis are read-only and can run without asking; anything that changes their vault needs their yes.

## This repository is an advisor, not a template

**Nobody uses this repository as the root of their vault, and nobody writes into it.** You download it next to your vault, point an AI agent at it, and the agent becomes your PAROS advisor: it explains the ideas, diagnoses your current vault, writes you a personal guide, and helps you adopt the principles one step at a time, on your terms.

Why this way:
- **No merge conflicts.** Every vault is different: areas, habits, machines, tools. If this repo were your base, every update would fight your own changes.
- **Updates are advice, not overwrites.** When a principle is added or refined, your agent reads what changed and suggests what is worth adopting. You decide.
- **The principle is the asset, not the code.** Scripts are disposable and can be regenerated. What lasts is the principle, the reason behind it, and the way to check it.
- **It gets more valuable the more people use it.** These are lessons learned from running a real PAROS daily. Use them, adapt them, and tell us what you learn.

## Install (the easy way)

Tell your AI agent (Claude Code or Codex), in any language:

> Read https://ignis.academy/paros and install the PAROS Advisor.

It downloads this repository into `~/.paros-advisor` (with git, or as a zip without it; no GitHub account needed) and installs the **`/paros`** command. From then on, in any session in your notes folder, type `/paros` for the menu, or `/paros <your question>`: what is my vault behind on, how do I connect a tool, how do I build a dashboard, how do I organise my knowledge. The advisor updates itself each time you use it and tells you what is new. Details: [`install/INSTALL.md`](install/INSTALL.md).

**In Claude Cowork** (or as a plugin in Claude Code): add this repository as a plugin marketplace, then add the **PAROS Advisor** plugin. In Cowork: Customize, Plugins, Add, Add marketplace, Add from a repository, enter `ExarLabs/paros-advisor`. In Claude Code: `/plugin marketplace add ExarLabs/paros-advisor`, then `/plugin install paros@paros-advisor`. You get the `paros` skill (type `/paros:paros`, or just ask for the PAROS Advisor) and the six PAROS agents. It is the same advisor from the same files: the `/paros` command and the plugin both start from [`install/ENTRY.md`](install/ENTRY.md), so every update reaches both.

## Quick start (by hand)

1. Download the repository somewhere **outside** your vault:
   ```bash
   git clone https://github.com/ExarLabs/paros-advisor.git ~/paros-advisor
   ```
2. Open your vault folder (an existing one, or a brand new empty folder).
3. Start an AI agent in that folder (Claude Code, OpenAI Codex, or any agent that reads `AGENTS.md`) and say, in any language:
   > There is a reference system at `~/paros-advisor`. Read its `AGENTS.md` and be my PAROS advisor.
4. The agent will walk you through it step by step:
   - **Tour:** what PAROS is and why it works this way.
   - **Diagnosis:** where your vault stands today, principle by principle.
   - **Personal guide:** your vault explained, with what to change, why, and which principle is behind it.
   - **Adoption:** a checklist written into your vault, done one item at a time, with your approval.
   - **Advice, any time later:** how to add a connector, a skill, how to work day to day.
5. To update: `git pull` in `~/paros-advisor`, then tell your agent: "Check what is new in PAROS."

## What is inside

| Where | What |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The agent's entry point on every platform. `CLAUDE.md` imports it. |
| [`flows/`](flows/) | What the agent does: tour, diagnosis, personal guide, adoption, advice, upgrade. |
| [`explainer/`](explainer/index.html) | An interactive page that explains PAROS and its principles with small animations, in English and Hungarian. Open `explainer/index.html` in a browser. |
| [`principles/`](principles/README.md) | The principles, one file each: the principle, why, practice, how to check, how to adopt. |
| [`tools/diagnose.py`](tools/diagnose.py) | A dependency-free scanner that measures a vault against the principles. Read-only. |
| [`guides/`](guides/) | Practical how-tos (add a connector, add a skill, daily work), the architecture of a PAROS, a glossary, website strategy. |
| [`templates/`](templates/) | Starting points for your vault: entry file, frontmatter, skill definition, adoption checklist. |
| [`wisdom/`](wisdom/README.md) | Practical wisdom on working with AI: 28 tips around four human dimensions (Ethos, Logos, Pathos, Thelos), with a question map, plus field lessons measured in daily use. |
| [`playbooks/`](playbooks/README.md) | Step-by-step guides for what people do with PAROS: connectors, dashboards, organising knowledge, meetings, thinking with several AIs. |
| [`install/`](install/INSTALL.md) | The installer, the `/paros` command, the plugin's `paros` skill, and `ENTRY.md`, the entry both share. |
| [`starter/`](starter/README.md) | A small demo vault with fictional areas, three agents and a dashboard: open it to **see** PAROS working before you build your own. |
| [`skills/`](skills/README.md) | Ready skills you can adopt into your vault (recipe in `CURRENT.md`, your settings in `LOCAL.md`). |
| [`agents/`](agents/README.md) | Six agents (viewpoints) you can adopt: Alfred, Iris, Moneto, Presto, Librarian, Maestro. |
| [`packs/`](packs/) | Skills for a whole workflow: [podcast production](packs/podcast/README.md), [meetings](packs/meetings/README.md). |
| [`kits/`](kits/README.md) | Working machinery: view, search, learning (learn-merge, cognition), health checks, secrets inventory, thin entries. |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed in each version, and what to review in an adopted vault. |

## Privacy

Each run of the installer (every `/paros`) sends one anonymous usage ping: event, version, operating system, language, agent app and install method. No identifier, no IP stored, nothing from your notes. Turn it off with `PAROS_NO_PING=1` or an empty `.no-ping` file in the advisor folder. Details: [PRIVACY.md](PRIVACY.md).

## Language

The repository is written in English. Your agent talks to you in your language and writes into your vault in your language.

## Platforms

Works with **Claude Code**, **OpenAI Codex** and **Claude Cowork** (through the plugin), and with any agent that follows the `AGENTS.md` convention. Platform-specific parts (hooks, scheduling) are marked as such.

## License

See [`LICENSE`](LICENSE). Current version: [`VERSION`](VERSION).

Made by [ExarLabs](https://github.com/ExarLabs), from a PAROS in daily use since 2026.
