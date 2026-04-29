# Sister Project Audit Prompt

Paste the prompt below into a Claude Code session inside `~/genealogy`, `~/genealogy-kindred`, or `~/genealogy-dry-cross`. It audits the project against upstream methodology changes (commit `6992b16` in `ai-genealogy`) and against memory-system best practices for long-running per-person research.

The prompt is self-contained — Claude in those sessions will not have the conversation context that produced it.

---

```
This sister project depends on ~/ai-genealogy for shared methodology and
lessons. Two recent changes upstream (commit 6992b16) and one structural
gap in our prior audit need to be reflected here.

UPSTREAM CHANGES TO MIRROR

1. ai-genealogy/CLAUDE.md (new, 47 lines) governs edits to that repo and
   pins model versions in grep-canonical form (opus-4-6, opus-4-7).
2. ai-genealogy/CONTRIBUTING.md rule format now carries a captured-on
   date:
     **Rule [CONFIRMED ×N] (captured YYYY-MM-DD): Title.** Explanation.
   Lessons without a date should be dated when next edited; do not infer
   dates from git history.

YOUR SCOPE

This project is a real research project with thousands of per-person
context files, not a methodology repo. The audit below is split into:
  A. CLAUDE.md health (fast)
  B. Local lessons date convention
  C. Memory-system architecture (the important section)
  D. Boundaries and symlink check

Run all four. Report findings; apply only items that fit and that you can
verify locally. Do NOT auto-commit. Surface diffs for human review.

────────────────────────────────────────────────────────────────────────
A. CLAUDE.md HEALTH
────────────────────────────────────────────────────────────────────────

The project's CLAUDE.md likely lives at .claude/CLAUDE.md.

  wc -l .claude/CLAUDE.md
    Target: ≤150 lines. Adherence drops sharply past that threshold.

  grep -nEi '\b(best practices|idiomatic|robust|proper|clean code|where applicable|as needed|if relevant|consider edge cases)\b' .claude/CLAUDE.md
    These hedged descriptors silently underperform on Opus 4.7. Replace
    with enumerations ("handle: null, empty, unicode" beats "handle edge
    cases"). Skip prose where the phrase is the negative example.

  grep -nEi 'opus-4-?[567]|sonnet-4-?[567]|claude-[0-9]' .claude/CLAUDE.md
    Pin the model version in canonical hyphen form (opus-4-7, not
    "Opus 4.7") so future audits find it.

  grep -nE 'see (rules/|\.claude/|[A-Z])' .claude/CLAUDE.md
    Mechanical "see X.md" cross-references are frequently not read on
    Opus 4.7. Either inline the critical rule or front-load it under a
    "READ FIRST" header.

────────────────────────────────────────────────────────────────────────
B. LESSONS DATE CONVENTION
────────────────────────────────────────────────────────────────────────

Local working log — auto-detect at:
  docs/LESSONS_LEARNED.md  |  LESSONS_LEARNED.md  |  research/LEARNINGS.md

For each rule entry, check whether it carries a captured-on date matching
the new format. If not, do NOT backfill from git — date the rule with
today's date when you next touch it. Discovery date and edit date are
not the same.

Then run:
  python3 ~/ai-genealogy/starter-kit/scripts/promote-lessons.py --check

Confirm any rules ready to graduate from PROVISIONAL to CONFIRMED ×2.
The script never writes to ai-genealogy/lessons directly; it surfaces
candidates. A human edits the upstream file.

────────────────────────────────────────────────────────────────────────
C. MEMORY-SYSTEM ARCHITECTURE
────────────────────────────────────────────────────────────────────────

This is the section that previous audits skipped. Genealogy projects
have a misleading total-corpus size (thousands to tens of thousands of
markdown files) but the working unit is the **per-person slice**:

  research/cache/{ID}.json     ← prior platform search history
  research/journals/{ID}.md    ← append-only research log
  + adjacent persons' slices   ← when doing graph-relevant work

Each session loads ONE slice plus selectively-relevant lessons, not the
whole corpus. The right archetype follows from this pattern, not from
total file count.

C1. CONFIRM THE LOAD UNIT
    ls research/cache | wc -l        # per-person caches
    ls research/journals | wc -l     # per-person journals
    Per-slice doc count is typically 1–3 files. Total corpus size is
    misleading; never use it to pick an archetype.

C2. ARCHETYPE DECISION
    The applicable framework is "Archetype A" (curated KB with selective
    context loading) — entity slices are tiny, queries target one entity
    at a time, and PII sensitivity rules out egress-heavy alternatives.

    Do NOT adopt Archetype G (PostgreSQL + pgvector + cross-tool shared
    memory) unless cross-entity semantic search becomes load-bearing.
    Archetype G is for concurrent multi-tool writes; you have one human
    + one Claude session at a time.

    Do NOT introduce vector DBs or embedding indexes for "smarter" load.
    Grep over journals already delivers recall when slice IDs are known.

C3. CONTEXT-FIRST ENFORCEMENT (HOOK CANDIDATE)
    Three of the lessons are about exactly this:
      - "Context-first": read cache before browser research
      - "Write journal entries in real-time"
      - "Audit brick walls before dispatching research agents" (read
        validation.evidence.sources before flagging a research target)

    All three are currently CLAUDE.md instructions. Instruction-only
    enforcement is ~80% reliable. Move the load-bearing ones to hooks:

    PreToolUse hook on browser/research tools:
      - Block if research/cache/{ID}.json hasn't been read this session
      - Block if validation.evidence.sources hasn't been checked when
        the target is flagged brick_wall=True

    The hook should fail loud (exit 2) and tell Claude exactly which
    file to read first. This is the highest-leverage harness change for
    long research sessions.

C4. SELECTIVE LESSON LOADING
    lessons/LESSONS.md (via the symlink to ai-genealogy) is currently
    loaded as a flat block. Many rules apply only in specific contexts:
      - Pre-1700 rules → only when researching a Gen N≥10 ancestor
      - Pre-1700 European rules → only with European lineage
      - WT-citation rules → only when contributing to WikiTree
      - Delayed-birth-cert rule → only for U.S. births 1900–1950

    Two paths to selective surfacing:
      (a) Path-conditional rules files. .claude/rules/pre-1700.md
          loaded only when working on Gen ≥10 persons; rules/wikitree.md
          loaded only on WikiTree contribution flows. Requires a router
          (hook or convention) that detects the active context.
      (b) Lum1104 / Understand-Anything wikilinks across lessons + per-
          person journals, surfacing relevant rules at session start.
          Adopt only if (a) feels too rigid. Below ~200 lessons,
          Lum1104 alone is sufficient — no Pass-2 LLM extraction.

    Prefer (a) first. It is local, deterministic, and PII-safe.

C5. HIERARCHICAL/GRAPH AWARENESS
    Genealogy is a graph. Researching person X often makes parents,
    children, and spouses relevant. Today, adjacent slices are loaded
    by hand.

    Optional improvement (do not implement on speculation): a
    pre-research helper that, given target ID X, returns the paths of
    X's cache + journal AND those of immediate kin, so Claude can read
    them in one batch. Build this only after a session log shows that
    cross-person lookups are repeatedly missed.

C6. EGRESS / PII CONSTRAINTS
    Family data is PII. Any tool that ships content to a vendor's LLM
    for Pass-2 extraction (Graphify Pass 2, embedding APIs, hosted
    vector DBs) creates an irreversible egress event even if the local
    index is later deleted. Do not adopt these without a PII review.

    Keep the methodology chapter's "no family data in shared lessons"
    rule load-bearing. Anything that crosses out of this project's
    directory needs explicit confirmation.

C7. CONTEXT COMPACTION RESILIENCE
    Long sessions hit auto-compaction around 83.5% context, with
    quality decline noticeable around 60%. The existing real-time
    journaling rule mitigates this but does not eliminate it. Two
    further mitigations to consider:
      - End-of-session checkpoint write to research/journals/{ID}.md
        even if no new findings (records the session boundary).
      - Smaller targeted sessions per person rather than multi-person
        marathon sessions, when feasible.

────────────────────────────────────────────────────────────────────────
D. BOUNDARIES AND SYMLINK
────────────────────────────────────────────────────────────────────────

  ls -la docs/lessons-shared 2>/dev/null
    Should be a symlink to ~/ai-genealogy/lessons. If absent:
      ln -s ~/ai-genealogy/lessons docs/lessons-shared

  Verify (do not change unless broken):
    - This project SHOULD have family data; ai-genealogy should not.
    - This project's CLAUDE.md SHOULD have person IDs, family names,
      local paths; ai-genealogy's should not.
    - Tier vocabulary (T1/T2a/T2b/T3/T4/T5) and confidence labels
      (VERIFIED/PROBABLE/POSSIBLE/UNVERIFIED) are canonical. Do not
      invent new ones.

────────────────────────────────────────────────────────────────────────
REPORTING FORMAT
────────────────────────────────────────────────────────────────────────

For each section A–D, return one of:
  - "clean"
  - "issues found:" + list with file:line and proposed fix
  - "applied:" + diff

For section C specifically, structure findings as:
  C1 load-unit: <typical slice size>
  C2 archetype: <current pattern, recommended pattern, gap>
  C3 hooks: <list of context-first rules currently instruction-only>
  C4 lessons: <flat-loaded count, candidates for path-conditional split>
  C5 graph: <missed kin loads observed in last N sessions, if any>
  C6 egress: <any tool currently shipping family data outward>
  C7 compaction: <session length distribution, if measurable>

Do NOT auto-commit. Hook proposals and rules-file splits are
non-trivial; they need human review before merging.
```

---

## How this prompt was built

Sources cited (frontmatter `evidence-tier` shown):

- `analysis/memory-system-patterns.md` (A) — per-entity context loading
- `analysis/memory-systems-recommendation-methodology.md` (Mixed A–D) — archetype decision tree, per-entity guidance
- `analysis/memory-systems-archetype-a-curated-kb.md` (C) — Lum1104 ≤200 docs guidance
- `analysis/memory-systems-archetype-g-team-shared-memory.md` (C–D) — when NOT to adopt
- `analysis/memory-systems-graphify-vs-understand-anything.md` (B) — tool comparison and egress caveat
- `analysis/behavioral-insights.md` (Mixed) — 60% / 83.5% / 80% thresholds
- `analysis/harness-engineering.md` (Mixed A–B) — hook-enforced load-bearing rules
- `analysis/model-migration-anti-patterns.md` (Mixed) — vague-descriptor and read-enforcement guidance
- `analysis/claude-md-progressive-disclosure.md` (Mixed A–B) — front-loading and 150-line cap

If a sister-project audit reports that the path-conditional rules pattern (C4a) works well, that is a candidate to promote upstream into `methodology/07-memory-architecture.md` after 2+ projects confirm.
