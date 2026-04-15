# Contested Rules

Rules where the sister projects have contradictory guidance, or where context makes the "right" answer different depending on circumstances.

These are worth understanding — they reveal genuine complexity, not simple errors. Both sides of each debate are documented.

---

## FS session token behavior: CDP extraction vs. real browser

**The debate**: Are FamilySearch session tokens extracted from Chrome CDP equivalent to tokens obtained from a real browser session?

**Side A (genealogy)**: CDP-extracted `fssessionid` tokens return HTTP 404 on `POST /platform/tree/child-and-parents-relationships`, while tokens from a manually-logged-in real browser session succeed on the same endpoint with the same request body. The endpoint itself works (confirmed by manually creating a relationship via FS website UI); the CDP-extracted token is the variable that changes behavior. Hypothesis: AWSELB sticky-session routing or FS flagging automated sessions and restricting write access.

**Side B (genealogy-kindred)**: CDP-extracted tokens have been used successfully for FS source harvest (`GET /platform/tree/persons/{PID}/sources`), person reads, and ancestry lookups. These are all read-only endpoints. No write operations have been tested from kindred using CDP tokens.

**Current resolution**: The disagreement may be endpoint-specific rather than categorical. CDP tokens appear to work for read operations. Write operations to collaborative tree endpoints (relationships, fact contributions) may require real-browser session quality. **Test before assuming CDP tokens work for any new write endpoint.**

**Status**: Unresolved — needs controlled testing with CDP tokens on the write endpoint.

---

## Obituary source tier: Tier 2 vs. Tier 3-4

**The debate**: What source tier do obituaries occupy?

**Side A (genealogy, dry-cross)**: Full-text obituaries published in newspapers are Tier 2-3 evidence. They are contemporary newspaper records, often naming parents, siblings, spouses, and children with specificity that vital records lack. They are especially valuable for relationships (who survived, who predeceased) that no single vital record documents. Treat as Tier 2 when published in a major newspaper with a verifiable publication date; Tier 3 for smaller or undated clippings.

**Side B**: Self-published funeral home obituaries posted on legacy.com or funeral home websites with no newspaper backing are written by the family, have no editorial review, and should be Tier 4 (family-provided document). The "obituary = Tier 2" rule should apply only to newspaper obituaries, not to all documents labeled "obituary."

**Current resolution**: The disagreement is about source type, not source category. **Rule**: Obituaries in verifiable newspaper archives (Newspapers.com, Chronicling America, digitized local papers) = Tier 2-3. Funeral home website obits with no newspaper attribution = Tier 4. When in doubt, look for whether the text was published in a newspaper or only on a funeral home/memorial site.

**Status**: Resolved in principle; formalize the rule in LESSONS.md once all three projects have applied it.

---

## POSSIBLE seeding: whether to allow unverified parent links in tree.json

**The debate**: Should a tree allow POSSIBLE-confidence parent links seeded from Tier 5 tree consensus?

**Side A (genealogy-kindred)**: Yes. The `Confidence Pipeline` model explicitly allows newly-added persons to enter at POSSIBLE confidence, sourced from FS Family Tree consensus, with an `upgrade_path` field describing what T1-3 evidence would promote them. This lets the tree grow in all directions quickly, then upgrade persons as evidence is found. The constraint is: never *contribute* POSSIBLE-confidence links to external platforms.

**Side B (genealogy, dry-cross)**: Allowing POSSIBLE-seeded parent links from Tier 5 sources risks graph-wiring errors cascading through the tree. If a bad Tier 5 link gets accepted as POSSIBLE and a researcher adds sources to the wrong person, the confidence can accidentally rise. Prefer no parent link at all over a Tier 5-sourced one; document the candidate parent in the journal instead.

**Current resolution**: Resolved with guardrails. POSSIBLE seeding is permitted IF: (1) the person carries a populated `upgrade_path` field describing exactly what T1-3 evidence would promote them; (2) the tree validation script flags any POSSIBLE person whose `upgrade_path` hasn't been actioned after N sessions, preventing indefinite stale seeding; (3) no POSSIBLE-confidence parent link is ever contributed to FamilySearch, WikiTree, or any external platform — the tree.json is a research workspace, not a contribution source. Projects that prefer no-link-at-all are equally valid and face less contamination risk; the choice is a project-phase judgment call. The critical invariant — no external contribution of POSSIBLE-confidence links — is non-negotiable regardless of which approach the project uses.

**Status**: Resolved with guardrails — see `methodology/02-evidence-standards.md` POSSIBLE Seeding section for implementation details.

---

## FS source harvest timing: bulk script vs. targeted API calls

**The debate**: For newly-added ancestors, is it better to run the bulk harvest script or make targeted API calls?

**Side A (dry-cross)**: For recently-added Gen 12-13 persons with known FS PIDs, direct targeted API calls per PID are more efficient. The bulk script processes persons in tree order and spends most of its time on already-sourced persons early in the queue.

**Side B (genealogy)**: The bulk script with `--limit N` and generation filtering is more maintainable and less error-prone than ad hoc targeted calls. It also handles deduplication, ARK extraction, and patch writing in a tested way.

**Current resolution**: Use the bulk script for sweeps (when you want to harvest across a whole generation range). Use targeted API calls when you have a specific list of newly-added persons and want results immediately. Both approaches produce correct output; the choice is efficiency vs. convenience.

**Status**: Resolved in principle (context-dependent).
