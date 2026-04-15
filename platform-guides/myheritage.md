# MyHeritage

Commercial genealogy platform with a records database, smart matching, and the OldNews.com newspaper archive. Acquired Geni in 2012 but operates independently.

---

## Overview

**MyHeritage Premium ≠ Geni Pro.** They are separate subscriptions despite being sister platforms. Buying one does not grant access to the other.

**Primary unique value vs other platforms:** The OldNews.com newspaper archive. This collection is not on FamilySearch or Ancestry. It is the main reason to check MyHeritage after exhausting other platforms.

Census records on MyHeritage mostly duplicate what FamilySearch and Ancestry already have — low incremental value for those record types.

---

## Authentication

- Browser-based. No documented public REST API for genealogy data.
- MyHeritage Premium required for: record access, full SmartMatch results, and the Geni bridge pipeline.
- Session persists in browser.

---

## OldNews.com — The Unique Value

Old newspapers digitized by MyHeritage and not available on FS, Ancestry, or Chronicling America. Content includes:
- Obituaries
- Birth and marriage announcements
- Legal notices and estate settlements

Search via MyHeritage record search; newspaper results are labeled with the source publication name. Treat OldNews results as:

| Condition | Tier |
|---|---|
| Dated newspaper with verifiable publication name | 2–3 |
| Undated or publication unclear | 4 |

---

## The Geni–MyHeritage Bridge Pipeline

For researchers with both active Geni Pro and MyHeritage Premium accounts, a bridge pipeline extracts MyHeritage record URLs from Geni's Merge Center SmartMatch suggestions:

1. **`--discover` phase:** Scrapes the Geni Merge Center for SmartMatch forward URLs. Requires active Geni Pro + MyHeritage Premium. Browser-based — no API shortcut.
2. **`--extract` phase:** Follows each forward URL from Geni to the MyHeritage record page. Browser-based, requires MH Premium.
3. Creates a URL list + JSONL progress file. Crash-safe and resumable.

**Critical efficiency step:** Filter the URL list to in-tree persons before extraction. In practice ~10% of discovered URLs belong to persons already in your tree; extracting all URLs wastes roughly 3 hours on unrelated people.

**Extraction rate:** ~1 URL per 10 seconds.

**Post-extraction triage:** OldNews.com newspaper hits are the primary value. Census records surfaced here are usually already in the tree from FS or Ancestry — skip them unless they add new information.

---

## SmartMatches

SmartMatch links a Geni profile to a MyHeritage tree profile. Both sides of the match are Tier 5.

Use SmartMatches to:
- Find MyHeritage tree owners who may have original documents to share.
- Discover OldNews.com newspaper articles attached to the matched profile.

Do not attach SmartMatch results as sources. Attach the underlying record they cite (if one exists with an image or verifiable citation).

---

## Data Quality

| Source Type | Tier | Notes |
|---|---|---|
| Census records | 2 | Usually duplicates FS/Ancestry |
| Vital records (birth, marriage, death) | 1–3 | Depends on originating archive |
| OldNews.com newspaper articles | 2–3 | Same standard as Chronicling America |
| SmartMatch tree links | 5 | Leads only |

---

## When MyHeritage Is Worth Checking

- After exhausting Ancestry and FamilySearch for newspaper evidence.
- When a Geni profile has SmartMatch suggestions pointing to MyHeritage records.
- For persons where obituaries or announcements are the primary remaining evidence type.
- When the Geni–MyHeritage bridge pipeline is active and subscription status allows.

---

## When to Skip

- Without an active Premium subscription: census, vital, and newspaper records are inaccessible.
- For record types already covered by FamilySearch and Ancestry (census, vitals) unless there is a specific reason to believe MH has a different copy.
- For persons without any Geni SmartMatch presence — the bridge pipeline has nothing to discover.
