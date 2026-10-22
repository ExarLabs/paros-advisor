# Installing the PAROS Advisor (instructions for an AI agent)

A person sent you here (or to https://ignis.academy/paros) to install the PAROS Advisor. Do this, then tell them in one or two lines what happened, in their language.

0. **Speak their language, in plain words, from the first line.** The install sentence is English by design, so it does not tell you their language. Look at the computer instead (folder names such as `Asztal` or `Dokumentumok`, the system locale) and write in that language; if you cannot tell, ask in one short line. The person may never have used a terminal: do not show them commands, describe what you do.
   **Prepare them for the permission prompt.** Downloading and running the advisor needs their permission in the agent app. Before you start, say in one or two plain sentences what will happen and what to click, for example: "I will now download the PAROS Advisor from GitHub (github.com/ExarLabs/paros-advisor) into a hidden folder and run its installer. It does not touch your notes. Your Claude app will ask whether I may do this: if you agree, click Allow." If the step is blocked anyway, explain it the same way, in their language, and ask for a plain yes; never offer terminal commands to someone who does not use a terminal.
**In Claude Cowork (or the Claude app outside the Code tab): install the plugin instead, and skip steps 1 to 3.** Cowork does not read `~/.claude/commands`, and a cloud session would install into its own temporary machine, not the person's. Guide the person, in their language, through the app: Customize, Plugins, Add, Add marketplace, Add from a repository, enter `ExarLabs/paros-advisor`, then add the **PAROS Advisor** plugin. After that they type `/paros:paros` (or simply ask for the PAROS Advisor) in a session that has their notes folder. The plugin is the same advisor from the same files (`install/ENTRY.md`), is updated by the app, and sends no usage ping. In Claude Code the plugin also works (`/plugin marketplace add ExarLabs/paros-advisor`, `/plugin install paros@paros-advisor`); use one of the two ways, not both, so the person sees one advisor.
1. **Check Python** (`python --version` or `python3 --version`; on Windows also `py -3 --version`). On Windows `python` may be only the Microsoft Store alias: it answers "Python was not found" (exit code 49) even when Python is installed, for example because the agent's shell has not picked up the new PATH yet. In that case use `py -3` in place of `python` in every command below. Use whichever name works; if none does, Python is missing: tell the person how to install it for their system and stop. Git is optional: with git the advisor is cloned, without it a zip is downloaded from GitHub (no account needed), and updates work either way.
2. **Get the repository** into a hidden folder in their home directory (not inside any notes folder):
   - with git:
     ```bash
     git clone https://github.com/ExarLabs/paros-advisor.git ~/.paros-advisor
     ```
     If `~/.paros-advisor` already exists, update it instead: `git -C ~/.paros-advisor pull --ff-only`.
   - without git: download the installer alone and let it fetch the rest:
     ```bash
     curl -fsSL -o paros-install.py https://raw.githubusercontent.com/ExarLabs/paros-advisor/main/install/install.py
     python paros-install.py
     ```
     It downloads the repository as a zip into `~/.paros-advisor` and installs `/paros` in one go (then skip step 3, and delete `paros-install.py`). On Windows `curl` is built in since Windows 10.
3. **Install the `/paros` command:**
   ```bash
   python ~/.paros-advisor/install/install.py
   ```
   (use `python3` if that is the name on their system, or `py -3` on Windows when `python` is not found). It works the same for a cloned and a downloaded copy. It writes the command for Claude Code (`~/.claude/commands/paros.md`) and, if Codex is used on this machine, for Codex (`~/.codex/prompts/paros.md`). It never touches their notes.
4. **Tell the person, in their language** (the install sentence is English by design; if you cannot tell their language, ask in one short line), that the advisor is installed and updates itself each time it is used, and in one plain sentence that each use sends an anonymous count (version, system, language; no name, no content) which they can turn off any time (`PRIVACY.md`). Then ask **one** question: do they already have a notes folder (for example an Obsidian vault)?
   - **Yes, and this session is in it:** offer to start right here (step 5).
   - **Yes, elsewhere:** explain how to open a session in that folder (Claude desktop app: the Code tab, a new session, choose that folder; terminal users: `cd` there and start the agent), then type `/paros`.
   - **No, or unsure:** offer to start from zero right now, in this session, with `~/.paros-advisor/playbooks/start-from-zero.md`: Obsidian first, one step at a time, no commands to type.
5. To start in this session, read `~/.paros-advisor/AGENTS.md` and follow it (the tour, or start-from-zero for someone without notes).

To remove: `python ~/.paros-advisor/install/install.py --uninstall`, then delete `~/.paros-advisor`.
