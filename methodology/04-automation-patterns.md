# Chapter 4: Automation Patterns

The core workflow is a four-phase pipeline: discovery, harvest, validate, contribute. Each phase produces artifacts consumed by the next. No phase writes directly to an external platform without human review. Understanding where the automation ends and where human judgment begins is the whole game.

---

## Discovery Phase

Discovery scripts query platforms for candidate IDs — FamilySearch PIDs, WikiTree IDs, Geni IDs — and write the results to a timestamped report file. They do not modify the tree.

**Separation of discovery and apply.** Discovery produces a report. Applying the report is a separate step. This separation lets you review candidates before they enter the tree, run multiple discovery passes without worrying about intermediate state, and roll back a bad batch by simply not applying it.

**Deduplication before apply.** Before writing any ID to the tree, the apply script checks whether the person already has that platform ID. Re-running discovery after a previous partial apply is safe because duplicates are dropped at apply time, not at discovery time.

**Platform-specific considerations:**
- FamilySearch: search by name, birth year, and generation band. Match on both name AND approximate birth year. A name match alone is not a person match.
- WikiTree: search by surname. If a woman's WikiTree LNAB differs from the tree's canonical surname (e.g., tree has "Hamspacher" but WT LNAB is "Eis"), the profile is missed entirely. Cross-search by maiden name and married name variants.
- Geni: session-based auth is more reliable than OAuth. OAuth refresh tokens expire; browser session cookies survive longer.

---

## Harvest Phase

Harvest retrieves evidence already attached to discovered profiles and pulls it into the local source record. Discovery tells you a profile exists; harvest tells you what that profile knows.

### FamilySearch Source Harvest

`GET /platform/tree/persons/{PID}/sources` returns a list of sources already attached to the FS profile. This is not a record search — it's reading FS's own annotation layer on that profile.

The harvest is fast: 500 profiles in roughly 2.5 minutes at 0.3s delay per request. No throttling observed at that rate, but go slower if you're seeing 429s.

Response structure that matters:
- `sourceDescriptions[].titles[0].value` — source title
- `sourceDescriptions[].about` — ARK URL (the durable identifier)
- `sourceDescriptions[].citations[0].value` — citation string

**Tier-5 filter at harvest time.** Before writing a source, check the title for phrases like "family tree", "pedigree", "ancestry.com tree", "patron submitted". These are Tier 5 (other users' trees) and should be classified accordingly, not discarded — they're leads — but they must not count toward confidence thresholds.

**Deduplication by ARK and normalized title.** An early mistake in this codebase was deduplicating by ARK URL only. Sources added before ARK backfill had no ARK field and were re-added on every harvest pass. Deduplicate by ARK first, then by normalized title as a fallback. Store both `ark` and `url` on every source object.

### Browser Record Search

The FS source harvest retrieves sources already linked to the profile. It does not find unlinked indexed records. A separate browser search step — using CDP to drive the FS search UI — finds records that exist in FS indexes but haven't been attached to the profile yet. Both steps are necessary; neither is a substitute for the other.

### FS Full-Text Search API

For pre-18th century records — wills, deeds, court proceedings — the person-record search index is thin. The full-text search API queries transcribed handwritten documents directly. This finds pre-1700 Virginia wills naming children, early court records establishing land ownership, and similar evidence that never got indexed as person records.

One important operator behavior: two quoted phrases submitted to this API are OR'd silently. To require a term, use the `+` prefix: `+"John Francis"` rather than `"John Francis"`. Not knowing this causes false-negative searches that appear exhaustive but are not.

### Harvest Sequencing Rule

Every harvest batch must be followed by source attachment before the next harvest. Do not run multiple harvest passes and then apply them all at once. Stale patch files accumulate inconsistencies — the second harvest may overwrite what the first was trying to add, and there's no diff resolution mechanism. One harvest, one attach, then the next harvest.

### Post-Harvest Confidence Recalculation

After attaching a harvest batch, run `recalculate-confidence.py`. New sources may push persons from POSSIBLE to PROBABLE, or PROBABLE to VERIFIED. This is the cheapest confidence upgrade operation in the pipeline — no research required, just recognizing what the evidence already supports.

---

## The Lineage Extension Loop

`loop-research-dispatch.py` extends parent-child links deeper into the tree by querying FamilySearch for parents of direct-line ancestors with gaps.

### Scope

The loop operates on **Ahnentafel-numbered ancestors only** — direct-line, not collateral. A sibling of an ancestor is not a target. An in-law of an ancestor is not a target. Restricting scope to Ahnentafel prevents lineage research from sprawling into collateral lines that will never be contributed.

### Per-Cycle Logic

1. Select the next direct-line ancestor in the configured generation band who is missing a father or mother link.
2. Query FS for that person's parents using the FS Family Tree API.
3. Evaluate stop signals (see below).
4. If no stop signals: stage a patch for human review.
5. Log outcome to progress JSONL (crash-safe, resumable).

### Stop Signals

The loop halts on a person — and adds them to the persistent skip list — when any of the following are present:

- **Tier-5-only sources on the claimed parent.** If the only evidence for the parent is other users' trees, stage nothing. Log the rejection reason.
- **FS dispute markers.** If the FS profile has a merge dispute or data quality flag, don't contribute on top of it.
- **Date conflicts.** If the claimed parent's birth year makes them younger than the child, or over ~100 years older, reject. Log the specific conflict.
- **Pre-1700 threshold.** At Gen 15+, require ≥2 T1-2 sources on both the child and the claimed parent. This is the strictest filter and exists specifically to prevent deep-ancestry cascades from Tier 5 trees masquerading as confirmed medieval nobility.

### What the Loop Does Not Do

The loop does not write to `tree.json` directly. It produces patches. A human runs `apply-research-patches.py` to review and selectively apply them. This is not optional caution — it's how the pipeline works. Skipping the review step removes the only human checkpoint before tree data changes.

### Patch Apply: Silent Drop Bug

The apply script originally skipped any patch where the target person already had a non-null `father_id` OR `mother_id`, treating this as "already done." But many patches were for the other parent (father set, patch is for mother). This silently discarded ~30% of valid patches. The correct check: look at which specific parent field the patch sets before deciding to skip.

### Skip List Semantics

`loop_research_state.json` stores a persistent `skip_list`. Persons on the skip list are not retried. The skip list is not the same as "researched" — it means "hit a stop signal, not safe to auto-extend." A human can still investigate these persons manually. Do not clear the skip list without reviewing why each entry is there.

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Script error |
| 2 | Queue drained (nothing left to process) |
| 3 | Rate-limited or FS token expired |
| 4 | Entire batch skipped (all candidates hit stop signals) |

Exit code 3 means the FS bearer token has expired (~2hr TTL). Refresh from the browser DevTools Network tab before the next run.

### Generation Cap

Extend to Gen 17 or wherever T1-3 evidence supports. Do not chase pre-1600 lineages without primary records. A 40-generation line back to Charlemagne through online trees is not a research finding; it's an audit failure waiting to happen.

---

## The Research Loop Dispatcher

`research-loop-dispatch.py` is a separate maintenance loop, not the lineage extension loop. It handles recurring quality actions that don't extend the tree but keep existing data current.

**Actions it manages:**
- Source backfill (harvest from newly discovered FS profiles)
- GPS precondition remediation (addressing PARTIAL search coverage and missing citations)
- Confidence recalculation
- Citation standardization

**Exhaustion tracking.** After N consecutive zero-yield cycles on an action, the dispatcher marks that action exhausted for the current run. This prevents wasted cycles trying to squeeze yield from a depleted source. Exhausted actions are re-eligible the next session.

**Priority ordering.** Highest-yield action runs first each cycle. Early sessions produce a lot of source backfill; later sessions the yield shifts toward GPS remediation.

**`--dry-run` flag.** Shows what the dispatcher would do without writing anything. Use this before the first run of a new session to confirm the queue state is what you expect.

---

## Validate Phase

Validation catches structural errors before they reach the contribution stage. Run validators after any batch apply, not just at session end.

### `validate-tree.py`

- Schema validation: required fields present, correct types
- Referential integrity: `father_id` and `mother_id` point to real persons in the tree
- Source integrity: `validation.source_count` matches `len(validation.evidence.sources)`
- Confidence-source consistency: VERIFIED persons must have ≥2 sources; PROBABLE must have ≥1 source

The last check was added after the validator's blind spot allowed 2 VERIFIED persons with empty source arrays into production. The basic schema pass was not enough.

### `reconcile-queue.py`

Syncs platform ID drift between `tree.json` and `research_queue.json`. When a discovery batch is applied to the tree, the queue's cached platform IDs may be stale. Reconcile keeps them in sync.

### `gps-compliance-report.py`

Reports per-person GPS (Genealogical Proof Standard) element status. GPS elements 1-5 are tracked separately:

| Element | What the script checks | Automated? |
|---------|----------------------|-----------|
| E1 | Search coverage across expected platforms | ✓ Yes |
| E2 | Complete and accurate citations | ✓ Yes |
| E3 | Analysis and correlation of all sources | ✗ Human only |
| E4 | Conflict resolution documented | Partial (flags unresolved concerns) |
| E5 | Soundly reasoned conclusion | ✗ Human only |

A person can be PARTIAL on E1 (WikiTree not yet checked) but PASS on E2 (all attached sources have full citations). The report surfaces these granular gaps for prioritizing remediation effort.

**Important**: This is a precondition checklist, not GPS compliance. A person whose E1-E4 preconditions are all met still requires human review to determine whether the overall conclusion is soundly reasoned (E5). "Passed the GPS precondition report" ≠ "GPS-compliant."

---

## Contribute Phase

Contribution is always staged. Nothing writes to an external platform as a side effect of running a script.

### Contribution Queue

`contribution_queue.json` tracks pending contributions with:
- The contribution type (source attachment, parent-child link, profile update)
- Evidence basis (which sources support it)
- Attestation status (human-reviewed or not)
- Target platform and platform-specific payload

### Platform-Specific Notes

**FamilySearch:**
- Source attachment: `POST /platform/tree/persons/{PID}/sources`
- Parent-child links: `POST /platform/tree/child-and-parents-relationships` with body `{"childAndParentsRelationships": [{"parent1": {...}, "child": {...}}]}`
- CRITICAL: `POST /platform/tree/relationships` with `"type": "ParentChild"` creates COUPLE relationships regardless of the type field value. This is a known FS API behavior that caused 1,543 wrong couple relationships before it was caught. Always use the correct endpoint.
- After any relationship contribution, verify the relationship type on the FS website before continuing.

**WikiTree:**
- No write automation. The rate limiter enforces 120s minimum between edits, 50/day, 150/rolling-7-days.
- Prepared edits are written to `data/wt_prepared_edits/{WTID}.md` as paste-ready content. Human opens the Edit Biography page, pastes, saves, then logs the edit with `wt-rate-check.py --record`.
- The 120s minimum is the core anti-automation signal. It exists to keep WikiTree from flagging the account.

**Ancestry:**
- Source hint acceptance requires human review via the UI. No batch acceptance via API.
- Internal hints API is cookie-based and useful for programmatic extraction of hint metadata, but the actual accept/decline action happens in the browser.

## Quality Metrics (Defense Against Volume Drift)

The automation pipeline optimizes for coverage — more persons, more sources attached. Left unchecked, coverage optimization undermines defensibility. Track these metrics after major sessions to make quality drift visible before it becomes a correction campaign.

| Metric | Alert Threshold | Why It Matters |
|--------|----------------|----------------|
| % direct-line ancestors at POSSIBLE confidence | >15% | Too many unverified lineage segments in active use |
| % sources from Tier 3-5 | >40% | Tree is relying too heavily on secondary/derivative sources |
| POSSIBLE persons missing `upgrade_path` | Any | These are research liabilities with no documented action path |
| Proposed contributions backed only by Tier 3-5 evidence | Any | Block; require T1-2 before contributing to any external platform |

Run `python3 scripts/metrics-report.py` to generate the current distribution. Add the summary output to `docs/SESSION_HISTORY.md` at each session close.

The Tier 3-5 threshold deserves emphasis: a tree where most sources come from census transcriptions and online trees will appear well-sourced while remaining structurally unverifiable. The source tier distribution is the single most informative quality signal — more so than raw source counts.

---

### Automation Gates Summary

| Activity | Level of automation |
|----------|-------------------|
| Source harvest | Fully automated |
| Deduplication | Fully automated |
| Tier classification | Automated (rule-based) |
| Confidence recalculation | Automated |
| Citation standardization | Automated |
| Queue management | Automated |
| GPS precondition report | Automated (preconditions only — E3/E5 require human) |
| External platform writes | Dry-run review required |
| GPS remediation patches | Dry-run review required |
| Confidence downgrades | Dry-run review required |
| Conflict resolution | Human only |
| Pre-1700 identity claims | Human only |
| WikiTree edits | Human only (no write automation) |
| FS relationship contributions | Human review + attestation |
| FS merge/combine operations | Human only |
