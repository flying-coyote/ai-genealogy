# Chapter 5: Human Judgment Gates

Automation accelerates genealogy research. It does not replace judgment. This chapter is about the decisions that require a human — not because the technology can't produce an answer, but because the answer won't be defensible without one.

The test for whether a decision needs human judgment: if the decision were wrong, could you trace back to a source and explain the error? If the answer depends on interpreting context, weighing informant credibility, or resolving a conflict between two plausible readings of the evidence, automation is not sufficient.

---

## Evidence Weight Assessment

When two sources contradict each other and both appear credible, the resolution requires historical context that no script can reliably supply.

A draft registration card says 1895. The 1900 census says 1897. Which is correct? The script sees two T1-2 sources and flags a conflict. A human asks: who was the informant? The draft card is self-reported by the registrant — usually the most accurate birth year available because the person filling it out had a direct interest in getting it right (military exemptions, age brackets). The census year is reported by whoever answered the enumerator's question, which may have been a neighbor, a spouse, or a child who guessed.

But not always. Some draft registrants inflated their age to avoid looking too young for exemption; some deflated it to avoid being called up. Some census records were captured directly from the householder under conditions where accuracy mattered. The "obvious" answer — draft card wins — is usually right, but not universally.

The human judgment required: evaluate the informant for each source, consider the context in which each was created, and document which wins and why. Documenting a coin flip as "AI applied the correction" is not defensible research.

**GPS Element 4 requires this documentation.** Conflict resolution must appear in `corrections_applied[]` with reasoning. The reasoning cannot be "the automation chose this one."

---

## Collateral vs. Direct-Line Classification

Whether a gap in the tree is a genuine research target depends entirely on whether the person is a direct-line ancestor.

Before queuing anyone for research, read two fields: `lineage_part` and `notes`. If `lineage_part` is null or the notes contain phrases like "not in direct lineage", "collateral", "second wife", or "wrong person", the parent gap for that person is acceptable. Researching it anyway wastes hours.

In-laws of ancestors are not ancestors. A great-great-grandmother's sister's husband is not in the Ahnentafel. Step-parents of ancestors are not blood ancestors. Getting this wrong doesn't just waste research time — it can pull in source attachment, GPS compliance work, and contribution campaigns for people who should never have been in the active research queue.

The script that builds the research queue should filter to Ahnentafel members only. But scripts have bugs and edge cases. Spot-checking the queue for collateral bleed-through before dispatching a research agent is faster than unwinding a session's worth of misplaced effort.

---

## Pre-1700 Identity Claims

European aristocracy and noble lineages before 1700 are the most thoroughly conflated record space in genealogy. Every online tree, every Geneanet entry, every FS profile claiming descent from a medieval king exists in an ecosystem of circular citation. Tree A cites Tree B which cites Tree C which cites Tree A.

A 12-step chain of Tier 5 links to a 14th-century nobleman is not evidence of descent. It is evidence that many people have copied the same unverified claim across platforms.

Before accepting any pre-1700 lineage link:

1. Evaluate the source chain for each individual link in the chain, not just the endpoint.
2. Confirm that at least one link in the chain traces to an original document — a parish register, a will, a court record, a land deed.
3. Confirm that the FS profile you're linking to has its own primary sources, not just other profiles citing it.

WikiTree's pre-1700 standards are explicit: FS trees, Ancestry trees, Geneanet, and personal websites are prohibited as sources for pre-1700 profiles. These are finding aids only. Trace to original parish registers, wills, or court records. If you cannot trace there, the link is not established.

The loop-research pipeline enforces this at Gen 15+: ≥2 T1-2 sources required on both the child and the claimed parent. This is the right threshold. Do not loosen it because a particular noble family has "good documentation" — the documentation needs to be on the specific profile in question, not on the dynasty generally.

---

## Conflict Resolution

When two T1-2 sources disagree — different parents named, different birth years, different birthplaces — the conflict must be resolved by a human and documented. Automation can surface the conflict; it cannot resolve it with authority.

Common conflict patterns and what to evaluate:

**Birth year conflicts (±2 years):** Usually round-number reporting in one source. Check which source's informant would have known the actual year. A birth certificate (if contemporary, not delayed) wins over a census.

**Birth year conflicts (>5 years):** More likely to indicate a real identity question. Two people with the same name in the same area at different ages are more common than they should be. Verify spouse name, children's names, and residence against each candidate before deciding.

**Different parents named:** Which source is closer in time to the birth? Who was the informant? A will naming children is usually authoritative. An obituary listing parents may be compiled from memory by a grieving family member decades later.

**Different birthplaces:** County vs. township vs. town is usually the same place described at different levels of specificity — not a conflict. State vs. state is a real conflict. Country vs. country is a serious conflict.

The resolution goes in `corrections_applied[]` with the reasoning. Future researchers — including future sessions of your own AI — will read this documentation. Write it for someone who doesn't have your context.

---

## Platform Contributions

FamilySearch, WikiTree, and Ancestry are shared public records used by thousands of researchers. A wrong parent-child link contributed to FamilySearch does not stay contained in your tree — it affects everyone who finds that profile and trusts the existing data.

This is why contribution gates exist. Discovery is automated. Contribution requires attestation.

The review step before any external write is not optional caution or bureaucratic overhead. It is the only human checkpoint between an automation error and a public record change. If you routinely skip it because "the automation is usually right," the only question is how long before "usually right" produces a contribution you'll need to retract.

Retractions are possible. They are time-consuming. On WikiTree, a wrong profile merge or conflation requires community intervention and may not be fully reversible if other users have since edited the merged profile.

---

## ThruLines and Lineage Hints

Ancestry ThruLines, FamilySearch Suggested Relatives, and similar hint systems are generated algorithmically from other users' trees. They are Tier 5 evidence by definition. Their value is as research leads: they point toward hypotheses worth investigating, not conclusions worth accepting.

Red flags that suggest a hint is based on conflated data:

- **Impossible lifespans on claimed parents.** A claimed parent born in 1780 for a child born in 1740 is not a data entry error — it's a wrong person.
- **Same "unique" name appearing in multiple unrelated branches.** If a hint shows that three different unrelated families all had a son named "Zebediah" who all have the same claimed grandparent, the grandparent is conflated.
- **Birth records dated after the target's own birth.** A ThruLines parent whose birth record is dated after the child's birth is a wrong person. FS sometimes attaches records to profiles incorrectly; hints propagate the error.

Accepting a hint means taking responsibility for the claim it represents. Verify the underlying evidence before accepting.

---

## DNA Evidence

DNA confirms or disproves relationships, but the interpretation requires context that raw cM numbers don't provide.

What AI can do: look up cM ranges in the Shared cM Project tables, note that 1,700 cM is consistent with a half-sibling or grandparent.

What requires human review:
- Which relationship the cM range actually supports given known family structure
- Whether endogamy inflates shared cM (common in Ashkenazi Jewish, Pennsylvania German, and closely settled colonial communities)
- Whether triangulation with a third person has been done to confirm the segment is IBD (identical by descent) rather than IBS (identical by state)
- Whether the testing company's relationship prediction algorithm is appropriate for the specific range

DNA-confirmed relationships should be documented with `parent_certainty.status = "confirmed_dna"`, citing the specific test, the comparison, and the cM value. "DNA test confirms" without the specifics is not a citation.

---

## The "Fill the Gap" Temptation

The hardest discipline in AI-assisted genealogy is resisting the pull to fill gaps quickly.

When a person has no parents listed on FamilySearch, the tempting response is to accept the first Tier 5 tree that has parents, because the alternative — logging a negative search and moving on — produces no visible progress.

The correct response to an empty parent field is:
1. Document the negative search (what platforms were checked, what search terms were used, what was not found). This proves the research was exhaustive.
2. Move on.
3. Return when evidence surfaces from a different source type.

A tree where every claim is traceable to a primary source is more valuable than a larger tree built on Tier 5 cascades — for the obvious reason that the smaller tree is actually correct.

The skip list in the lineage extension loop exists to enforce this. When a person hits a stop signal (Tier-5-only sources on the claimed parent, no primary records), they are skipped and not retried automatically. The skip list is not failure — it is the correct outcome for cases where the evidence is not yet sufficient.

Accepting a Tier 5 parent to fill a gap doesn't end the research question. It adds a wrong answer that now has to be undone when better evidence surfaces.
