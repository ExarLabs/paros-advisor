# P06. Search is a capability, index first

**Principle.** Searching the vault is a **capability** (a skill), not an agent. Search a fresh full-text index first, ranked; raw file search (grep) is for exact strings and code only.

**Why.** Retrieval is the R in PAROS: knowledge is worth what you can bring back at the right moment, and every other part (the agents, the learning loop, the diagnosis) depends on it. In a large vault, raw search is slow, noisy and eats context. Measured in practice: the index puts the right answer first far more often than grep. The index is derived (P01) and can be rebuilt at any time.

**Practice.**
- Turn the question into 2 to 4 characteristic word stems; the index ranks results, with `title` and `description` weighted above the body.
- If many files must be read together, a context-protecting worker (P03) does it with the same capability and returns only a summary.
- The health checks watch the index's freshness (P11).

**Check.**
- For five real questions, is the first hit right?
- How old is the index?

**Adopt.**
1. Up to about two hundred notes, Obsidian's search and grep are fine.
2. Above that, or as soon as a question needs more than one try: a SQLite FTS5 index over frontmatter and body (kit: `kits/search`), a skill that uses it, and the Librarian as its caretaker (`agents/librarian`). This is usually the first thing worth building after the entry file.
