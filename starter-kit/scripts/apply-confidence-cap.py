#!/usr/bin/env python3
"""apply-confidence-cap.py — the mechanical resolution of JOUR-1 (the consistency cap).

User-confirmed policy: an OPEN high-severity disagreement in a person's journal caps that
person's tree confidence — a VERIFIED/PROBABLE conclusion can't stand over an unresolved
high-severity conflict, so confidence is lowered to POSSIBLE with an audit note. This is a
MECHANICAL ceiling (same class as the overclaim corrections already applied), NOT a
resolution of the conflict — the conflict's actual resolution (re-point a parent, pick a
vital, confirm an identity) stays human. Once the human resolves/holds the disagreement in
the journal, JOUR-1 clears on its own.

Reads each person's journal (journal_io) for open high-severity disagreements; for every
VERIFIED/PROBABLE person with >=1, sets validation.confidence -> POSSIBLE and records a dated
validation.concern naming the capping disagreement(s). Writes tree.json + a contribution_log
entry (the commit-dance is left to the caller).

Usage: apply-confidence-cap.py --repo PATH [--apply]   (default DRY-RUN)
"""
from __future__ import annotations
import argparse, json, os, sys, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal_io as J

CONCLUDED = ("VERIFIED", "PROBABLE")


def open_high(diss):
    return [d for d in diss if d.get("status") in ("open", "researching", "lead_found")
            and d.get("severity") == "high"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    today = os.environ.get("JOURNAL_IO_TODAY") or datetime.date.today().isoformat()
    tree = json.loads((root / "data/tree.json").read_text())

    capped = []
    for p in tree["persons"]:
        v = p.get("validation") or {}
        if v.get("confidence") not in CONCLUDED:
            continue
        st = J.parse(J.journal_path(root, p["id"]))
        oh = open_high(st["disagreements"])
        if not oh:
            continue
        why = "; ".join(f"{d.get('cls')}/{d.get('field')}" for d in oh[:4])
        old = v["confidence"]
        capped.append({"id": p["id"], "name": p.get("canonical_name"), "from": old, "why": why})
        if a.apply:
            v["confidence"] = "POSSIBLE"
            v.setdefault("concerns", []).append({
                "date": today, "type": "confidence_cap",
                "concern": f"Confidence capped {old}->POSSIBLE: open high-severity disagreement(s) "
                           f"[{why}] in the journal (JOUR-1). Mechanical ceiling; resolve the "
                           f"disagreement to lift. See research/journals/{p['id'].strip('@')}.md."})
            p["validation"] = v

    print(json.dumps({"repo": root.name, "mode": "apply" if a.apply else "dry-run",
                      "capped": len(capped), "sample": capped[:12]}, indent=1, ensure_ascii=False))

    if a.apply and capped:
        tmp = root / "data/tree.json.tmp"
        with tmp.open("w") as f:
            json.dump(tree, f, indent=2, ensure_ascii=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, root / "data/tree.json")
        clp = root / "data/contribution_log.json"
        cl = json.loads(clp.read_text())
        cl["contributions"].append({
            "id": f"confidence-cap-{root.name}-{today}", "session_id": f"{today}_consistency_gate",
            "person_id": "BATCH", "person_name": f"Confidence cap (JOUR-1): {len(capped)} nodes -> POSSIBLE",
            "correction_type": "confidence_cap", "platform": "internal",
            "profile_id": f"BATCH-confidence-cap-{today}", "date": today,
            "details": ("Mechanical confidence cap (consistency gate JOUR-1): lowered VERIFIED/PROBABLE "
                        "nodes carrying an open high-severity journal disagreement to POSSIBLE with a dated "
                        "concern. Resolution of the disagreement stays human. Nodes: "
                        + " | ".join(f"{c['name']} {c['id']} {c['from']}->POSSIBLE [{c['why']}]" for c in capped))})
        cl.setdefault("metadata", {})
        if "total_contributions" in cl["metadata"]:
            cl["metadata"]["total_contributions"] = len(cl["contributions"])
        clp.write_text(json.dumps(cl, indent=1, ensure_ascii=False) + "\n")
        print(f"applied: {len(capped)} capped; contribution_log updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
