# Flow 2: Diagnosis

Goal: an honest picture of where the vault stands, principle by principle, with evidence. **Read-only.** Nothing in the vault changes, except that the result is written to `PAROS/DIAGNOSIS.md` at the end (ask first).

## Steps

0. **Boundaries first.** Before scanning anything, ask: "Is there any folder I must not open, for example something private?" If yes, exclude it **in the scanner**, not only in your head: pass `--exclude <folder>` (repeatable). Offer to record it durably in `PAROS/.parosignore` (one path per line; the scanner always reads it) and as an entry-file rule, each only with a yes. The report prints "Excluded, not opened: ..." so the person can see the boundary held.
0b. **The whole ecosystem, if asked.** When the person wants the diagnosis to cover more than the vault ("centralise everything", "my old knowledge is hard to find"), ask which other places hold their knowledge: project repositories, a team knowledge base, the Downloads folder, loose scripts next to the vault, the agent conversation history. Each extra folder is read-only and needs their yes; private folders inside them are excluded the same way (an absolute `--exclude` path, or the folder's own `.parosignore`). Pass them with `--also <folder>` (repeatable). The report then adds, per folder, its size, entry files, the kinds of knowledge it holds and **secret-like patterns** (the most serious findings are often in Downloads and in loose scripts), and lists **possible knowledge silos**: the same kind of knowledge in several places. The conversation history is not scanned here; it has its own playbook, [`mine-your-agent-history`](../playbooks/mine-your-agent-history.md).
1. **Measure.** Run the scanner from the vault root (Python 3.8+, no dependencies):
   ```bash
   python <path-to-paros>/tools/diagnose.py . --exclude "<private folder>" --json PAROS/diagnosis.json
   ```
   (Writing `PAROS/diagnosis.json` is a write: ask first, or omit `--json` and keep the result in the chat until the person agrees to save it.)
   It measures what can be measured without judgment: file counts, frontmatter and description coverage, entry files, skills and agents, learning files, archive, version control and sync, secret-like patterns (names only, never values), possible sync duplicates. If Python is not available, do the same checks by hand with the file tools you have.
2. **Ask** what cannot be measured. Keep it short, at most five questions, for example:
   - Which areas of your life and work does this vault cover?
   - How many machines do you use it on, and how does it sync?
   - Which external tools do you use daily (mail, calendar, tasks, CRM)?
   - Which agent platform do you use?
   - What annoys you most about working with your notes today? (This is the friction PAROS should remove first.)
3. **Judge.** For each principle, read its **Check** section and give a maturity level, with one line of evidence:

   | Level | Meaning |
   |---|---|
   | 0 | Not present |
   | 1 | Started: some pieces exist, not consistent |
   | 2 | In place: works for most of the vault |
   | 3 | Self-sustaining: checked automatically, improves with use |

   Also mark each principle `now`, `later` or `not needed` for this person (connectors can wait if they use no external tools; backup is never `not needed`).

   **Metadata only where retrieval fails.** A low frontmatter or description score is not by itself a reason to add headers to existing notes. Ask for three to five real things the person has tried to find, try to find them, and recommend headers or descriptions only for the parts of the vault where that failed. A useful mess is not a problem to fix.
4. **Write** `PAROS/DIAGNOSIS.md` (template: `templates/DIAGNOSIS.md`): date, reference version, the table, the three biggest gaps, and the one change that would remove the most friction. Fill the two frontmatter fields the advisor reads later: `open_gaps` (the IDs at level 0 or 1 that are marked `now`) and `next_check` (the date of the next diagnosis, two weeks from today). With a yes, refresh the **PAROS status** block in the vault's entry file (`templates/vault-AGENTS.md`), so ordinary sessions know the gaps too.
   **Retrieval first.** If P06 is below level 2 in a vault of more than about two hundred notes, it is one of the three biggest gaps whatever else is missing, and the first step names the search index and the Librarian.
5. **Map gaps to ready help:** for each of the three biggest gaps, check whether a skill or a kit closes it, and add it to `DIAGNOSIS.md` ("Ready help": name, what it does here, effort).
6. **Present** the result in a few lines in the chat: a small text map (one line per principle, level as blocks, for example `P01 Persistence  ██░  2`), the biggest gaps, and the suggested first step. Then offer the personal guide (flow 3) or going straight to adoption (flow 4).

## Rules

- Never print or store a secret value; the scanner reports file and pattern type only.
- Never open a folder the person declared off-limits, with the scanner or any other tool.
- Say what you measured and what you assumed. A diagnosis is evidence, not an impression.
- Repeat the diagnosis after adoption steps; the change in levels over time is the person's progress.
