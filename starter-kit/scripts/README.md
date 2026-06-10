---
type: StarterKit
title: "Starter-Kit Script Inventory"
---

# Starter-Kit Script Inventory

This directory ships a small set of **portable, family-data-free** scripts that work in any
sister project. They are reference implementations and templates, not a turnkey pipeline.

The methodology chapters and lesson files also *name* many other scripts (e.g.
`reconcile-queue.py`, `wt-contribution-dispatch.py`). Those are **not** shipped here: they are
too coupled to a specific family line, platform credential, or queue layout to live in a shared
hub (see `CONTRIBUTING.md` → "What Belongs Here vs. Project-Local"). Each project implements its
own, guided by the patterns in `methodology/04-automation-patterns.md`. This file is the map of
which is which, so a new project knows what it gets for free versus what it must build.

## Provided here (portable, run as-is)

| Script | Purpose |
|---|---|
| `validate-tree.py` | Validate `tree.json` against the schema and the GPS-element / source-quality rules. `--strict` fails on warnings. |
| `recalculate-confidence.py` | Recompute VERIFIED / PROBABLE / POSSIBLE from each person's evidence array. Dry-run by default; `--apply` writes. |
| `conformance-report.py` | Read-only standards-conformance checker + ratchet gate; modes report/summary/json/baseline/gate. |
| `promote-lessons.py` | Pull-based: read a sister project's local `LESSONS_LEARNED.md` and classify each rule against the shared `lessons/`. See "Lesson pipeline" below. |
| `lint-lessons.py` | Hub-side: validate `lessons/*.md` format conformance (rule format, captured dates, PROVISIONAL fields). Runs from this repo with no sister project. Used by CI. |
| `familysearch_api.py` | FamilySearch API client wrapper (token handling, person/source queries). Import as a library or run for ad-hoc calls. |
| `add-type-frontmatter.py` | Backfill the `type:` YAML frontmatter on docs. Idempotent, dry-run by default, never follows symlinks. |
| `tolaria_verify.py` | Reference vault-integrity checker for the Tolaria read-root convention (see `AGENTS.md`). |

## Named in the docs, implemented per project (NOT shipped)

These appear in `methodology/`, `lessons/`, and `platform-guides/` as examples of the kind of
automation a mature project runs. Treat them as a **specification to implement locally**, not a
missing dependency. Names are stable across the sister projects by convention.

### Queue & tree reconciliation
- `reconcile-queue.py` — sync research / contribution queues to current tree state; catch platform-ID drift and orphaned persons.
- `apply-research-patches.py` — apply staged research patches, skipping any whose target already has the field set (no-clobber guard).
- `add-generation.py`, `add-gen7-persons.py` — bulk-add a generation of persons; watch for gen-offset bugs at import boundaries.

### GPS compliance
- `gps-compliance-report.py` — fresh GPS audit across the tree.
- `gps-element1-remediate.py` — GPS Element 1 (exhaustive search) gap remediation.
- `gps-element2-remediate.py` — GPS Element 2 (citation standardization) remediation.
- `fix-evidence-quality.py` — source-quality audit + demotion via `--only <bucket>` (e.g. `lds-t5-demote`, `legacy-nfs-demote`, `ancestry-tree-content-demote`).
- `audit-confidence-upgrades.py` — audit confidence upgrades; `--sync-top` reconciles top-line state.
- `metrics-report.py` — current confidence-distribution metrics.

### FamilySearch
- `fs-refresh-token.py` — refresh the FS session token by reading creds from the running CDP browser.
- `batch-fs-source-attach.py` — batch-attach FamilySearch sources to persons.

### WikiTree contribution
- `wt-contribution-dispatch.py` — gate WikiTree bio contributions; reject invalid `<ref>` sources before dispatch.
- `gen-wikitree-bios.py` — generate WikiTree biographies from attached sources.
- `rebuild-wt-queue.py`, `rebuild-wt-bio-queue.py` — rebuild the WikiTree contribution / bio queues with the current source-quality filters.
- `batch-wikitree-link.py` — batch-link tree persons to WikiTree IDs (typically gated to require archival sources above a generation threshold).
- `wt-playwright-post.py` — post bios to WikiTree via Playwright; injects new refs into the bio body.
- `wt-rate-check.py` — WikiTree rate-limit guard using a shared lockfile across loops.
- `wikitree-plus-fetch.py` — fetch from the WikiTree+ backend.

### Research loops
- `loop-research-dispatch.py` — autonomous lineage-extension research loop.
- `research-loop-dispatch.py` — separate maintenance loop (distinct from lineage extension).

> If you add a script to this "implemented per project" list, keep it as a *name + one-line spec*.
> Do not commit the implementation here — project-coupled pipeline code stays in the sister project
> per the boundaries in `CLAUDE.md` and `CONTRIBUTING.md`.

## Lesson pipeline: `promote-lessons.py` vs. `lint-lessons.py`

Two complementary tools, run from different places:

- **`promote-lessons.py` (pull-based, run from a sister project).** Reads that project's local
  `LESSONS_LEARNED.md`, fuzzy-matches each rule against the shared `lessons/`, and classifies it
  (`ALREADY_CONFIRMED` / `CONFIRM_THIS` / `NEW_PROVISIONAL` / `SKIP`). A human applies the result.
- **`lint-lessons.py` (hub-side, run from this repo).** Validates that the shared `lessons/*.md`
  files are well-formed so the promotion machinery and the human reviewer can trust them: rules in
  canonical format, PROVISIONAL entries carrying `**Source**` and `**Needs confirmation in**`,
  CONTESTED entries with both sides. It also reports captured-date coverage on `LESSONS.md` (it
  never invents dates — per `CONTRIBUTING.md`, dates are added when a rule is next touched).

Run both before committing lesson changes: `lint-lessons.py` keeps the catalog parseable;
`promote-lessons.py` surfaces what should move up a tier.
