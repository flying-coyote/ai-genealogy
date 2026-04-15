# FamilySearch Platform Guide

## Overview

FamilySearch is the most important platform for American genealogy. It holds the largest collection of digitized vital records, census records, church registers, and probate documents — most freely accessible. It has both an API and a browser interface; they are not equivalent. FS PIDs are globally unique across the entire tree and link records across sessions. Plan to use both the API (for programmatic source harvest and profile reads) and the browser (for record search, Collaborate tab review, and relationship corrections).

---

## API Host

**Always use `api.familysearch.org`.** Never use `www.familysearch.org` for API calls. The `www` host runs behind a WAF that blocks scripted requests with `errorCode: 15`. This is not a transient error — it is a permanent block on non-browser traffic to that host.

```
CORRECT:  https://api.familysearch.org/platform/tree/persons/XXXX-XXXX
WRONG:    https://www.familysearch.org/platform/tree/persons/XXXX-XXXX
```

---

## Authentication

The `fssessionid` cookie value works as a Bearer token for API calls. Token TTL is approximately 2 hours from last activity.

**To extract the token:**
1. Open `www.familysearch.org` in Chrome
2. DevTools → Application → Cookies → `www.familysearch.org`
3. Copy the value of `fssessionid`

Use as a Bearer token in the `Authorization` header:
```
Authorization: Bearer <fssessionid value>
```

**CDP-extracted tokens**: Tokens extracted via Chrome DevTools Protocol work for read endpoints. They may return 404 on some write endpoints where a real-browser session token succeeds. Test any new write endpoint explicitly before assuming CDP tokens work — do not infer from read success.

**Token expiry**: A 401 response means the token expired. Re-extract from the browser; there is no programmatic refresh endpoint.

---

## Person Reads

```
GET /platform/tree/persons/{PID}
```

Returns full person data including name variants, vitals, and relationship IDs. Faster and more reliable than FS record search for retrieving data on a known person. Use when you have a PID and need their full profile.

---

## Source Harvest

```
GET /platform/tree/persons/{PID}/sources
```

Returns sources already attached to that FS profile. Response structure:

```json
{
  "sourceDescriptions": [
    {
      "id": "...",
      "titles": [{"value": "1880 United States Federal Census"}],
      "about": "https://familysearch.org/ark:/61903/1:1:XXXX-XXXX",
      "citations": [{"value": "Full citation text"}]
    }
  ]
}
```

Key fields:
- `titles[0].value` — human-readable source title
- `about` — ARK URL pointing to the underlying record
- `citations[0].value` — formatted citation string

**Rate**: 0.3s delay between requests is sufficient. No throttling observed at this rate for batches of 500+ profiles.

**Tier 5 filtering**: Skip sources that are other member trees, not original records. Check `titles[0].value` for these substrings (case-insensitive):
- `family tree`
- `pedigree`
- `ancestry.com tree`
- `patron submitted`
- `user submitted`
- `community tree`

**Deduplication**: Deduplicate by `about` (ARK URL) and by normalized lowercase title. The same record may appear with slightly different title formatting.

**Important**: This endpoint only returns sources *already attached* to the FS profile. It does not search the broader FS record index. A person may have highly relevant records that were never linked to their profile. See [FS Profile vs. Record Search](#fs-profile-vs-record-search) below.

---

## FS Profile vs. Record Search

These are two separate operations. Both are required for exhaustive research.

| Operation | What it finds | Endpoint |
|-----------|--------------|----------|
| Source harvest | Records already attached to the FS profile | `GET /platform/tree/persons/{PID}/sources` |
| Record search | Indexed records in the FS catalog, linked or not | Browser: `www.familysearch.org/search/record` |

A source attached to a profile is a record someone previously linked. Many records are indexed but never attached to any profile. Search both independently.

---

## Full-Text Search

For handwritten records, wills, deeds, and deed books — especially pre-1800 Southern records — the full-text search endpoint finds material that person-record search misses entirely.

```
GET /platform/records/search?q.textAvailable=true&q.fullText=%2B"Surname"&collection_id=...
```

**Critical syntax**: Use `+term` (URL-encoded as `%2B"term"`) to mark terms as REQUIRED. Two quoted phrases without `+` are OR'd silently, producing enormous irrelevant result sets. With `+`, both terms must appear in the document.

Example: To find "John Smith" in Virginia deed books:
```
q.fullText=%2B"John Smith"&collection_id=<VA deed book collection ID>
```

Finds wills, deeds, court orders, and church minutes that don't appear in the person-record index because they've never been name-indexed — only OCR'd.

---

## Parent-Child Relationship Endpoint (Critical Bug)

`POST /platform/tree/relationships` with `"type": "ParentChild"` creates **couple relationships**, not parent-child relationships. This is an undocumented FS API behavior. The `type` field is ignored.

This bug created 1,543 false couple relationships in one project before it was caught.

**Correct endpoint for parent-child links:**

```
POST /platform/tree/child-and-parents-relationships
Content-Type: application/x-fs-v1+json

{
  "childAndParentsRelationships": [
    {
      "parent1": {"resourceId": "FATHER-PID"},
      "parent2": {"resourceId": "MOTHER-PID"},
      "child": {"resourceId": "CHILD-PID"}
    }
  ]
}
```

Returns HTTP 201 on success. `parent2` is optional — omit if only one parent is known.

Do not use `POST /platform/tree/relationships` for any parent-child work.

---

## Source Description URL Patching

To add or correct the `about` URL on an existing source description:

```
POST /platform/sources/descriptions/{sourceId}
Content-Type: application/x-fs-v1+json

{
  "sourceDescriptions": [
    {
      "id": "{sourceId}",
      "about": "https://familysearch.org/ark:/61903/1:1:XXXX-XXXX"
    }
  ]
}
```

HTTP 204 = success (no response body). Use to backfill ARK URLs on sources that were created without them.

---

## Collaborate Tab

Before attaching any source to an FS profile, read the Collaborate tab on that profile's page. It surfaces:
- Known disputes about parentage or identity
- Competing parent sets with competing evidence
- Researcher notes and community flags
- Prior corrections that were reverted

Takes ~30 seconds. Prevents re-introducing errors the community already resolved.

---

## Setting Preferred Parents

To correct parentage on an FS profile:

1. Add the correct parents (do not remove the wrong parents first)
2. Use "Set Preferred Parents" to make the correct set primary
3. Optionally remove the wrong parents after verifying the correct set is showing

Removing wrong parents first leaves the person parentless mid-edit and can trigger merge suggestions or data issues. Always add before removing.

---

## FS Tree Search API (Broken)

`GET /platform/tree/search` returns 400 errors on all parameter combinations. The `q` query parameter is documented as "no longer supported." There is no working API endpoint for person search or deduplication by name/date. Use the browser search at `www.familysearch.org/search/tree` instead.

---

## Notes on Token Sources

| Source | Read endpoints | Write endpoints |
|--------|---------------|-----------------|
| Real browser session cookie | Works | Works |
| CDP-extracted cookie | Works | May fail (test each endpoint) |
| Programmatic refresh | Not available | Not available |

When a write operation returns 404 unexpectedly, the first thing to check is whether the token came from CDP vs. an active browser session.
