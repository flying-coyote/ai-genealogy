# WikiTree Platform Guide

## Overview

WikiTree is a single shared collaborative tree — all contributors edit the same profile for a given historical person, not separate copies. This means edits are visible to and reversible by the entire community. It is the most valuable platform for pre-1700 European ancestry and provides a useful cross-check against FS and Ancestry data on American lineages. The API is strictly read-only. All edits require the browser or browser automation via CDP.

**See also: [`wikitree-browser-extension.md`](./wikitree-browser-extension.md)** for the WikiTree Browser Extension capability reference (~100 features: Bio Check, WikiTree+ integration, Auto Bio, Find A Grave extractor, etc.). The extension's built-in Bio Check encodes Lukas Murphy's source-quality rules as executable logic — running it before save catches exactly the regressions he flagged.

---

## API (Read-Only)

```
Base URL: https://api.wikitree.com/api.php
```

The WikiTree API has no write actions. There is no `saveBio`, no `editPerson`, no `addPerson`. If you encounter scripts or documentation claiming otherwise, they were written speculatively and never tested — the actions don't exist. All profile edits require browser interaction (or Puppeteer/Playwright via CDP).

Common read actions:

| Action | Parameters | Returns |
|--------|-----------|---------|
| `getPerson` | `key=WikiTree-ID` | Single profile |
| `getPeople` | `keys=ID1,ID2,...` | Multiple profiles |
| `searchPerson` | `FirstName=...&LastName=...` | Search results |
| `getRelatives` | `keys=...&getChildren=1` | Family relationships |

---

## Rate Limiter

WikiTree enforces account-level edit rate limits. If you are contributing from multiple projects under the same account, use a shared rate-checker script to enforce these limits across all projects:

| Limit | Value |
|-------|-------|
| Edits per day | 50 |
| Edits per rolling 7 days | 150 |
| Minimum time between edits | 120 seconds |
| Edits per 30-minute window | 8 max |

The 120-second minimum is the anti-automation signal WikiTree monitors. Enforce it unconditionally. Violations appear to trigger account flags; at least one account was blocked after batch operations that violated this limit.

The rate checker reads and writes a shared log file at `~/.wikitree-contribution-log.jsonl` (not in any project repo — stored in home dir to be shared across projects).

---

## `getPeople` API: `bio` Field

The `bio` field (full biography text) only returns when `fields=*` is specified. Explicit field lists do not include it even if `bio` is named in the list:

```
# Does NOT return bio field:
fields=Id,Name,FirstName,LastName,bio

# Returns bio field:
fields=*
```

This is undocumented. If your script reads biography text and gets empty results, check the `fields` parameter first.

---

## Profile Discovery

WikiTree's `searchPerson` API and `getPerson` work for finding profiles. If API access is blocked or returning errors, `Special:SearchPerson` via browser POST still works as a fallback.

**Surname mismatch gap**: Discovery scripts that search by canonical surname miss profiles where the Last Name at Birth (LNAB) differs from the name in your tree. Women who married and are primarily known by married names, or persons whose name was anglicized, will not be found by surname search. For any NOT_FOUND result, also try:
- Maiden name (for women)
- Spelling variants and anglicizations
- WikiTree's own "Name Study" pages for common surname variants

Example: A person in your tree as "Rebecca Hamspacher" may be on WikiTree as profile Eis-167, where the LNAB is "Eis" and "Hamspacher" is the married name.

---

## Pre-1700 Profile Standards

FS/Ancestry member trees, Geneanet user trees, and personal genealogy websites are **prohibited as sources** for pre-1700 WikiTree profiles. These sources are Tier 5 (leads only) and are specifically excluded by WikiTree's sourcing guidelines for this period.

Acceptable sources for pre-1700 profiles:
- Original parish registers (baptism, marriage, burial)
- Wills and probate records
- Court records
- Published scholarly genealogies (peer-reviewed, with primary source citations)
- Finding aids — acceptable as pointers to primary sources, not as sources themselves

For finding aids: trace through to the original record they describe. A finding aid saying "baptism record exists at Parish X" is not itself the source. The baptism register is the source.

---

## Citation Format

WikiTree uses inline `<ref>` tags. Citations support specific facts in the biography text, not sections.

**Correct format:**
```
John Smith was born 14 March 1742 in Lancaster County, Pennsylvania.<ref>
Lancaster County Birth Register, 1742, entry for John Smith, 
[https://familysearch.org/ark:/61903/1:1:XXXX-XXXX FamilySearch ARK].
</ref>
```

After all inline citations, close with:
```
<references />
```

FS profile links (not sources — cross-platform pointers) go in a "See also:" section after `<references />`:
```
== See also ==
* [https://familysearch.org/tree/person/details/XXXX-XXXX FamilySearch profile]
```

**What not to do:**
- Do not create a separate `=== Sources ===` subsection with a bullet list of citations
- Do not use `=== Additional Records ===` or `=== Cross-Platform Profile Links ===` headers — these are non-standard
- Do not bulk-list citations at the end of the bio without inline ref tags

WikiTree's inline-citation model expects citations to appear at the specific facts they support, not collected at the bottom.

---

## Preferred Parents Correction

When correcting a parent-child relationship on WikiTree:

1. Add the correct parents first
2. Use "Set Preferred Parents" to make the correct set the displayed parents
3. Optionally remove the incorrect parents after confirming the correct set is showing

Do not remove the wrong parents first. Doing so leaves the person without parents temporarily, which can trigger merge suggestions and loses the evidence trail that explains why a correction was made.

---

## PGM Profiles (Pre-Genealogical Merit)

Pre-1500 profiles with the PGM (Pre-Genealogical Merit) tag have strict sourcing and editing standards. Before editing any PGM profile:

- Verify the person matches by birth year, death year, known spouse, and children
- Cross-conflation of historical figures with similar names is common in this period (multiple kings, nobles, and bishops with identical names across generations)
- Review the profile's existing sources and any tags indicating community oversight
- If uncertain about identity match, post to the profile's comments/talk section before editing

---

## CDP Browser Authentication

WikiTree authentication state is cookie-based. When using browser automation via Chrome CDP:

- `fetch()` calls from within the browser context inherit session cookies and work authenticated
- `page.goto()` to WikiTree pages may drop authentication state on navigation — do not rely on it for authenticated actions

For authenticated API calls from automation scripts, use `browser_evaluate` with `fetch()` rather than navigating to a URL directly. The session persists in the browser's cookie jar; `fetch()` accesses it while navigation may not.

---

## Batch Bio Updates via Puppeteer/CDP

For batch biography updates, a standalone Node.js/Puppeteer script connecting to Chrome on CDP port 9222 is the most effective approach. The pattern:

1. Connect to existing Chrome instance via CDP (`puppeteer.connect({ browserURL: 'http://localhost:9222' })`)
2. Navigate to the WikiTree edit page for the profile
3. Read the existing biography from the textarea
4. Apply the modification
5. Submit the form
6. Log the successful edit to the shared rate-checker log (`~/.wikitree-contribution-log.jsonl`)
7. Wait ≥120 seconds before the next edit

This approach has been tested at 660 profiles in approximately 8 minutes (with the minimum delay enforced, that bottleneck limits throughput far more than the actual edit operations).

**Chrome deconfliction**: CDP port 9222 is shared by all sessions. Do not run browser-using automation in the background while the main research session is using the browser. Use tab isolation (`browser_tabs`) if concurrent access is necessary — main session stays in tab 0; automation uses tab 1+.

---

## Account Flags and Recovery

WikiTree API "Access disallowed" errors can occur at the account level, independent of UI access. These are separate blocks:
- UI block: Cannot edit profiles through the browser
- API block: API calls return "Access disallowed" regardless of authentication

If API access is blocked, contact `info@wikitree.com`. UI-unblocked accounts may still have API-blocked status; these are resolved separately.

---

## Account blocking: duration and scope (2026-04-19)

When a WikiTree account triggers Error 2562 (automation rate limit), the block is both **durable** (48+ days observed) and **account-wide** (UI + API + login all fail). The account manager's identity does not transfer; blocked accounts cannot be recovered by a clean login from a new IP or session.

**Observed case**: Wiley-6910 (kurbyewiley@gmail.com) blocked 2026-03-02 after ~993 automated edits in 5 days. As of 2026-04-19 (day 48), still returns Error 2562 on every action. Email to `info@wikitree.com` did not yield recovery.

**Mitigation pattern**: use a secondary account for contributions (Wiley-6998 in the genealogy project), assigned to a mentor for supervision, with all edits via browser UI (no automation). Enforce per-account rate limits:
- 50 edits/day
- 150 edits/rolling-7-days
- ≥120s minimum between edits
- ≤8 edits per 30-minute window

Shared lockfile pattern: `~/.wikitree-contribution-log.jsonl` enforced by `scripts/wt-rate-check.py`. This is account-agnostic — protects the whole family of sister-project accounts using the same IP.

---

## Mentor-guided citation format

Per guidance from mentor Lukas Murphy (2026-04-11) on the Wiley-6998 account, WikiTree profiles should use inline `<ref>` citations with the format:

```wiki
Phillip Brogan was born about 1740 in Virginia.<ref name="brogan_families">Daniel S. Brogan, "The Brogan Families of Early America" (2011, revised 2022).</ref>
```

Pattern:
- One fact → one `<ref>` tag
- Title in quotes, publisher in italics (`''Publisher''`) when applicable
- Use FamilySearch ARK URLs when citing FS records
- FS source pages provide copy-paste-ready citation strings — prefer those over hand-written variants
- Profile prose is about the PERSON, not cross-family narrative connecting tree branches

Example profile for reference style: Reffitt-189 (timeline style), Rose Marie Clooney (narrative style).

Non-standard headers to avoid: `=== Additional Records ===`, `=== Cross-Platform Profile Links ===` — these are not WikiTree idiomatic.

## Source-quality: what NOT to cite (Lukas feedback 2026-04-21)

Three citation patterns the mentor flagged as unacceptable. These look plausible at a glance but are not valid sources for a WT profile:

### 1. WikiTree profile as source

**Bad**:
```wiki
<ref>WikiTree contributors, "James Nesbitt" (Nesbitt-1163), accessed 2026-04-13, https://www.wikitree.com/wiki/Nesbitt-1163</ref>
```

Another contributor's WT profile is not evidence. Their bio is built from *some* source — cite THAT source, not their page. If you genuinely cannot find the underlying record, drop the claim from the bio rather than cite a WT profile.

### 2. FamilySearch profile URL instead of record ARK

**Bad**:
```wiki
<ref>"FamilySearch Family Tree," FamilySearch (https://www.familysearch.org/tree/person/details/PCZW-TY2 : accessed 2026-03-02)</ref>
```

An FS person-detail URL is a navigation aid, not a source. The FS profile has specific records attached — cite THOSE, with their ARK URLs:

**Good**:
```wiki
<ref>"Maryland, Births and Christenings, 1650-1995", FamilySearch (https://www.familysearch.org/ark:/61903/1:1:HYG8-N9PZ), Jane Slater, 24 Mar 1773, Prince George's Co MD. Father: Richard Slater.</ref>
```

FS ARK URLs contain `/ark:/61903/` followed by a record identifier (`1:1:`, `3:1:`, etc.). If your URL doesn't have that pattern, it's a tree/profile URL and should not be a `<ref>`.

### 3. Vague citation with no specific document

**Bad**:
```wiki
<ref>German immigrant from Rumbach, Palatinate. Married Susan Catherine Eacus 1749, PA, accessed 28 Feb 2026</ref>
```

Problems:
- No record named (passenger list? church register? compiled genealogy?)
- Mixed facts (immigration + marriage) cited to one vague blob
- "accessed" date but no URL or archive/repository identifier

**Good** (split into two refs, one per fact, each pointing to a specific document):
```wiki
Heinrich Kern emigrated from Rumbach, Palatinate to Pennsylvania in the 1740s.<ref>"Pennsylvania German Pioneers", Volume I, Ralph Beaver Strassburger, ed. (Pennsylvania German Society, 1934), page 352: Heinrich Kern, Ship *Patience*, arrived Philadelphia 19 Sep 1748.</ref>

He married Susan Catherine Eacus on [date] in [county], Pennsylvania.<ref>Berks County, Pennsylvania, Marriage Records 1749-1800, Berks County Historical Society, Marriage of Heinrich Kern and Susan Catharina Eacus.</ref>
```

### Red-flag keywords

Before posting any `<ref>`, check whether the text contains any of:
- `accessed [date]` but no URL or archive — incomplete; add the URL or remove the ref
- `wikitree.com/wiki/XXX-NNNN` — WT profile, not a source
- `familysearch.org/tree/person/` — FS profile, not a record
- `FamilySearch. [name]. [date]. xxx` without `ark:` — missing specific record pointer
- Two facts in one `<ref>` — split into separate refs, one per record

### Audit pattern (tree.json sources)

To flag potentially-bad citations in a project's tree.json before exporting to WT:

```python
def is_suspect(source):
    url = (source.get('url') or source.get('ark') or '').lower()
    citation = (source.get('citation') or '').lower()
    # WT profile as source
    if 'wikitree.com/wiki/' in url: return 'wt_profile'
    # FS profile URL (not record ARK)
    if 'familysearch.org/tree/person/' in url: return 'fs_profile'
    # No URL + no specific document reference
    if not url and not any(k in citation for k in ['will book', 'deed book', 'page ', 'roll ', 'volume ', 'ark:']):
        return 'vague_no_url'
    return None
```

Use this as a pre-export gate, not a mass-rewrite trigger — most historical entries can be remediated during normal per-person research touches.

---

## Tier-2 remediation patterns: dangling-ref decision tree (kindred 2026-04-21/22)

**Source**: genealogy-kindred — 50 Tier-2 dangling-ref fixes across two days, zero rollbacks/2562s/manager complaints. Decision tree below was the dominant working pattern.

A "dangling ref" is a `<ref name="X">...</ref>` definition placed after `<references />` (or anywhere in the bio) with no inline `<ref name="X" />` invocation tying it to a specific factual claim. The 2026-03-01 audit flagged 117 such cases on the kindred-managed slice. Three branches resolve them; pick by inspecting the dangling ref's content vs. the bio's existing inline refs:

### Branch 1 — Exact-ARK duplicate → delete the dangling ref

If the dangling ref's ARK is byte-identical to an existing inline ref's ARK, the dangling definition adds no evidence and creates footnote clutter. Delete the dangling block; leave the inline invocation as-is.

Also applies to **circular self-refs** like `<ref name="source">WikiTree Profile Smith-123</ref>` on the Smith-123 profile itself — these have no evidentiary value and should be deleted outright (same call as the LESSONS rule "don't cite WT profiles as source").

### Branch 2 — Alt-ARK same-record → convergent invocation

If the dangling ref cites a *different* ARK that documents the **same factual claim** as an existing inline ref (e.g., a FamilySearch ARK for a 1850 census entry where the inline ref already cites an Ancestry index of the same census household), add `<ref name="dangling-name" />` next to the existing inline invocation. Both refs now flank the same claim and reinforce it. The audit's dangling-ref check passes; no generated prose needed.

This was the dominant resolution — applied to ~80% of the 50 fixes in the kindred blitz. Strongest cases were marriage and census records where Ancestry/FS/FAG cross-index the same primary source. Examples: Tucker-17772 (4 census refs paired), Spencer-33135 (marriage + 1920 census), Spencer-33138 (9 convergent refs across 5 census + marriage + burial).

A close cousin: **direct filiation from will/probate ARKs is T1 gold**. When a dangling ref points to a will that names the subject as a child or heir, it is the highest-quality evidence for filiation in the bio — invoke it inline against the parent-naming sentence specifically (e.g., Duncan-7077 `probate1820` for Charles Duncan's 1820 Daviess Co KY will naming "my son Samuel").

### Branch 3 — Different-subject ref → skip for human

If the dangling ref documents a *different person* (different name, different lifespan, contradicts bio's other facts), do not force-fit. Examples from the kindred batch: Grant-1781 (ref cites Thomas Grant + Hannah Corral marriage; bio's subject married Mary Bowden in 1726), Kindred-304 (ref cites a 1829 Susan Kindred marriage; bio's subject married Abraham Branaman in 1819 and died in 1829). These are research disputes, not formatting issues — flag in research notes, leave the bio alone.

### Skip conditions (do not edit, regardless of branch)

- **Pre-1700 birth without PGM cert**: Wiley-6998 (and any non-certified account) hits a UI textarea-lock on pre-1700 profiles. The edit page renders no editable field. Detect by birth year < 1700 and skip at queue-build time.
- **Empty/sparse bio (<200 chars, no inline refs)**: Resolving dangling refs here would require inventing inline factual sentences — exactly the automation signal that triggered the 2026-03-01 Error 2562 block. Defer to per-person research session.
- **Vague placeholder refs**: Citations like `"Published county history"` with no ARK or page number are not actionable for inline invocation. Needs human source research, not formatting cleanup.

### What this is not

This is not a general WT bio-writing pattern; it is a remediation tactic for one specific audit output (dangling `<ref name="X">...</ref>` blocks). For new content, follow the mentor-guided citation format earlier in this guide.

**Confirmed in**: genealogy-kindred (50 edits, 2026-04-21/22).
**Needs confirmation in**: genealogy, genealogy-dry-cross.
