# AI-Assisted Genealogy: Best Practices

A practical guide for using AI tools in genealogy research — built from hard-won lessons across three active family tree projects with 500+ research sessions.

## What this is

This repository documents a **methodology** for conducting genealogy research with an AI assistant (specifically Claude Code, though the principles apply broadly). It covers:

- How to structure tree data so AI can reason about it reliably
- Evidence standards that keep contributions defensible and retractable
- The automation pipeline from discovery through platform contribution
- Platform-specific gotchas and working API patterns
- What AI handles well, and what requires human judgment
- Failure modes we've actually hit — with case studies

## What this is not

- A data repository (no actual family data lives here)
- A software project (scripts are templates, not production tools)
- A casual tree-building guide (this targets BCG-standard research)

## Who it's for

Researchers who want to use AI to scale genealogy work without sacrificing source quality. You should already know what a census record is, what a vital record is, and why Tier 5 evidence (online trees) is not the same as evidence.

---

## Quick start

If you're starting a new AI genealogy project:

1. Copy `starter-kit/CLAUDE.md.template` → your project's `CLAUDE.md`
2. Fill in the family name, person count, and platform credentials section
3. Use `starter-kit/schema/tree.json.schema.json` to validate your data model
4. Read `methodology/02-evidence-standards.md` before your first research session

If you're here to learn the methodology without setting up a project, start with [`PHILOSOPHY.md`](PHILOSOPHY.md) then read the `methodology/` chapters in order.

---

## Repository map

```
methodology/          Core research workflow (6 chapters, read in order)
starter-kit/          Drop-in templates: CLAUDE.md, schema, core scripts
platform-guides/      FamilySearch, Ancestry, WikiTree, Find A Grave specifics
lessons/              Proven rules (LESSONS.md), open debates (CONTESTED.md),
                        unconfirmed patterns (PROVISIONAL.md)
PHILOSOPHY.md         Why this approach, the GPS standard, human-AI boundaries
CONTRIBUTING.md       How to add lessons, flag contestation, contribute as a sister project
```

---

## The three sister projects

This guide is distilled from three parallel genealogy projects:

| Project | Family line | Size | Focus |
|---|---|---|---|
| `genealogy` | Paternal direct line | ~3,200 persons, Gen 2-21 | Deep pedigree, FS lineage extension |
| `genealogy-kindred` | Maternal direct line | ~430 persons, Gen 2-14 | High-leverage audit patterns |
| `genealogy-dry-cross` | Multi-lineage (4 primary lines) | ~2,700 persons, Gen 1-16 | Multi-lineage convergence, scope control |

All three use the same methodology with the same evidence standards. Lessons discovered in one project are cross-validated against the others before being marked `[CONFIRMED]`. Rules that the projects dispute are documented in [`lessons/CONTESTED.md`](lessons/CONTESTED.md).

---

## Key concepts

**GPS compliance** — The [Genealogical Proof Standard](https://www.bcgcertification.org/resources/standard.html) has 5 elements: exhaustive search, complete citations, analysis of evidence, conflict resolution, and soundly reasoned conclusion. This is the north star; automation supports each element without shortcutting it.

**Source tiers** — Evidence quality runs Tier 1 (official records) → Tier 5 (online trees). Confidence levels are capped by source tier. Tier 5 alone never produces more than POSSIBLE confidence.

**Platform sequence** — Research platforms in this order: Ancestry → FamilySearch → WikiTree → Find A Grave → Geni → Chronicling America. The order reflects population coverage × access cost × data reliability.

**Contribution gates** — The pipeline separates discovery (automated) from contribution (staged, human-reviewed). Nothing is pushed to an external platform without a dry-run review step and human attestation.
