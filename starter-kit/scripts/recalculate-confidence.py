#!/usr/bin/env python3
"""
recalculate-confidence.py — Recalculate confidence for every person in tree.json.

Applies a rule-based rubric derived from the source evidence attached to each
person. Does NOT do research — it re-derives what the confidence label should
be given the sources already recorded.

Rules (applied in order, highest first):
  VERIFIED  — ≥2 sources with tier ≤ 2, no blocking concerns
  PROBABLE  — ≥1 source with tier ≤ 3, no blocking concerns
  POSSIBLE  — default (0 sources, or only tier 4-5 sources)
  UNVERIFIED — never auto-assigned; only written manually to flag bad data.
               The script will not upgrade an UNVERIFIED person.

Blocking concerns:
  A concern string in validation.concerns[] blocks promotion to PROBABLE or
  VERIFIED unless the concern begins with "RESOLVED" or "resolved".

DNA protection:
  A person with validation.dna_evidence set and currently VERIFIED will never
  be demoted, even if the source count logic would suggest POSSIBLE.

Dual confidence field warning:
  The CANONICAL confidence location is validation.confidence.
  A top-level 'confidence' field exists on a small number of legacy persons.
  This script reads and writes ONLY validation.confidence and ignores the
  top-level field entirely. If you see discrepancies, the top-level field is
  stale and can be removed.

Usage:
    python3 recalculate-confidence.py --dry-run           # show changes, no write
    python3 recalculate-confidence.py --apply             # write tree.json
    python3 recalculate-confidence.py --apply --verbose   # write + show details

Run from the project root (directory containing data/).
"""

import json
import sys
import argparse
import copy
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Tier ≤ this value counts as "strong" evidence for VERIFIED
VERIFIED_TIER_THRESHOLD = 2
VERIFIED_MIN_STRONG = 2      # need this many strong sources

# Tier ≤ this value counts as qualifying evidence for PROBABLE
PROBABLE_TIER_THRESHOLD = 3
PROBABLE_MIN_QUALIFYING = 1  # need this many qualifying sources

# Confidence levels in order (highest → lowest) for comparison
CONFIDENCE_ORDER = ["VERIFIED", "PROBABLE", "POSSIBLE", "UNVERIFIED"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_tree(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: {path} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_tree(path: Path, tree: dict):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(tree, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def has_blocking_concerns(validation: dict) -> bool:
    """Return True if any unresolved concern would block promotion.

    Concerns beginning with 'RESOLVED' or 'resolved' are treated as closed
    and do not block promotion.
    """
    concerns = validation.get("concerns") or []
    for concern in concerns:
        if isinstance(concern, str):
            lowered = concern.strip().lower()
            if not lowered.startswith("resolved"):
                return True
    return False


def has_dna_protection(validation: dict) -> bool:
    """Return True if DNA evidence protects VERIFIED from demotion."""
    return bool(validation.get("dna_evidence"))


def derive_confidence(person: dict) -> str | None:
    """Derive the appropriate confidence level from sources.

    Returns the derived level string, or None if the person should not
    be touched (UNVERIFIED — never auto-assigned).

    Current confidence is read from validation.confidence.
    The legacy top-level confidence field is ignored.
    """
    validation = person.get("validation") or {}
    current = validation.get("confidence")

    # Never auto-promote or demote UNVERIFIED persons.
    # UNVERIFIED is a deliberate manual flag indicating data problems.
    if current == "UNVERIFIED":
        return None

    sources = (validation.get("evidence") or {}).get("sources") or []

    # Count qualifying sources at each tier threshold
    strong_sources = [
        s for s in sources
        if isinstance(s.get("tier"), int) and s["tier"] <= VERIFIED_TIER_THRESHOLD
    ]
    qualifying_sources = [
        s for s in sources
        if isinstance(s.get("tier"), int) and s["tier"] <= PROBABLE_TIER_THRESHOLD
    ]

    blocked = has_blocking_concerns(validation)
    dna_protected = has_dna_protection(validation) and current == "VERIFIED"

    # Apply rules from highest to lowest
    if (
        len(strong_sources) >= VERIFIED_MIN_STRONG
        and not blocked
    ):
        derived = "VERIFIED"
    elif (
        len(qualifying_sources) >= PROBABLE_MIN_QUALIFYING
        and not blocked
    ):
        derived = "PROBABLE"
    else:
        derived = "POSSIBLE"

    # DNA protection: never demote a VERIFIED-with-DNA person
    if dna_protected and derived != "VERIFIED":
        return "VERIFIED"  # protected — keep VERIFIED

    return derived


def confidence_rank(level: str) -> int:
    """Lower number = higher confidence. UNVERIFIED gets highest number."""
    try:
        return CONFIDENCE_ORDER.index(level)
    except ValueError:
        return len(CONFIDENCE_ORDER)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(dry_run: bool, apply: bool, verbose: bool) -> int:
    if not dry_run and not apply:
        print("ERROR: specify --dry-run or --apply", file=sys.stderr)
        sys.exit(1)

    tree_path = Path("data/tree.json")
    tree = load_tree(tree_path)
    persons = tree.get("persons", [])

    upgrades = []    # (id, name, old, new)
    downgrades = []
    skipped_unverified = []
    skipped_dna = []
    unchanged = 0

    for person in persons:
        pid = person.get("id", "<missing>")
        name = person.get("canonical_name", "?")
        validation = person.get("validation") or {}
        current = validation.get("confidence")
        derived = derive_confidence(person)

        if derived is None:
            # UNVERIFIED — skip
            skipped_unverified.append(pid)
            continue

        if derived == current:
            unchanged += 1
            if verbose:
                print(f"  unchanged  {pid}  {name}  → {current}")
            continue

        # Classify as upgrade or downgrade
        if current is None:
            # No confidence set — treat as assignment
            upgrades.append((pid, name, current, derived))
        elif confidence_rank(derived) < confidence_rank(current):
            upgrades.append((pid, name, current, derived))
        else:
            # Check DNA protection (derive_confidence already handles this,
            # but we label the skip here for reporting)
            if has_dna_protection(validation) and current == "VERIFIED":
                skipped_dna.append(pid)
                if verbose:
                    print(f"  dna-prot   {pid}  {name}  stays VERIFIED (DNA)")
                continue
            downgrades.append((pid, name, current, derived))

        if verbose:
            direction = "↑" if confidence_rank(derived) < confidence_rank(current or "POSSIBLE") else "↓"
            print(f"  {direction} {current or 'None'} → {derived}  {pid}  {name}")

        # Apply change in-place (only writes if --apply)
        if apply:
            if "validation" not in person or person["validation"] is None:
                person["validation"] = {}
            person["validation"]["confidence"] = derived

    # Print summary
    print(f"\nRecalculate confidence — {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Persons processed:  {len(persons)}")
    print(f"Upgrades:           {len(upgrades)}")
    print(f"Downgrades:         {len(downgrades)}")
    print(f"Unchanged:          {unchanged}")
    print(f"Skipped (UNVERIFIED): {len(skipped_unverified)}")
    print(f"Skipped (DNA prot): {len(skipped_dna)}")

    if upgrades:
        print("\nUpgrades:")
        for pid, name, old, new in upgrades:
            print(f"  {old or 'None':12} → {new:12}  {pid}  {name}")

    if downgrades:
        print("\nDowngrades:")
        for pid, name, old, new in downgrades:
            print(f"  {old or 'None':12} → {new:12}  {pid}  {name}")

    if dry_run:
        print("\n(dry-run — no changes written)")
    else:
        save_tree(tree_path, tree)
        total_changed = len(upgrades) + len(downgrades)
        print(f"\nWrote {tree_path} ({total_changed} persons updated)")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recalculate confidence levels in data/tree.json from source evidence."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing tree.json",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write recalculated confidence values to tree.json",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every person's result, not just changes",
    )
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run, apply=args.apply, verbose=args.verbose))
