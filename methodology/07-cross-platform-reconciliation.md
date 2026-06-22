---
type: Methodology
title: "Chapter 7: Cross-Platform Reconciliation"
---

# Chapter 7: Cross-Platform Reconciliation

Classic genealogical method assumes one researcher building one proof. AI-assisted genealogy across multiple platforms breaks both assumptions: you are not building a single conclusion, you are continuously reconciling your conclusions against three or more external conclusion-trees (Ancestry, FamilySearch, WikiTree) that change under you, and you are doing it across thousands of people with automated producers rather than by hand. This chapter defines how to do that correctly. It builds on the evidence and confidence rules already in Chapter 2 — it does not restate the source tiers, the Tier-5 Rule, or the confidence thresholds, which are assumed here.

The short version: the per-person research journal is the single source of truth for what each platform claims, where those claims disagree, and what has been done about it; `tree.json` stays the validated conclusion store; and everything queryable is derived from the journals, never authored alongside them.

## The five layers

Genealogy already separates evidence from conclusions — the GenTech / Evidence-Explained model, and FamilySearch's own GEDCOM-X, which distinguishes a *record persona* (what a record claims) from a *tree person* (a reasoned conclusion). Most reconciliation bugs come from collapsing these layers. The model that keeps them apart, per person:

1. **Evidence** — sourced records, tiered (Chapter 2). The immutable substrate.
2. **Observed claims** — what each platform asserts *right now*, captured as timestamped snapshots by the reconciliation walk. These are inputs to reconcile, **not** our truth.
3. **Conclusion** — our reasoned `tree.json` value, its confidence, and the evidence it rests on.
4. **Reconciliation** — the disagreements between our conclusion and the claims (or among the claims), classified and status-tracked.
5. **Provenance** — who or what changed each thing, when, and why.

Layers 2, 4, and 5 are owned by the **journal**. Layer 3 is owned by `tree.json`. The journal references the conclusion rather than copying it, so there are not two sources of truth for a vital. A consistency gate (below) binds them.

## The seven disagreement classes

Every cross-platform disagreement is one of seven kinds. The class drives severity, routing, and how it can be resolved.

- **VITAL** — a birth/death date or place differs across platforms. *Signature:* same person, different date or place. The dangerous sub-cases are anachronisms (a place that did not exist at the stated date), transatlantic-impossibles, and a date contradicted by the person's own children.
- **PARENTAGE** — a parent edge differs, including the null-vs-named case where a platform supplies a parent above a slot we have empty (a brick-wall lead). *Signature:* a different named parent, or a parent where we have none. Beware the relatives-scrape artifact, where a platform jams both parents into one field or leaks a father's name into the mother slot — these read as conflicts but are noise.
- **IDENTITY** — our platform id maps to a *different person*. *Signature:* the linked profile's name and vitals diverge wildly from ours (a multi-decade or multi-century gap). This is the highest-leverage class: a wrong id silently corrupts every downstream vital and parent comparison.
- **CONFLATION** — two distinct people fused into one node. *Signature:* an internally incoherent vital set — two birthplaces decades apart, a spouse and children on a different continent than the death.
- **OVERCLAIM** — the stated confidence exceeds what the sources prove. Detected live by the conformance checker (CONF-1/2/3), not stored.
- **SOURCE** — a wrong-person source attached, or a defective citation. Partly live (conformance SRC-1/DUR-1).
- **COVERAGE** — a platform not yet searched, or no negative search recorded. Live (conformance COV-1/DOC-1).

The first four are *observed-claim* reconciliations that need per-person status tracking, so they live in journals. The last three are *process* checks computed live from `tree.json` by the conformance report — storing them in journals would duplicate a derived signal, so they are deliberately not migrated.

## The status lifecycle

Each disagreement carries a status on a small directed graph:

```
open → researching → lead_found → contributed → resolved
  ↘ held          ↘ disproven
```

`resolved` and `disproven` are terminal. `held` parks a disagreement that needs an external record or a manager's reply. The lifecycle is what turns a pile of conflicts into a backlog you work down over time: a resolved or disproven item stops resurfacing, which is the failure the old fragment files had — the same finding was rediscovered every session because nothing recorded that it had been settled.

## The consistency invariant and two policies

The gate binding journals to conclusions is one rule: **an open high-severity disagreement caps the node's confidence.** A conclusion cannot claim VERIFIED or PROBABLE while a high-severity identity or conflation question about it sits unresolved. Two policies, chosen deliberately:

- **Auto-cap the ceiling, don't block or hide.** When an open high-severity disagreement sits under a VERIFIED/PROBABLE node, a mechanical tool lowers the confidence to POSSIBLE with a dated audit note. This is the same overclaim-correction the project already applies by hand, made automatic. It is a *ceiling*, not a resolution — the conflict's actual resolution (re-point a parent, choose a vital, confirm an identity) stays human, and closing the journal disagreement lifts the cap. Capping rather than blocking keeps commits flowing; capping rather than warning keeps the tree honest. (We rejected silent-warn precisely because overclaim-that-persists is the thing this whole discipline guards against.)
- **Mechanical-only auto-close.** A producer may open a disagreement, refresh its values, and auto-close *only* the mechanical cases — the person was deleted, or the tree value now equals the source value, so the conflict literally no longer exists — with an audit note. A judgment close (resolving or disproving a live conflict) is reserved for a human or a gated apply. A producer never overwrites a human-set status. This is the same mechanical-vs-judgment split the project uses everywhere: reasonable-assumptions for vitals and links, never for the graft-prone calls.

## How the components wire

The discipline that makes this hold across thousands of people and several automated producers is ordinary distributed-systems hygiene applied to genealogy:

- **One write path.** Every producer — the reconciliation walk, the brick-wall discriminator, the conflation tooling, a one-time migration — writes disagreements through a single library (`journal_io.upsert_disagreement`), idempotent on `(class, field)`, appending to a trail only when something changed. No producer owns a bespoke file format. This is what dissolves the incompatible-schema problem: the schemas were incompatible because the contract lived nowhere; now it lives in the journal.
- **The index is derived, never authored.** The queryable, prioritized backlog is *computed* by parsing journal frontmatter (`build-disagreement-index.py`), the same way a maturation queue is computed from the graph. Because it is derived, resolving a disagreement in its journal drops it from the next run — there is no queue to update and no way for the queue to lie.
- **Conformance stays a read-checker.** The gate reads journals and `tree.json` and reports; it never writes journal records (that would be a write loop). The cap's *resolution* is a separate, explicit, gated tool.
- **Producers feed in, consumers read the index, humans gate the graft-prone mutations.** A finding enters at a journal, surfaces in the index by priority, gets worked, and resolves at the same journal — visible forever.

## A worked example

Consider a person our tree concludes is `John Pocklington`, VERIFIED, mapped to FamilySearch `LZZM-3X4`. The reconciliation walk fetches that profile and finds FamilySearch displays it as *Richard* Pocklington, and our own attached sources are all "Richard." That is an **IDENTITY** disagreement (`field: fs_mapping`), high severity, because if the mapping is to a different person every other comparison is poisoned. It lands in the journal:

```yaml
disagreements:
  - cls: IDENTITY
    field: fs_mapping
    values: {tree: John Pocklington, familysearch: Richard Pocklington}
    status: open
    severity: high
    next_record: "FS LZZM-3X4 displays Richard; our sources all read Richard"
    trail:
      - {date: 2026-06-22, by: recon-walk, note: "name-vs-records tangle"}
```

The consistency gate then caps the node from VERIFIED to POSSIBLE with a dated concern, because a VERIFIED conclusion cannot stand over an open high-severity identity question. The index surfaces it near the top of the direct-line backlog. A human investigates, decides the node really is Richard, and resolves the disagreement — which lifts the cap and lets the confidence be re-raised on the corrected identity. None of that required a second registry, a fragment file, or rediscovering the tangle next session.

## Why this is worth publishing

GPS and the evidence-conclusion model tell you how to reason to a sound conclusion as one researcher. They do not tell you how to keep a knowledge graph honest against three external graphs that disagree with you and with each other, edited by automated agents, with corrections flowing back out. That reconciliation-and-contribution layer — the seven classes, the status lifecycle, the confidence cap, the single-write-path-and-derived-index architecture — is the contribution. The reference implementation lives in `starter-kit/` (the journal v2 schema, `journal_io.py`, the index builder, the conformance JOUR checks) and is proven across three sibling trees.
