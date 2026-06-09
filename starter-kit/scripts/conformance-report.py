#!/usr/bin/env python3
"""
conformance-report.py — Cross-project conformance checker for the AI-genealogy standard.

Scores a project's data/tree.json against the *checkable* best-practice standards in
ai-genealogy/methodology/ and reports violations by severity. This is the "downward"
half of the methodology loop: promote-lessons.py lifts confirmed lessons UP from a
project into the shared standard; this verifies a project actually conforms DOWN to it.

A standard that is only prose drifts (measured: documented negative-search coverage
ran 3% / 16% / 41% across three sister projects that all cite the same hub). A standard
carried by a check holds. This script turns the methodology's checkable rules into a
check, and the gate makes "did this project follow the standard?" answerable in CI.

Standards checked — each cites methodology chapter §section:

  ERROR  (data-quality bugs; the gate blocks any commit that increases these):
    CONF-1  VERIFIED needs >=2 sources of tier<=2           (02 §Confidence Rules)
    CONF-2  no PROBABLE/VERIFIED with zero sources           (02 §Confidence Rules)
    CONF-3  no Tier-5-only person at PROBABLE or above       (02 §The Tier 5 Rule)

  WARN   (process/coverage; tracked + surfaced at session close, not commit-blocking
          unless --strict, so bulk capture runs are not frozen on aspirational metrics):
    SRC-1   source objects carry every required field        (02 §Required Source Fields)
    COV-1   concluded persons show search on Ancestry AND FS (03 §Platform Research Sequence)
    DOC-1   concluded persons have a documented negative search OR cross-platform sources
                                                             (02 §Negative Searches)
    UPG-1   POSSIBLE persons carry an upgrade_path           (02 §POSSIBLE Seeding)
    DUR-1   Ancestry-sourced persons are anchored to an FS ARK (02 §Durability Tiering)

Usage (run from project root, the directory containing data/):
    conformance-report.py                 # full human report (default)
    conformance-report.py --summary       # scorecard + per-check totals only
    conformance-report.py --json          # machine-readable per-check counts
    conformance-report.py --baseline      # write .conformance-baseline.json from current counts
    conformance-report.py --gate          # compare to baseline; exit 1 on any ERROR regression
    conformance-report.py --gate --strict # also gate on WARN regressions

The checker is dependency-free (stdlib only) and READ-ONLY on tree.json. Output names
person IDs, never personal names — safe to paste into a public issue. Designed to be
SYMLINKED into each project (scripts/conformance-report.py -> this file) so it cannot
fork the way the copied validators did.
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASELINE_FILE = ".conformance-baseline.json"

# Confidence thresholds — mirror the hub validate-tree.py so the two agree.
VERIFIED_MIN_TIER2_SOURCES = 2   # VERIFIED needs >=2 sources of tier <= 2
CONCLUDED = ("VERIFIED", "PROBABLE")

SEVERITY = {
    "CONF-1": "ERROR", "CONF-2": "ERROR", "CONF-3": "ERROR",
    "SRC-1": "WARN", "COV-1": "WARN", "DOC-1": "WARN",
    "UPG-1": "WARN", "DUR-1": "WARN",
}
STANDARD_REF = {
    "CONF-1": "02 §Confidence Rules (VERIFIED >=2 T1/2a)",
    "CONF-2": "02 §Confidence Rules (zero sources = POSSIBLE max)",
    "CONF-3": "02 §The Tier 5 Rule (T5-only -> POSSIBLE max)",
    "SRC-1":  "02 §Required Source Fields",
    "COV-1":  "03 §Platform Research Sequence (search Ancestry + FamilySearch)",
    "DOC-1":  "02 §Negative Searches (GPS Element 1)",
    "UPG-1":  "02 §POSSIBLE Seeding (upgrade_path required)",
    "DUR-1":  "02 §Durability Tiering (anchor Ancestry evidence to FS ARK)",
}
REQUIRED_SOURCE_FIELDS = ["name", "title", "tier", "platform", "type",
                          "added", "proves", "evidence_type"]


# --------------------------------------------------------------------------- #
# tolerant accessors (the three trees carry minor schema drift)
# --------------------------------------------------------------------------- #
def asdict(x): return x if isinstance(x, dict) else {}
def aslist(x): return x if isinstance(x, list) else []
def asstr(x):
    if isinstance(x, str): return x
    if isinstance(x, list): return " ".join(str(i) for i in x)
    return str(x) if x else ""

def confidence(p): return asstr(asdict(p.get("validation")).get("confidence")).upper()
def sources(p): return aslist(asdict(asdict(p.get("validation")).get("evidence")).get("sources"))

def tier_major(s):
    """Leading digit of the tier field; handles int, '2a'/'2b', 'T3'."""
    t = s.get("tier")
    if isinstance(t, int): return t
    m = re.search(r"[1-5]", asstr(t))
    return int(m.group()) if m else None

def src_blob(s):
    return " ".join(asstr(s.get(k)) for k in ("platform", "url", "name", "ark")).lower()

def is_ancestry(s): return "ancestry" in src_blob(s)
def is_fs_ark(s):
    b = src_blob(s)
    return ("ark:/" in b) or ("familysearch" in b and bool(s.get("ark")))

def is_collateral(p):
    if p.get("lineage_part") is None and not p.get("generation"):
        return True
    return bool(re.search(r"collateral|not in (the )?direct|in-?law|step-|wrong person",
                          asstr(p.get("notes")), re.I))

def has_negative_search(p):
    v = asdict(p.get("validation")); ev = asdict(v.get("evidence"))
    for loc in (ev.get("negative_searches"), v.get("negative_searches"),
                asdict(p.get("research_status")).get("negative_searches")):
        if isinstance(loc, list) and loc:
            return True
    return False

def platform_searched(p, key, src_pred):
    """True if the person shows evidence of a search on a platform: a platform_id,
    a source from it, or a documented negative search naming it."""
    if asdict(p.get("platform_ids")).get(key):
        return True
    if any(src_pred(s) for s in sources(p)):
        return True
    ev = asdict(asdict(p.get("validation")).get("evidence"))
    for ns in aslist(ev.get("negative_searches")):
        if key in asstr(asdict(ns).get("platform")).lower():
            return True
    return False


# --------------------------------------------------------------------------- #
# checks — each returns a list of offending person IDs
# --------------------------------------------------------------------------- #
def run_checks(persons):
    viol = {k: [] for k in SEVERITY}
    for p in persons:
        pid = p.get("id", "<no-id>")
        c = confidence(p)
        S = sources(p)
        tier2 = [s for s in S if (tier_major(s) or 9) <= 2]
        majors = [tier_major(s) for s in S if tier_major(s)]

        # ERROR: confidence gate
        if c == "VERIFIED" and len(tier2) < VERIFIED_MIN_TIER2_SOURCES:
            viol["CONF-1"].append(pid)
        if c in CONCLUDED and len(S) == 0:
            viol["CONF-2"].append(pid)
        if c in ("VERIFIED", "PROBABLE") and majors and min(majors) >= 5:
            viol["CONF-3"].append(pid)

        # WARN: source-field completeness
        for s in S:
            if not (s.get("tier") and s.get("proves") and (s.get("ark") or s.get("url"))):
                viol["SRC-1"].append(pid)
                break

        # WARN: coverage / documentation — concluded, non-collateral persons only
        if c in CONCLUDED and not is_collateral(p):
            anc = platform_searched(p, "ancestry", is_ancestry)
            fs = platform_searched(p, "familysearch",
                                   lambda s: "familysearch" in src_blob(s) or "ark:/" in src_blob(s))
            if not (anc and fs):
                viol["COV-1"].append(pid)
            if not has_negative_search(p) and not (anc and fs):
                viol["DOC-1"].append(pid)

        # WARN: POSSIBLE without an upgrade_path
        if c == "POSSIBLE" and not p.get("upgrade_path"):
            viol["UPG-1"].append(pid)

        # WARN: Ancestry evidence not anchored to a durable FS ARK
        if any(is_ancestry(s) for s in S) and not any(is_fs_ark(s) for s in S):
            viol["DUR-1"].append(pid)
    return viol


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def counts(viol): return {k: len(v) for k, v in viol.items()}

def coverage_stats(persons):
    n = len(persons) or 1
    anc = sum(1 for p in persons if asdict(p.get("platform_ids")).get("ancestry"))
    fs = sum(1 for p in persons if asdict(p.get("platform_ids")).get("familysearch"))
    wt = sum(1 for p in persons if asdict(p.get("platform_ids")).get("wikitree"))
    neg = sum(1 for p in persons if has_negative_search(p))
    return {"persons": len(persons),
            "ancestry": round(100*anc/n), "familysearch": round(100*fs/n),
            "wikitree": round(100*wt/n), "neg_search": round(100*neg/n)}

def print_report(persons, viol, summary_only=False):
    cov = coverage_stats(persons)
    c = counts(viol)
    err = sum(c[k] for k in SEVERITY if SEVERITY[k] == "ERROR")
    warn = sum(c[k] for k in SEVERITY if SEVERITY[k] == "WARN")
    print("=" * 72)
    print("  CONFORMANCE REPORT vs ai-genealogy methodology")
    print("=" * 72)
    print(f"  persons {cov['persons']}   platform coverage: "
          f"ANC {cov['ancestry']}%  FS {cov['familysearch']}%  WT {cov['wikitree']}%   "
          f"neg-search {cov['neg_search']}%")
    print(f"  ERRORS {err}    WARNINGS {warn}")
    print("  " + "-" * 68)
    for k in SEVERITY:
        print(f"  [{SEVERITY[k]:<5}] {k:<7} {c[k]:>6}   {STANDARD_REF[k]}")
    if not summary_only:
        print("  " + "-" * 68)
        for k in SEVERITY:
            if viol[k]:
                sample = ", ".join(viol[k][:8])
                more = f"  (+{len(viol[k])-8} more)" if len(viol[k]) > 8 else ""
                print(f"  {k} sample: {sample}{more}")
    print("=" * 72)
    return err, warn


# --------------------------------------------------------------------------- #
# gate (ratchet against baseline)
# --------------------------------------------------------------------------- #
def load_baseline(root):
    f = root / BASELINE_FILE
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except Exception:
        return None

def gate(root, viol, strict):
    cur = counts(viol)
    base = load_baseline(root)
    if base is None:
        print(f"conformance: no {BASELINE_FILE} found — run --baseline once to set the floor.",
              file=sys.stderr)
        return 0  # do not block a repo that has not adopted the gate yet
    regressed = []
    for k, n in cur.items():
        if SEVERITY[k] == "ERROR" or strict:
            floor = base.get(k, 0)
            if n > floor:
                regressed.append((k, floor, n))
    if regressed:
        print("conformance GATE FAILED — these checks regressed above baseline:", file=sys.stderr)
        for k, floor, n in regressed:
            print(f"  [{SEVERITY[k]}] {k}: baseline {floor} -> {n}  ({STANDARD_REF[k]})",
                  file=sys.stderr)
        print("Fix the new violations, or if intentional re-baseline with "
              "conformance-report.py --baseline.", file=sys.stderr)
        return 1
    # passed; note if the project has improved below its floor
    improved = [k for k in cur if cur[k] < base.get(k, 0)]
    if improved:
        print(f"conformance: gate passed; {len(improved)} check(s) improved below baseline — "
              f"run --baseline to ratchet the floor down.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Conformance checker vs the AI-genealogy standard.")
    ap.add_argument("--tree", default="data/tree.json", help="path to tree.json")
    ap.add_argument("--summary", action="store_true", help="scorecard + totals only")
    ap.add_argument("--json", action="store_true", help="machine-readable per-check counts")
    ap.add_argument("--baseline", action="store_true", help=f"write {BASELINE_FILE} from current counts")
    ap.add_argument("--gate", action="store_true", help="compare to baseline; exit 1 on ERROR regression")
    ap.add_argument("--strict", action="store_true", help="with --gate, also gate WARN regressions")
    args = ap.parse_args()

    tree_path = Path(args.tree)
    if not tree_path.exists():
        print(f"ERROR: {tree_path} not found. Run from project root.", file=sys.stderr)
        return 1
    root = tree_path.resolve().parent.parent  # project root = parent of data/
    persons = json.loads(tree_path.read_text()).get("persons", [])
    viol = run_checks(persons)

    if args.baseline:
        (root / BASELINE_FILE).write_text(json.dumps(counts(viol), indent=2) + "\n")
        print(f"wrote {root / BASELINE_FILE}: {counts(viol)}")
        return 0
    if args.gate:
        return gate(root, viol, args.strict)
    if args.json:
        print(json.dumps({"coverage": coverage_stats(persons), "counts": counts(viol),
                          "severity": SEVERITY}, indent=2))
        return 0
    err, _ = print_report(persons, viol, summary_only=args.summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
