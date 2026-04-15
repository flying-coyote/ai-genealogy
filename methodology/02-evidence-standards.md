# Chapter 2: Evidence Standards

Genealogical proof is not about accumulating sources — it is about reasoning from evidence. This chapter covers the Genealogical Proof Standard, how to apply it in an AI-assisted workflow, how confidence levels map to evidence, and the specific rules that govern what gets contributed to external platforms.

---

## The Genealogical Proof Standard (GPS)

The BCG's Genealogical Proof Standard has five elements. Every genealogical conclusion you commit to your tree should satisfy all five.

| Element | What it requires |
|---|---|
| 1. Reasonably exhaustive search | All sources that could plausibly address the question have been searched, or the gaps are documented |
| 2. Complete, accurate citations | Every piece of evidence is cited well enough that another researcher can locate the same source |
| 3. Analysis and correlation | Each source is analyzed for what it directly states vs. what can only be inferred; multiple sources are correlated |
| 4. Conflict resolution | Conflicting evidence is addressed and resolved with explicit reasoning |
| 5. Soundly reasoned conclusion | The conclusion follows from the evidence; alternative interpretations are considered and excluded |

AI can assist each element — searching platforms, drafting citations, flagging conflicts, generating competing hypotheses. GPS remains a human standard. AI output is a research aid, not a proof.

---

## Source Tier Hierarchy

| Tier | Category | Examples |
|---|---|---|
| 1 | Official government records | Birth certificates, death certificates, marriage licenses, probate wills and inventories, military service records, naturalization records, land deeds |
| 2a | Original near-contemporaneous records | Church registers in original archives, contemporaneous newspapers, original passenger manifests, original draft registrations, original county deed/will books |
| 2b | Derivative/transcribed near-primary records | Indexed census transcriptions (Ancestry/FS), FindAGrave transcriptions from stones, city directories (abstracts of records), microfilm or digital copies of registers |
| 3 | Published genealogies with citations | Book genealogies that cite T1-2 sources inline, articles in peer-reviewed genealogical journals (NGSQ, TAG, NEHGR) |
| 4 | Family documents and oral history | Family bibles, diaries, letters, oral testimony, home photographs with identified subjects |
| 5 | Online trees | Ancestry member trees, FamilySearch collaborative tree, Geni, WikiTree biographies without inline citations |

The practical consequence of this hierarchy is that most of the easily accessible online material sits at Tier 5. It takes active effort to trace T5 claims back to T1-2 records — that effort is what genealogical research actually is.

---

## The Tier 5 Rule

**Online trees are research leads, not evidence.** They point to records; they do not constitute evidence.

When a FamilySearch tree or Ancestry member tree lists someone's parents, the correct action is:

1. Find the T1-2 records that tree is (hopefully) based on.
2. Attach those records as sources.
3. Cite the records, not the tree.

A claim backed only by Tier 5 sources has a maximum confidence of POSSIBLE. No exceptions.

This matters most for parent-child links. It is easy to accept a FS tree's parent assignment, tag it PROBABLE, and move on. That is how conflation spreads. Trees mix up people of the same name constantly — same given name, same surname, same general era, different people. The fact that five trees agree does not make the conclusion more reliable; they may all copy from the same original error.

---

## POSSIBLE Seeding

Newly added persons may enter the tree at POSSIBLE confidence sourced from FamilySearch tree consensus, provided:

- The person carries an `upgrade_path` field describing exactly what T1-3 evidence would promote them.
- The person is marked with the FS tree source at Tier 5.
- Their parent links are not contributed to any external platform.

POSSIBLE-seeding lets you extend a lineage speculatively for research purposes without contaminating external platforms with unverified claims. The `upgrade_path` field converts "needs more research" into a specific, actionable research target.

**The critical invariant**: POSSIBLE-confidence links are never contributed to FamilySearch, WikiTree, or any other external platform. The tree is a research workspace. External contributions require T1-3 backing.

> **Note**: POSSIBLE seeding is debated across projects. The risk is that a wrong Tier 5 link, once accepted as POSSIBLE, can attract sources for the wrong person and silently rise in confidence. See [`lessons/CONTESTED.md`](../lessons/CONTESTED.md) — "POSSIBLE seeding" entry — before adopting this pattern. The guardrails that make it acceptable: populated `upgrade_path`, validate-tree checks that flag stale POSSIBLE persons, and the non-negotiable no-external-contribution rule.

---

## Negative Searches

Documenting what you searched and found nothing is GPS Element 1 evidence. It proves exhaustive search. Record it.

"Searched Ancestry indexed vital records for Virginia death certificates 1912-1940 for John Henry Wiley; no match found" is evidence. It tells future researchers — and future AI sessions — that this avenue was already tried and is not worth retrying until new record collections are digitized.

Store negative searches in `validation.evidence.negative_searches[]` as structured entries:

```json
{
  "platform": "ancestry",
  "collection": "Virginia Deaths and Burials, 1853-1912",
  "query": "John Henry Wiley, Augusta County VA",
  "date_searched": "2026-04-15",
  "result": "no match"
}
```

Also record in the research journal. If you are running multi-agent research loops, both locations ensure the negative result survives context compaction.

---

## Required Source Fields

Every source object must carry:

| Field | What it captures |
|---|---|
| `name` | Short display name |
| `title` | Full title as it appears in the source |
| `tier` | Integer 1-5 |
| `platform` | Where you found it |
| `type` | Record type: vital, census, church, military, probate, newspaper, tree, etc. |
| `added` | Date attached (ISO 8601) |
| `proves` | What this source establishes — be specific |
| `evidence_type` | direct, indirect, or negative |
| `ark` | Persistent URL or ARK identifier |

The `proves` field is not optional. "Birth record" is not sufficient. "Birth certificate confirms birth 15 March 1842 in Augusta County VA, parents Thomas Wiley and Mary Ann Holt" is the target level of specificity. This field enables automated confidence recalculation and evidence analysis.

---

## Evidence Type

| Type | Definition | Example |
|---|---|---|
| `direct` | The source directly addresses the question without inference | A birth certificate proving the date and place of birth |
| `indirect` | The source requires inference to address the question | A 1850 census showing a 8-year-old child, from which you infer birth circa 1842 |
| `negative` | The absence of a record or entry is itself informative | No death record found in a well-indexed collection → person likely died outside that jurisdiction or time window |

Most genealogical evidence is indirect. A census does not record birth dates — it records ages, which you convert to birth years. A will that names "my son John" is direct evidence of the father-son relationship but indirect evidence of John's birth year. Track this accurately.

---

## Confidence Rules

| Confidence | Minimum evidence |
|---|---|
| `VERIFIED` | ≥2 independent Tier 1 or Tier 2a sources, no unresolved blocking concerns |
| `PROBABLE` | ≥1 Tier 1 or Tier 2a source; OR ≥2 independent Tier 2b sources from distinct derivations |
| `POSSIBLE` | No T1-2a sources; or Tier 2b/3/4/5 only |
| `UNVERIFIED` | Not yet researched |

The Tier 2a/2b distinction matters here. A church register image and a census transcription are both "Tier 2" in many systems, but only the original register qualifies as Tier 2a. Two Ancestry-transcribed census records are both Tier 2b — they can support PROBABLE together, but two 2b sources from the *same* original record do not count as independent.

"Independent" means the sources do not derive from the same original record. A transcription and the original document are not independent. Two censuses both copied from the same family's self-report are borderline — they corroborate each other but share the same informant.

**Zero sources = POSSIBLE maximum.** No script, no prior session, and no inherited tree value overrides this. If you find a person marked PROBABLE with no sources in `validation.evidence.sources`, that is a data quality bug to fix before any research session.

Any confidence upgrade must be backed by evidence that actually supports the new level. Confidence is not a research goal — it is a conclusion. Upgrading confidence to mark something "done" without the evidence is the most common data quality error in AI-assisted genealogy.

---

## Parent Certainty Tracking

Person confidence and parent certainty are tracked separately because a person can be VERIFIED (well-documented individual) while their parentage remains uncertain.

```json
"parent_confidence": {
  "father": {
    "status": "uncertain",
    "type": "biological",
    "evidence": ["1870 census lists possible father age 45 in same household"],
    "wikitree_status": "unconfirmed",
    "last_reviewed": "2026-04-15"
  }
}
```

Before contributing a parent-child link to any external platform, `status` must be at least `confident` with supporting T1-3 evidence in the `evidence` array. `uncertain` links stay in the local tree only.

---

## Concerns and Corrections

**`validation.concerns[]`** is for open issues that have not been resolved:

```json
"concerns": [
  "Death date 1891 predates documented land sale 1893 — investigate"
]
```

Any unresolved concern with temporal impossibility (death before a documented later event, birth after a documented earlier event, impossible age gaps between parent and child) blocks confidence upgrades until resolved.

When two persons in the tree are involved in the same conflict, add the concern to **both** records. A cross-record conflict that is documented on only one side is only half-documented.

**`validation.corrections_applied[]`** is for resolved corrections:

```json
"corrections_applied": [
  {
    "date": "2026-04-15",
    "issue": "Death year was 1891 in original source; land sale record 1893 proves error",
    "resolution": "Death year corrected to post-1893; likely 1895 per obituary",
    "sources": ["Augusta County deed book 14 p.223", "Staunton Spectator 1895-11-04"]
  }
]
```

This array is how you close GPS Element 4 (conflict resolution). The reasoning for every correction is preserved in the record, not just in git history.

---

## Conflict Resolution

When two high-tier sources disagree, the process is:

1. Document both sources and what they state in `concerns`.
2. Investigate which is more likely to be accurate — consider informant knowledge, timing of record creation, transcription error rates.
3. Resolve with explicit reasoning.
4. Move the resolution to `corrections_applied` with the sources that support the resolution.
5. Never silently delete a conflicting source. Retain it with a note about why it was not determinative.

A person with an unresolved concern from a T1-T2 conflict should not be upgraded to VERIFIED until the conflict is documented and resolved.

---

## The `upgrade_path` Field

For every POSSIBLE-confidence person, add an `upgrade_path` field at the person level:

```json
"upgrade_path": "Locate 1860 Augusta County VA census household to confirm family membership; obtain VA marriage record for Thomas Wiley and Mary Ann Holt 1838-1845"
```

This converts the abstract status "needs research" into a specific, actionable target. When you run out of easy wins and return to brick walls, the `upgrade_path` is what lets you triage efficiently across hundreds of POSSIBLE persons without re-reading their entire research history.

---

## Delayed Birth Certificates

Delayed birth certificates (common in the US South, often filed decades after birth for Social Security eligibility) may list a stepmother if the biological mother died before the certificate was filed. The informant is typically the person themselves, relying on memory.

Before treating a delayed birth certificate as T1 evidence for the mother's identity:

- Check a census from near the birth year for household composition.
- If the census shows a different woman as head-of-household or mother figure, investigate which woman is biological vs. step.
- The certificate proves the informant's belief at filing time, not necessarily biological parentage.

---

## Pre-1700 Standards

Pre-1700 genealogy operates under stricter standards because record survival is poor, the same names repeat across generations, and European trees are heavily conflated from centuries of copying.

**Minimum standard**: ≥2 independent Tier 1-2 sources on both the child and the claimed parent, explicitly linking them.

**Prohibited sources for WikiTree pre-1700 profiles**: Ancestry trees, FamilySearch collaborative tree, Geneanet user trees, personal websites. These are finding aids only — use them to trace a claim back to a parish register, will, or court record, then cite the original.

**Why this matters in practice**: A single conflated ancestor in a pre-1700 European noble lineage can cascade into hundreds of incorrect downstream assignments. The famous "Gateway Ancestors" (Plantagenet-line gateway immigrants) are particularly vulnerable because thousands of trees share the same lineage and the same errors.

When a lineage hits the pre-1700 wall and the only available sources are Tier 5, mark the person POSSIBLE, note the constraint in `upgrade_path`, and stop. Do not paper over the gap with tree-to-tree citations.
