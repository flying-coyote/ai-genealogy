# Contributing to AI Genealogy Best Practices

This repository is distilled from three active genealogy projects. Lessons are promoted here only after cross-project validation. This document describes how to add, update, and contest rules.

---

## How Lessons Get Here

Each sister project maintains its own working log (`LESSONS_LEARNED.md` or `LEARNINGS.md`). When a pattern is observed:

1. It goes into the local project log first
2. When a second project confirms it independently, it's promoted to `lessons/LESSONS.md` with `[CONFIRMED ×2]`
3. When all three confirm it, it's updated to `[CONFIRMED ×3]`
4. Patterns seen in only one project go to `lessons/PROVISIONAL.md` until confirmed

Rules that the projects disagree on go to `lessons/CONTESTED.md` — not deleted, because contested rules often reveal genuine complexity.

---

## Rule Format

In `LESSONS.md`, every rule follows this format:

```markdown
**Rule [CONFIRMED ×N] (captured YYYY-MM-DD): Short imperative title.** Explanation of the rule,
what it prevents, and why it matters. Include a concrete example when the rule was discovered
through a failure.
*(project1, project2)*
```

The confidence tag is:
- `[CONFIRMED ×3]` — all three sister projects have validated this rule
- `[CONFIRMED ×2]` — two projects have validated it
- `[PROVISIONAL]` — one project so far (full entry in PROVISIONAL.md)
- `[CONTESTED]` — projects have contradictory guidance (full entry in CONTESTED.md)

The *(project1, project2)* attribution at the end is optional for `[CONFIRMED ×3]` rules (all three projects), required for `[CONFIRMED ×2]` rules to show which two confirmed it.

The `(captured YYYY-MM-DD)` field anchors revalidation. When a new Claude model ships or a lesson is touched after long inactivity, re-check whether the rule still holds against current platform behavior and current model behavior before treating it as confirmed. Lessons without a captured-on date should be dated when next edited; do not infer dates from git history alone, since edits may not coincide with the actual observation.

---

## Promoting a Rule

### From PROVISIONAL to CONFIRMED ×2

1. Find the rule in `lessons/PROVISIONAL.md`
2. A second project has now observed the same pattern
3. Move the rule to the appropriate section in `lessons/LESSONS.md` with tag `[CONFIRMED ×2]`
4. Remove it from `PROVISIONAL.md`
5. Update the "Needs confirmation in" note on any remaining PROVISIONAL entries

### From CONFIRMED ×2 to CONFIRMED ×3

1. Find the rule in `lessons/LESSONS.md`
2. A third project has confirmed it
3. Change the tag from `[CONFIRMED ×2]` to `[CONFIRMED ×3]`
4. Remove the attribution if you want (or keep it)

### Adding a new PROVISIONAL rule

1. Add an entry to `lessons/PROVISIONAL.md` following the section format:
   ```markdown
   ## Rule title (short, imperative)
   
   **Source**: project-name (YYYY-MM-DD)
   
   Explanation of the pattern, what triggered the discovery, why it matters.
   Code examples if relevant.
   
   **Needs confirmation in**: other-project-1, other-project-2
   ```

---

## Contesting a Rule

If your project's experience contradicts an existing rule in `LESSONS.md`:

1. Move the rule to `lessons/CONTESTED.md` (or add it there if the original stays in LESSONS.md as "Side A")
2. Document both sides fully — the original rule and the contradicting experience
3. Add a "Current resolution" note explaining whether:
   - The contradiction is context-dependent (both are right under different conditions)
   - One side is probably wrong and needs investigation
   - The rule needs a scope qualifier ("this applies only when X")

Do not simply delete a rule that another project found valuable. Contradictions are data.

---

## Resolving a CONTESTED Rule

When a contested rule gets resolved:

1. Write the resolved version in `LESSONS.md` with the appropriate `[CONFIRMED ×N]` tag
2. Update `CONTESTED.md` to show "Status: Resolved — see LESSONS.md"
3. Keep the CONTESTED.md entry with its two-sided history — it documents the reasoning

---

## Symlink Setup (Sister Projects)

The `lessons/` directory in this repo is designed to be symlinked from each sister project. This means any edit to `lessons/LESSONS.md` is immediately visible from all three project directories.

**Setup (run once per sister project)**:
```bash
# From within the sister project directory:
ln -s /path/to/ai-genealogy/lessons docs/lessons-shared
```

After setup, each project's CLAUDE.md can reference:
```
## Cross-Project Lessons
See `docs/lessons-shared/LESSONS.md` for confirmed rules across all three sister projects.
```

Each project's own `LESSONS_LEARNED.md` / `LEARNINGS.md` stays as the local working log for patterns under observation. Promote to `lessons/LESSONS.md` when confirmed.

---

## What Belongs Here vs. Project-Local

**Belongs in this repo (cross-project)**:
- Rules confirmed in 2+ projects
- API patterns and gotchas (platform behavior is platform behavior)
- Evidence standards and tier definitions
- Automation patterns that work identically across projects
- Failure modes that any project could hit

**Belongs in the local project CLAUDE.md**:
- Project-specific person IDs, family names, generation ranges
- Local script paths and command-line flags
- Platform account status (blocked/expired/active)
- Session-specific notes and current focus

**Does not belong anywhere in this repo**:
- Credentials, tokens, or account-specific config
- Actual family data or person records
- Project-specific pipeline scripts (too coupled to specific family lines)
- Active research queue state

---

## Session Contribution Workflow

At the end of any session where you documented a new pattern in your local `LESSONS_LEARNED.md`:

1. Run: `python3 /home/jerem/ai-genealogy/starter-kit/scripts/promote-lessons.py --check`
2. Review the output: it classifies each rule as ALREADY_CONFIRMED, CONFIRM_THIS, NEW_PROVISIONAL, or SKIP
3. **CONFIRM_THIS**: edit `lessons/LESSONS.md` directly — change `[PROVISIONAL]` → `[CONFIRMED ×2]` and add attribution
4. **NEW_PROVISIONAL**: run with `--stage` to append the entry to `lessons/PROVISIONAL.md`
5. **SKIP**: no action needed (already documented in CONTESTED.md)
6. Commit any `LESSONS.md` or `PROVISIONAL.md` changes in the **ai-genealogy repo** (not the sister project)

`promote-lessons.py` never writes to `LESSONS.md` directly — it only surfaces candidates. Human judgment decides whether a candidate truly belongs. The script uses fuzzy matching with a 65% similarity threshold to detect duplicate rules across minor wording variations.

The script auto-detects the local lessons file (`docs/LESSONS_LEARNED.md`, `LESSONS_LEARNED.md`, `research/LEARNINGS.md`) and the shared lessons directory (`docs/lessons-shared/` symlink or `/path/to/ai-genealogy/lessons`). Pass `--local` or `--lessons-dir` to override.

---

## The Three Sister Projects

| Project | Primary line | Size |
|---|---|---|
| `genealogy` | Paternal direct line | ~3,200 persons, Gen 2-21 |
| `genealogy-kindred` | Maternal direct line | ~430 persons, Gen 2-14 |
| `genealogy-dry-cross` | Multi-lineage (4 primary lines) | ~2,700 persons, Gen 1-16 |

All three use the same methodology and evidence standards. When a rule appears in all three independently, it's confirmed as genuinely cross-project.
