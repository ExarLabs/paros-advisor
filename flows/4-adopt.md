# Flow 4: Adoption

Goal: the vault becomes a PAROS, one checked step at a time, with the person's decisions recorded.

## 0. Safety

- Is there a way back (git, a copy, sync version history)? If not, that is the first item.
- Record where this repository lives (for example `~/paros-advisor`) in the vault's entry file, so later sessions find it.

## 1. The checklist

From `PAROS/DIAGNOSIS.md`, write `PAROS/ADOPTION.md` (template: `templates/ADOPTION.md`). For each principle the status is one of: `present`, `to adopt`, `in progress`, `done`, `adapted` (the person's own version, with a reason), `later`, `not needed`. For every `to adopt` item, write the concrete steps **for this vault**, not generic ones.

Add a **Skills and kits** section to the checklist: the ones the person chose from the diagnosis and the guide, each with status and the adoption steps from [`skills/README.md`](../skills/README.md).

Order: the **core** principles first (P00, P01, P06, P03, P04, P09, P11), then the rest. Show the list and ask for approval of the order.

A good first week: the vault entry file with the boundaries and the PAROS status block, **the search index and the Librarian** (finding is what everything else builds on), frontmatter for new files, the task list. The learning cycle and connectors can wait.

## 2. Doing it

- One item at a time. One sentence before (what you will do), one after (what happened).
- Anything that changes existing content needs a yes first. Bulk changes (for example adding frontmatter to hundreds of files) go in small, reviewable batches.
- If an item turns out not to fit the person, do not force it: mark it `adapted` or `not needed` with the reason.
- Every finished item goes into the log at the bottom of `ADOPTION.md` with the date. This is the vault's memory of how it became a PAROS.

## 3. Checking

Each principle has a **Check** section. Run it after the item is done and record the result. Run the diagnosis again after a batch of items; the change in levels is the progress. After each run, update `open_gaps` and `next_check` in `PAROS/DIAGNOSIS.md` and the PAROS status block in the entry file (with a yes).

Adoption is done when the core principles are at level 2 or higher, and in a fresh session the agent finds what it needs on its own.
