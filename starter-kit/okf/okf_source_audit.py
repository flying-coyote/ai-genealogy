#!/usr/bin/env python3
"""Source-field drift audit across the three trees (run on a cadence, like okf_health).

Counts how many source records carry a non-accepted key (per the source-field registry),
and which keys drift most — the worklist for a gated rewrite to the canonical names.

Usage:
  python3 scripts/okf_source_audit.py            # summary + top drift keys
  python3 scripts/okf_source_audit.py --brief
  python3 scripts/okf_source_audit.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from okf_source_fields import accepted_source_keys, noncanonical_keys  # noqa: E402

TREES = {
    "genealogy": "/home/jerem/genealogy/data/tree.json",
    "dry-cross": "/home/jerem/genealogy-dry-cross/data/tree.json",
    "kindred": "/home/jerem/genealogy-kindred/data/tree.json",
}


def audit():
    accepted = accepted_source_keys()
    drift_keys = Counter()
    per_tree = {}
    total_sources = 0
    sources_with_drift = 0
    for tree, path in TREES.items():
        try:
            persons = json.loads(Path(path).read_text()).get("persons", [])
        except OSError:
            continue
        t_sources = t_drift = 0
        t_keys = Counter()
        for p in persons:
            for s in (p.get("validation", {}).get("evidence", {}).get("sources") or []):
                t_sources += 1
                nc = noncanonical_keys(s, accepted)
                if nc:
                    t_drift += 1
                    t_keys.update(nc)
        per_tree[tree] = {"sources": t_sources, "sources_with_drift": t_drift,
                          "top_drift_keys": dict(t_keys.most_common(10))}
        total_sources += t_sources
        sources_with_drift += t_drift
        drift_keys.update(t_keys)
    return {
        "accepted_key_count": len(accepted),
        "total_sources": total_sources,
        "sources_with_drift": sources_with_drift,
        "drift_pct": round(100 * sources_with_drift / total_sources, 1) if total_sources else 0.0,
        "distinct_drift_keys": len(drift_keys),
        "top_drift_keys": dict(drift_keys.most_common(25)),
        "per_tree": per_tree,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    r = audit()
    flag = "✅" if r["sources_with_drift"] == 0 else "⚠️"
    line = (f"{flag} source-field drift: {r['drift_pct']}% of {r['total_sources']} sources "
            f"({r['sources_with_drift']}) carry one of {r['distinct_drift_keys']} non-accepted keys; "
            f"{r['accepted_key_count']} accepted keys")
    if args.brief:
        print(line); return 0
    if args.json:
        print(json.dumps(r, indent=2)); return 0
    print("━" * 74)
    print("tree.json source-field drift audit")
    print("━" * 74)
    print(line)
    print()
    print(f"{'tree':14} {'sources':>9} {'w/drift':>9}")
    for t, v in r["per_tree"].items():
        print(f"{t:14} {v['sources']:>9} {v['sources_with_drift']:>9}")
    print("\ntop drift keys (→ see merge map in research/source-field-registry.md):")
    for k, n in r["top_drift_keys"].items():
        print(f"  {k:24} {n}")
    print("━" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
