#!/usr/bin/env python3
"""OKF-derived next-work signals for the genealogy graph — the maturation queue, COMPUTED.

Replaces a hand-kept maturation_queue.json. Reads the typed-markdown graph (journals,
brick walls) AND each tree's tree.json (structured authority), and derives a ranked list of
next-work candidates from the structure already there. Because it's derived, the moment you
act on an item the next run drops it — no queue to update, no way for the queue to lie.

Signal classes:
  stale-journal             ResearchJournal, status ACTIVE, last_session older than N days
  open-brickwall            BrickWall whose status is still open/EXHAUSTED_ONLINE
  missing-parent            tree.json person, >=1 null parent, FS-queryable, not yet worked
  possible-no-upgrade-path  tree.json POSSIBLE with no validation.upgrade_path (stalled)
  confidence-violation      tree.json PROBABLE/VERIFIED whose best source tier is weak (surface, don't recompute)

Local-file only. tree.json is read directly (structured authority) — never as markdown.

Usage:
  python3 scripts/okf_signals.py                 # ranked table (top 25)
  python3 scripts/okf_signals.py --top 60
  python3 scripts/okf_signals.py --by-class
  python3 scripts/okf_signals.py --brief
  python3 scripts/okf_signals.py --json          # full derived queue + bridge diagnostics
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
_BASE = Path(os.environ.get("GENEALOGY_HOME", str(Path.home())))

sys.path.insert(0, str(Path(__file__).resolve().parent))
from okf import GENEALOGY_ROOTS, load_notes, split_frontmatter  # noqa: E402

TODAY = datetime.date.today()

# Per-tree structured authority (id-space differs per tree; the bridge measures itself).
TREES = {
    "genealogy": Path(str(_BASE / "genealogy")),
    "dry-cross": Path(str(_BASE / "genealogy-dry-cross")),
    "kindred": Path(str(_BASE / "genealogy-kindred")),
}

# Conservative tunables — a short, real list, not the whole backlog.
JOURNAL_STALE_DAYS = 120
QUERYABLE_MAX_GEN = 14         # closer-in band where online records exist
WEAK_TIER = 4                  # source tiers >= this are "weak" (1=best .. 5=tree-only)
WORKED_STATUSES = {"EXHAUSTED_ONLINE", "BRICK_WALL", "RESEARCHED", "DISPROVEN"}


@dataclass
class Signal:
    cls: str
    id: str
    score: int
    action: str
    rel: str
    meta: dict = field(default_factory=dict)


def as_date(v):
    if v is None:
        return None
    if isinstance(v, (datetime.datetime,)):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    if m:
        try:
            return datetime.date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            return None
    return None


def tier_int(v):
    """Leading digit of a tier ('2a' -> 2, 5 -> 5, '5' -> 5)."""
    m = re.match(r"\s*(\d)", str(v))
    return int(m.group(1)) if m else None


def _short(s, n=88):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


# --- frontmatter signals ---------------------------------------------------------

def stale_journals(notes):
    out = []
    for n in notes:
        if n.type != "ResearchJournal":
            continue
        fm = n.frontmatter
        if str(fm.get("status", "")).upper() != "ACTIVE":
            continue
        last = as_date(fm.get("last_session"))
        if not last:
            continue
        age = (TODAY - last).days
        if age < JOURNAL_STALE_DAYS:
            continue
        out.append(Signal(
            "stale-journal", str(fm.get("gedcom_id") or n.rel),
            20 + min(age // 30, 12),
            f"Revisit {fm.get('person', '?')} — ACTIVE, stale {age}d",
            n.rel, {"last_session": str(last), "age_days": age}))
    return out


def open_brickwalls(notes):
    out = []
    for n in notes:
        if n.type != "BrickWall":
            continue
        st = str(n.frontmatter.get("status", "")).upper()
        if st in {"RESOLVED", "CLOSED", "DISPROVEN"}:
            continue
        score = 50 if "EXHAUSTED" not in st else 30  # un-exhausted = more online room
        out.append(Signal(
            "open-brickwall", n.rel, score,
            f"Brick wall open ({st or '?'}): {_short(n.frontmatter.get('title') or Path(n.rel).stem, 70)}",
            n.rel, {"status": st}))
    return out


# --- tree.json (structured authority) signals ------------------------------------

def _persons(tree_root):
    p = tree_root / "data" / "tree.json"
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("persons", [])


def _ged(p):
    return (p.get("platform_ids") or {}).get("gedcom") or p.get("id")


def missing_parents(tree, persons):
    out = []
    for p in persons:
        gen = p.get("generation")
        if not isinstance(gen, int) or gen > QUERYABLE_MAX_GEN:
            continue
        if p.get("father_id") and p.get("mother_id"):
            continue
        rsc = str(p.get("research_status_canonical") or p.get("research_status") or "").upper()
        if rsc in WORKED_STATUSES:
            continue
        if not (p.get("platform_ids") or {}).get("familysearch"):
            continue  # need a queryable handle
        miss = "both" if not p.get("father_id") and not p.get("mother_id") else \
               ("father" if not p.get("father_id") else "mother")
        out.append(Signal(
            "missing-parent", _ged(p), max(40 - gen, 6),
            f"[{tree}] gen{gen} {p.get('canonical_name', '?')} — missing {miss}",
            f"{tree}:tree.json", {"tree": tree, "generation": gen, "missing": miss}))
    return out


def possible_no_upgrade(tree, persons):
    out = []
    for p in persons:
        v = p.get("validation", {})
        if v.get("confidence") == "POSSIBLE" and not v.get("upgrade_path"):
            out.append(Signal(
                "possible-no-upgrade-path", _ged(p), 45,
                f"[{tree}] POSSIBLE, no upgrade_path: {p.get('canonical_name', '?')} (gen {p.get('generation', '?')})",
                f"{tree}:tree.json", {"tree": tree, "generation": p.get("generation")}))
    return out


def confidence_violations(tree, persons):
    """Surface PROBABLE/VERIFIED resting on weak sources. Surface, don't recompute —
    cross-check against recalculate-confidence.py / conformance CONF-3."""
    out = []
    for p in persons:
        v = p.get("validation", {})
        conf = v.get("confidence")
        if conf not in ("PROBABLE", "VERIFIED"):
            continue
        srcs = (v.get("evidence") or {}).get("sources") or []
        tiers = [t for t in (tier_int(s.get("tier")) for s in srcs) if t is not None]
        if tiers and min(tiers) >= WEAK_TIER:
            out.append(Signal(
                "confidence-violation", _ged(p), 60 + (min(tiers) - WEAK_TIER) * 5,
                f"[{tree}] {conf} but best source tier {min(tiers)}: {p.get('canonical_name', '?')}",
                f"{tree}:tree.json", {"tree": tree, "confidence": conf, "best_tier": min(tiers)}))
    return out


# --- bridge diagnostic (measure before you trust) --------------------------------

def bridge_join_rate(tree_root):
    persons = _persons(tree_root)
    pid = {p.get("id") for p in persons}
    ged = {(p.get("platform_ids") or {}).get("gedcom") for p in persons}
    jdir = tree_root / "research" / "journals"
    stems = [f.stem for f in jdir.glob("*.md")] if jdir.exists() else []

    def variants(s):
        return {s, f"@{s}@", s.strip("@")}

    by_id = sum(1 for s in stems if variants(s) & pid)
    by_ged = sum(1 for s in stems if variants(s) & ged)
    return {"journals": len(stems), "match_person_id": by_id, "match_gedcom": by_ged,
            "best_join_pct": round(100 * max(by_id, by_ged) / len(stems), 1) if stems else None}


# --- collect / present -----------------------------------------------------------

def collect():
    notes = load_notes(GENEALOGY_ROOTS)
    sigs = stale_journals(notes) + open_brickwalls(notes)
    for tree, root in TREES.items():
        persons = _persons(root)
        sigs += missing_parents(tree, persons)
        sigs += possible_no_upgrade(tree, persons)
        sigs += confidence_violations(tree, persons)
    sigs.sort(key=lambda s: (-s.score, s.cls, s.id))
    return sigs


def one_line(sigs):
    by = Counter(s.cls for s in sigs)
    top = sigs[0].action if sigs else "nothing flagged"
    parts = [f"{by.get(c, 0)} {c}" for c in
             ("missing-parent", "possible-no-upgrade-path", "confidence-violation",
              "open-brickwall", "stale-journal")]
    flag = "✅" if not sigs else "🧭"
    return f"{flag} maturation signals: " + " · ".join(parts) + f" — top: {_short(top, 80)}"


def main() -> int:
    ap = argparse.ArgumentParser(description="OKF-derived genealogy maturation signals")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--by-class", action="store_true")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sigs = collect()
    if args.brief:
        print(one_line(sigs)); return 0
    if args.json:
        print(json.dumps({
            "generated": TODAY.isoformat(),
            "summary": one_line(sigs),
            "count": len(sigs),
            "by_class": dict(Counter(s.cls for s in sigs)),
            "bridge": {t: bridge_join_rate(r) for t, r in TREES.items()},
            "signals": [asdict(s) for s in sigs],
        }, indent=2)); return 0

    if args.by_class:
        print("━" * 78)
        print(f"🧭 maturation signals by class · {TODAY.isoformat()}")
        print("━" * 78)
        for cls in ("missing-parent", "possible-no-upgrade-path", "confidence-violation",
                    "open-brickwall", "stale-journal"):
            grp = [s for s in sigs if s.cls == cls]
            print(f"\n{cls} ({len(grp)}):")
            for s in grp[:args.top]:
                print(f"  [{s.score:>3}] {_short(s.action)}")
            if len(grp) > args.top:
                print(f"   … and {len(grp) - args.top} more (--json for all)")
        print("━" * 78)
        return 0

    print("━" * 78)
    print("🧭 OKF-derived maturation queue (genealogy, all 3 trees + hub)")
    print(f"   {TODAY.isoformat()} · {len(sigs)} candidates")
    print("━" * 78)
    print(one_line(sigs))
    print()
    print(f"{'#':>2} {'score':>5}  {'class':24} action")
    for i, s in enumerate(sigs[:args.top], 1):
        print(f"{i:>2} {s.score:>5}  {s.cls:24} {_short(s.action)}")
    if len(sigs) > args.top:
        print(f"   … and {len(sigs) - args.top} more (--top {len(sigs)} or --json)")
    print("━" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
