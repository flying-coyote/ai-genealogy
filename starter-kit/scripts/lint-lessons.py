#!/usr/bin/env python3
"""
lint-lessons.py — Hub-side validator for the shared lessons catalog.

Unlike promote-lessons.py (which is pull-based and runs from a sister project),
this script runs from the ai-genealogy hub itself and checks that
lessons/LESSONS.md, lessons/PROVISIONAL.md, and lessons/CONTESTED.md are
well-formed, so the promotion machinery and human reviewers can trust them.

Checks
------
LESSONS.md
  - every **Rule ...** entry has a recognized tag
    ([CONFIRMED ×2] / [CONFIRMED ×3] / [PROVISIONAL] / [CONTESTED])
  - reports captured-date coverage ((captured YYYY-MM-DD)); missing dates are a
    WARNING, not an error — per CONTRIBUTING.md, dates are added when a rule is
    next touched and must never be inferred from git history
  - [CONFIRMED ×2] rules carry a *(project, project)* attribution

PROVISIONAL.md
  - every "## " entry carries **Source** and **Needs confirmation in**
  - "Needs confirmation in" names at least one known sister project

CONTESTED.md
  - every "## " entry has body content (both sides / resolution)

All three
  - YAML frontmatter present with `type:` and `title:`

Exit status
-----------
  0  no errors (warnings allowed)
  1  one or more errors, or --strict and any warnings

Usage
-----
  python3 lint-lessons.py                       # auto-detect ./lessons or repo root
  python3 lint-lessons.py --lessons-dir lessons
  python3 lint-lessons.py --strict              # warnings also fail (CI gate)
"""

import argparse
import re
import sys
from pathlib import Path

KNOWN_PROJECTS = {"genealogy", "genealogy-kindred", "genealogy-dry-cross"}
VALID_TAGS = {"CONFIRMED ×2", "CONFIRMED ×3", "PROVISIONAL", "CONTESTED"}
CAPTURED_RE = re.compile(r"\(captured \d{4}-\d{2}-\d{2}\)")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def find_lessons_dir(override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    here = Path.cwd()
    for candidate in (here / "lessons", here):
        if (candidate / "LESSONS.md").exists():
            return candidate
    return None


def check_frontmatter(text: str, fname: str, rep: Report) -> None:
    if not text.startswith("---"):
        rep.error(fname, "missing YAML frontmatter block")
        return
    block = text.split("---", 2)
    if len(block) < 3:
        rep.error(fname, "unterminated YAML frontmatter block")
        return
    front = block[1]
    if "type:" not in front:
        rep.error(fname, "frontmatter missing `type:`")
    if "title:" not in front:
        rep.error(fname, "frontmatter missing `title:`")


def check_lessons(text: str, rep: Report) -> None:
    fname = "LESSONS.md"
    check_frontmatter(text, fname, rep)

    # Each rule: **Rule [TAG]: Title.** ... (tag required in this file)
    rule_re = re.compile(r"\*\*Rule\s*(\[[^\]]*\])?\s*:?\s*(.*?)\*\*", re.DOTALL)
    matches = list(rule_re.finditer(text))
    if not matches:
        rep.error(fname, "no **Rule ...** entries found")
        return

    total = len(matches)
    dated = 0
    for m in matches:
        raw_tag = (m.group(1) or "").strip("[] ")
        title = (m.group(2) or "").strip().rstrip(".:").strip()
        label = title[:60] if title else "<untitled rule>"

        if not raw_tag:
            rep.error(fname, f"rule '{label}' has no [tag]")
        else:
            # tag may be "CONFIRMED ×2" possibly followed by "(captured ...)"
            tag_core = CAPTURED_RE.sub("", raw_tag).strip()
            if tag_core not in VALID_TAGS:
                rep.error(fname, f"rule '{label}' has unrecognized tag '[{raw_tag}]'")

        # captured-date coverage (warning only)
        # look at the bolded header span for the date
        header = m.group(0)
        if CAPTURED_RE.search(header):
            dated += 1

        # ×2 rules should name the two confirming projects nearby
        if "CONFIRMED ×2" in raw_tag:
            tail = text[m.end():m.end() + 600]
            if not re.search(r"\*\([^)]*\)\*", tail):
                rep.warn(fname, f"[CONFIRMED ×2] rule '{label}' lacks a *(project, project)* attribution")

    rep.note(f"LESSONS.md: {total} rules, {dated} with captured dates "
             f"({(100 * dated // total) if total else 0}% coverage)")
    if dated < total:
        rep.warn(fname, f"{total - dated} rule(s) lack a (captured YYYY-MM-DD) date "
                        f"— add when next touched (do not backfill from git history)")


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (title, body) for each '## ' section."""
    out = []
    for chunk in re.split(r"\n## ", "\n" + text)[1:]:
        lines = chunk.strip().splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip()
        out.append((title, body))
    return out


def check_provisional(text: str, rep: Report) -> None:
    fname = "PROVISIONAL.md"
    check_frontmatter(text, fname, rep)
    sections = split_sections(text)
    if not sections:
        rep.error(fname, "no '## ' entries found")
        return
    for title, body in sections:
        label = title[:60] or "<untitled>"
        if "**Source**" not in body and "**Sources**" not in body:
            rep.error(fname, f"entry '{label}' missing **Source**")
        m = re.search(r"\*\*Needs confirmation in\*\*:\s*(.+)", body)
        if not m:
            rep.error(fname, f"entry '{label}' missing **Needs confirmation in**")
            continue
        named = {p.strip().lower() for p in re.split(r"[,;]", m.group(1)) if p.strip()}
        if not (named & {p.lower() for p in KNOWN_PROJECTS}):
            rep.warn(fname, f"entry '{label}' 'Needs confirmation in' names no known project: {m.group(1).strip()[:60]}")
    rep.note(f"PROVISIONAL.md: {len(sections)} entries")


def check_contested(text: str, rep: Report) -> None:
    fname = "CONTESTED.md"
    check_frontmatter(text, fname, rep)
    sections = split_sections(text)
    if not sections:
        rep.note("CONTESTED.md: no entries (that's fine)")
        return
    for title, body in sections:
        label = title[:60] or "<untitled>"
        if len(body) < 40:
            rep.warn(fname, f"entry '{label}' looks empty — a contested rule should document both sides")
    rep.note(f"CONTESTED.md: {len(sections)} entries")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the shared lessons catalog.")
    ap.add_argument("--lessons-dir", metavar="DIR", help="Path to lessons/ (default: auto-detect)")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures (CI gate)")
    args = ap.parse_args()

    lessons_dir = find_lessons_dir(args.lessons_dir)
    if not lessons_dir:
        print("ERROR: could not locate a lessons/ directory (looked for LESSONS.md).", file=sys.stderr)
        return 1

    rep = Report()
    checks = {
        "LESSONS.md": check_lessons,
        "PROVISIONAL.md": check_provisional,
        "CONTESTED.md": check_contested,
    }
    for fname, fn in checks.items():
        path = lessons_dir / fname
        if not path.exists():
            rep.error(fname, "file not found")
            continue
        fn(path.read_text(encoding="utf-8"), rep)

    print(f"=== lint-lessons.py — {lessons_dir} ===\n")
    for n in rep.notes:
        print(f"  · {n}")
    print()
    for w in rep.warnings:
        print(f"  WARN  {w}")
    for e in rep.errors:
        print(f"  ERROR {e}")

    print(f"\n{len(rep.errors)} error(s), {len(rep.warnings)} warning(s).")
    if rep.errors:
        return 1
    if args.strict and rep.warnings:
        print("(--strict: warnings count as failures)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
