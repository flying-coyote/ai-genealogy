# Geneanet

French genealogy platform with 9B+ indexed individuals, strong European church record coverage, and 7.9M+ grave photos. Acquired by Ancestry in August 2021 but operates as an independent subsidiary — no "Sign in with Ancestry," and Ancestry Premium does **not** grant Geneanet Premium.

---

## Overview

Strong for European genealogy: French état civil, German Kirchenbücher, Swiss and Austrian Catholic registers, emigration lists. Weak for US-only research.

**Two data types:**
1. **User-submitted trees** — may have Tier 1–3 sources embedded if the contributor cited original records.
2. **Partner-indexed archives** — indexed by partner organizations from original registers. Treat as Tier 2–3.

Pre-1700 rule: WikiTree explicitly lists Geneanet as a prohibited source for pre-1700 profiles, same category as FS/Ancestry trees. User trees here are Tier 5 regardless.

---

## Authentication

- Login: `https://en.geneanet.org/connexion/`
- **Free account (no Premium):** User tree data is fully visible. Archive record field names are visible, but data shows as "XXXXXX". Not usable for source citation without Premium.
- **Premium:** ~$4.55/month (pricing varies by region). Unlocks full archive record data, occupation search, spouse/parents search, name variants, and event type filters.
- **Alternative free Premium access:** FamilySearch Family History Centers (onsite only) offer Geneanet Premium access at the terminal.
- Practical tip: enable "Don't show Premium entries" in search filters to avoid clicking into masked records and wasting time.

---

## Search Endpoints

No documented REST API — all search via URL parameters. These work for browser automation and direct navigation:

**All records search:**
```
https://en.geneanet.org/fonds/individus/?nom={SURNAME}&prenom={FIRSTNAME}&from={YEAR}&to={YEAR}&go=1
```

**Surname only (minimal):**
```
https://en.geneanet.org/fonds/individus/?nom={SURNAME}&go=1
```

**With place:**
```
https://en.geneanet.org/fonds/individus/?nom={SURNAME}&prenom={FIRSTNAME}&place__0__={CITY}&zonegeo__0__={REGION_OR_COUNTRY}&go=1
```

**User tree person page:**
```
https://gw.geneanet.org/{username}?n={surname}&p={firstname}&type=fiche
```

**Full parameter reference:**

| Parameter | Value | Notes |
|---|---|---|
| `nom` | Surname | Required |
| `prenom` | Given name | Optional |
| `sexe` | `M` or `F` | Optional |
| `place__0__` | City/village name | Optional |
| `zonegeo__0__` | Region or country name | Optional |
| `from` | Start year | Optional |
| `to` | End year | Optional |
| `type_periode` | `between`, `before`, or `after` | Use with `from`/`to` |
| `go` | `1` | Always required to trigger search |
| `page` | Page number | Pagination |
| `source` | Source type filter | Optional |

---

## Evidence Tiers

| Record Type | Tier | Notes |
|---|---|---|
| Archive records (church/civil), indexed | 2–3 | Verify with original image when available |
| Archival register transcription | 2 | Volunteer extractions of parish registers |
| Emigration/departure lists | 1–2 | Often from national or state archives |
| Cemetery grave photos (Save our Graves) | 2–3 | 7.9M+ European graves, photographed in situ |
| User tree with Kirchenbuch sources cited | 3 | Quality varies by contributor |
| User tree without source citations | 5 | Leads only |
| Library/book references | 3 | |

---

## Automation Gotchas

- Search results open user tree links in new tabs (`target="_blank"`). Handle tab switching explicitly in Playwright flows.
- Cookie consent dialog appears on first visit — must be accepted before any interaction can proceed.
- No significant SPA loading delays (unlike SGGEE — see that guide for contrast).
- Duplicate entries are common: the same person appears in multiple user trees with differing data. Do not assume the first result is authoritative.
- Language barrier: records and tree notes are often in French, German, Polish, or other European languages. OCR quality on older scanned records varies.

---

## Cross-Platform Interaction Pattern

Geneanet user tree citations sometimes surface in FamilySearch "Collaborate" tabs when contributors cite them in FS discussions. When reviewing FS Collaborate notes on a disputed person, a Geneanet tree citation in a dispute comment signals that another researcher has worked this line. The Geneanet tree owner may have original sources worth contacting them about via Geneanet's messaging system.

---

## Best Uses

- **German lineages:** user trees with Kirchenbücher citations embedded in the About section are the primary value for pre-immigration German ancestors.
- **French civil registration and parish records.**
- **Pre-immigration European origins:** connecting US immigrants to departure records and European parishes.
- **Cemetery search:** `https://en.geneanet.org/cemetery/` — free, no Premium needed, European focus.
- **Collection discovery:** collection names visible in free search results let you identify which archives hold relevant records; search those same collections on FamilySearch or Ancestry.
- **Contacting European researchers:** tree owners with strong Kirchenbuch citations are worth contacting via Geneanet messaging for original materials.

---

## Not Useful For

- US-only research (essentially no US records).
- Post-immigration records.
- Detailed archive record data without Premium.
- Pre-1700 WikiTree sourcing — Geneanet is prohibited for this purpose.
