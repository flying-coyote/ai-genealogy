#!/usr/bin/env python3
"""
validate-tree.py — Portable genealogy tree validator.

Validates data/tree.json against the standard AI genealogy data model.
Checks structural integrity, required fields, cross-references, and
source quality rules. Zero dependencies on any specific family tree data.

Usage:
    python3 validate-tree.py            # exit 0 if no errors, 1 if errors
    python3 validate-tree.py --strict   # treat warnings as errors too

Run from the project root (directory containing data/).
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Required fields and allowed values
# ---------------------------------------------------------------------------

REQUIRED_PERSON_FIELDS = ["id", "canonical_name", "gender", "generation"]

VALID_CONFIDENCE = {"VERIFIED", "PROBABLE", "POSSIBLE", "UNVERIFIED"}

VALID_GENDER = {"M", "F", "U"}

REQUIRED_SOURCE_FIELDS = [
    "name", "title", "tier", "platform", "type",
    "added", "proves", "evidence_type",
]

VALID_EVIDENCE_TYPE = {"direct", "indirect", "negative"}

# Sources that count toward confidence thresholds
# (tiers 1-3 are primary/secondary; tier 4-5 are derivative/online trees)
VERIFIED_MIN_SOURCES = 2      # need ≥2 sources total for VERIFIED
VERIFIED_MAX_TIER = 2         # at least 2 of those must be tier ≤ 2
PROBABLE_MIN_SOURCES = 1      # need ≥1 source for PROBABLE
PROBABLE_MAX_TIER = 3         # at least 1 must be tier ≤ 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_tree(path: Path) -> dict:
    """Load and parse tree.json. Raises on file or JSON errors."""
    if not path.exists():
        print(f"ERROR: {path} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_id_set(persons: list) -> set:
    """Return the set of all person IDs for cross-reference checks."""
    return {p.get("id") for p in persons if p.get("id")}


class ValidationReport:
    """Accumulates warnings and errors with structured context."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


# ---------------------------------------------------------------------------
# Per-person checks
# ---------------------------------------------------------------------------

def check_required_fields(person: dict, report: ValidationReport):
    """Every person must have id, canonical_name, gender, generation."""
    pid = person.get("id", "<missing id>")
    for field in REQUIRED_PERSON_FIELDS:
        if field not in person or person[field] is None:
            report.error(f"{pid}: missing required field '{field}'")


def check_id_format(person: dict, report: ValidationReport):
    """Person IDs should follow @I<digits>@ or @I_<NAME>@ conventions."""
    pid = person.get("id", "")
    if not pid:
        return
    # Accept @I12345@, @I_NAME@ (synthetic), and @I_FS_*@ (FS-synthetic).
    # Warn (not error) if the pattern is unexpected — may be legacy IDs.
    if not (pid.startswith("@I") and pid.endswith("@")):
        report.warn(f"{pid}: id does not match expected @I...@ format")


def check_gender(person: dict, report: ValidationReport):
    """Gender must be M, F, or U."""
    pid = person.get("id", "<missing id>")
    gender = person.get("gender")
    if gender is not None and gender not in VALID_GENDER:
        report.error(f"{pid}: invalid gender '{gender}' (expected M/F/U)")


def check_generation(person: dict, report: ValidationReport):
    """Generation must be a positive integer."""
    pid = person.get("id", "<missing id>")
    gen = person.get("generation")
    if gen is not None:
        if not isinstance(gen, int) or gen < 1:
            report.error(f"{pid}: generation must be integer ≥ 1, got {gen!r}")


def check_confidence(person: dict, report: ValidationReport):
    """Confidence must be one of the four defined levels.

    NOTE: The canonical confidence field is validation.confidence.
    A top-level 'confidence' field is legacy (affects only ~18 persons in
    practice) and is intentionally ignored by this validator.
    """
    pid = person.get("id", "<missing id>")
    validation = person.get("validation") or {}
    confidence = validation.get("confidence")
    if confidence is None:
        report.warn(f"{pid}: validation.confidence is missing")
    elif confidence not in VALID_CONFIDENCE:
        report.error(
            f"{pid}: invalid confidence '{confidence}' "
            f"(expected one of {sorted(VALID_CONFIDENCE)})"
        )


def check_parent_refs(person: dict, all_ids: set, report: ValidationReport):
    """father_id and mother_id must point to existing person IDs if set."""
    pid = person.get("id", "<missing id>")
    for role in ("father_id", "mother_id"):
        ref = person.get(role)
        if ref is not None and ref not in all_ids:
            report.error(f"{pid}: {role} '{ref}' does not exist in persons list")


def check_child_refs(person: dict, all_ids: set, report: ValidationReport):
    """child_ids entries must point to existing person IDs if present."""
    pid = person.get("id", "<missing id>")
    for child_id in person.get("child_ids") or []:
        if child_id not in all_ids:
            report.warn(f"{pid}: child_ids contains unknown id '{child_id}'")


def check_spouse_refs(person: dict, all_ids: set, report: ValidationReport):
    """spouse_ids entries must point to existing person IDs if present."""
    pid = person.get("id", "<missing id>")
    for spouse_id in person.get("spouse_ids") or []:
        if spouse_id not in all_ids:
            report.warn(f"{pid}: spouse_ids contains unknown id '{spouse_id}'")


def check_sources(person: dict, report: ValidationReport):
    """Validate each source object and check confidence-vs-source rules.

    Rules:
    - Every source must have all REQUIRED_SOURCE_FIELDS.
    - tier must be an integer 1–5.
    - evidence_type must be 'direct', 'indirect', or 'negative'.
    - VERIFIED persons need ≥2 sources.
    - PROBABLE persons need ≥1 source.
    - validation.source_count must equal len(sources) when both are present.
    """
    pid = person.get("id", "<missing id>")
    validation = person.get("validation") or {}
    evidence = validation.get("evidence") or {}
    sources = evidence.get("sources") or []
    confidence = validation.get("confidence")

    # --- source_count consistency ---
    # The model stores source_count at both validation.source_count and
    # validation.evidence.source_count; both must match actual source list.
    declared_count_v = validation.get("source_count")
    declared_count_e = evidence.get("source_count")
    actual_count = len(sources)

    if declared_count_v is not None and declared_count_v != actual_count:
        report.error(
            f"{pid}: validation.source_count={declared_count_v} "
            f"but found {actual_count} sources"
        )
    if declared_count_e is not None and declared_count_e != actual_count:
        report.error(
            f"{pid}: validation.evidence.source_count={declared_count_e} "
            f"but found {actual_count} sources"
        )

    # --- per-source field checks ---
    for i, src in enumerate(sources):
        label = f"{pid} source[{i}]"

        for field in REQUIRED_SOURCE_FIELDS:
            if field not in src or src[field] is None:
                report.error(f"{label}: missing required field '{field}'")

        tier = src.get("tier")
        if tier is not None:
            if not isinstance(tier, int) or not (1 <= tier <= 5):
                report.error(f"{label}: tier must be integer 1–5, got {tier!r}")

        et = src.get("evidence_type")
        if et is not None and et not in VALID_EVIDENCE_TYPE:
            report.error(
                f"{label}: invalid evidence_type '{et}' "
                f"(expected {sorted(VALID_EVIDENCE_TYPE)})"
            )

    # --- confidence vs source count rules ---
    if confidence == "VERIFIED":
        if actual_count < VERIFIED_MIN_SOURCES:
            report.error(
                f"{pid}: VERIFIED requires ≥{VERIFIED_MIN_SOURCES} sources, "
                f"has {actual_count}"
            )
        # Check that at least 2 sources have tier ≤ 2
        strong = [s for s in sources if isinstance(s.get("tier"), int) and s["tier"] <= VERIFIED_MAX_TIER]
        if len(strong) < VERIFIED_MIN_SOURCES:
            report.warn(
                f"{pid}: VERIFIED — only {len(strong)} source(s) with tier ≤ {VERIFIED_MAX_TIER} "
                f"(recommend ≥{VERIFIED_MIN_SOURCES})"
            )

    elif confidence == "PROBABLE":
        if actual_count < PROBABLE_MIN_SOURCES:
            report.error(
                f"{pid}: PROBABLE requires ≥{PROBABLE_MIN_SOURCES} source(s), "
                f"has {actual_count}"
            )
        qualifying = [
            s for s in sources
            if isinstance(s.get("tier"), int) and s["tier"] <= PROBABLE_MAX_TIER
        ]
        if not qualifying:
            report.warn(
                f"{pid}: PROBABLE — no sources with tier ≤ {PROBABLE_MAX_TIER}"
            )


def check_lineage_part(person: dict, report: ValidationReport):
    """lineage_part must be an integer 1–16 or null (None)."""
    pid = person.get("id", "<missing id>")
    lp = person.get("lineage_part")
    if lp is not None:
        if not isinstance(lp, int) or not (1 <= lp <= 16):
            report.warn(f"{pid}: lineage_part={lp!r} outside expected range 1–16")


# ---------------------------------------------------------------------------
# Tree-level checks
# ---------------------------------------------------------------------------

def check_duplicate_ids(persons: list, report: ValidationReport):
    """Person IDs must be unique across the tree."""
    seen: dict[str, int] = defaultdict(int)
    for p in persons:
        pid = p.get("id")
        if pid:
            seen[pid] += 1
    for pid, count in seen.items():
        if count > 1:
            report.error(f"duplicate id '{pid}' appears {count} times")


def check_metadata(tree: dict, report: ValidationReport):
    """metadata block should be present with at least a title."""
    meta = tree.get("metadata")
    if not meta:
        report.warn("metadata block is missing")
    elif not meta.get("title"):
        report.warn("metadata.title is missing")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(strict: bool = False) -> int:
    tree_path = Path("data/tree.json")
    tree = load_tree(tree_path)

    persons = tree.get("persons", [])
    report = ValidationReport()

    # Tree-level checks
    check_metadata(tree, report)
    check_duplicate_ids(persons, report)

    # Build ID set once for cross-reference validation
    all_ids = build_id_set(persons)

    # Per-person checks
    for person in persons:
        check_required_fields(person, report)
        check_id_format(person, report)
        check_gender(person, report)
        check_generation(person, report)
        check_confidence(person, report)
        check_parent_refs(person, all_ids, report)
        check_child_refs(person, all_ids, report)
        check_spouse_refs(person, all_ids, report)
        check_sources(person, report)
        check_lineage_part(person, report)

    # Print results
    print(f"\nTree: {tree_path}")
    print(f"Persons: {len(persons)}")

    if report.warnings:
        print(f"\nWarnings ({len(report.warnings)}):")
        for w in report.warnings:
            print(f"  WARN  {w}")

    if report.errors:
        print(f"\nErrors ({len(report.errors)}):")
        for e in report.errors:
            print(f"  ERROR {e}")

    # Summary line
    error_count = len(report.errors) + (len(report.warnings) if strict else 0)
    valid_count = len(persons)  # "valid" = passed all hard checks per person
    # Approximate valid count by subtracting persons that had errors
    errored_ids = set()
    for msg in report.errors:
        # Extract the id prefix (everything before the first colon)
        errored_ids.add(msg.split(":")[0].strip())
    valid_count = len(persons) - len(errored_ids)

    print(
        f"\nSummary: {len(persons)} persons | "
        f"{valid_count} valid | "
        f"{len(report.warnings)} warnings | "
        f"{len(report.errors)} errors"
    )

    if strict and report.warnings:
        print("(--strict mode: warnings treated as errors)")

    if error_count == 0:
        print("OK")
        return 0
    else:
        print("FAILED")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate data/tree.json against the AI genealogy data model."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit 1 if any warnings exist)",
    )
    args = parser.parse_args()
    sys.exit(run(strict=args.strict))
