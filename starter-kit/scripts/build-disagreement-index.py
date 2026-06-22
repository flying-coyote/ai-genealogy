#!/usr/bin/env python3
"""build-disagreement-index.py — the DERIVED, queryable read-model of cross-platform
disagreements, computed by parsing per-person journal frontmatter (the single source of
truth). Like okf_signals.py: because it's derived, the moment a disagreement is resolved in
its journal the next run drops it — there is no index file to author, drift, or lie.

This REPLACES the retired build-disagreement-registry.py, which built a registry FROM the
gitignored fragment JSONs (a competing source of truth). Here the journals are authoritative
and this is a read-only projection.

Each journal's `disagreements[]` (schema/journal.schema.json) is flattened into ranked rows,
joined with the journal's own generation/lineage/confidence (set at reconcile time). Only
not-yet-settled items (open / researching / lead_found) show by default.

Usage (stdout-first; no file written):
  build-disagreement-index.py                       # ranked table (top 40) across all 3 trees
  build-disagreement-index.py --repo PATH           # one tree only
  build-disagreement-index.py --class IDENTITY      # filter by class (repeatable)
  build-disagreement-index.py --status open         # filter by status (repeatable; default: unsettled)
  build-disagreement-index.py --lineage direct      # direct | collateral | unknown
  build-disagreement-index.py --min-severity high   # high | med | low
  build-disagreement-index.py --top 100 | --by-class | --json | --counts
"""
from __future__ import annotations
import argparse, json, os, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "okf"))
from okf import GENEALOGY_ROOTS, load_notes  # noqa: E402

UNSETTLED = ("open", "researching", "lead_found")
SEV_RANK = {"high": 3, "med": 2, "low": 1}
CLS_WEIGHT = {"IDENTITY": 50, "CONFLATION": 45, "PARENTAGE": 30, "OVERCLAIM": 25,
              "VITAL": 20, "SOURCE": 8, "COVERAGE": 5}
REPO_OF = {"genealogy": "genealogy", "genealogy-dry-cross": "dry-cross",
           "genealogy-kindred": "kindred"}


def lineage_of(fm: dict) -> str:
    lp = fm.get("lineage_part")
    if lp not in (None, "?", "", "unknown"):
        return "direct"
    return "unknown"


def score(d: dict, fm: dict, lineage: str) -> int:
    s = 0
    if lineage == "direct":
        s += 100
    s += {"high": 40, "med": 20, "low": 5}.get(d.get("severity", "low"), 5)
    s += CLS_WEIGHT.get(d.get("cls"), 10)
    legs = [k for k, v in (d.get("values") or {}).items() if v not in (None, "")]
    s += 25 if len(legs) >= 3 else (10 if len(legs) == 2 else 0)
    if d.get("next_record"):
        s += 15
    g = fm.get("generation")
    if isinstance(g, int) and g <= 8:
        s += 10
    return s


def collect(roots):
    rows = []
    for note in load_notes(roots):
        if note.type != "ResearchJournal":
            continue
        fm = note.frontmatter or {}
        diss = fm.get("disagreements")
        if not diss:
            continue
        repo = REPO_OF.get(note.root.name, note.root.name)
        lineage = lineage_of(fm)
        for d in diss:
            if not isinstance(d, dict):
                continue
            rows.append({
                "repo": repo,
                "person_id": fm.get("gedcom_id"),
                "name": fm.get("person") or fm.get("canonical_name"),
                "generation": fm.get("generation"),
                "lineage": lineage,
                "cls": d.get("cls"),
                "field": d.get("field"),
                "status": d.get("status", "open"),
                "severity": d.get("severity", "med"),
                "values": d.get("values") or {},
                "next_record": d.get("next_record"),
                "priority": score(d, fm, lineage),
            })
    rows.sort(key=lambda r: -r["priority"])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Derived cross-platform disagreement index (from journals)")
    ap.add_argument("--repo", default=None, help="single tree root (default: all 3)")
    ap.add_argument("--class", dest="classes", action="append", default=[])
    ap.add_argument("--status", action="append", default=[])
    ap.add_argument("--lineage", default=None)
    ap.add_argument("--min-severity", default=None)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--by-class", action="store_true")
    ap.add_argument("--counts", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    roots = [Path(a.repo).resolve()] if a.repo else GENEALOGY_ROOTS
    rows = collect(roots)

    want_status = set(a.status) if a.status else set(UNSETTLED)
    rows = [r for r in rows if r["status"] in want_status]
    if a.classes:
        cl = {c.upper() for c in a.classes}
        rows = [r for r in rows if r["cls"] in cl]
    if a.lineage:
        rows = [r for r in rows if r["lineage"] == a.lineage]
    if a.min_severity:
        m = SEV_RANK.get(a.min_severity, 0)
        rows = [r for r in rows if SEV_RANK.get(r["severity"], 0) >= m]

    if a.json:
        print(json.dumps({"total": len(rows), "rows": rows}, indent=1, ensure_ascii=False, default=str))
        return 0
    if a.counts:
        print(json.dumps({
            "total": len(rows),
            "by_class": dict(Counter(r["cls"] for r in rows).most_common()),
            "by_status": dict(Counter(r["status"] for r in rows).most_common()),
            "by_severity": dict(Counter(r["severity"] for r in rows).most_common()),
            "by_lineage": dict(Counter(r["lineage"] for r in rows).most_common()),
            "by_repo": dict(Counter(r["repo"] for r in rows).most_common()),
        }, indent=1))
        return 0

    if a.by_class:
        print("━" * 88)
        print(f"🔀 disagreement index by class · {len(rows)} unsettled")
        print("━" * 88)
        by = {}
        for r in rows:
            by.setdefault(r["cls"], []).append(r)
        for cls in sorted(by, key=lambda c: -len(by[c])):
            grp = by[cls]
            print(f"\n{cls} ({len(grp)}):")
            for r in grp[:a.top]:
                print(f"  [{r['priority']:>3}] {r['repo']:<9} {(r['name'] or '?')[:26]:<26} {r['field']:<14} {r['status']:<11} {r['severity']}")
            if len(grp) > a.top:
                print(f"   … and {len(grp)-a.top} more")
        return 0

    print("━" * 96)
    print(f"🔀 cross-platform disagreement index · {len(rows)} unsettled (top {min(a.top, len(rows))})")
    print("━" * 96)
    print(f"  {'pri':>3}  {'repo':<9} {'class':<11} {'person':<26} {'field':<14} {'status':<11} sev  next")
    for r in rows[:a.top]:
        nr = (r["next_record"] or "")[:40]
        print(f"  {r['priority']:>3}  {r['repo']:<9} {r['cls']:<11} {(r['name'] or '?')[:26]:<26} {r['field']:<14} {r['status']:<11} {r['severity']:<4} {nr}")
    print("━" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())
