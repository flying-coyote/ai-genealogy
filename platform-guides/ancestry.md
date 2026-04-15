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

## Playwright: Ignore Button Re-query Bug

When automating "ignore all" or "click all X buttons" operations, `page.$('button.ignoreButton')` re-queries the live DOM after each click. After clicking the first button, the DOM updates, but the selector finds what appears to be the same button (now in a different state) and clicks it again. This produces incorrect behavior and may click the same button multiple times.

**Fix**: Use `page.$$('button.ignoreButton')` once to collect all element handles into an array before any clicks, then iterate the handle array:

```javascript
const buttons = await page.$$('button.ignoreButton');
for (const btn of buttons) {
  await btn.click();
}
```

This pattern applies to any "click all matching elements" operation in Playwright on Ancestry (or any React-rendered page where DOM state changes on interaction).

---

## React Combobox Date/Place Fields

Ancestry uses React-controlled inputs for date and place fields. Setting `element.value = '...'` and dispatching an `input` event sets the DOM value visibly in the UI, but does NOT update the underlying React state. When you save, the old value persists — the React component ignores the DOM mutation.

**What works for plain text fields** (first name, last name): JS setter + `dispatchEvent('input')` updates React state correctly.

**What fails for combobox date/place fields**: Same approach does not update React state.

**Fix for combobox fields**: Use Playwright native `browser_click` on the field to focus it, then `browser_type` to enter the value character by character. This triggers the actual keyboard event handlers React is listening for, and the state updates correctly.

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
