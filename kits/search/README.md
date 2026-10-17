# Kit: search (P06, index first)

A working reference for [P06](../../principles/P06-search.md): a SQLite FTS5 index of the vault's markdown, a ranked search on 2 to 4 word stems, and a read-only skill that uses it.

Read it, then rebuild or adapt it for the vault. Up to about two hundred notes, Obsidian's own search and grep are fine; above that, this index and the Librarian (`agents/librarian`) are usually the first thing worth building, because everything else in PAROS depends on finding.

## Why an index

In a large vault, raw search is slow, noisy and eats an agent's context: grep returns every line that matches, unranked, and the agent reads far too much to find the one file it needed. A ranked index with the header weighted above the body puts the right file first far more often. The index is **derived** (P01): it can be deleted and rebuilt at any time, so it lives outside the vault and never syncs.

## Files

| What | Where | Kind |
|---|---|---|
| The indexer | `index.py` | standard library only (`sqlite3` with FTS5, present in every common Python build) |
| The search | `search.py` | standard library only, opens the index read-only |
| The skill entry | [`SKILL.md`](SKILL.md) | thin entry (P04), finds the live definition |
| The live definition | [`CURRENT.md`](CURRENT.md) | when to use, how to turn a question into stems, what to read |
| The index | `~/.paros/index.db` | derived, outside the vault, one per machine |

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PAROS_VAULT` | the current directory | the vault root |
| `PAROS_INDEX` | `~/.paros/index.db` | the database file |
| `PAROS_INDEX_SKIP` | none | extra folder names to skip, comma separated (for example an archive) |

Both scripts also take `--vault` and `--db`.

## Commands

```bash
python index.py                       # incremental: only files whose mtime or size changed; removed files drop out
python index.py --full                # rebuild from scratch
python search.py "invoic remind"      # ranked search, top 10
python search.py "garden" --area Home --limit 5
python search.py "budget" --json      # machine output
python search.py --status             # index path, note count, size, last build and its age
python search.py "garden" --files     # force the file-walk fallback
```

## What is indexed

For every `.md` file: the path, the frontmatter `title` (or the file name), `description`, `tags`, and the body. The frontmatter reader is deliberately tiny: flat `key: value` lines, inline lists and block lists. Skipped folders: `.git`, `.obsidian`, `.trash`, `.claude`, virtual environments, `node_modules`, plus `PAROS_INDEX_SKIP`.

## How the ranking works

- Words of the query are lowercased, stopwords drop out (a short English list and a short Hungarian list as an example of a second language; extend them for your languages).
- Each remaining word becomes a prefix term, and the terms are OR-ed: `"invoic"* OR "remind"*`. Prefixes handle word endings in inflected languages; OR keeps a near miss in the list instead of returning nothing.
- `bm25` with column weights title 10, description 5, tags 2, body 1. This is why a good `description` (P01) matters so much: it is the second strongest signal.
- The tokenizer removes diacritics, so a query with or without accents finds the same notes.

## Keeping it fresh

Run `index.py` on a schedule (every 15 to 60 minutes; an incremental run over a few thousand notes takes well under a second when little changed): cron or a systemd timer, Windows Task Scheduler, launchd, or a session hook. The health kit ([`kits/health`](../health/README.md)) checks the index's age (`index_fresh`) and runs an end-to-end canary through it, so a dead indexer does not go unnoticed (P11).

## Platforms

| Part | Claude Code | Codex | Elsewhere |
|---|---|---|---|
| `index.py`, `search.py` | yes | yes | any Python 3.8+ |
| `SKILL.md` | as a skill under `.claude/skills/search/` | point to `CURRENT.md` from `AGENTS.md` | read `CURRENT.md` |
| Scheduling | a hook or the OS scheduler | the OS scheduler | the OS scheduler |

## Known limits

- Markdown only. PDFs and other formats need their own extractor before they can be indexed.
- No semantic search: the query must share word stems with the note. Writing good descriptions is the cheap fix.
- One writer per index: run `index.py` from one scheduler per machine.
