---
type: Lesson
title: "Genealogy AI Best Practices: Confirmed Lessons"
---

# Genealogy AI Best Practices: Confirmed Lessons

Rules confirmed across the sister projects. Confidence tags indicate how many projects have validated each rule:
- `[CONFIRMED ×3]` — all three projects
- `[CONFIRMED ×2]` — two projects
- `[PROVISIONAL]` — one project so far (see also PROVISIONAL.md for unproven patterns)

For disputed rules, see [CONTESTED.md](CONTESTED.md).

---

## Research fundamentals

**Rule [CONFIRMED ×3] (captured 2026-04-15): Trees are leads, never sources.** `POST /platform/tree/relationships` with type "ParentChild" creates couple relationships on FamilySearch regardless — the correct endpoint is `POST /platform/tree/child-and-parents-relationships`. More broadly: Ancestry, WikiTree, Geni, MyHeritage, and FamilySearch family trees are all Tier 5. They point to records; they are not themselves evidence. Extract the attached records and cite those. A parent link built on tree-only evidence is POSSIBLE confidence at best and should carry an `upgrade_path` field describing what T1-3 evidence would promote it.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Verify cross-platform identity before assigning platform IDs.** A name match alone is not a person match. Before assigning a FS PID, WikiTree ID, or Ancestry record to a tree person, require ≥2 of: name match, birth/death span within ±3 years, spouse or child name match, birthplace match, or source consistency with documented facts. Wrong-person matches are the most common source of cascading errors in AI-assisted genealogy — they appear to add sources, raise confidence incorrectly, and attract further wrong-person evidence. The cost of a false match exceeds the cost of a missed one.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Document negative searches.** Explicitly recording "searched X platform for Y person, found nothing" proves exhaustive research (GPS Element 1) and prevents re-running the same dead-end search next session. Write it in the research journal *and* in `validation.evidence.negative_searches[]`.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Context-first rule.** Never start a browser research session without first reading the person's cache file (`research/cache/{ID}.json`). It holds prior platform search history, attached sources, and known gaps. Skipping it produces duplicated work.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Write journal entries during research, not after.** AI context compaction can drop mid-session work. Log platform + query + result as you go. Decision Log entries should be written at the moment of decision with reasoning, not reconstructed afterward.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Platform search order.** Ancestry → FamilySearch → WikiTree → Find A Grave → Geni → Chronicling America. This order reflects population coverage × access cost × data reliability for most American genealogy (1700-1950). Adjust for non-US lineages.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Confidence cannot exceed evidence.** 0 sources = POSSIBLE max regardless of what a prior session set. PROBABLE requires ≥1 Tier 1-3 source. VERIFIED requires ≥2 independent Tier 1-2 sources. Any upgrade requires the evidence to actually support the new level.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Audit brick walls before dispatching research agents.** Before any research loop iteration targeting a `brick_wall=True` person, first read that person's `validation.evidence.sources` array. If a T1-3 source already names a parent ("daughter of", "son of", "wife to", "father of", "DAU OF", "child of" in citation text), the brick wall is a graph-wiring bug, not a research gap. A 5-minute tree-completion fix beats a 60-minute research agent dispatch. *(Confirmed repeatedly in kindred and dry-cross sessions.)*

**Rule [CONFIRMED ×3] (captured 2026-04-15): Read notes before flagging a parent gap as a research target.** Collateral branches and step-relatives with null parents look identical to direct-line gaps in bulk audits. A notes-field read + lineage_part cross-check confirms whether the gap is actionable.

**Rule [CONFIRMED ×2] (captured 2026-04-15): Obituaries name relationships explicitly.** Full obituary text is Tier 2-3 evidence for parents, siblings, and children — often superior to vital record indexes when those records are unavailable. Search newspaper archives (Newspapers.com, Chronicling America, local library digital collections) before deferring to onsite research. *(kindred, dry-cross)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Child naming patterns betray family lines.** Middle names on children often match grandparent surnames (e.g., "Robert Bryant Martin" → father's middle name = maternal grandfather's surname). Strong indirect evidence when paired with geographic correlation. Verify across 3+ generations before claiming the pattern. *(dry-cross, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Temporal impossibilities are strong disqualifiers.** A death date before a documented marriage, birth record, or land transaction means either the death date is wrong or the record is a different person. Block confidence upgrades until resolved; document as a concern, not a minor note. *(dry-cross, kindred)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Cross-record conflicts must be documented on ALL affected persons.** If a conflict involves two persons in the tree, add an INVESTIGATE concern to both records — not just the one you were working on. *(kindred, dry-cross)*

---

## Evidence handling

**Rule [CONFIRMED ×3] (captured 2026-04-15): Primary-source preference.** Self-reported Tier 1 primary sources (draft cards, SSDI, birth certificates, deeds, wills) trump Tier 5 tree conclusions when they conflict. Document the resolution in `validation.corrections_applied[]` with reasoning — this closes GPS Element 4.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Delayed birth certificates may list stepmother.** If the birth mother died before the certificate was filed (common with delayed certs, sometimes filed decades later), the "mother" line may name the current household mother. Cross-check against the census household at the year of birth. The nearest census to the birth date is more authoritative than a delayed certificate filed 30+ years later.

**Rule [CONFIRMED ×3] (captured 2026-04-15): FAG dates without source citations stay Tier 5.** Specific-looking dates on FindAGrave memorials with no cited source are no better than Tier 5 trees. Use only for corroboration against other evidence, never as standalone support.

**Rule [CONFIRMED ×2] (captured 2026-04-15): Birthplace anchor provenance check.** Before designing a parish-register search, verify the geographic anchor's source tier. Tier 5 tree cascade + Tier 4 indirect source = provisional anchor only. Require ≥2 independent T1-2 corroborators before building a search plan around a specific locality. A Gen 6 ancestor "born in Denbighshire" based on an FS source titled "Denbighshire Parish Registers" still needs verification — the actual person's daughter may have cited Caernarvonshire (100 miles apart). *(kindred)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): `fs_audit` / `audit_metadata` tier-0 entries are pointers, not evidence.** Source objects with `source_type: audit_metadata` and `tier: 0` record that an FS profile was reviewed, not that evidence was found. Naive source-count scripts will flag persons carrying only audit entries as under-verified when they may be well-sourced via FS. *(kindred, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Surname "Americanization" can invert under deeper research.** An apparent Americanization hypothesis (Doss → Dawes) can prove incorrect when you find a Gen+1 ancestor with the "original" spelling, showing the relationship is inverted. Require 3+ generations of consistent spelling before claiming an etymology pattern. *(dry-cross, genealogy)*

**Rule [CONFIRMED ×3] (captured 2026-04-21): Citations must point to specific records, not to profiles or aggregator collection names.** Three invalid-citation patterns (flagged by mentor Lukas Murphy 2026-04-21, confirmed across all 3 projects in 2026-04-23 cleanup):
1. **WikiTree profile as source** — `<ref>WikiTree contributors, "Nesbitt-1163"...</ref>`. Another contributor's profile is not evidence; cite the underlying record or drop the claim.
2. **FS profile URL instead of record ARK** — `<ref>... FamilySearch (https://www.familysearch.org/tree/person/details/PCZW-TY2)</ref>`. FS person pages are navigation; cite the specific records attached to them (URLs with `ark:/61903/1:1:` or `ark:/61903/3:1:`).
3. **Vague collection-name citation with no URL/document** — `"Virginia Land/Marriage/Probate 1639-1850; Isabella Baughzel"` (no specific record, no URL, multiple facts crammed into one ref).
Cross-project source-quality audit (2026-04-23) found: genealogy 14.3% no-URL rate, kindred 9.4%, dry-cross 2.0%. Remediation via `scripts/fix-evidence-quality.py` with `--only {fs-backfill|wt-demote|geni-mh-demote|ancestry-split|findagrave-id|narrative-tier1}` buckets dropped the no-URL rate substantially across all 3 projects. Full audit + remediation guidance in `platform-guides/wikitree.md` "Source-quality: what NOT to cite" section. The WikiTree Browser Extension's Bio Check feature enforces the same rules at save-time — enable it before any WT bio edit. *(All 3 projects — genealogy/kindred/dry-cross 2026-04-21 → 2026-04-23)*

---

## FamilySearch patterns

**Rule [CONFIRMED ×3] (captured 2026-04-15): Always use `api.familysearch.org`, never `www.familysearch.org` for API calls.** The `www.` host blocks scripts with WAF errorCode 15. Scripts using `www.` will fail silently or with cryptic errors.

**Rule [CONFIRMED ×3] (captured 2026-04-15): FS parent-child relationship endpoint.** `POST /platform/tree/relationships` with type field "ParentChild" creates **couple** relationships regardless of the type field value. This is a FS API bug. The correct endpoint for parent-child links is `POST /platform/tree/child-and-parents-relationships` with body `{"childAndParentsRelationships": [{"parent1": {...}, "child": {...}}]}`. Using the wrong endpoint created 1,543 false couple relationships in production before this was caught.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Read the FS Collaborate tab before attaching any source.** It surfaces known conflicts, competing parent sets, researcher disputes, and flags from other contributors. Takes ~30 seconds and prevents re-introducing errors that the community has already flagged and resolved.

**Rule [CONFIRMED ×3] (captured 2026-04-15): FS profile reads beat record search when the PID is known.** Navigate directly to the person's FS profile and read Parents and Siblings — faster and more reliable than FS record search, which is intermittently broken. Yields Tier 5 evidence (tree consensus) for lineage extension; upgrade persons individually via source harvest later.

**Rule [CONFIRMED ×3] (captured 2026-04-15): FS browser record search ≠ FS API source harvest.** The API `/platform/tree/persons/{PID}/sources` returns only sources already attached to the FS profile. The browser record search finds indexed records that were never linked. Both steps are necessary for exhaustive research.

**Rule [CONFIRMED ×2] (captured 2026-04-15): FS Full-Text Search: use `+` REQUIRED operator.** Two quoted phrases combined in a query are OR'd silently — this produces enormous irrelevant result sets. Use `+term` to require each term: `+"Full Name" +County`. Found 4 key 18th-century wills (Stringer 1789, Echols 1749, Echols 1764) via Full-Text that were invisible to person-record search. *(kindred, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): FS Full-Text Search finds 18th-century wills and deeds not in record indexes.** OCR-indexed deed books and will books surface via full-text that don't appear in person-record search. Run Full-Text Search before deferring a pre-1800 will/deed search to the onsite backlog. *(kindred, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): FS "Set Preferred Parents" for parentage corrections.** Don't remove wrong parents first. Add correct parents, use "Set Preferred" to make them primary, then optionally remove wrong parents. Leaves the evidence trail intact. *(kindred, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-06-10): Record/administrative unit must predate the event being searched.** Before searching a parish-register or county collection for a pre-1800 baptism, marriage, or burial, check that the record series — and the administrative unit named in the place string — actually existed at the event date. A register that begins after the event date cannot hold the record, so the search returns zero for a structural reason, not an indexing gap, and an anchor placename that postdates the person is usually a tree-cascade error inherited from a later record. Look up the register start year (Findmypast, Forebears, GENUKI, NLW/ScotlandsPeople/PRONI) or the unit's formation date before building the search; if the event predates it, redirect to bishop's transcripts, marriage bonds, or probate. Examples: Westfield NJ Presbyterian register begins 1759 (a 1736 marriage cannot exist); Llandwrog Caernarvonshire baptisms begin 1711 (a 1695 baptism cannot exist); Cambridge St Paul parish was not established until 1837 (a 1629 birth there is impossible). *(dry-cross 2026-04-21 register-start cases; genealogy-kindred 2026-04-20 parish-establishment + county-organization cases)*

---

## Ancestry patterns

**Rule [CONFIRMED ×3] (captured 2026-04-15): Ancestry hint cards contain duplicate URLs — deduplicate before processing.** Each hint card contains two `hintStatus=pending` links with identical `/collections/{cid}/records/{rid}` paths. Any automated extraction without deduplication will double-count every hint.

**Rule [CONFIRMED ×2] (captured 2026-04-15): Ancestry ignore buttons re-query the DOM — fetch all handles upfront.** `page.$('button.ignoreButton')` re-queries after each click and finds the same already-clicked button again. Use `page.$$('button.ignoreButton')` to get all handles at once; iterate the handle array. *(dry-cross, kindred)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Use the `hintStatus=pending` review URL for accepts, not the merge URL.** The merge URL (`/merge/tree/...`) does not show a "Yes, this is a match" button. The original hint review URL always has the Yes/Save flow. *(dry-cross, kindred)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): County-organization date anachronism scan.** After any bulk import, check birth/death places against known county organization dates. Anachronisms (e.g., "born in Daviess County KY" before 1815) indicate tree-cascade errors. *(kindred, dry-cross)*

---

## Find A Grave patterns

**Rule [CONFIRMED ×2] (captured 2026-04-15): Search married women by SSDI/death-record surname, not maiden name.** FAG memorials use the final married surname. Search maiden name returns nothing for women who remarried. Check SSDI first for the death-record surname; also try abbreviated first-name variants ("Mantha" for "Armantha"). *(dry-cross, genealogy)*

---

## WikiTree patterns

**Rule [CONFIRMED ×2] (captured 2026-06-10): Pre-1700 Certification badge is required to edit pre-1700-born profiles — probe before queuing.** A WikiTree profile for a person born before 1700 loads the edit page but renders no `#wpTextbox1` textarea and shows "Please see Pre-1700 Profiles. Thank you for understanding." unless the editing account holds the Pre-1700 Certification badge. Before staging any WT bio edits that touch pre-1700 profiles, run a one-shot probe on a single pre-1700 target to confirm the textarea renders; if it doesn't, filter pre-1700 out of the plan, mark `skipped_pre_1700_cert_required`, and either obtain the badge or hand the bio to the profile manager via a WT comment. In one dry-cross session this killed 13 of 16 otherwise-ready bios; in a kindred session it killed 3 of 6. *(dry-cross 2026-04-20 Cox-580; genealogy-kindred 2026-04-20 Coulson-2392/Kindred-729/Nutt-2112)*

**Rule [CONFIRMED ×2] (captured 2026-06-10): Merge a prepared WT bio additively when the live bio carries community enrichment.** A prepared bio goes stale once other contributors enrich the live profile, so a full replace strips their work. Decide by current bio length and content: a near-stub (under ~300 chars, template + URLs only) can be full-replaced with care to preserve `{{templates}}` and `[[Category:...]]` lines; a bio with community narrative (census transcriptions, biographical notes, family lore) must be merged additively — keep the existing text, extract only the new `<ref name="...">` blocks not already present (match by `name`), inject them before `<references />`, and house inherited content under a new subsection like `=== Census transcriptions ===`. If there are no new refs to inject, skip and drop the prepared file. *(genealogy 2026-04-18 ref-dedup injection; dry-cross 2026-04-20 narrative-preserving merge — Draughon-300 grew 901→2439 chars additively, Cross-9834 full-replaced)*

---

## Data integrity patterns

**Rule [CONFIRMED ×3] (captured 2026-04-15): Stored GPS/confidence fields drift from computed values.** `gps_compliance` and `confidence` stored in tree.json can be stale after bulk operations. Run the GPS report and confidence recalculation script after each session before committing.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Journal frontmatter drifts from tree state.** Check that YAML frontmatter (confidence, last_session, status) matches tree.json at session start; resync if different.

**Rule [CONFIRMED ×2] (captured 2026-04-15): Generation-shifted siblings are easy to add wrong.** Siblings should be the same generation as the direct-line sibling (Gen N), not the parents' generation (Gen N-1). Copy generation from the sibling, not the parent record. *(dry-cross, kindred)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Multi-lineage convergence creates intentional generation-diff artifacts.** When the same person appears in two lineages at different generation depths, the generation mismatch in validation is expected, not a bug. Document as convergence in triage notes. *(dry-cross, genealogy)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Don't commit regeneratable reports.** Raw timestamped script outputs (JSON reports, harvest results) do not belong in git. They inflate commit sizes past push timeouts. Add report patterns to `.gitignore` from the start; commit only the tree.json and meaningful summaries to `docs/`. *(dry-cross, genealogy)*

---

## Project maintenance

**Rule [CONFIRMED ×3] (captured 2026-04-15): Priority plan staleness is a recurring problem.** Every session that changes the tree should also update `RESEARCH_PRIORITY_PLAN.md`. Signs of staleness: resolved brick walls still listed as active, "pending" platform IDs that already exist in the tree, priorities that no longer match research reality.

**Rule [CONFIRMED ×3] (captured 2026-04-15): Archive completed queue items.** Both `research_queue.json` and `contribution_queue.json` have `completed` arrays. Move resolved items there on every session wrap-up. The active queue is a work stack; the `completed` array is a searchable history.

**Rule [CONFIRMED ×2] (captured 2026-04-15): Scope analysis after parent-link corrections.** When a parent-link correction replaces person A with person B as the parent of a direct-line ancestor, A and A's own ancestors become orphans — disconnected but still in the tree, still consuming research effort. Run `ancestor_set` analysis after any parent correction and flag newly-disconnected persons for pruning review. *(dry-cross)*

**Rule [CONFIRMED ×2] (captured 2026-04-15): Collateral bleed-through via Ancestry hint acceptance.** Accepting hints for spouses-of-ancestors can pull in the spouse's paternal line — none of whom are direct ancestors. Verify a person is in `ancestor_set(primary)` before accepting hints that would extend their own lineage. Accept hints on spouses only for identity corroboration, not lineage extension. *(dry-cross)*

---

## Run order after bulk changes

After any significant batch operation (source harvest, GPS remediation, confidence recalculation), run in this order:

```
1. gps-element1-remediate.py --apply    # exhaustive search proof
2. gps-element2-remediate.py --apply    # citation standardization
3. gps-compliance-report.py             # fresh GPS audit
4. validate-tree.py --strict            # schema validation
5. reconcile-queue.py                   # platform ID drift check
6. recalculate-confidence.py --dry-run  # REVIEW before --apply
7. recalculate-confidence.py --apply    # promote eligible persons
```
