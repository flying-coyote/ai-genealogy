# Geni

Collaborative single World Family Tree (207M+ profiles). Not a records platform — purely a tree platform. Owned by MyHeritage since 2012 but operates independently: separate account, separate subscription.

---

## Overview

One tree shared by all users — edits affect everyone immediately. This is both the value and the danger.

**Profile border colors:**
- **Blue border** — claimed profile. An active member owns it; you cannot edit without their permission.
- **Green border** — unclaimed profile. Anyone in the family group can edit.

Merges are permanent. Only Geni curators can undo a bad merge. A wrong merge is worse than a duplicate — verify identity before merging, not after.

---

## Authentication

- Browser-based only. Login: `https://www.geni.com/login`
- Session persists in the browser across tabs.
- No working public API for batch operations. Discovery scripts use `requests.Session` with a CSRF token, not OAuth.
- OAuth authorization endpoint (`/platform/oauth/authorize`) returns 500 errors intermittently. Session-based login is more reliable.
- CDP browser drops session cookies on `page.goto()` navigation. For any API calls inside a browser automation context, use `fetch()` from the page context instead of navigating to the endpoint URL.

**Geni Pro vs Basic:**
- Pro: required for Merge Center (pending Tree Match dashboard) and GEDCOM export beyond the first ~100 profiles.
- Basic (free): sufficient for search, profile reads, and managing unclaimed profiles.

---

## Account Status Warning

Geni Pro subscriptions expire. After expiry, Tree Match resolution is blocked after the first free match per month. Maximize Pro features (GEDCOM export, Merge Center) before the subscription lapses — you cannot easily recapture that work later.

---

## Discovery Automation

Two-phase approach:

**Phase A — name search:** Query Geni's search database. Faster, lower quality, more false positives.

**Phase B — profile detail extraction:** Fetch full profile data for each Phase A candidate. ~3.5 seconds per profile (1.5s delay + network). ~60 minutes for 1,000 profiles.

**Apply phase:** Cross-reference candidates against your local tree, auto-apply high-confidence matches.

**Memory warning:** BFS traversal of the Ahnentafel map in discovery scripts must include a visited set. Without it, pedigree collapse causes exponential traversal and memory exhaustion. Always verify the visited-set guard before running at scale.

**Parallelism warning:** Never run Geni Phase B in parallel with another heavy discovery script (e.g., WikiTree batch discovery). Both are memory-intensive. Run one at a time.

---

## Data Quality and Evidence Tiers

All Geni data is **Tier 5 (leads only)** unless the About section cites primary sources with images.

| Source Type | Tier | Notes |
|---|---|---|
| About section with Kirchenbuch/probate citations | 3 | Quality varies — check the citation |
| Project-curated notes | 3–4 | Depends on project rigor |
| Uploaded document images | 2–4 | Depends on document type |
| SmartMatch links to MyHeritage trees | 5 | Another tree — leads only |
| Pre-1700 profiles ("Master Profile" designation) | 5 | No exceptions |
| Uncited user tree data | 5 | Leads only |

---

## Genealogy Projects (High Value)

Geni maintains thousands of curated Projects organized by ethnicity, geography, religion, and historical event. Project trees are still Tier 5, but the quality of citations embedded in About sections varies significantly by project. German colonists in Eastern Europe have especially well-built project trees.

- Browse by tag: `https://www.geni.com/projects/tag/{category}`
  - Examples: `germany`, `american-revolution`, `holocaust`, `volhynia`
- Search projects: `https://www.geni.com/project/search?q={QUERY}`

Use project profiles as leads, then verify with SGGEE, parish records, or other primary sources.

---

## Useful URLs

| Purpose | URL Pattern |
|---|---|
| People search | `https://www.geni.com/search?names={FIRSTNAME}+{SURNAME}` |
| Profile page | `https://www.geni.com/people/{Name}/{ID}` |
| Relationship path | `https://www.geni.com/path/between/{ID1}/{ID2}` |
| Surname overview | `https://www.geni.com/surnames/{SURNAME}` |
| Project tag browse | `https://www.geni.com/projects/tag/{category}` |
| Project search | `https://www.geni.com/project/search?q={QUERY}` |

The relationship path tool is free (no Pro required) and useful for quickly determining how two profiles connect across the World Family Tree.

---

## Do Not Use Geni For

- Any pre-1700 confidence claim — Tier 5 regardless of profile designation.
- Merging profiles without T1-3 evidence confirming they are the same person.
- Persons with no existing Geni presence (nothing to discover).
- Primary source research — Geni has no indexed records database.
