# Changelog

Every entry: what changed, and **what to review in a vault that has already adopted PAROS.**

## 0.16.0 (2026-10-11)

- **New playbook `keep-your-mac-awake` and kit `kits/mac-power/`:** two power modes for a Mac. Prezi keeps the display on while presenting, on battery too (a deck in full screen can switch it on by itself with a Screen Wake Lock). Agent keeps the Mac working with the lid closed so long agent runs finish, on battery too, with the display off. Terminal commands (`prezi`, `agent-on`, `agent-off`, `power`), an "Agent" Focus in Control Center through two shortcuts and a logging helper, a lid watcher, a sudoers rule for exactly two commands, a timer and a battery guard. The intent comes first, so it carries to Linux and Windows too; eight pitfalls with fixes.
- To review: nothing to adopt. If you run long agent sessions on a Mac laptop, ask `/paros keep my Mac awake`.

## 0.15.1 (2026-10-10)

- **New `explainer/`:** an interactive page that explains what PAROS is and walks through the thirteen principles (P00 to P12), each with a short animation, the reason behind it, the practice and an everyday analogy. English and Hungarian (follows the browser language; `?lang=hu` or `?lang=en` forces one). A tour mode plays them in order; the arrow keys step through. Open `explainer/index.html` in any browser, no install.
- To review: nothing to adopt. Useful when you introduce PAROS to someone else.

## 0.15.0 (2026-10-10)

From a proposal sent through the advisor's feedback (thank you): three things that made "connect my email" and a Windows install harder than they need to be.

- **New playbook `connect-your-email`:** the starting point for "connect my email". The agent first asks which accounts (personal or work; Gmail, Microsoft 365, outlook.com or another provider), then sends each one to the right playbook: `connect-gmail-multiple`, `connect-microsoft-365` or `connect-any-mailbox`.
- **`connect-microsoft-365`: check with IT first.** A work account often needs the tenant admin's approval ("Admin approval required"), even for the official connector. The playbook now says so up front, adds a short request template you send to IT yourself, and sends personal Microsoft accounts (`@outlook.com`, `@hotmail.com`, `@live.com`) to `connect-any-mailbox`.
- **Windows: `py -3` as a fallback.** When `python` is only the Microsoft Store alias ("Python was not found", exit code 49) although Python is installed, `/paros` and the install instructions now try `py -3` instead of stopping.
- To review: if you asked to connect a work Microsoft 365 account and saw "Admin approval required", ask `/paros connect my email` for the request to IT. On Windows, nothing to do: the next `/paros` refreshes the command.

## 0.14.1 (2026-10-08)

From a bug report sent through the advisor's feedback (thank you): P07 reported a vault as clean while it held a plaintext login, because the label was not in English.

- **P07 never says "clean" without saying what it checked.** With no match, the evidence now reads "no matches, which is not proof", followed by what was and was not checked; the text report ends with the same coverage line.
- **Credential labels in six languages**, with or without accents: English, Hungarian (`jelszó` / `jelszo`, `titkos kulcs`, ...), German, French, Romanian, Spanish, in notes, config and code (`password: x`, `DB_PASSWORD=x`, `"api_key": "x"`). Placeholders, references to environment variables and prose ("password: kept in the manager") are not hits.
- **Login blocks in any language:** in notes, a short `label: value` line with a password-shaped value next to an email address, a URL or a login label (user name, belépés, Benutzername, ...). Dates, versions, ids, slugs, file names and codes are not password-shaped.
- New tests: `python tools/test_diagnose.py`.
- To review: run the diagnosis again (`/paros diagnose my vault`). New P07 hits are worth a look even if an earlier run was clean; move what you find into your secret store and delete it from the notes.

## 0.14.0 (2026-10-07)

- **Anonymous usage ping.** Each installer run (install, and every `/paros`, which starts with `install.py --update`) sends one ping: event (install, update or use), version, previous version, operating system, language, agent app, install method. No identifier, no IP stored, no content from your vault; the server adds only the day and the country. It tells the maintainers how many people use the advisor and which versions and systems to support. Everything is in the new [PRIVACY.md](PRIVACY.md).
- **Turn it off** with `PAROS_NO_PING=1` or an empty `.no-ping` file in the advisor folder; updates keep the file.
- The installer says so in one line at the end, and the agent mentions it in one sentence after installing.
- To review: nothing to change in your vault. If you prefer no ping, create `~/.paros-advisor/.no-ping`.

## 0.13.0 (2026-10-06)

From the first proposal sent by a user through the advisor's feedback (thank you):

- **Diagnose the whole knowledge ecosystem:** `tools/diagnose.py --also <folder>` (repeatable) scans project repositories, a team knowledge base, Downloads or loose scripts next to the vault, read-only: size, entry files, kinds of knowledge, secret-like patterns. The report lists **possible knowledge silos** (the same kind of knowledge in several places) and counts them under P12. Each extra folder honours its own `.parosignore` and absolute `--exclude` paths. Flow: `flows/2-diagnose.md` step 0b.
- **New playbook `mine-your-agent-history`** and **`tools/agent_history.py`**: a local, read-only digest of your past agent sessions (Claude Code, also inside WSL): your own requests and the stored session summaries, secrets masked, nothing sent anywhere, only counts printed; then extraction by area and new notes only with a yes.
- **`share-with-your-team`:** a new section for when your company already has a knowledge base: map the silos, decide owners per kind once, no double maintenance, publish deliberately, agents on both sides.
- **P07:** scan for secrets beyond the vault too (Downloads, loose scripts, project folders).
- The feedback form now keeps text after angle brackets (`<path>`); before, everything after the first `<` was cut off.
- To review: if your knowledge lives in several places, ask `/paros diagnose my whole ecosystem`.

## 0.12.0 (2026-10-05)

A full pass over the maintainers' own PAROS (every slash command, skill, capability, principle note and memory rule), publishing what is general and not personal.

- **15 playbooks are now ready:** email-triage, connect-any-mailbox (with safe inbox clean-up), connect-microsoft-365, unified-calendar, youtube-knowledge-base, recap-and-journal, share-with-your-team, shared-memory-across-machines, publish-a-microsite, presentations, print-design, publish-from-your-vault, measure-your-ai-usage, and two new ones: measure-your-skills (a harness bench) and report-as-code.
- **`wisdom/field-lessons.md`:** 51 measured lessons from daily use, by theme (agents, browsers, publishing, media, data and reports, files and scripts, learning, design and print).
- **New guides:** `guides/architecture.md` (the layers of a PAROS), `guides/glossary.md` (about 60 terms), `guides/website-strategy.md` (seven layers from identity to site, three tiers).
- **New skill `cv-tailoring`** (evidence-only framing, source untouched, a coverage table) and **new kit `share-gate`** (blocks publishing on your personal deny list, secrets or private emails; pre-commit hook).
- **Updated:** `skills/think` 1.1.0 (an exhausted API credit switches the member to the browser; long prompts through a file input; patient waits for deep reasoning modes), and the recipes of Alfred (chat mode; "what drops out?"), Librarian (integrate deny list; never merge near-duplicates), Moneto (cash tracked itemised is not an expense; differences on their own line) and Presto (template life cycle; when not to exhaust).
- **Principle candidates as open proposals:** `proposals/2026-10-05-principle-candidates.md` (freshness and write-back; the harness matters more than the model; a wall between thinking and distribution; silence is the default; verb classes for permissions). The principles themselves are unchanged.
- To review: ask `/paros what is new for me in 0.12.0?`; the advisor matches the new playbooks to what your vault already does.

## 0.11.0 (2026-10-05)

- New playbook **session-naming**: every session titled `<MACHINE> <AREA> · <topic>`, readable on a phone, with codes from your own areas (template `templates/SESSION_NAMING.md`). The advisor offers it by itself as soon as you work in two or more areas or on two or more machines; once adopted, the agent titles sessions itself where the app allows, otherwise suggests the title once. `/paros` applies it at the start of every session.
- `/paros` updates now also refresh the command itself, so changes to it reach you without reinstalling.
- To review: if you work in several areas or on several machines, ask `/paros set up session naming`.

## 0.10.1 (2026-10-05)

- Install: the first line comes in the person's language, in plain words, and prepares them for the permission prompt of their agent app ("click Allow"); the installer's closing message asks whether a notes folder exists and offers start-from-zero.
- `install.py` no longer repoints an existing `/paros` command to another copy (for example a test install) unless you pass `--force`.
- Whenever a session ends, also early, the advisor offers to save where you are.
- To review: nothing to do.

## 0.10.0 (2026-10-05)

Lessons from the first live simulation (a complete beginner and a person with a messy existing vault, played by another AI against the real advisor):

- New playbook **start-from-zero**, Obsidian first: notes, vault, Obsidian, the agent and PAROS in plain words; installing Obsidian; creating the vault; opening the agent inside it; every area of life in one place; a minimal structure created piece by piece with a yes; a first useful result; how it grows; phone, cost, backup and stopping; saving the session for the next one.
- **Every durable write is a small transaction** (AGENTS.md safety rule 7): file, why, exact effect, how to undo, then a yes. A yes covers exactly what was shown, never an extra log, folder or rule.
- **Privacy said accurately** (rule 8): the notes stay local and nothing is published, but what the agent reads goes to the AI service behind it; PAROS maintainers have no access; sync and connectors are separate.
- **Off-limits folders as a technical boundary** (rule 9): `tools/diagnose.py --exclude` and `PAROS/.parosignore`; the diagnosis asks about private folders before scanning and prints what it excluded.
- **Learning starts as a proposal** (rule 10), and some kinds of rules are never learned silently.
- The diagnosis no longer pushes headers onto existing notes: metadata only where real retrieval fails.
- The agent now notices gaps in the advisor by itself and offers to report them at a natural pause.
- After installing, the agent answers in the person's language and asks whether a notes folder exists; without one, it offers to start from zero.
- To review: if you keep a private folder in your vault, add it to `PAROS/.parosignore`. If your agent created a file without asking, tell it; the rule now forbids it.

## 0.9.0 (2026-10-05)

- **No GitHub account needed, for anything.** Install and updates work without git: the installer downloads the repository as a zip from GitHub and refreshes it the same way later, keeping your local settings (`install/install.py`, new `--update`; `/paros` now updates through it). One-line bootstrap without git in [`install/INSTALL.md`](install/INSTALL.md).
- **Feedback goes straight to the maintainers by default,** through ignis.academy into the maintainers' CRM: no account, no login, and nobody but the maintainers can read what arrives. An email address is sent only if you agree to be contacted. GitHub stays available (`--via github` for a pull request, `--via issue` for an issue page).
- To review: nothing to do. If you installed before 0.9.0 with git, run the installer once (`python ~/.paros-advisor/install/install.py`) to refresh the `/paros` command.

## 0.8.0 (2026-10-05)

- **Feedback that improves the advisor, without spam.** When the advisor notices a gap in itself (a missing playbook, a wrong instruction, a failing kit, a better way), it asks you once, in your language: report it to the maintainers? (yes / no / never ask again). With your yes it shows you the exact text, checks it for personal data, and sends it: as a pull request from your own fork if the GitHub CLI is signed in, otherwise as a pre-filled issue you submit yourself. At most one question a day, never twice about the same topic, nothing after "never". `tools/feedback.py`, `proposals/`, `CONTRIBUTING.md`.
- New playbook **sync-and-backup**: choosing between Obsidian Sync, iCloud, Google Drive, OneDrive, Dropbox and git, setting it up, adding a real backup and testing a restore.
- README: the three things the advisor does (ask and diagnose, build, advise).
- To review: nothing to do; if you never want to be asked about reporting, run `python ~/.paros-advisor/tools/feedback.py optout`.

## 0.7.1 (2026-10-05)

- New playbook **connect-a-web-app-without-api**: how to use any web app without an API from your agent, the way PAROS uses NotebookLM. The connection ladder (API, client, the app's own JSON endpoints, screen automation), your own signed-in browser, a recipe note per app, the measured bridge rules, wrapping it as a skill, and safety for apps that post or send. If your team builds the app, the recipe doubles as the specification for a real API.
- To review: ask `/paros we have a tool without an API, how do we use it like NotebookLM?`

## 0.7.0 (2026-10-05)

- New `wisdom/`: 28 practical tips on working with AI, around four human dimensions (Ethos, Logos, Pathos, Thelos), with a question map; the advisor uses them for "how do I work better with AI" questions (creativity, focus, prompting, your own voice).
- Nine playbooks are now **ready**, step by step: organise your knowledge, the task inbox, several Gmail accounts, Google Workspace, the daily briefing, capture, meetings, building a dashboard, NotebookLM notebooks as experts.
- New kits: `google-workspace`, `activity-ledger`, `reels`; new skill: `portfolio`.
- To review: ask `/paros how do I organise my knowledge?` or `/paros how do I stay creative with AI?`.

## 0.6.0 (2026-10-05)

- **One-sentence install and the `/paros` command.** Tell your agent "Read https://ignis.academy/paros and install the PAROS Advisor": it clones this repository into `~/.paros-advisor` and installs `/paros` for Claude Code (and Codex if present). `/paros` updates the advisor on every use, tells you what is new, and answers questions about your vault.
- New `playbooks/`: the catalog of step-by-step guides (connectors, dashboards, organising knowledge, meetings, thinking with several AIs, and more), with what is ready and what is coming.
- To review: install `/paros` once; after that, updates reach you on their own.

## 0.5.0 (2026-10-05)

- **Renamed to PAROS Advisor** (`ExarLabs/paros-advisor`; the old address redirects). The repository is an advisor engine for building your own PAROS, not PAROS itself.
- New `agents/`: six viewpoints you can adopt, names kept: Alfred (chief of staff), Iris (people), Moneto (finance), Presto (marketing), Librarian (knowledge caretaker), Maestro (system caretaker, learning review and cognitive cycle). Each with a recipe, a `LOCAL.example.md`, and entries for Claude Code and Codex.
- New `packs/`: podcast production (12 skills) and meetings (3 skills).
- New `starter/`: a small demo vault with fictional areas, three agents and a dashboard (navy, red and yellow design tokens, zero dependencies), to see PAROS working before building your own.
- To review: if you use any of these viewpoints already under other names, compare their rules with yours; adopt Alfred first if you have none.

## 0.4.0 (2026-10-05)

- New kits, working and tested: `thin-entry` (build thin skill entries with the "vault always wins" version report, promote with snapshots, a learning digest), `search` (a standalone FTS5 index outside the vault and ranked search), `health` (canary, index, secrets, frontmatter, learning cycle and backup checks, alerts only on state change).
- New skills: `think` (several AIs on one question, with a state file), `transcribe` (Groq Whisper with a completeness check), `speed-reader`, `language-editor`.
- New convention, **recipe and spice**: the general procedure is in `CURRENT.md`; personal settings go into `LOCAL.md` (shipped as `LOCAL.example.md`), which never leaves your vault and is never touched by updates.
- To review: if you adopted a skill earlier, move anything personal from its `CURRENT.md` into a `LOCAL.md`, so future updates merge cleanly.

## 0.3.0 (2026-10-05)

- New kits, working and tested: `view` (no app, a zero-build Node.js view with search, note preview, tasks written back to markdown and live refresh, or step-by-step React instructions on the same API), `learn-merge` (typed rule changes without compaction, plus the independent judge), `cognition` (weighted rules and the cognitive cycle), `secrets` (inventory without values).
- New: shared skills in `skills/` (`frontmatter-header`, `project-state`, `adversarial-second-pass`), each with a live definition, a thin entry, a changelog and a golden example, and the adoption mechanism: a skill lives in your vault with an `upstream:` block, and updates from here arrive as suggestions judged by your own learning loop.
- The advisor now always offers matching skills and kits: at the end of the tour, the diagnosis and the personal guide, and whenever you ask what you can adopt.
- To review: ask your agent "Which PAROS skills and kits would help me most?" and adopt the ones that remove your biggest friction.

## 0.2.1 (2026-10-04)

- Vision stated: a minimal, cognitive operating system that adapts to you.
- P02 refined: the view is minimal and disposable; no app is needed at the start, and a live view should be zero-build (a small local server and plain HTML), never a required framework.
- To review: if your vault depends on a heavy frontend for daily use, check that no knowledge lives only there (P01), and consider whether a simpler view would do.

## 0.2.0 (2026-10-04)

- The repository is now in English, and is an **advisor**: tour, diagnosis, personal guide, adoption, advice and upgrade flows (`flows/`).
- New: `tools/diagnose.py`, a dependency-free, read-only scanner that measures a vault against the principles.
- New guides: add a connector, add a skill, daily work.
- Principles P00 to P12 translated and renamed (English file names); content unchanged.
- To review: nothing for adopted vaults beyond running the diagnosis once to get a baseline.

## 0.1.0 (2026-10-04)

- First internal version (Hungarian): entry file, adoption and upgrade flow, 13 principles, templates.
