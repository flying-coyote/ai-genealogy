---
type: Type
title: "tree.json source-field registry — canonical source-record keys + merge map"
status: organized
created: 2026-06-19
tags: [source-field-registry, tree-json, schema, okf, km]
---

# tree.json source-field registry

The canonical key names for objects in `validation.evidence.sources[]` across all three trees.
Same registry+merge-map discipline as `_type-registry.md`, applied to structured data instead of
markdown frontmatter, because the validation tooling (`validate-tree.py`, `recalculate-confidence.py`,
`conformance-report.py`) reads these keys — so synonym drift silently degrades them.

**Audit (2026-06-19):** 96 distinct source-record keys across the 3 trees. The well-populated ones
are real; the tail is synonym-drift (`what_it_proves` for `proves`, `record_url`/`record_link` for
`url`, `familysearch_ark`/`fs_id` for `ark`, `date_checked`/`date_found` for `date_accessed`, `note`
for `notes`) plus genuine one-offs (`sale_bidders`, `inventory_summary`). Nothing is *wrong* — it is
*inconsistent*, which is worse, because it's invisible until a tool reads the data as a schema.

**Rule:** use an accepted key; if a genuinely new field is needed, add it to "Extended" HERE first.
`scripts/okf_source_fields.py` parses this doc; `scripts/okf_source_audit.py` measures drift on a
cadence; `validate-tree.py` emits a NON-BLOCKING warning per non-accepted key (defensive — no-ops if
this doc or the module can't be read; never breaks a commit).

**Migration is NOT automatic.** This doc records the canonical set + the synonym map so a future
rewriter (gated, with `--dry-run`) can apply it; it does not rewrite `tree.json` on its own.

## Accepted source keys

### Canonical (core — every source should carry these)
`tier` · `evidence_type` · `proves` · `citation` · `title` · `name` · `platform` · `type` · `url`

### Extended (legitimate, optional — keep, do not warn)
`ark` · `added` · `added_by` · `added_date` · `date_accessed` · `accessed` · `manual_review` ·
`notes` · `concerns` · `disproves` · `does_not_prove` · `supports` · `source_type` · `record_type` ·
`citation_type` · `description` · `key_facts` · `published_work` · `classification_note` ·
`legacy_nfs` · `fs_attachment` · `fs_attached` · `ancestry_dbid` · `demote_log` · `tier_audit` ·
`tier_original` · `match_confidence` · `match_score` · `date` · `repository` · `collection` ·
`collection_id` · `fhl_film` · `image` · `image_id` · `record_id` · `local_pdf` · `local_copy` ·
`place` · `category` · `reference`

> `name` vs `title`: kept distinct (a 2026-05-26 size optimization omits `name` when identical to
> `title`); `validate-tree.py` already treats them as interchangeable for the "missing both" check.
> `source_type` (27k uses) is kept canonical rather than force-merged into `type` — verify their
> semantics differ before any merge; flagged but not collapsed.

## Merge map (drift → canonical; record the intent, migrate later under --dry-run)

| Drift key(s) | → canonical |
| --- | --- |
| `what_it_proves`, `proves_parentage`, `evidence_supports`, `proves_previous` | `proves` |
| `record_url`, `record_link`, `ancestry_record`, `ancestry_id`, `wikitree_ref`, `wikitree_profile`, `fag_index` | `url` |
| `familysearch_ark`, `familysearch_id`, `fs_id`, `fs_source_id` | `ark` |
| `date_checked`, `date_found`, `date_verified`, `date_attached_fs`, `audit_date`, `date_source` | `date_accessed` |
| `note`, `note_source`, `reliability_note`, `proves_note`, `interpretation`, `detail` | `notes` |
| `archive_ref` | `repository` |
| `platform_source`, `platform_type` | `platform` |
| `contributed_to_fs`, `attached_to`, `discovered_via`, `found`, `is_metadata`, `phase7b_patched`, `tier5_skip`, `structural_invalidity`, `demotion_reason`, `sale_bidders`, `inventory_summary`, `transcript_excerpts` | fold into `notes` (one-off content) |

## Related: validation-level confidence keys (separate concern)

At the `validation` level (not source records), three keys exist for one concept: `confidence`
(canonical, ~per-person), `confidence_level` (66 uses), `confidence_audit` (the audit-trail list).
`confidence` is canonical; `confidence_level` → `confidence`; `confidence_audit` is a distinct
audit-trail field, keep. Tracked here for visibility; enforce via the same okf_source_fields path
if it proves worth it.
