# CLAUDE.md — Repo-Maintenance Instructions

This file governs editing **this repository** (`ai-genealogy`). It is *not* the operating instructions for downstream genealogy projects — that artifact is `starter-kit/CLAUDE.md.template`, which gets copied and customized per project.

## Boundaries (read first)

1. **No family data lives here.** Person records, GEDCOM files, platform credentials, and research caches stay in the sister projects. If a draft contains a real name + birth year + place, it does not belong in this repo.
2. **The starter-kit template is an artifact, not your operating instructions.** Do not follow `starter-kit/CLAUDE.md.template` as if it governed your behavior in this repo; edit it as documentation.
3. **No `.claude/` harness.** This repo is a methodology hub with no agent loop. Do not add hooks, skills, or MCP servers to it. Hooks for downstream projects are documented in `methodology/04-automation-patterns.md`.

## Model version

Lessons in `lessons/LESSONS.md` and prose in `methodology/` were captured on Claude `opus-4-6` and `opus-4-7` sessions (Opus 4.6 and Opus 4.7). When a new Claude model ships, lessons should be revalidated before being treated as still-confirmed — see the captured-on-date convention in `CONTRIBUTING.md` ("Rule Format" section).

## Evidence vocabulary used in this repo

The methodology defines two orthogonal scales. Use them consistently in any prose, lesson, or guide:

- **Source tiers** (T1, T2a, T2b, T3, T4, T5) — describe the *source*. T1 = official records; T5 = online trees (leads only). Full table in `methodology/02-evidence-standards.md`.
- **Person confidence** (VERIFIED, PROBABLE, POSSIBLE, UNVERIFIED) — describe the *conclusion* about a person. Each level has a minimum-evidence rule.

Do not invent new tiers or confidence labels. If a lesson seems to need one, that is a signal the existing scales need a clarifying note, not an extension.

## Lessons lifecycle

- New patterns enter `lessons/PROVISIONAL.md` with a single-project source attribution.
- A pattern observed independently in a second project graduates to `lessons/LESSONS.md` tagged `[CONFIRMED ×2]`.
- A third independent observation upgrades the tag to `[CONFIRMED ×3]`.
- Contradictions go to `lessons/CONTESTED.md` with both sides documented; do not silently delete a contested rule.
- Full procedure: `CONTRIBUTING.md`. Promotion candidates are surfaced (not auto-applied) by `starter-kit/scripts/promote-lessons.py --check`.

When editing a lesson, preserve the captured-on date if present. Lessons without a date should be dated when next touched, so revalidation has an anchor.

## Writing style

- Prose is for practitioners who already know genealogy basics. Define BCG, GPS, T1–T5 once where they first appear; do not re-define in every chapter.
- Use enumerations over hedged language. Prefer "applies when X, Y, Z" to "applies as needed."
- When citing an external standard or platform behavior, link the source. When citing a sister project's experience, name the project.
- See `PHILOSOPHY.md` for the underlying frame (mechanical work vs. judgment calls). Do not contradict it.

## What goes where

- Cross-project rules → `lessons/LESSONS.md` (after 2+ confirmations).
- Methodology principles → `methodology/*.md` (numbered chapters).
- Platform-specific behavior, APIs, and gotchas → `platform-guides/{platform}.md`.
- Onboarding for new projects → `starter-kit/`.
- Local project specifics (person IDs, family names, paths) → never here. Sister project's own `CLAUDE.md`.
