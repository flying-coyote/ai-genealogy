# Chapter 6: Failure Modes

This chapter catalogs things that actually went wrong across three sister genealogy projects. The goal is not to document embarrassment but to build a warning system. Most of these failures were not obvious in advance. Several repeated across projects before the pattern was recognized.

Each entry includes what happened, what the consequence was, and what the fix looks like. Read this before starting any new automation campaign.

---

## 1. Wrong API Endpoint: 1,543 False Couple Relationships

**What happened:** `POST /platform/tree/relationships` with `"type": "ParentChild"` in the request body creates COUPLE relationships regardless of the type field value. This is an undocumented FamilySearch API behavior. The correct endpoint for parent-child relationships is `POST /platform/tree/child-and-parents-relationships`.

**Consequence:** 1,543 false couple relationships were created across multiple sessions before the bug was caught. Each had to be identified and deleted individually via the FS API. The cleanup consumed a full session.

**Fix:**
```
POST /platform/tree/child-and-parents-relationships
Body: {"childAndParentsRelationships": [{"parent1": {"resourceId": "..."}, "child": {"resourceId": "..."}}]}
```

**Detection method:** After any FS relationship contribution, open the person's profile on the FS website and verify the relationship type is listed as parent-child, not as a couple relationship. Do this for the first contribution in any new batch before running the rest.

---

## 2. CDP Session Tokens Failing on Write Endpoints

**What happened:** The `fssessionid` cookie extracted via Chrome CDP returned HTTP 404 on `POST /platform/tree/child-and-parents-relationships`. The same endpoint, same request body, using a token extracted from a real browser DevTools session, succeeded.

**Root cause:** Unknown. Likely AWSELB sticky-session routing or FS flagging sessions originating from CDP-automated contexts. The two token sources produce functionally different sessions.

**Consequence:** An entire contribution campaign stalled until the token source was changed. Hours of debugging what appeared to be a body format issue.

**Fix:** Extract the `fssessionid` from a real browser DevTools session (Network tab, any FS API request, copy the Cookie header). Do not use CDP-extracted tokens for write operations. Test any new write endpoint with a single request before building a batch around it.

---

## 3. Source Deduplication Failure: 17,379 Duplicate Sources

**What happened:** The harvest script deduplicated by ARK URL only. Sources added before the ARK backfill campaign had no `ark` field — only a title. These sources were not caught by the deduplication check and were re-added on every harvest pass.

**Consequence:** Source counts were inflated by roughly 50%. After deduplication cleanup, 153 persons had their confidence downgraded because their inflated source counts had been pushing them above the PROBABLE threshold.

**Fix:** Deduplicate by ARK first, then by normalized lowercase title as a fallback. Store both `ark` and `url` on every source object from the point of creation. Track which profiles have been harvested in a progress file (JSONL is good — crash-safe and resumable) to prevent re-processing profiles across sessions.

---

## 4. Staged Patches Silently Dropped on Apply

**What happened:** The apply-research-patches.py script skipped any patch where the target person already had a non-null `father_id` or `mother_id`. The logic was: if either parent is set, the research is done. But many patches were for the other parent — father already set, patch is for the mother, or vice versa.

**Consequence:** Roughly 30% of valid patches were silently discarded. Progress metrics appeared lower than actual work warranted. Some valid lineage extensions were delayed by multiple sessions before the bug was found.

**Fix:** The apply script must check which specific parent field the patch sets before deciding to skip. The correct guard: if `patch.field == "father_id"` and `person.father_id is not None`, skip. If the patch targets a field that is null, apply it.

**Detection:** After any apply run, compare the count of patches in the input report against the count of changes made. A significant gap (>10%) warrants investigation.

---

## 5. WikiTree Discovery Missing LNAB-Different Profiles

**What happened:** WikiTree discovery scripts searched by the surname in the tree's canonical name. For women whose WikiTree Last Name at Birth (LNAB) differs from the married name stored in the tree, the WT profile was missed entirely. Example: tree had "Rebecca Hamspacher" (married name) but the WT profile was listed under LNAB "Eis" as Eis-167.

**Consequence:** Known WT profiles went undiscovered for months. WT IDs were not linked; contributions were blocked because the profile appeared to not exist.

**Fix:** For any woman in the tree, search WT by maiden name, married name, and any known name variants. Check FS profiles' "See Also" sections — FS sometimes links the WT profile directly. Cross-reference NOT_FOUND candidates against the FS platform ID's linked profiles before concluding the WT profile doesn't exist.

---

## 6. BFS Traversal Without Visited Set: Memory Explosion

**What happened:** A discovery script built an Ahnentafel map via BFS traversal of the family graph. The traversal had no visited set. In trees with pedigree collapse — where the same ancestor appears in multiple lineages — the BFS revisited nodes exponentially. Ahnentafel numbers grew to thousands of digits. Memory usage climbed until the session crashed.

**Consequence:** Two session crashes before the root cause was identified. The script appeared to run normally for the first few minutes, then consumed all available memory.

**Fix:**
```python
visited = set()
while queue:
    cur = queue.pop()
    if cur in visited:
        continue
    visited.add(cur)
    # ... process cur
```

Always use a visited set in any BFS or DFS traversal of the family graph. Pedigree collapse is not rare — it occurs whenever two lines of a tree share a common ancestor, which is common in any population with limited geographic mobility over multiple centuries.

---

## 7. Wrong Person Confirmed: John Francis Conflation

**What happened:** FamilySearch had two John Francis profiles with similar names but different birth years: 1598 and 1658. The discovery script matched on name and approximate generation without verifying the birth year. Sources from the 1598 John Francis were attached to the profile for the 1658 John Francis.

**Consequence:** Incorrect sources were attached and propagated. The WikiTree community caught the conflation and flagged the profile. Retracting the contribution required manual cleanup and community communication.

**Fix:** Always verify birth year, death year, and spouse name before accepting a FS or WT profile match. A name match alone is not a person match. For any profile match, the script should require name AND birth year within a configurable tolerance (±5 years is reasonable for pre-civil-registration births). Matches outside that tolerance should be flagged for manual review, not auto-accepted.

---

## 8. Collateral Bleed-Through via Ancestry Hints

**What happened:** Accepting Ancestry hints for a spouse-of-ancestor pulled in the spouse's paternal line. None of these people are direct ancestors. They ended up in the tree, generated research targets, and triggered source attachment and GPS compliance work.

**Consequence:** Research effort spent on persons who will never be contributed and whose parent gaps don't belong in the active queue. The effect compounds: adding collateral relatives adds their source gaps, which add to GPS metrics, which look like work needing to be done.

**Fix:** Before accepting any hint that would extend a person's own lineage (not just confirm their identity), verify that person is in the ancestor set of the primary research subject. For spouses of ancestors: accept identity-corroborating hints (birth records, death records, census appearances that confirm they are the right person). Do not accept hints that add parents, grandparents, or siblings of the spouse.

---

## 9. VERIFIED With Zero Sources: Validator Blind Spot

**What happened:** The schema validator checked that confidence level was a valid enum value. It did not check whether the confidence level was consistent with the number of attached sources. VERIFIED with an empty sources array passed validation.

**Consequence:** Two VERIFIED persons with zero sources entered production. The error was caught by the GPS compliance audit, not the basic validator.

**Fix:** Add an explicit check in validate-tree.py:

```python
if person['validation']['confidence'] == 'VERIFIED':
    assert len(sources) >= 2, f"{person_id}: VERIFIED with {len(sources)} sources"
if person['validation']['confidence'] == 'PROBABLE':
    assert len(sources) >= 1, f"{person_id}: PROBABLE with 0 sources"
```

Run this check in the validator, not just in the GPS audit, so it catches violations as close to the point of introduction as possible.

---

## 10. Priority Plan Staleness: Researching Already-Resolved Brick Walls

**What happened:** The research priority plan listed several brick walls as active targets. Some had been resolved in sessions 3-4 sessions earlier, but the plan was not updated at session close. A research agent was dispatched to investigate a person whose parents had already been found and linked.

**Consequence:** Wasted session time re-investigating resolved questions. The agent found the same evidence that had already been acted on and produced a redundant report.

**Fix:** Make "update RESEARCH_PRIORITY_PLAN.md" a mandatory closing checklist item for every session. Resolved brick walls must be moved to the completed section in the session they are resolved, not in a future cleanup pass. The priority plan is only useful if it reflects current state.

---

## 11. Context Compaction Losing Mid-Session Research

**What happened:** AI context compaction dropped research findings from earlier in the session. Journal entries that had not yet been written to disk were lost. The session appeared — in both the AI's context and in the commit log — to have covered more ground than it actually preserved.

**Consequence:** The next session repeated platform searches that had already been done. Negative search results (which prove exhaustive research) were not documented and had to be regenerated.

**Fix:** Write journal entries in real-time during research, not as a closing batch. The journal file survives compaction; in-context notes do not. Specifically: after completing research on any platform for a person, write that finding to the journal before moving to the next platform. "Checked Ancestry vital records for John Francis 1658 VA — found 1680 will naming son Thomas, no parents named" is a sentence, not a distraction.

The journal is not documentation overhead. It is the only record that persists across context boundaries.

---

## 12. Delayed Birth Certificate Misidentifying the Mother

**What happened:** A delayed birth certificate — filed 30 years after the birth — named a woman as the mother. The biological mother had died shortly after the birth. The certificate named the current household mother, who was the stepmother. The certificate was accepted as a T1 source identifying the biological mother.

**Consequence:** Wrong mother linked in the tree with PROBABLE confidence, sourced to what appeared to be a primary record.

**Fix:** For any delayed certificate (filed more than 5 years after the birth event), cross-check the named "mother" against the census household at the year of birth. The nearest census to the birth date, showing who was actually in the household as wife/mother, is more authoritative than a delayed certificate recalling household composition decades later. A contemporary death record for the biological mother before the delayed certificate was filed is also diagnostic.

Document this analysis in the journal. "Birth certificate names X as mother; 1880 census shows Y as wife of father; X does not appear in household; Y confirmed as mother" is the reasoning chain that makes the source evaluation defensible.

---

## Pattern Recognition Across These Failures

Looking across the twelve entries, most failures share one of three root causes:

**Missing a guard condition.** Deduplication by ARK but not title. Visited set omitted from BFS. Validator checking confidence but not source count. Each guard was added after the failure, not before. The lesson is to ask "what case does this not handle?" at design time.

**Trusting the automation to be right because it was right before.** CDP tokens worked for reads, so they were assumed to work for writes. The apply script handled most patches correctly, so the silent-drop case went unnoticed for sessions. Spot-checking output — especially after the first run of any new batch — is not optional.

**Deferring documentation.** Journal entries written at session end instead of in real-time. Priority plans not updated at resolution time. The gap between when something was learned and when it was written down is where the loss happens.

None of these failures required exotic conditions. They required ordinary inattention at a point where the system appeared to be working.
