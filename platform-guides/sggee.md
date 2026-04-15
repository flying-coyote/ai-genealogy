# SGGEE

Society for German Genealogy in Eastern Europe — Calgary-based society maintaining databases of Germans who settled in Russian Poland, Volhynia (Ukraine), and surrounding regions. Core coverage: 1800–1918. Partner in IGGP (International German Genealogy Partnership). Subscription-based.

---

## When to Use

Only research on SGGEE when the target person meets at least one of these criteria:

- German surname
- Known ancestry in Russian Poland, Volhynia, Podolia, Kiev, or Lublin regions
- Eastern European birth or death places (Prussia, Poland, Ukraine, Russia)
- Connection to Lutheran, Baptist, or Catholic church parishes in these regions

Skip SGGEE for persons without German–Eastern European connections. The platform is narrow in scope but deep within it.

---

## Authentication

- Login: `https://serve.sggee.org/` → hamburger menu → login option
- Subscription required for members-only databases (see below).
- Verify logged in: your email address is visible in the hamburger menu when authenticated.
- Session persists in browser.

---

## Databases

### Members-Only

| Database | Path | Content | Notes |
|---|---|---|---|
| **Master Pedigree Database (MPD)** | `/members/genealogy/search` | 572,931 pedigree records | Primary target; updated periodically |
| Lodz Trinity | `/members/lodz/search` | Lutheran records 1826–1851 | Extracted by Michael Radke, compiled by John Marsch |
| Lublin Births | `/members/lublin/birth/search` | Lublin region birth records | Volunteer parish extractions |
| Lublin Marriages | `/members/lublin/marriage/search` | Lublin region marriage records | Volunteer parish extractions |
| Lublin Deaths | `/members/lublin/death/search` | Lublin region death records | Volunteer parish extractions |
| Parish Records Index | `/members/parish-records-idx/search` | ~368,800 names | Name + parish only; no full record |
| Volhynian Archives 1900–18 (Births) | `/members/volhynian/birth/search` | Volhynia birth records | |
| Volhynian Archives 1900–18 (Marriages) | `/members/volhynian/marriage/search` | Volhynia marriage records | |
| Volhynian Archives 1900–18 (Deaths) | `/members/volhynian/death/search` | Volhynia death records | |
| Maps: Ukraine | `/members/ukraine/map/search` | Village location data | Use to find ancestral village coordinates |
| Maps: Russia-Poland | `/members/russia-poland/map/search` | Village location data | Historical German settlement locations |

### Public (No Login Required)

| Database | Path | Content |
|---|---|---|
| VKP (Volhynia/Kiev/Podolia) | `/stpete/birth/search` etc. | Parish records 1833–1885 from St. Petersburg Archives |
| Breyer Maps | `/breyer/map/search` | Historical German settlement maps |

---

## MPD Search

URL-first navigation is preferred — the search sidebar can intercept clicks on result cards in the SPA interface. Build URLs directly:

**Surname search:**
```
https://serve.sggee.org/members/genealogy/search?surname={SURNAME}&pageNum=1&perPage=50
```

**Surname + birth year range:**
```
https://serve.sggee.org/members/genealogy/search?surname={SURNAME}&birthYearStart={Y1}&birthYearEnd={Y2}&pageNum=1&perPage=50
```

**Record by ID:**
```
https://serve.sggee.org/members/genealogy/search?id={ID}&pageNum=1&perPage=10
```

**Search tips:**

- SGGEE stores spelling variants with "OR" (e.g., "GIESEL OR GISEL"). Search by one spelling — partial match finds variants automatically.
- Enable **Partial Match** for substring finds: "Ges" will find Gesell, Gieseler, Gessell.
- Birth/Death Place uses modern Polish voivodeships (e.g., "Mazowieckie") — not historical place names from the 1800s.
- Always try variant spellings before concluding a surname is absent from the database.

---

## MPD Source Codes

Source codes on MPD records identify the origin and reliability of the data:

| Code Pattern | Source Type | Tier |
|---|---|---|
| Letter + 3 digits (e.g., `A009`) | Member-submitted personal records | 3–4 |
| `SGGEExxxrN` (e.g., `SGGEE001r10`) | Volunteer-extracted parish or area records | 2–3 |
| `SGGEE001` | Central Poland parishes | 2–3 |
| `SGGEE003` | Kiev parish records | 2–3 |
| `SGGEE008` | EWZ (Einwandererzentralstelle) wartime resettlement data | 2–3 |

To obtain the original microfilm or archive film numbers for an MPD record: email `databases-sggee@googlegroups.com` with the MPD record ID. This is the path to the Tier 1–2 originals.

---

## Contributions

No self-service submission interface. Submit via email to `databases-sggee@googlegroups.com`. Include:
- GEDCOM or structured family data
- Source citations with parish names and film numbers

Data is assigned a source code and merged at the next database update cycle.

---

## SPA Loading Warning

SGGEE uses Nuxt.js. Pages display "Loading..." for 3–5 seconds after navigation before results render. In Playwright or any browser automation:

- Always wait for the loading indicator to disappear before reading results or interacting with elements.
- Prefer direct URL navigation over clicking sidebar links — the sidebar can intercept clicks intended for result cards.
- Do not assume the page is ready immediately after `page.goto()` returns.

---

## Evidence Tiers

| Source | Tier | Notes |
|---|---|---|
| VKP records (St. Petersburg Archives index) | 2 | Index only — request original film for Tier 1 |
| Lodz Trinity extracted parish records | 2 | |
| Lublin region parish extractions | 2 | |
| MPD with parish source code (SGGEExxx) | 2–3 | Volunteer extraction quality varies |
| MPD with member source code (A009 etc.) | 3–4 | Personal submission, unverified |
| Family links within MPD | 3–4 | Leads — verify with original records |

Family links (parent-child, spouse) shown in MPD records are derived from source submissions. Treat as leads that require corroboration from the underlying parish records before use as evidence for conclusions.
