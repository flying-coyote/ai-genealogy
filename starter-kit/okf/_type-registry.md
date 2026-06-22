---
type: Type
title: "Genealogy vault type registry — canonical OKF frontmatter types"
status: organized
created: 2026-06-19
tags: [type-registry, vault-conventions, okf, km]
---

# Genealogy vault type registry

The canonical `type:` values for the genealogy knowledge graph, spanning all three tree
repos (`~/genealogy`, `~/genealogy-dry-cross`, `~/genealogy-kindred`) and the shared
methodology hub (`~/ai-genealogy`). This is the **single source of truth** that the OKF
reader parses (`scripts/okf.py:load_canonical_types`) — the guard can never disagree with the
doc because it reads these same bytes. It consolidates the six-type convention previously
duplicated as prose across the three `research/AGENTS.md` files.

**The rule:** pick a type from this registry when creating a note; if none fits, add the new
type HERE first (one line + rationale), so the registry stays the inventory instead of drifting
behind it. The merge map records consolidations so old values stay greppable in git history.

**Boundary (PII):** the OKF tooling is local-file + local-script only (`pathlib` + `PyYAML` +
`json`, no network). `scripts/okf.py` SKIP_DIRS excludes `data/`, `backups/`, and caches so the
reader structurally cannot pick up `tree.json` or per-record family data. Never point a
hosted-egress step (graphify Pass 2, embedding indexers, hosted vector DBs) at the journal
corpus or `tree.json`.

## Canonical types (12)

| Group | Types |
| --- | --- |
| Per-person research | `ResearchJournal` · `Session` · `BrickWall` · `Correction` |
| Narrative & planning | `FamilyNarrative` · `StrategyDoc` · `Report` · `Audit` |
| Reference (hub + repos) | `RefDoc` · `Methodology` · `PlatformGuide` · `Lesson` |

Definitions:
- `ResearchJournal` — per-person research log (`research/journals/@ID@.md`); the per-person graph node, and the single source of truth for observed platform claims + classified disagreements + research status. Already in use. **Frontmatter v2 contract:** `starter-kit/schema/journal.schema.json` (a strict superset — `platform_identity`, `disagreements[]`, derived `status_summary`; pre-v2 extras stay valid). Written only through `starter-kit/scripts/journal_io.py`. See `methodology/07-cross-platform-reconciliation.md`.
- `Session` — dated research-session log (`research/sessions/`). Already in use.
- `BrickWall` — an open research blocker + status (`brickwall_*.md`, `research/brick-walls/`). Already in use.
- `Correction` — a documented detach / ID-swap / disproof (`data/corrections/`). Already in use.
- `FamilyNarrative` — family-history prose for a person/line/place (`research/narratives/`). New 2026-06-19 (the Vanport chapter is the first).
- `StrategyDoc` — planning + priority docs (`research/RESEARCH_PRIORITY_PLAN.md`, `research/DEADLINE_MATURATION_LOOP_*.md`). Already in use.
- `Report` — handoffs, dispositions, sweep outputs (`data/reports/*.md`). New — currently the biggest untyped cluster (0/100 typed as of 2026-06-19).
- `Audit` — confidence / source / conformance audits (`*_audit_*.md`). New (fold into `Report` if you'd rather stay at 11).
- `RefDoc` — schema, tooling, workflow guides (`docs/*.md`). Already in use.
- `Methodology` — public method docs (`~/ai-genealogy/methodology/`). New (hub only).
- `PlatformGuide` — per-platform how-to (`~/ai-genealogy/platform-guides/`). New (fold into `RefDoc` if preferred).
- `Lesson` — `[CONFIRMED ×N]` methodology lessons (`~/ai-genealogy/docs/lessons-shared/`, `PROVISIONAL`, `CONTESTED`). New.

Deliberately **no `Person` type**: persons live in `data/tree.json` as structured data
(vitals, `father_id`/`mother_id`/`spouse_ids`/`child_ids`, `platform_ids`,
`validation.evidence.sources[]`). Each person is represented in the graph by their
`ResearchJournal`, joined to `tree.json` by id (see `scripts/okf_signals.py` bridge). Do NOT
promote persons to markdown notes — it would create two sources of truth for every vital.

## Intentional singletons (declare, never merge)

One file each, by design — excluded from the "used once = drift" audit:
`README` · `AGENTS` · `MEMORY` (per-project memory index) · `brickwall_INDEX` ·
`TOOLS-TRACKER` · `PHILOSOPHY` · `Type` (this registry + any `_type-*` stub) ·
`collection-index` (generated INDEX surfaces).

## Merge map (markdown types)

The markdown type set has **not** drifted yet (journals were typed from creation; the gap is
*untyped* files — `data/reports/*.md` — not mis-typed ones). No consolidations needed today.
This section exists so the parser's region scan terminates here, and so future drift is
recorded rather than silently rewritten. First expected entries when backfill runs:

| Old | → |
| --- | --- |
| _(none yet — backfill `data/reports/*.md` to `Report`/`Audit`, don't invent synonyms)_ | |

## Related registry (separate, planned)

The `tree.json` **source-field** schema HAS drifted badly — 60 distinct key names in
`validation.evidence.sources[]` (kindred), with synonym clusters (`url`/`record_link`/
`record_url`/`familysearch_ark`/`ancestry_record`; `citation`/`title`/`name`;
`date_accessed`/`date_checked`/`date_added`/`date_verified`/`date_found`) and three keys for
one concept (`confidence`/`confidence_level`/`confidence_audit`). That deserves the same
registry+merge-map discipline, but as a SEPARATE **source-field registry** next to
`tree.json.schema.json`, enforced by `validate-tree.py` (warn on non-canonical keys) — it is
not a markdown `type:` concern and is tracked as the next OKF work item, not folded in here.
