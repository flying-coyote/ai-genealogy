#!/usr/bin/env python3
"""
promote-lessons.py — Pull-based lesson promotion tool.

Reads local LESSONS_LEARNED.md (or LEARNINGS.md) for **Rule**-tagged entries,
fuzzy-matches them against the shared LESSONS.md and PROVISIONAL.md, and
classifies each rule for promotion.

Classifications:
  ALREADY_CONFIRMED  — already in LESSONS.md with [CONFIRMED ×2/3]
  CONFIRM_THIS       — in PROVISIONAL.md with "Needs confirmation in: this-project"
  NEW_PROVISIONAL    — not in any shared file; ready to stage to PROVISIONAL.md
  SKIP               — matches a CONTESTED.md entry (already documented as disputed)

Usage:
  # Check only — report candidates without writing anything
  python3 promote-lessons.py --check

  # Check + stage NEW_PROVISIONAL candidates to PROVISIONAL.md
  python3 promote-lessons.py --stage

  # Specify a different local lessons file
  python3 promote-lessons.py --check --local docs/LESSONS_LEARNED.md

  # Specify a different shared lessons dir (default: auto-detected)
  python3 promote-lessons.py --check --lessons-dir /path/to/ai-genealogy/lessons

Run from the sister project root directory. The script auto-detects the shared
lessons directory by looking for 'docs/lessons-shared/' symlink or falling back
to '/home/jerem/ai-genealogy/lessons/'.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_LOCAL_FILES = [
    "docs/LESSONS_LEARNED.md",
    "LESSONS_LEARNED.md",
    "research/LEARNINGS.md",
    "LEARNINGS.md",
]

DEFAULT_LESSONS_DIRS = [
    "docs/lessons-shared",            # symlink present
    "/home/jerem/ai-genealogy/lessons",  # absolute fallback
]

SIMILARITY_THRESHOLD = 0.65  # fuzzy match cutoff for "same rule"


# ---------------------------------------------------------------------------
# Rule extraction
# ---------------------------------------------------------------------------

RULE_PATTERN = re.compile(
    r"\*\*Rule(?:\s+\[.*?\])?\s*:?\s*(.*?)\*\*\s*(.+?)(?=\n\n|\n\*\*Rule|\Z)",
    re.DOTALL,
)


def extract_rules(text: str) -> list[dict]:
    """
    Extract all **Rule ...** entries from a markdown file.
    Returns list of dicts with keys: title, body, full_text, tag.
    """
    rules = []
    # Match pattern: **Rule [TAG]: Title.** Body text
    pattern = re.compile(
        r"\*\*Rule(?:\s+(\[.*?\]))?\s*:?\s*([^*]+?)\*\*\s*([^\n].*?)(?=\n\n|\n\*\*Rule|\Z)",
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        tag = (m.group(1) or "").strip()
        title = m.group(2).strip().rstrip(".")
        body = m.group(3).strip()
        rules.append(
            {
                "tag": tag,
                "title": title,
                "body": body,
                "full_text": f"**Rule {tag}: {title}.** {body}".strip(),
            }
        )
    return rules


def extract_contested_slugs(text: str) -> list[str]:
    """Extract section headings from CONTESTED.md as slugs for SKIP matching."""
    headings = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
    return [h.strip().lower() for h in headings]


def extract_provisional_rules(text: str) -> list[dict]:
    """
    Extract PROVISIONAL rule entries (formatted as ## Title sections).
    Returns list of dicts: title, body, needs_confirmation_in.
    """
    rules = []
    # Split on ## headings
    sections = re.split(r"\n## ", "\n" + text)
    for section in sections[1:]:
        lines = section.strip().splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        needs = ""
        m = re.search(r"\*\*Needs confirmation in\*\*:\s*(.+)", body)
        if m:
            needs = m.group(1).strip()
        rules.append({"title": title, "body": body, "needs_confirmation_in": needs})
    return rules


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

def similarity(a: str, b: str) -> float:
    """Return SequenceMatcher similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_best_match(rule_title: str, candidates: list[str]) -> tuple[float, str]:
    """Return (best_score, best_candidate) from a list of strings."""
    best_score = 0.0
    best_candidate = ""
    for c in candidates:
        s = similarity(rule_title, c)
        if s > best_score:
            best_score = s
            best_candidate = c
    return best_score, best_candidate


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def classify_rule(
    rule: dict,
    confirmed_rules: list[dict],
    provisional_rules: list[dict],
    contested_slugs: list[str],
    project_name: str,
) -> dict:
    """
    Classify a local rule into one of:
      ALREADY_CONFIRMED, CONFIRM_THIS, NEW_PROVISIONAL, SKIP
    """
    title = rule["title"]

    # 1. Check CONTESTED — SKIP
    score, match = find_best_match(title, contested_slugs)
    if score >= SIMILARITY_THRESHOLD:
        return {
            "status": "SKIP",
            "reason": f"Matches CONTESTED entry: '{match}' ({score:.0%})",
            "rule": rule,
        }

    # 2. Check LESSONS.md confirmed rules — ALREADY_CONFIRMED
    confirmed_titles = [r["title"] for r in confirmed_rules]
    score, match = find_best_match(title, confirmed_titles)
    if score >= SIMILARITY_THRESHOLD:
        matched_rule = confirmed_rules[confirmed_titles.index(match)]
        return {
            "status": "ALREADY_CONFIRMED",
            "reason": f"Matches '{match}' {matched_rule.get('tag', '')} ({score:.0%})",
            "rule": rule,
        }

    # 3. Check PROVISIONAL.md — CONFIRM_THIS if this project is in "Needs confirmation in"
    provisional_titles = [r["title"] for r in provisional_rules]
    score, match = find_best_match(title, provisional_titles)
    if score >= SIMILARITY_THRESHOLD:
        idx = provisional_titles.index(match)
        prov = provisional_rules[idx]
        needs = prov.get("needs_confirmation_in", "")
        if project_name.lower() in needs.lower() or any(
            project_name.lower() in part.strip().lower()
            for part in needs.split(",")
        ):
            return {
                "status": "CONFIRM_THIS",
                "reason": f"Matches PROVISIONAL '{match}' ({score:.0%}); this project listed in 'Needs confirmation in'",
                "provisional": prov,
                "rule": rule,
            }
        else:
            return {
                "status": "ALREADY_CONFIRMED",
                "reason": f"Matches PROVISIONAL '{match}' ({score:.0%}); this project not listed as needing confirmation",
                "rule": rule,
            }

    # 4. New pattern — NEW_PROVISIONAL
    return {
        "status": "NEW_PROVISIONAL",
        "reason": "No match in LESSONS.md, PROVISIONAL.md, or CONTESTED.md",
        "rule": rule,
    }


# ---------------------------------------------------------------------------
# Staging
# ---------------------------------------------------------------------------

def build_provisional_entry(rule: dict, project_name: str) -> str:
    """Format a rule as a PROVISIONAL.md section entry."""
    title = rule["title"]
    body = rule["body"]
    today = __import__("datetime").date.today().isoformat()
    # Determine the other two projects
    all_projects = ["genealogy", "genealogy-kindred", "genealogy-dry-cross"]
    others = [p for p in all_projects if p.lower() != project_name.lower()]
    needs = ", ".join(others)
    return (
        f"\n## {title}\n\n"
        f"**Source**: {project_name} ({today})\n\n"
        f"{body}\n\n"
        f"**Needs confirmation in**: {needs}\n"
    )


def stage_provisional(entries: list[str], provisional_path: Path) -> None:
    """Append new entries to PROVISIONAL.md."""
    existing = provisional_path.read_text(encoding="utf-8") if provisional_path.exists() else ""
    with provisional_path.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n\n"):
            f.write("\n\n---\n")
        for entry in entries:
            f.write(entry)
            f.write("\n---\n")
    print(f"\n  Staged {len(entries)} new provisional rule(s) to {provisional_path}")


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    "ALREADY_CONFIRMED": "✓",
    "CONFIRM_THIS":      "→",
    "NEW_PROVISIONAL":   "+",
    "SKIP":              "~",
}

STATUS_LABELS = {
    "ALREADY_CONFIRMED": "Already confirmed (no action needed)",
    "CONFIRM_THIS":      "Ready to promote to CONFIRMED ×2 — edit LESSONS.md directly",
    "NEW_PROVISIONAL":   "New pattern — stage to PROVISIONAL.md",
    "SKIP":              "Disputed — documented in CONTESTED.md",
}


def print_report(results: list[dict]) -> None:
    by_status: dict[str, list] = {}
    for r in results:
        by_status.setdefault(r["status"], []).append(r)

    totals = {s: len(v) for s, v in by_status.items()}
    print("\n=== promote-lessons.py results ===\n")
    print(
        f"  {totals.get('CONFIRM_THIS', 0)} rule(s) ready to confirm   "
        f"  {totals.get('NEW_PROVISIONAL', 0)} new provisional candidate(s)   "
        f"  {totals.get('ALREADY_CONFIRMED', 0)} already covered   "
        f"  {totals.get('SKIP', 0)} contested"
    )
    print()

    for status in ("CONFIRM_THIS", "NEW_PROVISIONAL", "SKIP", "ALREADY_CONFIRMED"):
        group = by_status.get(status, [])
        if not group:
            continue
        icon = STATUS_COLORS[status]
        label = STATUS_LABELS[status]
        print(f"{icon} {label}:")
        for item in group:
            rule = item["rule"]
            print(f"    • {rule['title'][:80]}")
            print(f"      {item['reason']}")
            if status == "CONFIRM_THIS":
                prov = item.get("provisional", {})
                print(f"      Action: promote '{prov.get('title', '')}' in PROVISIONAL.md to LESSONS.md [CONFIRMED ×2]")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def detect_project_name(project_root: Path) -> str:
    """Infer project name from directory."""
    name = project_root.name
    return name if name else "unknown-project"


def find_local_file(project_root: Path, override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.exists() else project_root / override if (project_root / override).exists() else None
    for candidate in DEFAULT_LOCAL_FILES:
        p = project_root / candidate
        if p.exists():
            return p
    return None


def find_lessons_dir(project_root: Path, override: str | None) -> Path | None:
    if override:
        return Path(override)
    for candidate in DEFAULT_LESSONS_DIRS:
        p = project_root / candidate if not Path(candidate).is_absolute() else Path(candidate)
        if p.exists() and p.is_dir():
            return p
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Surface local rule patterns for promotion to shared LESSONS.md"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report promotion candidates without writing anything (default if no flag given)",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Stage NEW_PROVISIONAL candidates to PROVISIONAL.md",
    )
    parser.add_argument(
        "--local",
        metavar="FILE",
        help="Path to local lessons file (default: auto-detect LESSONS_LEARNED.md etc.)",
    )
    parser.add_argument(
        "--lessons-dir",
        metavar="DIR",
        help="Path to shared lessons directory (default: auto-detect)",
    )
    args = parser.parse_args()

    # Default to --check if neither flag given
    if not args.check and not args.stage:
        args.check = True

    project_root = Path.cwd()
    project_name = detect_project_name(project_root)

    # Locate files
    local_file = find_local_file(project_root, args.local)
    if not local_file:
        print(
            f"ERROR: No local lessons file found. Checked: {DEFAULT_LOCAL_FILES}\n"
            "Pass --local <path> to specify one.",
            file=sys.stderr,
        )
        sys.exit(1)

    lessons_dir = find_lessons_dir(project_root, args.lessons_dir)
    if not lessons_dir:
        print(
            "ERROR: Could not locate shared lessons directory.\n"
            f"Checked: {DEFAULT_LESSONS_DIRS}\n"
            "Pass --lessons-dir <path> to specify one.",
            file=sys.stderr,
        )
        sys.exit(1)

    lessons_md = lessons_dir / "LESSONS.md"
    provisional_md = lessons_dir / "PROVISIONAL.md"
    contested_md = lessons_dir / "CONTESTED.md"

    print(f"Project:      {project_name}")
    print(f"Local file:   {local_file}")
    print(f"Lessons dir:  {lessons_dir}")

    # Read files
    local_text = local_file.read_text(encoding="utf-8")
    confirmed_text = lessons_md.read_text(encoding="utf-8") if lessons_md.exists() else ""
    provisional_text = provisional_md.read_text(encoding="utf-8") if provisional_md.exists() else ""
    contested_text = contested_md.read_text(encoding="utf-8") if contested_md.exists() else ""

    # Extract
    local_rules = extract_rules(local_text)
    confirmed_rules = extract_rules(confirmed_text)
    provisional_rules = extract_provisional_rules(provisional_text)
    contested_slugs = extract_contested_slugs(contested_text)

    if not local_rules:
        print(f"\nNo **Rule**-tagged entries found in {local_file}.")
        print("Format: **Rule: Title.** Description")
        sys.exit(0)

    print(f"\nFound {len(local_rules)} local rule(s) in {local_file.name}")

    # Classify
    results = [
        classify_rule(rule, confirmed_rules, provisional_rules, contested_slugs, project_name)
        for rule in local_rules
    ]

    print_report(results)

    # Stage if requested
    if args.stage:
        new_provs = [r for r in results if r["status"] == "NEW_PROVISIONAL"]
        if not new_provs:
            print("Nothing to stage — no NEW_PROVISIONAL candidates.")
        else:
            entries = [
                build_provisional_entry(r["rule"], project_name) for r in new_provs
            ]
            stage_provisional(entries, provisional_md)
            print(
                f"\nNext step: review {provisional_md} and confirm accuracy before committing.\n"
                "Commit changes in the ai-genealogy repo (not the sister project)."
            )

    confirm_this = [r for r in results if r["status"] == "CONFIRM_THIS"]
    if confirm_this:
        print(
            "To confirm a CONFIRM_THIS rule:\n"
            f"  1. Edit {lessons_md} directly\n"
            "  2. Change [PROVISIONAL] → [CONFIRMED ×2] and add attribution\n"
            f"  3. Remove the entry from {provisional_md}\n"
            "  4. Commit in the ai-genealogy repo"
        )


if __name__ == "__main__":
    main()
