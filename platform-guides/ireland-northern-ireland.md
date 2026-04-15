# Ireland and Northern Ireland Research

Civil registration and church records for Ireland and Northern Ireland. Primary platforms: IrishGenealogy.ie (free) and PRONI (onsite).

## IrishGenealogy.ie

Free public access. No login required.

**What it has**
- Ireland civil registration PDFs: births from 1864, marriages from 1845, deaths from 1864
- Catholic parish registers (baptisms/marriages) pre-civil registration, digitized for many parishes
- 1901 and 1911 Ireland Census (free, searchable by name)
- 1851 Census fragments (partial survival; limited coverage)

**Key URLs**
| Resource | URL |
|---|---|
| Civil records search | `https://civilrecords.irishgenealogy.ie/churchrecords/civil-search.jsp` |
| 1901/1911 Census | `https://www.census.nationalarchives.ie/` |
| NLI Catholic parish registers | `https://registers.nli.ie/` |

**How search results work**
The search returns a list of matching register PDFs, not individual record entries. Each PDF must be downloaded and reviewed manually. A search for a common surname in a broad county + year range may return 40+ results — open each and check whether the person matches by age, spouse name, townland, or other corroborating detail.

PDFs are downloadable as evidence. Store locally at `research/evidence/{surname}_{country}/` with the source URL noted.

**When IrishGenealogy.ie returns negative**
Document the search and escalate to PRONI for onsite access. A documented negative search on IrishGenealogy.ie is GPS Element 1 evidence (exhaustive search).

Example documentation: "Searched IG.ie civil marriage index 1845-1870 for all name variants — 0 results."

**Evidence tiers**
- Civil registers (births, marriages, deaths): Tier 1
- 1901/1911 Census returns: Tier 2
- 1851 Census fragments: Tier 2 (partial records, some transcription error)

## PRONI (Public Record Office of Northern Ireland)

Location: Belfast. Onsite access only for most records.

Finding aid (online, no record images): `https://www.nidirect.gov.uk/articles/public-record-office-northern-ireland-proni`

eCatalogue (online search of holdings): `https://www.nidirect.gov.uk/articles/using-proni-ecatalogue`

**What it has**
- Church and nonconformist registers for Northern Ireland (Anglican, Presbyterian, Catholic, Non-Subscribing Presbyterian)
- Griffith's Primary Valuation — land valuation 1847-1864
- Tithe Applotment Books — 1823-1837
- Ulster Covenant 1912 — signatories by address (useful for placing family location)
- Estate papers, will books, census substitutes

**PRONI record reference format**
References follow `{series}/{reference}`, e.g.:
- `CR4/12` = Templepatrick Non-Subscribing Presbyterian congregational records
- `MIC1/1B` = Church of Ireland, Diocese of Down

Use the PRONI eCatalogue to look up specific references before a visit. Knowing exact references saves significant onsite time.

**When PRONI becomes necessary**
- IrishGenealogy.ie negative on all name variants → PRONI church registers may have pre-1864 records
- Nonconformist families (Presbyterian, Quaker, NSP) whose registers were not submitted for civil indexing
- Estate papers for landed families: tenant lists, rent rolls, estate correspondence
- Pre-1864 Catholic registers not digitized at NLI registers.nli.ie

**Evidence tiers**
- Original church and court records: Tier 1
- Land valuations and census substitutes: Tier 2

## Research Sequence for Irish Ancestors

1. IrishGenealogy.ie civil records (births/marriages/deaths 1845+)
2. NLI Catholic parish registers (registers.nli.ie) for pre-civil registration
3. 1901/1911 Census (census.nationalarchives.ie)
4. Griffith's Valuation at AskAboutIreland.ie (`https://www.askaboutireland.ie/griffith-valuation/`) — places family in specific townland, useful for narrowing parish
5. PRONI eCatalogue — identify specific collections before onsite visit
6. PRONI onsite — church registers, estate papers, nonconformist records

## Common Research Challenges

**Townland matters**
Irish records are organized by townland, not street address. If you know the townland, you can identify the correct parish and narrow your search considerably. Townland lookup: `https://www.townlands.ie/`

**Name variants across partition eras**
Gaelic names were Anglicized inconsistently. "Ó Maolalaidh" might appear as "Molloy," "Malley," or "Mally" in different records. Search all plausible variants.

**Pre-1922 vs. post-1922 records**
Records created before the 1922 partition are held at the National Archives in Dublin (Republic) or PRONI (Northern Ireland) depending on county. Post-1922 civil registration records for Northern Ireland are held by the General Register Office of Northern Ireland (GRONI).

**1922 fire — Public Record Office of Ireland**
A large portion of pre-1922 Irish national records were destroyed in the Four Courts fire during the Civil War. Census returns for 1821-1851 are almost entirely lost. Church registers that survived are the primary pre-1860 source.
