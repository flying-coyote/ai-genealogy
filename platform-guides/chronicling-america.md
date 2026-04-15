# Chronicling America (Library of Congress)

Free public API for US newspapers 1789-1963. No login required.

## Overview

Strongest coverage 1860-1920. Sparse before 1840. Geographic gaps: rural areas may have no digitized papers.

Check state coverage before searching: `https://chroniclingamerica.loc.gov/newspapers/`

**Platform sequence**: search after FS, WikiTree, FAG. Best for: obituaries (appear 1-7 days after death), legal notices (probate, land — weeks/months after event), persons in small-town US with uncommon names.

## API Endpoints

All free, no API key required.

**Search**
```
https://www.loc.gov/collections/chronicling-america/?q={query}&fo=json&c={count}&sp={page}
```

Parameters:
- `q` — query text (required)
- `fo=json` — required for JSON response
- `c` — result count per page (max 100)
- `sp` — page number (1-indexed)
- `dates` — date range, e.g. `1880/1920`
- `fa` — facet filter, e.g. `location:tennessee`

**Fulltext metadata**
```
https://www.loc.gov/resource/{LCCN}/{DATE}/ed-1/?sp={PAGE}&fo=json
```
Extract `resources[0].fulltext_file` from the response to get the OCR text URL.

**OCR text**
```
GET {fulltext_file_url}
```
Returns JSON with `full_text` field containing the raw OCR text for that page.

## Critical API Bug

Do NOT use `pagination.total` as the hit count. It counts *collections* — always returns 1 for Chronicling America, not the number of newspaper pages matched. Use `len(results)` instead.

## Cloudflare / Rate Limiting

- `www.loc.gov` resource viewer is behind Cloudflare and blocks curl and headless Chrome for page renders.
- The `tile.loc.gov` fulltext service is NOT behind Cloudflare — use for OCR text retrieval.
- At 0.5s intervals: ~60% of requests return empty or non-JSON responses. At 2.0s intervals: requests succeed reliably.
- Retry with 3s backoff on empty response. Use 2.5s between requests in production.

## Two-Phase Pipeline

**Phase 1 — Search**
Query the LOC API for persons matching name + date range + state. Collect candidate hits with LCCN, date, and page number.

**Phase 2 — Verify**
Fetch OCR text via the fulltext API. Fuzzy-match against known details: name variants, family members, place names. Classify relevance: HIGH / MEDIUM / LOW / UNLIKELY.

OCR is noisy — build fuzzy matching for common OCR substitution errors:
- `ff` → `fi`
- `m` → `rn`
- `cl` → `d`
- `1` → `l`
- `vv` → `w`

## Evidence Tiers

| Record Type | Tier | Notes |
|---|---|---|
| Obituary | 2-3 | Names relationships, death date, burial location |
| Marriage announcement | 2-3 | Often names parents |
| Legal notice (probate/land) | 2 | Actionable for proving estate timelines |
| Social note / hotel register | 4 | Proves presence in a place |
| Name-only advertisement | 4-5 | Corroboration only |

## Best Uses

- Persons who died 1850-1920, uncommon name, known US state or county.
- Obituaries for persons missing from SSDI.
- Probate notices for wills not yet found in courthouse records.
- Marriage announcements naming parents (valuable for maiden name discovery).
- Negative confirmation: "searched Chronicling America for [name] in Tennessee 1890-1910, 0 relevant results" counts as GPS Element 1 documentation.

## Not Useful For

- European ancestors.
- Pre-1840 persons (coverage very sparse).
- Common names without strong location + date filters applied.
- Persons in areas with no digitized papers — check the coverage map first.
