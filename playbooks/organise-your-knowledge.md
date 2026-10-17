---
title: organise-your-knowledge
status: active
description: Playbook for organising a PAROS vault around lasting areas instead of short projects, with a frontmatter header and content description on every note, an entry file agents read, header backfill in batches, and index-first search with optional tier indexes.
---

# Playbook: organise your knowledge

## What you get

A vault organised around **areas** (the lasting responsibilities of your life and work) instead of short projects, where every note starts with a frontmatter header whose `description` says what is in it, and an entry file that tells every agent how the vault is laid out. Agents find the right note by reading headers and indexes instead of opening dozens of files, and you stop moving folders around every time a "project" turns out to last for years.

## Before you start

- A vault folder (an existing one, or an empty one). If you want to see the result first, open [`starter/`](../starter/README.md).
- **A way back** (AGENTS.md safety rule 1): git, a copy, or your sync service's version history. Reorganising touches many files; without a way back it does not start.
- About an hour for the structure and the entry file. Headers on existing notes are added gradually, in batches, over days or weeks.
- Optional: Python 3.8 or newer, for the diagnosis scanner and the search kit.

## Steps

### 1. Measure where the vault stands

**Agent:** runs the read-only scanner from this repository and shows the numbers: how many markdown files, how many have frontmatter, how many have a description about the content, and which top-level folders exist.

```bash
python <paros-advisor>/tools/diagnose.py <your-vault>
```

**You decide:** nothing yet. This is the baseline you will compare against at the end (P11).

*In the repo:* `tools/diagnose.py`.

### 2. Decide what your main unit is

**Agent:** asks how your work actually runs. The key question: when you say "project", does it end? Many people who manage or operate something (a business, a client relationship, a team, a household, a course they teach every year) have "projects" that last for years and have phases but no end. For them, **areas** are the main unit, and a project folder would never be closed.

**You decide:** which model fits you.

- **Areas-dominant (the usual choice):** most of the vault lives in areas. A projects folder exists only for short, deadline-bound work that cuts across areas, and is often empty.
- **Project-dominant:** if most of your work really starts and ends (a freelancer with discrete deliveries, for example), projects can be the main unit. Say so, and the rest of this playbook adapts.

Do not let the agent push a textbook system on you. If your "projects" are relationships, they are areas.

### 3. Lay out the top level

**Agent:** proposes a small, fixed set of top-level folders with one sentence each, using your own words. A typical layout:

| Folder | What goes there |
|---|---|
| `Projects/` | Only short, cross-cutting, deadline-bound work. Often empty. |
| `Areas/` | Most of the vault. Lasting responsibilities: one folder per area. |
| `Resources/` | Outside input: books, podcasts, transcripts, articles. |
| `Archive/` | Inactive and closed. Not indexed deeply by default (P09). |
| `Daily/` | Daily notes, if you keep them. |
| `PAROS/` | Skills, agents, the adoption log. |
| `Templates/` | Templates. |

**You decide:** the folder names (in your language, numbered or not) and **your list of areas**. Fictional example: `Areas/Bakery/`, `Areas/Book Club/`, `Areas/Fitness/`.

Inside an area, organise by the area's own domain (`Bakery/Suppliers/`, `Bakery/Recipes/`, `Bakery/Wholesale/`), not by repeating the top-level scheme inside it. An area is not a miniature vault.

### 4. Move existing notes, in small batches

**Agent:** maps existing folders to the new layout and shows a move plan per batch: from, to, and how many files. Uses moves that keep links working (Obsidian's own move, or a script that rewrites wiki links), and never deletes: anything that seems obsolete goes to `Archive/` with a date and a reason (P09).

**You decide:** yes or no per batch. One area at a time is a good rhythm. After each batch the agent reports what moved and whether any link broke.

### 5. Fix the frontmatter schema

**Agent:** proposes the header every note starts with, from [`templates/frontmatter.md`](../templates/frontmatter.md):

```yaml
---
title: <file name>
date: <YYYY-MM-DD>
author: <you>
status: active | draft | done | archived
description: <one or two sentences about the CONTENT, required>
id: <uuid4>
tags: [optional]
version: <semver, only for versioned files>
---
```

It explains the field that matters most: **`description`**. Search ranks on it and agents decide from it whether a file is worth opening. It must be about the content ("Wholesale price list for October with the three cafe discounts and the new rye loaf"), not generic ("Notes about prices").

Two rules worth fixing now, because they save the most trouble later:

- **`id` never changes.** It survives renames and moves. If a note is split, the original keeps its id and the new one gets a fresh id; if two merge, the merged note gets a fresh id and records which ids it came from.
- **Optional fields have an allowed list.** A header is not a place to dump random fields. If you need more (an `area`, a `related` list, a `schema` for a kind of note, a field that opts a note out of the index), add them to the schema first.

**You decide:** the field list. Keep it short; you can add fields later, you cannot easily take them away.

### 6. Write the vault entry file

**Agent:** creates or extends `AGENTS.md` at the vault root from [`templates/vault-AGENTS.md`](../templates/vault-AGENTS.md) (for Claude Code, also `CLAUDE.md` containing one line: `@AGENTS.md`). It records:

- who you are and what the vault is, in one paragraph, with the list of areas;
- the organising model you chose in step 2 and **why** (so no future agent "helpfully" proposes a different one);
- the folder table from step 3;
- the frontmatter schema, or a link to it;
- how to search (step 9);
- where the task list lives ([`task-inbox`](task-inbox.md)).

**You decide:** you read the whole file before it is written.

### 7. Every new note is born with a header

**Agent:** adopts the `frontmatter-header` skill so that every note it creates starts with a correct header, and adds the rule to the entry file.

**Also for scripts.** Any script, generator or copy step that writes markdown into the vault writes the full header itself, with the same fields, a `generated_by: <script name>` field, and a description built from the generated content (period, main numbers, subject), not a template sentence. In practice, headerless files come mostly from generators, not from hand-written notes: fixing the generator once beats repairing its output forever. If many headerless files in one folder share a name pattern, look for the generator.

*In the repo:* skill [`skills/frontmatter-header`](../skills/frontmatter-header/).

### 8. Add headers to existing notes, in batches

**Agent:** works through the notes without headers, one batch at a time (for example one area, or 50 files), with this procedure:

1. List the files without a header (from the step 1 scan).
2. Exclude: mirrors of outside systems, reference files a skill reads raw, frozen version snapshots, generated lists, anything that holds a secret. For generated files, fix the generator first (step 7).
3. For template-based notes (daily notes and the like), strip the template lines with a script first and read only what remains. Many turn out to be empty; an empty note gets a short "Empty note." description and is excluded from the index.
4. Write each `description` by hand, from the content. Be discreet: personal, health, salary and family details appear only as a topic, never with their values.
5. Put the header in front of the file byte for byte, leaving the body untouched.
6. Parse every written header with a YAML parser to prove it is valid.

**You decide:** yes per batch. You can spot-check five descriptions per batch and correct them; each correction teaches the skill (P05).

*Written at adoption:* the small batch script (list, strip template lines, prepend header, validate). It is disposable and specific to your vault.

### 9. Turn on search and indexes

**Agent:** sets up search to match the vault's size.

- **Small vault (up to about two hundred notes):** Obsidian's search and grep are fine. Write that into the entry file.
- **Larger:** the search kit builds a full-text index over headers and bodies, outside the vault, with `title` and `description` weighted above the body. Questions become 2 to 4 word stems.

```bash
python <paros-advisor>/kits/search/index.py --vault <your-vault>
python <paros-advisor>/kits/search/search.py "wholesal price cafe"
```

- **Tier indexes (optional, for large vaults):** generated overview files at the vault root (an index, a knowledge map, open decisions, open questions, gaps), and the same set inside an area once it earns one: about 30 files or more, its own current-state file, or active work going on. These are derived files: regenerated, never edited by hand, and each says what it was made from and when (P12).

**You decide:** whether you need the index now, and which areas get their own tier indexes.

*In the repo:* kit [`kits/search`](../kits/search/README.md); tier indexes come with the [Librarian](../agents/librarian/CURRENT.md) agent.

## Check that it works

Look at the output, not at the plan (P11):

1. **Run the scanner again** and compare with step 1: the share of files with a content description should rise with every batch.
2. **Five real questions.** Ask five questions you actually had last month ("what did we agree with the flour supplier?"). For each, is the right note the first hit, found from its header, without the agent opening a pile of files?
3. **Sample twenty random notes.** How many have a header, and how many descriptions would let you decide whether to open the file without opening it?
4. **A new note from a script** (any generator you have): does it come out with a full header?
5. **Fresh session test.** Start a new agent session and ask "how is this vault organised?". The answer should come from the entry file and match what you decided in step 2.

## Pitfalls

- **Textbook PARA for a long-running life.** If "projects" never close, a project-first layout leaves you with a projects folder full of things that should be areas and an archive nobody trusts. Decide the main unit from how your work really runs, and write the reason into the entry file so it is not reopened every month.
- **Generic descriptions.** "Notes about the meeting" is worse than nothing: search ranks it, the agent opens it, and learns nothing. A description says what is *in* the file.
- **Generators that write headerless files.** Hand repair is a symptom fix; the generator recreates the debt on every run. In a real cleanup, most of the missing headers came from scripts, copies and generated outputs.
- **Two indexes.** If two search indexes exist side by side, one goes stale silently while still answering. Keep one, and let the health checks watch its age.
- **Duplicates through folder aliases.** A symlink or junction that makes a folder appear twice puts every file into the index twice. Exclude aliases from indexing.
- **Status tables are intent, not fact.** Before relying on an index, check that the file exists and when it was generated.
- **Multi-line descriptions.** Keep `description` to one or two lines, no block scalars: several tools read it as a single line.
- **Changing ids.** An `id` that changes on rename breaks every link and lineage built on it. Generate once, never again.
- **Big-bang moves.** Moving the whole vault in one go makes it impossible to review and hard to undo. Batches, with a way back.

## Principles behind it

- [P01](../principles/P01-persistence.md): knowledge lives in markdown; the header is what makes it findable.
- [P06](../principles/P06-search.md): search is a capability, index first.
- [P09](../principles/P09-forgetting-and-archiving.md): archive, do not delete.
- [P11](../principles/P11-health-contract.md): prove it with output.
- [P12](../principles/P12-one-fact-one-owner.md): generated indexes are derived and say what they came from.

## Related

- Skill: [`frontmatter-header`](../skills/frontmatter-header/) (writes and repairs headers).
- Skill: [`project-state`](../skills/project-state/) (one current-state file per area, which also earns the area its tier index).
- Kit: [`search`](../kits/search/README.md) (index-first search).
- Kit: [`health`](../kits/health/README.md) (the `metadata` check catches new files without a header; `index_fresh` watches the index).
- Agent: [Librarian](../agents/librarian/CURRENT.md) (tier indexes, frontmatter and link audits, tidying).
- Template: [`templates/frontmatter.md`](../templates/frontmatter.md), [`templates/vault-AGENTS.md`](../templates/vault-AGENTS.md).
- Playbook: [`task-inbox`](task-inbox.md).
