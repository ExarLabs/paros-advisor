# Flow 1: Tour

Goal: the person understands what PAROS is, why it works this way, and what happens next. Talk, do not lecture: short steps, a question at the end of each, and examples from **their** vault where you can (a quick look at its folder structure is allowed and helpful).

## Steps

0. **Is there a vault at all?** If the person has no notes folder yet, or has never used Obsidian, switch to [`playbooks/start-from-zero.md`](../playbooks/start-from-zero.md); the tour comes later, in small pieces, along the way.
1. **What is the agent app, what is PAROS.** Most people first meet PAROS through an agent app (Claude Code, Codex) and credit PAROS with what the app does, or the other way round. Make the split clear before anything else, with this picture: the agent app is a capable colleague; PAROS is the office the colleague works in.

   | The agent app gives | PAROS gives (it lives in your vault) |
   |---|---|
   | reading and writing files, running commands, using tools | the order of your folders, one fact in one place (P12) |
   | the conversation, the session, its context | frontmatter and a `description` for each note, so an agent can judge a file without opening it (P01) |
   | the mechanism for skills, agents and memory files | **the search index and the Librarian:** ranked answers in a fraction of a second, and a caretaker who keeps the vault findable (P06) |
   | | the learning loop: a correction becomes a rule that stays (P05) |
   | | the boundaries, backups and health checks (P00, P10, P11) |

   Then say: "Without these, you have a good assistant in a folder. With them, you have a PAROS." Ask which column they have experienced so far.
2. **One sentence.** PAROS is a person's knowledge in plain markdown, which AI agents handle through a few viewpoints, which keeps learning from use, and where fast, deterministic, shared work stays in external tools (SaaS) while judgment and glue come from the AI.
3. **The name.** Personal, Agentic, Retrieval, Operating System. Stress the R: knowledge is worth what you can bring back at the right moment.
4. **Five ideas that carry everything** (one short paragraph each, then ask if it makes sense):
   - Markdown is the truth; everything else is derived (P01).
   - An agent is a viewpoint, not a separate program (P03).
   - The system learns from every correction, with weighted knowledge, without ever rewriting what it knows (P05).
   - Nothing works without proof: every automatic process has a check on its output (P11).
   - SaaS is the backbone, AI is the glue (P08).
5. **The boundaries** (P00): what an agent never does alone.
6. **How this repository works:** it is an advisor, not a template; updates are advice.
7. **Show finding, on their own vault** (read-only). Ask for one thing they searched for recently. Find it once the plain way (the agent app's file search: count how many files it had to open and how long it took), and once through the index if the vault has one (`kits/search`). If there is no index, say what the plain search cost and that the index plus the Librarian is the first thing worth building. The difference on their own notes explains P06 better than any description.
8. **What is in the box:** besides the principles there are ready skills and kits. Name two or three that fit what you have seen of their vault, each with one sentence on what it would do for them (see [`skills/README.md`](../skills/README.md) and [`kits/README.md`](../kits/README.md)).
9. **What happens next:** offer the diagnosis (flow 2). Explain it is read-only and takes a few minutes, and that it becomes the list of gaps the advisor keeps in mind from then on.

## Tone

Plain words. No jargon unless explained. Follow their curiosity (`AGENTS.md`, "Adapt to their curiosity"): a curious person gets steps 3 to 6 in full and the reasons behind them; a hurried one gets steps 1, 7 and 9 and a one-line offer for the rest.
