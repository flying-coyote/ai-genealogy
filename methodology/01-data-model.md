# Chapter 1: Data Model

A genealogy project that runs AI-assisted workflows needs a data model that can be queried, validated, and patched by code — not just browsed by a human. This chapter covers how to structure that model, why flat arrays beat nested hierarchies, and what every field in a well-designed person record should carry.

---

## Why Flat Array + References

The instinctive data structure for a family tree is a nested hierarchy: a person contains their children, who contain their children, and so on. That feels natural but creates real problems at scale.

**The pedigree collapse problem.** In any lineage going back more than a dozen generations, the same ancestor appears at multiple positions in the tree. Royalty, isolated colonial communities, and endogamous ethnic groups collapse early and heavily. A true-nested representation would store the same person dozens of times with no way to ensure those copies stay in sync. When you find a new source for Thomas Wiley born 1742, you need to update one record — not hunt through every branch where he appears.

**Referential integrity and validation.** A flat array where every person has a unique ID, and relationships are expressed as ID references (`father_id`, `mother_id`, `child_ids`), lets you validate the whole graph in one pass: check that every referenced ID actually exists, that parent–child references are symmetric, that no person is their own ancestor. This catches bugs that nested structures silently hide.

**O(1) lookups.** Build an index `{id: person}` once at load time. Every subsequent lookup by ID — following a `father_id`, resolving a `child_ids` list — is constant time regardless of tree size.

**Clean AI prompting.** When you pass a person record to an AI for research or analysis, you want a flat JSON object with no recursive nesting. Flat records serialize cleanly, fit in context windows, and make prompts predictable.

---

## Top-Level Structure of `tree.json`

```json
{
  "metadata": {
    "tree_name": "...",
    "owner": "...",
    "created": "YYYY-MM-DD",
    "last_modified": "YYYY-MM-DD",
    "total_persons": 3161,
    "schema_version": "2.0"
  },
  "persons": [ ... ],
  "relationships": [ ... ]
}
```

- **`metadata`**: project identity, modification timestamp, person count, schema version. Keep `last_modified` accurate — it's your first sanity check when comparing two copies of the file.
- **`persons`**: the flat list of every person in the tree. All business logic lives here.
- **`relationships`**: optional. Use for couple relationships or non-standard kinship that `father_id`/`mother_id` can't express. Most trees don't need this array.

---

## Person Fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | GEDCOM format: `@I12345@`. Primary key. |
| `canonical_name` | string | Legal or best-known name. Use for display and search. |
| `gender` | string | `"M"`, `"F"`, `"U"` |
| `generation` | integer | 1 = subject, 2 = parents, 3 = grandparents, etc. |
| `name_variants` | list\[string\] | All known spelling variants, maiden names, aliases |
| `lineage_part` | string\|null | Which of 16 direct-line ancestor groups (see below). `null` for collateral/in-laws. |
| `birth` | event object | See Event Object section |
| `death` | event object | See Event Object section |
| `father_id` | string\|null | ID of biological father, or null if unknown |
| `mother_id` | string\|null | ID of biological mother, or null if unknown |
| `spouse_ids` | list\[string\] | IDs of spouses (all marriages) |
| `child_ids` | list\[string\] | IDs of children |
| `platform_ids` | object | External IDs by platform (see below) |
| `validation` | object | Confidence, sources, concerns (see below) |
| `research_status` | object | `{"status": "COMPLETE"\|"PARTIAL"\|"UNRESEARCHED"}` |
| `notes` | string | Free text. Scan this before queuing for research. |

---

## GEDCOM IDs

The primary identifier format is `@I12345@` — the standard GEDCOM individual identifier. When building your own tree from scratch, any unique string works, but GEDCOM format interoperates with every major platform export.

For ancestors backfilled from FamilySearch without a local GEDCOM ID, use `@I_FS_{FSID}@` (e.g., `@I_FS_LZNY-BK3@`). For ancestors backfilled from other sources without any platform ID, use `@I_{LASTNAME_FIRSTNAME}@` in uppercase. These synthetic IDs are real data — do not treat them as placeholders or rename them without updating every reference.

**Always build an ID index before working with the tree:**

```python
persons_by_id = {p['id']: p for p in tree['persons']}
```

---

## Platform IDs Object

```json
"platform_ids": {
  "wikitree": "Wiley-123",
  "familysearch": "LZNY-BK3",
  "gedcom": "I12345",
  "findagrave": "12345678",
  "ancestry": "...",
  "geni": "..."
}
```

Add fields as you find them. Check for `None` before using any platform ID — many persons will be missing one or more platforms. Platform IDs are how you push contributions back to external systems and how you avoid creating duplicate profiles.

---

## Validation Object

```json
"validation": {
  "confidence": "VERIFIED",
  "source_count": 4,
  "concerns": [],
  "corrections_applied": [],
  "evidence": {
    "source_count": 4,
    "sources": [ ... ],
    "negative_searches": []
  },
  "parent_confidence": {
    "father": { ... },
    "mother": { ... }
  }
}
```

**Critical: Two confidence fields exist.** `p['validation']['confidence']` is the canonical field used by the validator and all pipeline scripts. `p['confidence']` is a legacy field present on a small number of persons from early schema versions. Always read and write `p['validation']['confidence']`. If a script reads `p.get('confidence')` it may silently pick up a stale value.

`source_count` appears in two places: `validation.source_count` and `validation.evidence.source_count`. Both must equal `len(validation.evidence.sources)`. The validator checks this. Keep them in sync manually or run the reconcile script after bulk changes.

---

## Parent Certainty Object

```json
"parent_confidence": {
  "father": {
    "status": "confident",
    "type": "biological",
    "evidence": ["1850 census lists as son", "1860 census confirms"],
    "wikitree_status": "confirmed",
    "last_reviewed": "2026-04-01"
  },
  "mother": {
    "status": "uncertain",
    "type": "biological",
    "evidence": [],
    "wikitree_status": "unconfirmed",
    "last_reviewed": null
  }
}
```

| Status value | Meaning |
|---|---|
| `confirmed_dna` | DNA evidence confirms this parent-child link |
| `confident` | Multiple independent T1-2 sources support the link |
| `uncertain` | Limited evidence; working hypothesis |
| `non_biological` | Adoptive, step, or foster — see `type` |
| `disproven` | Evidence proves this link is wrong; retain for audit trail |

Parent certainty is tracked separately from person confidence because a person can be VERIFIED (well-documented individual) while their parentage remains uncertain.

---

## Confidence Levels

| Level | Requirement |
|---|---|
| `VERIFIED` | ≥2 independent Tier 1-2 sources, no unresolved blocking concerns |
| `PROBABLE` | ≥1 Tier 1-3 source |
| `POSSIBLE` | Tier 5 / tree-only, or no T1-3 sources; requires `upgrade_path` field |
| `UNVERIFIED` | Not yet researched |

Zero sources = POSSIBLE maximum, regardless of what a prior session set. If you inherit a tree where names have PROBABLE or VERIFIED confidence but the source list is empty, that is a data quality bug — correct it before contributing anywhere.

POSSIBLE-confidence persons may be added to the tree as research placeholders, but their relationships are never contributed to external platforms (FamilySearch tree, WikiTree, etc.). External contributions require T1-3 backing.

---

## Event Object

```json
"birth": {
  "date": "1842-03-15",
  "date_original": "15 Mar 1842",
  "place": "Augusta County, Virginia, USA",
  "confidence": "PROBABLE"
}
```

- `date`: ISO 8601. Use `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` depending on precision available. Do not invent false precision.
- `date_original`: the string exactly as it appears in the source. Preserves ambiguous dates like "abt 1842", "between 1840 and 1845", "Mar 1842".
- `place`: most-specific known place, normalized to current place-name conventions with historical name preserved in the source citation.
- `confidence`: event-level confidence, independent of person-level confidence. A person can be VERIFIED while their birthplace remains POSSIBLE.

Either field can be `null`. Always use `p.get('birth') or {}` to avoid `NoneType` errors when the event is absent.

---

## Source Object

Every source in `validation.evidence.sources` must carry these fields:

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Short display name: "1850 US Census" |
| `title` | yes | Full title as it appears in the finding aid or record |
| `tier` | yes | Integer 1-5 (see tier table below) |
| `platform` | yes | "familysearch", "ancestry", "wikitree", "findagrave", etc. |
| `type` | yes | "vital", "census", "church", "military", "probate", "newspaper", "tree", etc. |
| `added` | yes | ISO 8601 date the source was attached |
| `proves` | yes | What this source establishes: "birth 1842 Augusta County VA" |
| `evidence_type` | yes | "direct", "indirect", or "negative" |
| `ark` | recommended | Persistent URL or ARK identifier |

Missing any required field will fail schema validation. When attaching sources in bulk, always verify the field set before committing.

---

## Source Tier Table

| Tier | Category | Examples |
|---|---|---|
| 1 | Official government records | Birth/death/marriage certificates, probate records, military service records, naturalization papers, deeds |
| 2 | Near-contemporary records | Federal/state census, church registers (baptism/burial/marriage), newspapers, city directories, passenger lists |
| 3 | Published genealogies with citations | Book genealogies citing T1-2 sources, peer-reviewed genealogical journal articles |
| 4 | Family documents and oral history | Family bibles, diaries, letters, oral testimony, home photographs |
| 5 | Online trees | Ancestry member trees, FamilySearch tree, Geni, WikiTree biographies without inline citations |

Tier 5 sources are research leads, not evidence. When a tree points to a census record or birth certificate, attach the record — not the tree.

---

## The Pedigree Collapse Problem

In an ideal pedigree, 10 generations back you have 1,024 distinct ancestors. In practice, cousin marriages — common in isolated communities, nobility, and endogamous populations — mean some of those 1,024 slots are occupied by the same person. That person may appear at Ahnentafel positions 512, 768, 896, and others simultaneously.

A flat array handles this without friction. Thomas Wiley exists once in `persons`, with his own `id`. Any descendant who is also a descendant through another line just references the same ID from multiple directions. There is no duplication, no sync problem, and no confusion about which copy is canonical.

A nested tree cannot represent this cleanly. Some implementations silently drop one branch, others duplicate the person. Both create invisible data corruption.

---

## The `lineage_part` Field

`lineage_part` identifies which of the 16 patrilineal/matrilineal ancestor groups a direct-line ancestor belongs to. The exact labeling scheme is project-specific, but the field enables queries like "find all Tier 3-or-worse persons on the maternal grandfather's side."

For collateral persons (siblings of direct ancestors, spouses of collaterals, step-relatives, in-laws), `lineage_part` is `null`. Before using this field in any script, filter null values:

```python
direct_line = [p for p in tree['persons'] if p.get('lineage_part') is not None]
```

Running analytics on the full persons list without this filter inflates counts and produces misleading reports.

---

## Validation

Run the schema and referential integrity check after any bulk change:

```
python3 scripts/validate-tree.py
```

This checks: required fields present, ID references resolve, parent–child references are symmetric, source counts match, confidence levels are consistent with source counts, and no person is their own ancestor. Fix all errors before committing. The validator is the ground truth for tree health — not visual inspection of the JSON.
