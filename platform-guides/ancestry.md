---
type: PlatformGuide
title: "Ancestry Platform Guide"
---

# Ancestry Platform Guide

## Overview

Ancestry is the primary platform for American records from roughly 1800–1950. It holds the largest collections of U.S. federal census records, vital records, city directories, and passenger lists. The hint system is the main working interface — but the value of a hint is the attached indexed record, not the member tree conclusion that triggered the hint. Member trees are Tier 5 leads. The attached records are Tier 1–3 sources worth extracting and evaluating independently.

---

## Hints API

Ancestry has an internal JSON endpoint for programmatic hint retrieval:

```
GET /hints/api/tree/{treeId}/record?page=1&pageSize=50
```

Auth: cookie-based only (active browser session required — no API key or Bearer token). Extract the session cookie from an authenticated browser session.

Response contains JSON hint metadata including record URLs, collection IDs, hint status, and person IDs.

**Known limitation**: `category` and `group` query parameters exist in the schema but do not filter results. Any value you pass is ignored. You will always get the full unfiltered hint list regardless of those parameters.

**Update (verified 2026-06)**: this JSON endpoint now returns `{"error":null,"groups":[],"totalCount":0}` for every tree, including trees that demonstrably have thousands of pending hints, and it stays empty whether or not you echo the `sage_csrf` cookie as an `X-CSRF-Token` header. Treat the JSON endpoint as deprecated. The working paths today are the rendered hint pages: the tree-wide page `https://www.ancestry.com/hints/tree/{treeId}/hints?hf=record&hs=date` (filters `hf=record|photo|story|tree`) and the per-person page `https://www.ancestry.com/person/tree/{treeId}/person/{personId}/hints`. Read counts and collection IDs from the DOM there rather than the JSON API.

---

## Hint Card Deduplication

Each hint card contains two `hintStatus=pending` links with identical `/collections/{cid}/records/{rid}` paths. If you extract links from hint cards without deduplication, every hint is double-counted. Deduplicate by the record path (`/collections/{cid}/records/{rid}`) before processing.

---

## Review URL vs. Merge URL

Two different hint workflows exist in the UI:

- **Review URL**: The `hintStatus=pending` link. Shows the "Yes, this is a match" and "No, not a match" buttons. Use this path for accepting or rejecting hints.
- **Merge URL**: The `/merge/tree/...` path. Does not show the match confirmation button. Will not record a hint acceptance.

When scripting hint review, construct or follow the `hintStatus=pending` URL, not the merge URL.

---

## Automated Hint Triage & Acceptance

The conventional wisdom — including an earlier version of this guide — was that hint acceptance has to be manual because the accept action lives in the browser, not an API. That is half right: there is no accept API, but the browser action *can* be driven, and the per-hint human judgment can be replaced with a per-collection policy. The result is a loop that accepts known-good record hints unattended while never blind-accepting anything it doesn't recognize.

The mechanism is a **collection registry** keyed on the collection ID in each hint's review URL (`/collections/{cid}/records/{rid}`). Every pending hint resolves to one of three decisions:

- **IGNORE** — matched by URL pattern *before* any registry lookup: `PersonMatch.aspx` (member trees) and `mediaui-viewer` (member-uploaded photos, which is where the generic flag/portrait images live). Because this check runs first, member content can never be wrongly accepted through a mislabeled collection entry. Keep it first; the safety of the whole loop depends on that ordering.
- **ACCEPT** — the collection ID is in the registry as a known record collection (census, vital, probate, marriage, military/pension, church/parish, tax, land, cemetery index, immigration), tagged with an evidence tier. The engine follows the review URL, clicks "Yes, this is a match," then "Save to tree."
- **MANUAL** — the collection isn't in the registry, *or* it fails an era check (for example a post-1850 record matched to a person born before ~1800). Flagged for a human, never auto-accepted.

Three things make this safe and maintainable.

**The collection-ID space is the review-URL id, not the `hdbid` filter.** The number in `/collections/{cid}/records/{rid}` is what you classify. It is not always the same as the `hdbid` value used in the tree-wide hints filter (`?hf=record&hdbid=...`) — we have seen the two diverge for the same collection. So don't seed the registry by bulk-importing an external census-DBID list; verify each `cid → collection name` from a live hint page before adding it. A wrong tier is recoverable, a wrong decision is not.

**Unknown collections are the growth mechanism, not a failure.** Everything the registry doesn't recognize lands in a MANUAL queue carrying its live `cid → name`. Reviewing that queue and adding the unambiguous record collections is how the registry grows — a one-time dry-run scan across the highest-hint persons surfaces the long tail of collections fast, and each addition is verified rather than guessed. The registry only ever auto-accepts collection *types* a human has vetted, so the trust boundary is a few hundred collection types instead of tens of thousands of individual hints.

**Acceptance attaches on Ancestry's side, not in your local data.** Clicking "Save to tree" enriches the Ancestry tree; it does not write your `tree.json`. The durable artifact is a GEDCOM re-export after the loop runs, which matters before a subscription lapses — the accepted records survive in the export, the hint system does not.

A representative slice of the classification:

| Collection type | Example | Decision | Tier |
|---|---|---|---|
| Federal / state census | 1820 U.S. Federal Census | ACCEPT | 2 |
| Vital record | State births / deaths index | ACCEPT | 1–2 |
| Will / probate | County wills & probate | ACCEPT | 1 |
| Military / pension | War of 1812 pension files | ACCEPT | 1 |
| Cemetery index | Find a Grave index | ACCEPT | 2 |
| Member tree | Ancestry Member Trees / `PersonMatch` | IGNORE | 5 |
| Member photo | `mediaui-viewer` upload | IGNORE | — |
| Unrecognized | anything not in the registry | MANUAL | — |

The human judgment doesn't disappear; it moves up a level, from "is this the right person for this hint" to "should this collection type ever be auto-accepted." Validate the registry the way you'd validate any classifier — keep a set of known `cid → expected-decision` cases and re-run them as offline tests whenever you edit it, so a bad entry shows up as a red test rather than a wrong accept in production.

---

## County Organization Date Anachronism

County-level birthplace data from member tree imports frequently contains anachronisms. A person described as "Born in Daviess County, KY" in 1810 is impossible — Daviess County was organized in 1815. The place existed, but the county didn't.

After any bulk import of tree data or hint acceptance batch, run a scan comparing birth/death place county names against known county organization dates. Common sources of this error:
- Tree-to-tree copying where the original entry used modern county names retroactively
- Hint acceptance that pulls in place data from a different era's enumeration

Flag these as data quality issues and correct the place to the appropriate jurisdiction that existed at the time of the event.

---

## Member Tree Hints as Research Leads

Member tree hints are commonly used only for source attachment — accept if the attached record matches, ignore if it's a tree-only hint. That approach misses a secondary use.

Member trees that point to persons you can't identify, or hint at parents you don't have, are brick wall research leads. Another researcher may have sources on your brick wall ancestor that were never attached to the ancestor's own profile. These sources may exist:
- On the other researcher's tree profile for that ancestor
- In their research notes or attached documents
- Linked from the hint card as "additional records"

Before declaring a brick wall, check hint cards (including ignored ones) for the target person. If another tree shows a parent connection, trace the sources on that tree — not the tree conclusion itself, but the records attached to it.

---

## Collateral Bleed-Through

Accepting hints for spouses-of-ancestors can extend the spouse's own lineage (their parents, grandparents) rather than your direct line. This is correct behavior for building a complete family tree, but creates a problem for projects focused on a specific pedigree.

Before accepting any hint that would add new ancestors to a spouse's line, verify the person is a direct-line ancestor of the primary subject. A person who is only an ancestor of your ancestor's spouse is collateral — not wrong to research, but should be tracked separately if your project scope is a specific pedigree.

---

## Platform Search Order

For a given research target, search in this order before moving to the next platform:

1. Ancestry (primary for 1800–1950 American records, census, vital records)
2. FamilySearch (strongest for pre-1900 international and church records)
3. WikiTree (cross-check for pre-1700 European ancestry)
4. Find A Grave (death date, burial location, inscription relationships)
5. Chronicling America (newspapers 1789–1963, LOC API)

Document negative searches. A confirmed negative at Ancestry (exhaustive search, no results) is evidence of absence that saves future researchers the same time.

## Exporting the tree as GEDCOM (pre-cancellation backup)

If subscription access is ending, export each Ancestry tree to GEDCOM first — it is the most complete and irreplaceable backup, and it does not require an active subscription to download.

Steps (browser / CDP): Tree → **Settings** (`/family-tree/tree/<treeId>/settings`) → **"Export tree"** → confirm **"Export"** in the dialog. Generation is asynchronous and server-side ("Generating a GEDCOM file... (N% completed)") and **continues even if you navigate away** — so kick off all trees, then come back. When ready, a **"Download your GEDCOM file"** link appears, pointing at an authenticated `/api/media/retrieval/...` URL. The download is a **ZIP** (`<TreeName>.zip`) containing one `.ged`; the CDP browser saves it to `~/Downloads`. `unzip` may be missing on the host — extract with Python `zipfile`.

**Why it matters most:** the Ancestry working tree is frequently *much* larger than a curated local `tree.json`. In one case the Ancestry tree held ~21,855 individuals versus 5,770 in the maintained tree.json — a ~3.8× gap. The GEDCOM therefore preserves thousands of people and their attached Ancestry source citations that the curated dataset never imported. Treat the final pre-cancellation GEDCOM as the frozen reference for "what did Ancestry have."

## Mapping local persons to Ancestry person-IDs via the GEDCOM

To sweep or accept hints programmatically you need each local person's Ancestry `personId` (the value in `/person/tree/{treeId}/person/{personId}/hints`). The slow way is to search Ancestry per person and match. The fast way is already sitting in the GEDCOM you just exported: **the INDI cross-reference id is the Ancestry personId.** An exported record reads `0 @I<personId>@ INDI` (e.g. `0 @I100200300400@ INDI`), and that digit string is exactly the personId for that individual in that tree. So mapping is a local file operation — parse the GEDCOM for `INDI` xref + name + birth year, match against the local tree by normalized name and birth year (exact name + exact year as a high-confidence tier), and write the personId into `platform_ids.ancestry`. No browser, no search, no rate limit.

Two cautions. First, the Ancestry working tree and your curated tree are different populations: the Ancestry tree may be smaller (only the people you actually built there), so the discoverable ceiling is the GEDCOM's INDI count, not your local person count — persons that exist only in your local data have no Ancestry id to find. Second, some stored ids may carry a `{treeId}/{personId}` composite form or point at an *older* tree; the personId is the last path component, and a first component that isn't the current treeId flags a cross-tree mapping that needs rediscovery.

## DNA / ThruLines: verify a test is linked first

ThruLines and DNA Matches exist only when the login has a linked AncestryDNA test. Confirm before budgeting capture time: an account with no test shows "Register a kit / Buy now" at `/dna/` and 404s on `/dna/matches`. No test ⇒ no ThruLines to capture, and any DNA/Pro-Tools expiry sub-deadline is irrelevant.
