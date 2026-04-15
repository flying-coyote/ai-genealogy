# Philosophy: AI-Assisted Genealogy

## Why AI and genealogy are a good fit

Genealogy research has a structure AI handles well: it's a graph traversal problem with evidence quality constraints. Each person in a family tree is a node with edges (parent, child, spouse) that need to be established by evidence, not assertion. AI can reason about graph structure, evaluate evidence quality, track research coverage, and maintain a consistent data model across hundreds of sessions.

The bottleneck in genealogy is not research speed — it's research *quality*. Anyone can build a large tree quickly by accepting Ancestry hints without scrutiny. The hard problem is building a defensible tree where every claim is traceable to primary sources, every conflict is resolved, and every gap is documented. That's where AI assistance adds the most value: not by doing more, but by enforcing rigor at scale.

## What AI does well

- **Pattern matching across sessions** — remembering that you searched a platform in 2024 and found nothing, so you don't repeat it
- **Batch source processing** — harvesting 500 FS sources, deduplicating them, classifying tiers, and attaching them to the right persons
- **Graph integrity checking** — detecting impossible dates, generation mismatches, missing parent links, confidence drift from evidence
- **Systematic coverage tracking** — knowing that 14 of 20 Gen 6 ancestors have FS IDs but only 9 have been source-harvested
- **Research loop dispatch** — autonomously selecting the next best research target, running the appropriate query, and logging results with proper citations
- **Cross-platform correlation** — matching a person's FS record against their Ancestry census hits and WikiTree profile without losing track of which platform confirmed which fact

## What AI must not decide alone

- **Evidence weight** — whether two contradictory sources mean the record is wrong or the record is about a different person. This requires understanding historical context.
- **Collateral vs. direct line** — whether a gap in a tree is a genuine research target or an acceptable gap for a collateral relative. Misclassifying this wastes hours.
- **Pre-1700 identity claims** — European nobility and aristocracy records are heavily conflated across online trees. Before accepting a lineage back to a medieval ancestor, a human must evaluate the source chain for each link.
- **Conflict resolution** — when two high-tier sources disagree (e.g., a draft card says 1895, a census says 1897), the decision requires judgment about which informant had better knowledge.
- **Platform contributions** — pushing data to FamilySearch, WikiTree, or Ancestry affects shared public records. Human review before any external write is not optional.

## The GPS Standard

The [Genealogical Proof Standard (BCG)](https://www.bcgcertification.org/resources/standard.html) has five elements:

1. **Reasonably exhaustive search** — you've searched every platform and record type that could reasonably contain relevant evidence
2. **Complete and accurate citations** — every source is cited with enough information that another researcher can find the same record
3. **Analysis and correlation** — you've analyzed what each source proves, noted conflicts, and correlated evidence across sources
4. **Resolution of conflicts** — contradicting evidence has been addressed and documented
5. **Soundly reasoned conclusion** — the confidence level is justified by the evidence

This guide treats GPS readiness as a set of preconditions tracked per person. AI automation verifies preconditions for each element: coverage tracking (E1), batch citation standardization (E2), conflict flagging (E4). Elements E3 and E5 require human judgment — no script can evaluate whether evidence was properly correlated or declare a conclusion "soundly reasoned." GPS is a human standard. The scripts check whether the mechanical prerequisites are in place; a human determines whether the conclusion meets the standard.

## The human-AI boundary

The right frame is not "AI does the research" but "AI handles the mechanical work so the human can focus on judgment calls."

Mechanical work that scales well with AI:
- Source harvesting, deduplication, attachment
- Evidence tier classification
- Citation formatting
- Cross-platform platform ID reconciliation
- Research session journaling
- Queue management and priority ordering
- Batch confidence recalculation

Judgment calls that stay with the human:
- Which conflicting source wins and why
- Whether a claimed lineage link is plausible given historical context
- Whether to push a contribution to a public platform
- Whether a brick wall is genuinely unresearchable or just needs a different approach
- Pre-1700 identity verification

This boundary is enforced architecturally: automation writes to draft reports, humans review before apply, and external contributions require explicit attestation. "The AI ran the script" is not a substitute for "a human reviewed the output."

## On tree quality vs. tree size

Most genealogy software optimizes for size — more persons, more connections, more records. This methodology optimizes for *defensibility*. A 300-person tree where every claim is traceable to primary sources is more valuable than a 3,000-person tree built on Tier 5 evidence cascades.

Size matters only when it reflects real research. The three sister projects grew from the same starting points — actual primary research on the direct line, then lineage extension only when supported by evidence. That means accepting that Gen 16+ ancestors are POSSIBLE confidence until primary sources are found, and that some brick walls are permanent.

The hardest discipline in AI-assisted genealogy is resisting the impulse to fill gaps quickly. The correct response to "no parents on FamilySearch for this person" is to log the negative search, move to the next target, and return when new evidence surfaces — not to accept the first Tier 5 tree that has a parent listed.
