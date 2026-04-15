# Polish Genealogy Research Portals

Free and subscription databases for Polish vital records, parish registers, and state archives.

## Overview

Polish genealogy research spans two distinct record systems:

1. **Catholic/Lutheran parish registers pre-1868** — Latin, German, or Polish; often on microfilm at FamilySearch or scanned at Geneteka/Metryki
2. **Civil registration 1868-1939+** — split by partition:
   - Russian partition: "Russian-style" metrical books
   - Prussian partition: church civil registers
   - Austrian partition (Galicia): Austrian civil registers

The Partition era (1795-1918) means records are split across Russian, Prussian, and Austrian archive systems. Knowing which partition your ancestor's village fell under determines which record series and which archive holds the documents.

## Platform Sequence

FamilySearch Catalog → Geneteka → Metryki → Szukaj w Archiwach → Ancestry (emigration/naturalization) → SGGEE (if German colonists in eastern territories)

---

## Geneteka

`https://geneteka.genealodzy.pl/`

**What it is**: The primary Polish genealogy index — volunteer-indexed vital records from hundreds of Polish parishes and civil registration offices. Not a record image host; it's an index that points to where images can be found.

**Access**: Free. No login required.

**Coverage**: 9M+ indexed records. Best coverage for Mazovia (Warsaw region), Greater Poland (Poznan region), and Galicia. Coverage varies widely by parish — check the parish coverage page before assuming a negative result is exhaustive.

**Search URL**
```
https://geneteka.genealodzy.pl/index.php?op=se&lang=eng&search_lastname={SURNAME}&search_name={FIRSTNAME}&bdm={TYPE}&from_year={YEAR}&to_year={YEAR}&region={REGION_CODE}
```

Parameters:
- `bdm`: `B` = births, `D` = deaths, `M` = marriages, `S` = other
- `region` codes: listed at `https://geneteka.genealodzy.pl/` in the region selector
- `lang=eng` for English interface

**What results show**: name, year, parish, act number, parents' names (for births), spouse name (for marriages).

**Always click through**: the "Source" link in results points to the original image on Metryki or FamilySearch Catalog. Verify the index entry against the original.

**Polish surname gender endings**: male "Kowalski" → female "Kowalska". Search both variants. This applies to most Polish surnames.

**Spelling variants across partitions**: "Wroblewski" in Polish records may appear as "Wroblewsky" or "Wroblefski" in German-partition records. Build a variant list before concluding negative results.

**Evidence tier**: The Geneteka index itself is Tier 3-4 (finding aid). The original parish register it points to is Tier 1-2.

---

## Metryki

`https://metryki.genealodzy.pl/`

**What it is**: Scanned image repository for Polish parish registers and civil records. Companion to Geneteka — Geneteka index entries link here for images.

**Access**: Free for browsing and low-resolution viewing. Free registration for high-resolution downloads.

**Coverage**: Scanned registers from many Polish dioceses. Strong for 19th-century records; pre-1800 coverage is patchier.

**Workflow**: Use Geneteka to find the act/page number, then navigate to that exact page on Metryki to view the original. Do not browse Metryki blind — use Geneteka first to identify the act number.

**Browse path**: `https://metryki.genealodzy.pl/` → region → parish → collection → page browse.

**Evidence tier**: Tier 1-2 (original register images).

---

## Szukaj w Archiwach

`https://www.szukajwarchiwach.gov.pl/`

**What it is**: The Polish state archive portal. Aggregates finding aids from all Polish state archives — Archiwum Glowne Akt Dawnych (AGAD), Archiwum Panstwowe in each voivodeship, and specialized archives.

**Access**: Free. No login for browsing.

**What to search for**: Collections not indexed on Geneteka or Metryki. Estate records, court records, notarial acts, conscription lists, census substitutes, guild records.

**Search tip**: Search by record type AND administrative location. Polish state archives organize by county (powiat) and commune (gmina). Knowing the administrative unit for your ancestor's village narrows results dramatically. Use the historical administrative division, not modern boundaries.

**Evidence tier**: Tier 1-2 for original documents accessed through the portal.

---

## FamilySearch Catalog for Polish Records

A large portion of Polish parish registers are on FamilySearch microfilm — name-unindexed, so they do not appear in person searches. Always check the FS Catalog for the specific parish and record type.

```
https://www.familysearch.org/search/catalog?place=Poland&subject=Church%20records
```

Navigate path: Catalog → Poland → voivodeship → county → town/parish → film list.

Then browse the film manually page-by-page. This finds records that Geneteka has not indexed yet — for many parishes, the microfilm is the only access point.

---

## PTG (Polish Genealogical Society)

PTG (Polskie Towarzystwo Genealogiczne) administers Geneteka and Metryki.

Their forum at `https://forum.genealodzy.pl/` is the primary community for Polish genealogy questions. Post in Polish when possible — members are overwhelmingly native Polish speakers. English questions are accepted but receive fewer responses.

---

## Partition Reference

| Region | Partition | Primary Record Type | Archive |
|---|---|---|---|
| Mazovia, Lublin, Kielce | Russian | Russian metrical books (in Russian, Latin, or Polish) | AGAD Warsaw, local AP |
| Greater Poland, Pomerania | Prussian | German civil registers, Lutheran/Catholic parish registers | Poznan, Bydgoszcz AP |
| Galicia (south/southeast) | Austrian | Latin/Polish parish registers, Austrian civil registers | Krakow, Lwow AP, Metryki |
| Silesia | Prussian/Austrian | German Lutheran/Catholic registers | Wroclaw AP, Matricula |

Knowing the partition for the specific village prevents searching the wrong archive system. Partition maps are available at `https://www.familysearch.org/en/wiki/Poland_Maps`.
