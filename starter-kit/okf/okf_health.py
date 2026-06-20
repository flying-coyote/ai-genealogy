#!/usr/bin/env python3
"""OKF graph health check for the genealogy knowledge graph.

Reports, per root, whether the typed-markdown graph is healthy and complete:
  - coverage: typed notes / eligible markdown
  - drift:    typed notes whose `type:` is not in the canonical registry
  - gaps:     knowledge-candidate files with no `type:` at all

A health SIGNAL on a cadence, not a commit gate. Local-file only.

Usage:
  python3 scripts/okf_health.py                 # all four roots (federated)
  python3 scripts/okf_health.py --brief         # one-line signal
  python3 scripts/okf_health.py --json          # machine-readable
  python3 scripts/okf_health.py --gaps          # also list the untyped gap files
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from okf import (  # noqa: E402
    GENEALOGY_ROOTS, load_notes, load_canonical_types, is_graph_candidate,
)


def area_stats(root: Path, canon: set[str]) -> dict:
    notes = load_notes([root])
    typed = [n for n in notes if n.type]
    drift = [n for n in typed if n.type not in canon]
    gaps = [n for n in notes if not n.type and is_graph_candidate(n)]
    total = len(notes)
    return {
        "area": root.name or str(root),
        "total_md": total,
        "typed": len(typed),
        "coverage_pct": round(100 * len(typed) / total, 1) if total else 0.0,
        "drift_count": len(drift),
        "drift": sorted({f"{n.type} :: {n.rel}" for n in drift})[:40],
        "gap_count": len(gaps),
        "gaps": sorted(n.rel for n in gaps)[:60],
        "by_type": dict(Counter(n.type for n in typed).most_common()),
    }


def build_report(roots) -> dict:
    canon = load_canonical_types()
    areas = [area_stats(Path(r), canon) for r in roots]
    g_total = sum(a["total_md"] for a in areas)
    g_typed = sum(a["typed"] for a in areas)
    g_drift = sum(a["drift_count"] for a in areas)
    g_gaps = sum(a["gap_count"] for a in areas)
    return {
        "canonical_type_count": len(canon),
        "canonical_types": sorted(canon),
        "graph_total": g_total,
        "graph_typed": g_typed,
        "graph_coverage_pct": round(100 * g_typed / g_total, 1) if g_total else 0.0,
        "total_drift": g_drift,
        "total_gaps": g_gaps,
        "areas": areas,
    }


def one_line(r: dict) -> str:
    flag = "✅" if r["total_drift"] == 0 else "⚠️"
    return (f"{flag} OKF: {r['graph_coverage_pct']}% typed "
            f"({r['graph_typed']}/{r['graph_total']}), "
            f"{r['total_drift']} drift, {r['total_gaps']} gaps, "
            f"{r['canonical_type_count']} canonical types")


def main() -> int:
    ap = argparse.ArgumentParser(description="OKF graph health check")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gaps", action="store_true", help="list untyped gap files per area")
    args = ap.parse_args()

    r = build_report(GENEALOGY_ROOTS)
    if args.brief:
        print(one_line(r)); return 0
    if args.json:
        print(json.dumps(r, indent=2)); return 0

    print("━" * 74)
    print("OKF graph health — genealogy (federated)")
    print("━" * 74)
    print(one_line(r))
    print()
    print(f"{'area':22} {'cov%':>6} {'typed':>7} {'total':>7} {'drift':>6} {'gaps':>6}")
    for a in r["areas"]:
        print(f"{a['area']:22} {a['coverage_pct']:>6} {a['typed']:>7} "
              f"{a['total_md']:>7} {a['drift_count']:>6} {a['gap_count']:>6}")
    print()
    for a in r["areas"]:
        if a["by_type"]:
            top = ", ".join(f"{t}:{c}" for t, c in list(a["by_type"].items())[:8])
            print(f"  {a['area']} types → {top}")
    if r["total_drift"]:
        print("\nDRIFT (non-canonical types):")
        for a in r["areas"]:
            for d in a["drift"]:
                print(f"  {a['area']}: {d}")
    if args.gaps:
        print("\nGAPS (untyped knowledge candidates):")
        for a in r["areas"]:
            if a["gaps"]:
                print(f"\n  [{a['area']}] {a['gap_count']} untyped:")
                for g in a["gaps"]:
                    print(f"    {g}")
    print("━" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
