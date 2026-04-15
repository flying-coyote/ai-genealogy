# Chapter 3: Research Workflow

Research workflows degrade over time. A session starts with the best intentions, digs into one thread, and ends without closing the loop — no journal entry, no confidence update, no queue hygiene. The next session starts cold, re-covers the same ground, and adds a duplicate source. This chapter is about preventing that failure mode.

---

## Platform Research Sequence

For American genealogy 1700-1950, work platforms in this order:

1. **Ancestry** — Largest indexed record collection for US vital records, census, military, newspapers. Most researchers' primary source. Start here.
2. **FamilySearch** — Strongest for international records and pre-1900 US. Free. Strong for LDS-adjacent communities. Record images often available where Ancestry only has indices.
3. **WikiTree** — Collaborative tree with inline citations. Useful for finding published genealogies attached to profiles and for cross-checking work against other researchers.
4. **Find A Grave** — Burial records, headstone photos, obituaries. Essential for death dates and confirming maiden names from headstones.
5. **Geni** — World Family Tree. Useful for European lineages and as a cross-check on deep ancestry. Collaborative model means quality varies.
6. **Chronicling America (loc.gov)** — Digitized US newspapers 1789-1963. Free. Strong for rural communities underrepresented on Ancestry. Use the fulltext API, not just the web UI.

**Adjust for non-US lineages.** For German ancestry: Matricula, Archion, Archivportal-D, FamilySearch German parish collections. For British Isles: FindMyPast, ScotlandsPeople, GRONI (Northern Ireland). For Scandinavian: DIS-Sverige, Arkiv Digital. Platform sequence should follow record availability, not habit.

---

## The Context-First Rule

**Never start browser research without reading the person's context cache file first.**

The cache file at `research/cache/{GEDCOM_ID}.json` contains:

- Prior platform search history (what was searched, when, what was found)
- Attached sources with their ARK URLs
- Identified gaps (what has not been found yet)
- Research mode (active vs. brick wall vs. complete)

Starting a research session without reading the cache means you will almost certainly repeat searches that were already run, reach the same conclusions, and possibly attach duplicate sources. This wastes time and degrades data quality.

If no cache file exists for a person, check the research journal at `research/journals/{GEDCOM_ID}.md` — it may contain the same information in less structured form. If neither exists, the person has not been researched systematically.

---

## Session Preflight Checklist

Before opening a browser or calling any API:

- [ ] Read `research/cache/{ID}.json` — what has already been searched?
- [ ] Read `research/journals/{ID}.md` — what decisions were made, what is still open?
- [ ] Check `research/RESEARCH_PRIORITY_PLAN.md` — is this person actually a priority right now?
- [ ] Verify journal frontmatter (confidence, status) matches current `tree.json` state. If they differ, resync before proceeding — the journal may be ahead of (or behind) the tree.
- [ ] Verify the person is not collateral — check `lineage_part` and `notes`. If `lineage_part` is null and the notes suggest step-relative or in-law, parent gaps are acceptable. Do not consume research time on acceptable gaps.

---

## The Audit-First Rule

Before dispatching a research agent or starting any brick-wall investigation:

**Read `validation.evidence.sources` in tree.json for the target person first.**

If a T1-3 source is already attached and contains language like "daughter of", "son of", "child of", or names a parent explicitly — that is a graph-wiring bug, not a research gap. The data is in the tree, just not connected.

Fix the parent link in tree.json (5-minute edit), run the validator, done. Dispatching a research agent for a 60-minute session to find something that is already documented in the tree is the single most common source of wasted effort in AI-assisted genealogy workflows.

This check is worth running even when you are confident it will turn up nothing. It catches real bugs regularly.

---

## Writing Journal Entries in Real Time

Write journal entries **during** research, not after.

AI-assisted sessions are long and context-heavy. Compaction drops mid-session work. If you research for 40 minutes, find three relevant records, and then write one summary at the end — and the session then crashes or compacts — you lose 35 minutes of work.

The discipline is:

- Log platform + query + result as you go: "Ancestry, VA Death Records, searched John Henry Wiley 1890-1910, found: nothing matching."
- Write a Decision Log entry at the moment you make a decision, not reconstructed later: "Accepting 1880 census match as probable father based on age and location; noting no T1 confirmation yet."
- After every source attachment: update journal with what was attached and what it proves.

The journal is your continuity layer between sessions. Treat it as the primary record; the cache file is a derived index.

---

## Notes-Field Scan Before Queuing

Before adding a person to the research queue for parent-gap work, read:

- `p['notes']` — free text field. Look for: "not in direct lineage", "collateral", "second wife", "step-", "in-law", "wrong person".
- `p['lineage_part']` — null means collateral. Confirm before queuing.

Persons who are step-relatives, in-laws, siblings of direct ancestors, or collateral kin have parent gaps that do not need to be filled. Their position in the tree is documented for context, not for lineage extension. Queuing them wastes research cycles and can lead to attaching evidence for the wrong research question.

---

## Session Close Checklist

At the end of every session that touches a person:

- [ ] All found sources attached to `validation.evidence.sources`
- [ ] Journal updated with what was done, found, and decided
- [ ] Negative searches documented in both journal and `negative_searches[]`
- [ ] Confidence recalculated against current source list — did it change?
- [ ] `upgrade_path` updated for POSSIBLE persons if the target changed
- [ ] Open concerns added to `validation.concerns[]`
- [ ] Resolved concerns moved to `validation.corrections_applied[]`
- [ ] Research queue updated: completed persons moved to completed array
- [ ] `RESEARCH_PRIORITY_PLAN.md` updated if any priorities changed

Skipping close hygiene means the next session restores from a degraded state. Over dozens of sessions, this compounds into a tree where confidence values do not reflect current evidence and the research queue contains items that were resolved months ago.

---

## Research Journal Format

Per-person journals live at `research/journals/{GEDCOM_ID}.md`. They are append-only — do not edit prior entries, only add new ones.

**YAML frontmatter** (update at session start/close):

```yaml
---
id: "@I12345@"
canonical_name: "John Henry Wiley"
confidence: PROBABLE
last_session: 2026-04-15
status: PARTIAL
---
```

**Journal body structure:**

```
## Session 2026-04-15

### Sources Reviewed
- [what you read]

### Searches Run
- Platform: Ancestry | Collection: VA Deaths | Query: John Henry Wiley, b.1842 | Result: no match

### Decisions
- [reasoning documented at moment of decision]

### Open Threads
- [what still needs to be done]
```

If frontmatter confidence differs from tree.json, the tree.json value is authoritative. Resync the journal at session start.

---

## Priority Plan Staleness

`RESEARCH_PRIORITY_PLAN.md` is only useful if it reflects current tree state. Signs of staleness:

- Brick walls listed that have since been resolved
- Platform IDs marked "pending" that are already in tree.json
- Persons listed as UNVERIFIED that have been promoted
- Research targets from two phases ago still in the "current" section

Every session that makes substantive changes to the tree should update the priority plan before closing. If the plan is more than two sessions out of date, run `python3 scripts/reconcile-queue.py` and rebuild the plan from current tree state rather than trying to patch it manually.

---

## Queue Hygiene

Both `research_queue.json` and `contribution_queue.json` have `active` and `completed` arrays. Completed items that stay in `active` cause double-processing and inflate the apparent backlog.

Move resolved items to `completed` on every session wrap-up. If you are not sure whether an item is complete, check the tree — if the condition that placed it in the queue has been satisfied (parent link found, source attached, confidence upgraded), it is complete.

---

## Run Order After Bulk Changes

After any bulk operation that changes confidence, sources, or parent links:

```
python3 scripts/gps-element1-remediate.py   # GPS E1: gaps in search coverage
python3 scripts/gps-element2-remediate.py   # GPS E2: citation format issues
python3 scripts/gps-compliance-report.py    # Summary of GPS status
python3 scripts/validate-tree.py            # Schema + referential integrity
python3 scripts/reconcile-queue.py          # Sync queues to tree state
python3 scripts/recalculate-confidence.py --dry-run  # Preview confidence changes
python3 scripts/recalculate-confidence.py   # Apply
```

Always run `--dry-run` on confidence recalculation first. Bulk recalculation can demote persons if sources were removed or if the confidence rules changed since the last run. Review the diff before committing.

---

## Brick Walls

A person is a brick wall when every reasonable platform has been searched and no T1-3 evidence for the next generation has been found.

Before declaring a brick wall:

1. Run the Audit-First Rule. If a T1-3 source is already attached and names a parent, it is a wiring bug.
2. Verify negative searches are documented on all platforms in the sequence. A brick wall without documented negatives on each platform is an incomplete search, not a brick wall.
3. Check county-level record availability — some counties have complete online coverage, others have almost none. A negative search on a county with 20% record digitization is weak evidence of absence.

When a person is confirmed as a brick wall:

```json
"research_status": {
  "status": "BRICK_WALL",
  "brick_wall_reason": "No death record found in VA pre-1912 period; 1900/1910 census not located; no probate in Augusta County records"
}
```

Document the `upgrade_path` as specifically as possible: what record collection, what repository, what date range would break this wall. This is what ONSITE research backlog entries are built from.

---

## Cross-Record Conflicts

When a conflict involves two persons in the tree (e.g., two persons with overlapping vital dates suggesting they may be the same person, or a death date that contradicts a marriage date in a sibling's record), add the concern to **both** records.

A concern on only one side leaves the other person's record in a state that looks clean but isn't. It also means whoever is researching the other person next session has no warning.

Pattern for cross-record concerns:

```json
"concerns": [
  "INVESTIGATE: Death date 1881 conflicts with sibling @I678@'s marriage record listing this person as witness in 1884"
]
```

Use the word INVESTIGATE as a searchable prefix. When running a concern triage, grep for INVESTIGATE to find all cross-record issues at once.

---

## Temporal Impossibilities

A death date before a documented marriage, birth, land transaction, or military record is either:

- The wrong date (transcription error, calendar conversion, wrong record matched)
- The wrong person (two persons with the same name conflated)

Do not upgrade confidence for a person with an unresolved temporal impossibility. Add a `concerns` entry, document both conflicting data points and their sources, and investigate before moving on.

Common sources of date errors:

- Census age misreporting (underreporting or overreporting by 5-10 years is common)
- Julian/Gregorian calendar confusion for pre-1752 English records
- Death indexes reporting the filing date, not the death date
- Wrong record matched: "John Wiley died 1881" attributed to the wrong John Wiley

When the dates reconcile, move the explanation to `corrections_applied`. Until then, the concern blocks any upgrade.
