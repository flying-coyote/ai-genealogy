---
type: RepoDoc
title: ai-genealogy Vault Conventions
status: organized
---

# ai-genealogy — Vault Conventions (AGENTS.md)

This repo is the **methodology hub**: AI-assisted genealogy best practices, platform
guides, and cross-project lessons distilled from the sister tree repos. It holds **no
family data and no PII**. Tolaria reads this file for local conventions; for Tolaria
*product* behavior, defer to the bundled agent-docs.

Type comes from frontmatter, not folder location. Every note answers *what is this?*,
*what is it useful for?*, and *is it captured / organized / archived?*

## Role in the Tolaria setup (read before adding anything)

This repo is a **passive, shared read root**. The tree repos (`~/genealogy`,
`~/genealogy-kindred`, `~/genealogy-dry-cross`) each register this directory in their own
`.mcp.json` `VAULT_PATHS`, so a research session in any tree can search this methodology
from inside its own vault. Honor this repo's no-harness rule (`CLAUDE.md`): **do not add a
`.claude/` directory, hooks, skills, or an MCP server here.** This `AGENTS.md` is
documentation, not a harness, and the backfill/promotion scripts live under
`starter-kit/scripts/` where tooling already belongs.

## Types in this vault

| Type | Frontmatter `type` | Location | Purpose |
| --- | --- | --- | --- |
| Methodology chapter | `Methodology` | `methodology/0X-*.md` | Numbered chapters: data model, evidence standards, workflow, automation, judgment gates, failure modes. |
| Platform guide | `PlatformGuide` | `platform-guides/*.md` | Per-platform behavior, APIs, and gotchas (WikiTree, Ancestry, FamilySearch, …). |
| Lesson | `Lesson` | `lessons/LESSONS.md`, `PROVISIONAL.md`, `CONTESTED.md` | Cross-project rules by lifecycle tier. |
| Philosophy | `Philosophy` | `PHILOSOPHY.md` | The underlying frame: GPS standard, mechanical work vs. judgment. |
| Repo doc | `RepoDoc` | `README.md`, `CONTRIBUTING.md` | Repo meta and onboarding. |
| Starter artifact | `StarterKit` | `starter-kit/*.md` | Drop-in templates for new tree repos (scaffolding, not live notes). |

## Lifecycle

Lessons promote `PROVISIONAL → LESSONS` once confirmed across two or more sister projects
(`[CONFIRMED ×2/3]` tags); disputed rules land in `CONTESTED`. Run
`python3 starter-kit/scripts/promote-lessons.py --check` after a session. Nothing is
deleted — supersede in place. Git is the audit trail.

## Operating notes for agents

- The Tolaria MCP server is **read-only** (search / get / list): it cannot create or edit
  notes. Write via normal file editing.
- `starter-kit/scripts/add-type-frontmatter.py` backfills the `type:` field idempotently
  and never follows symlinks (the tree repos link `docs/lessons-shared` here — that link
  must not be rewritten from this side).
- Model-version note: lessons were captured across Opus 4.6 / 4.7 / 4.8 sessions; weigh
  accordingly when a lesson reads as model-specific.
