# Playbooks: how to do it, step by step

A playbook is a guided path for one thing people want to achieve with PAROS: connect a tool, build a dashboard, organise knowledge, run meetings, think with several AIs. Each one comes from how PAROS is used every day, and the advisor walks you through it in **your** vault.

Ask with `/paros <question>`, for example `/paros how do I connect two Gmail accounts?` or `/paros how do I build a dashboard on my vault?`

**Status:** `ready` has a full playbook here; `planned` means the advisor answers from the principles, skills and kits that already exist, and a detailed playbook is on the way.

## Foundations
| Playbook | What you get | Status |
|---|---|---|
| [`start-from-zero`](start-from-zero.md) | No notes yet: Obsidian installed, a vault, your agent working in it, the areas of your life in one place, a first useful result, phone, cost and privacy explained; Obsidian first, no commands to type | **ready** |
| [`organise-your-knowledge`](organise-your-knowledge.md) | Areas instead of projects, frontmatter with content descriptions, an entry file your agents read | **ready** |
| [`task-inbox`](task-inbox.md) | One task list with an inbox you drop things into unformatted; the agent sorts them | **ready** |
| `project-state` | One current-state file per long-running project or area | ready (skill: `skills/project-state`) |
| `search-your-vault` | Index-first search, ranked, in milliseconds | ready (kit: `kits/search`) |
| [`shared-memory-across-machines`](shared-memory-across-machines.md) | One agent memory for every machine: the folder lives in the vault, each machine links to it, machine-specific entries marked, main index under 200 lines | **ready** |
| [`sync-and-backup`](sync-and-backup.md) | Your vault on every device (Obsidian Sync, iCloud, Google Drive, OneDrive, Dropbox or git, chosen for you) plus a real backup with a test restore | **ready** |
| [`session-naming`](session-naming.md) | Every session titled MACHINE AREA · topic, readable on a phone; codes from your own areas; the agent renames sessions itself where the app allows | **ready** |
| [`mine-your-agent-history`](mine-your-agent-history.md) | The decisions, prices, terms and rules that live only in past agent conversations, recovered into your vault: a local digest of your own requests (secrets masked), extraction by area, each note with a yes | **ready** |
| [`keep-your-mac-awake`](keep-your-mac-awake.md) | Two Mac power modes: prezi keeps the display on while presenting, agent keeps the Mac working with the lid closed (on battery too); terminal commands and an "Agent" Focus, a two-command sudo rule, a timer and a battery guard | **ready** |

## Learning and reliability
| Playbook | What you get | Status |
|---|---|---|
| `teach-your-agents` | Corrections become rules, reviewed and integrated without compaction | ready (kits: `learn-merge`; agent: `maestro`) |
| `cognitive-cycle` | Weighted rules, visible use, a cycle report with a heat map | ready (kit: `kits/cognition`) |
| `health-checks` | End-to-end canary and checks that alert only on state change | ready (kit: `kits/health`) |
| `secrets-and-new-machines` | Secrets outside the vault, an inventory, encrypted transfer between machines | ready in part (kit: `kits/secrets`) |
| `build-your-own-skills` | Thin entries, live definitions, versions, packaging skills as plugins | ready (kit: `kits/thin-entry`) |
| [`measure-your-skills`](measure-your-skills.md) | A harness bench: fixed tasks, several models and runs, deterministic checks plus a judge; tells whether a learned rule helped and which model is good enough | **ready** |
| [`report-as-code`](report-as-code.md) | A monthly report built by code, not prose: no guessed assignments, inverse checks, a second independent parser, regression on accepted months | **ready** |

## Connectors
| Playbook | What you get | Status |
|---|---|---|
| [`connect-your-email`](connect-your-email.md) | Start here for "connect my email": a few questions (which accounts, personal or work, which provider), then the right playbook for each; work accounts checked with IT first | **ready** |
| [`connect-gmail-multiple`](connect-gmail-multiple.md) | Several Gmail accounts in parallel, each with its own token | **ready** |
| [`connect-microsoft-365`](connect-microsoft-365.md) | Outlook, Teams and SharePoint for work accounts: a check with IT first (admin approval, request template), an extra tenant through its own app and device-code login, read scopes first, a local SharePoint index with links | **ready** |
| [`connect-any-mailbox`](connect-any-mailbox.md) | Any IMAP and SMTP mailbox, password kept outside the vault, sending as a dry run unless approved; safe clean-up: delete only by UID to Trash, never expunge, one-click unsubscribe only, never from spam | **ready** |
| [`connect-google-workspace`](connect-google-workspace.md) | Sheets, Forms, Drive and Calendar from scripts, several accounts | **ready** |
| `connect-a-crm` | A CRM as the shared truth: contacts, deals, events, sign-ups synced from forms | planned |
| `connect-project-tools` | Jira, Trello, Redmine, GitHub: read freely, write with approval | planned |
| [`unified-calendar`](unified-calendar.md) | Every calendar in one agenda: noise filtered, areas tagged by rules, duplicates merged, meeting prep from your vault, invitations only with approval | **ready** |
| [`notebooklm-experts`](notebooklm-experts.md) | NotebookLM notebooks as consultable experts, with a knowledge map of what each knows | **ready** |
| [`connect-a-web-app-without-api`](connect-a-web-app-without-api.md) | Use any web app that has no API (a notebook tool, an admin portal, a social media tool your team builds) from your agent: connection ladder, your signed-in browser, a recipe note per app, the bridge rules, a skill around it | **ready** |
| [`youtube-knowledge-base`](youtube-knowledge-base.md) | Followed channels and podcasts as a searchable library with links to the exact second, notebook-ready chunks, a registry, append-only updates | **ready** |

## Thinking with AI
| Playbook | What you get | Status |
|---|---|---|
| `think-with-several-ais` | One question to several AIs (API and browser), a state file, a synthesis | ready (skill: `skills/think`) |
| `independent-judge` | A second model family that checks the first one's conclusions | ready (kit: `learn-merge/judge.py`) |

## Personal operations
| Playbook | What you get | Status |
|---|---|---|
| [`daily-briefing`](daily-briefing.md) | Today's plan from tasks, calendar and mail | **ready** |
| [`email-triage`](email-triage.md) | Every unread mail across all accounts read into prepared dossiers with draft replies: a processed-mail log, about 15 threads per run and account, "save this?" when unsure, only important mail in the journal, nothing sent without you | **ready** |
| [`capture`](capture.md) | Raw thoughts dropped in, sorted later | **ready** |
| [`recap-and-journal`](recap-and-journal.md) | What you did, from a passive activity log: a recap that states its coverage, answers "I am not doing enough" with facts, treats saved mail as data | **ready** |
| `planner-and-timeline` | A priority board and a life timeline generated from your notes | planned |

## People and money
| Playbook | What you get | Status |
|---|---|---|
| `people-notes` | Per-person notes, append-only, across areas | ready in part (agent: `iris`) |
| `household-finance` | Family bookkeeping and a budget sheet | ready in part (agent: `moneto`) |
| `business-finance` | Methodology per organization, analysis, bookkeeping behind a gate | ready in part (agent: `moneto`) |

## Content and media
| Playbook | What you get | Status |
|---|---|---|
| [`meetings`](meetings.md) | Prep, recording, transcript, intake, second pass, archive | **ready** |
| `transcribe` | Audio, video or YouTube to text, with a completeness check | ready (skill: `skills/transcribe`) |
| `podcast` | From episode prep to publishing | ready (pack: `packs/podcast`) |
| `reels-from-video` | Short clips from long video with captions | planned |
| `speed-reading` | A book or article into a structured note | ready (skill: `skills/speed-reader`) |
| `marketing-campaigns` | Campaigns, adapting to platforms, a publishing gate, a publication log | ready in part (agent: `presto`) |
| `language-editing` | Native-quality editing in any language, your rules in `LOCAL.md` | ready (skill: `skills/language-editor`) |

## Views, web and presentations
| Playbook | What you get | Status |
|---|---|---|
| [`build-a-dashboard`](build-a-dashboard.md) | No app, a zero-build view, or a React app on the same API | **ready** |
| [`publish-a-microsite`](publish-a-microsite.md) | A small website from your notes: build plus design judgement, legal pages with the real header and footer, pre-deploy checks, staging first, commit and push after every deploy | **ready** |
| [`presentations`](presentations.md) | Slide decks as code on one design system: 1920x1080 slides that stay slides on a phone, copy buttons on prompts, one shareable link | **ready** |
| [`print-design`](print-design.md) | Roll-ups, posters and banners in real centimetres: bleed, height zones, accent contrast and longest-line size measured first, the print PDF checked | **ready** |
| [`publish-from-your-vault`](publish-from-your-vault.md) | Selected views of your vault made public: generated, never hand-edited, a share gate before every deploy | **ready** |
| [`measure-your-ai-usage`](measure-your-ai-usage.md) | How you use your AI tools per machine and over time, with the traps that undercount handled | **ready** |

## Working with others
| Playbook | What you get | Status |
|---|---|---|
| [`share-with-your-team`](share-with-your-team.md) | Shared tools lead in the shared domain, your vault in its own; deliberate publish with a provenance header, pull into dated snapshots, a deny list | **ready** |
| `shared-orchestration` | Several personal systems coordinated on shared tools | planned (concept: `principles/P08`) |


Also new: [`guides/website-strategy.md`](../guides/website-strategy.md) (seven layers from identity to site, three tiers), [`guides/architecture.md`](../guides/architecture.md), [`guides/glossary.md`](../guides/glossary.md), and [`wisdom/field-lessons.md`](../wisdom/field-lessons.md): measured lessons from daily use.
