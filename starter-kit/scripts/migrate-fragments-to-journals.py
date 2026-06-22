#!/usr/bin/env python3
"""migrate-fragments-to-journals.py — one-time, idempotent migration of the scattered
disagreement fragments (gitignored data/reports/*.json) + the live conformance checker INTO
the per-person journals, via journal_io.upsert_disagreement(by="migration"). After this the
journals hold the accumulated disagreement history and the fragments are disposable scratch.

Reads each fragment through a small ADAPTER (the readers that used to live in the retired
build-disagreement-registry.py), resolves every key to the canonical tree id, freshness-checks
each value against the CURRENT tree.json, and upserts. Mechanical freshness drives auto-close:
  * person no longer in tree            -> auto_close=person_gone
  * the tree value now equals the source -> auto_close=value_matched  (conflict is gone)
  * the tree value changed since capture -> still upsert open, note the change in the trail
Unresolvable keys are written to data/reports/migration_unresolved.json (never silently dropped).

Idempotent: re-running upserts the same (cls,field) records -> journal_io dedups, no growth,
and never overwrites a human-set status.

Usage: migrate-fragments-to-journals.py --repo PATH [--apply] [--gen-max N] [--limit N]
Default DRY-RUN: reports what would be upserted (counts per class/action) + a sample, writes nothing.
"""
from __future__ import annotations
import argparse, glob, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal_io as J

VITAL_FIELDS = {"birth_date", "birth_place", "death_date", "death_place"}
SEV = {"IDENTITY": "high", "CONFLATION": "high", "OVERCLAIM": "high",
       "PARENTAGE": "med", "VITAL": "med", "SOURCE": "low", "COVERAGE": "low"}


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def load_tree(root: Path):
    persons = json.loads((root / "data/tree.json").read_text()).get("persons", [])
    by_id, by_fs = {}, {}
    for p in persons:
        by_id[p["id"]] = p
        by_id[p["id"].strip("@")] = p
        pl = p.get("platform_ids") or {}
        fs = pl.get("familysearch") or pl.get("fs_pid") or p.get("fs_pid")
        if fs:
            by_fs[fs] = p
    return by_id, by_fs


def tree_value(person: dict, field: str):
    if field in VITAL_FIELDS:
        grp, sub = field.split("_")
        return (person.get(grp) or {}).get(sub)
    if field == "father":
        return person.get("father_id")
    if field == "mother":
        return person.get("mother_id")
    return None


def reports(root: Path):
    return root / "data" / "reports"


# ---------------------------------------------------------------- adapters (readers)
# each yields raw records: {pid_key, key_is_fs, cls, field, tree, fs, severity?, verdict?, next_record?, note?}
def a_recon_bulk(root):
    f = reports(root) / "recon_bulk_conflicts.json"
    if not f.exists():
        return
    for x in json.loads(f.read_text()):
        if not x.get("id") or not x.get("field"):
            continue
        cls = "VITAL" if x.get("kind") == "vital" else "PARENTAGE"
        yield {"pid": x["id"], "cls": cls, "field": x["field"], "tree": x.get("tree"),
               "fs": x.get("fs"), "verdict": "conflict", "src": "recon_bulk"}


def a_conflicts_to_judge(root):
    f = reports(root) / "conflicts_to_judge.json"
    if not f.exists():
        return
    for x in json.loads(f.read_text()):
        if not x.get("id"):
            continue
        if x.get("conflation_suspect"):
            yield {"pid": x["id"], "cls": "CONFLATION", "field": "identity", "tree": None, "fs": None,
                   "verdict": "conflation_suspect", "src": "conflicts_to_judge",
                   "note": f"{x.get('divergent_vital_count')} divergent vitals across platforms"}
        for c in x.get("conflicts", []):
            fld = c.get("field")
            if not fld:
                continue
            cls = "VITAL" if fld in VITAL_FIELDS else "PARENTAGE"
            yield {"pid": x["id"], "cls": cls, "field": fld, "tree": c.get("tree"),
                   "fs": c.get("fs"), "verdict": "conflict", "src": "conflicts_to_judge"}


def a_fs_date_conflicts(root):
    f = reports(root) / "fs_date_conflicts_manual_review.json"
    if not f.exists():
        return
    blob = json.loads(f.read_text())
    for x in (blob.get("conflicts", []) if isinstance(blob, dict) else blob):
        if not x.get("fs_pid"):
            continue
        yield {"fs_pid": x["fs_pid"], "cls": "VITAL", "field": "date_conflict",
               "tree": x.get("local_value"), "fs": x.get("fs_value"),
               "verdict": "conflict", "src": "fs_date_conflicts"}


def a_brickwall(root):
    f = reports(root) / "fs_brickwall_judged.json"
    if not f.exists():
        return
    blob = json.loads(f.read_text())
    for bucket, sev in (("high", "med"), ("med", "low")):
        for x in (blob.get(bucket) or []) if isinstance(blob, dict) else []:
            if not isinstance(x, dict) or not x.get("node_id"):
                continue
            yield {"pid": x["node_id"], "cls": "PARENTAGE", "field": x.get("slot", "parent"),
                   "tree": None, "fs": x.get("fs_parent_name"), "verdict": "brick_lead",
                   "severity": sev, "next_record": x.get("next_record"), "src": "fs_brickwall",
                   "note": f"FS proposes {x.get('fs_parent_name')} ({x.get('fs_parent_id')}); src_count={x.get('source_count')}"}


def a_conformance(root):
    import importlib.util
    spec = importlib.util.spec_from_file_location("conf", root / "scripts/conformance-report.py")
    conf = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(conf)
    except Exception:
        return
    persons = json.loads((root / "data/tree.json").read_text())["persons"]
    viol = conf.run_checks(persons)
    CLS = {"CONF-1": "OVERCLAIM", "CONF-2": "OVERCLAIM", "CONF-3": "OVERCLAIM",
           "SRC-1": "SOURCE", "DUR-1": "SOURCE", "COV-1": "COVERAGE",
           "DOC-1": "COVERAGE", "UPG-1": "COVERAGE", "GEN-1": "COVERAGE"}
    for chk, ids in viol.items():
        for pid in ids:
            yield {"pid": pid, "cls": CLS.get(chk, "COVERAGE"), "field": chk, "tree": None, "fs": None,
                   "verdict": "conformance", "severity": "high" if conf.SEVERITY.get(chk) == "ERROR" else "low",
                   "src": "conformance"}


# NOTE: a_conformance is deliberately NOT migrated. OVERCLAIM/SOURCE/COVERAGE are PROCESS
# checks computed live by conformance-report.py (itself a derived read-model) + gated in
# pre-commit; storing them as journal disagreements would duplicate a derived signal and
# create a write loop. Journals hold the cross-platform OBSERVED-CLAIM conflicts only.
ADAPTERS = [a_recon_bulk, a_conflicts_to_judge, a_fs_date_conflicts, a_brickwall]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--gen-max", type=int, default=None, help="only persons with generation <= N")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    by_id, by_fs = load_tree(root)

    actions = Counter()
    cls_counts = Counter()
    unresolved = []
    samples = []
    seen = 0

    for adapter in ADAPTERS:
        for rec in adapter(root) or []:
            # resolve to a tree person
            person = None
            if rec.get("pid"):
                person = by_id.get(rec["pid"]) or by_id.get(str(rec["pid"]).strip("@"))
            elif rec.get("fs_pid"):
                person = by_fs.get(rec["fs_pid"])
            if person is None:
                unresolved.append({"src": rec.get("src"), "key": rec.get("pid") or rec.get("fs_pid"),
                                   "cls": rec.get("cls"), "field": rec.get("field")})
                continue
            if a.gen_max is not None:
                g = person.get("generation")
                if not isinstance(g, int) or g > a.gen_max:
                    continue
            pid = person["id"]

            # freshness vs current tree
            field = rec["field"]
            auto_close = None
            note = rec.get("note")
            if field in VITAL_FIELDS or field in ("father", "mother"):
                cur = tree_value(person, field)
                if cur is not None and rec.get("fs") is not None and norm(cur) == norm(rec["fs"]):
                    auto_close = "value_matched"
                elif rec.get("tree") is not None and cur is not None and norm(cur) != norm(rec["tree"]):
                    note = (note + " | " if note else "") + f"tree value changed since capture ({rec['tree']!r}->{cur!r})"

            values = {"tree": rec.get("tree"), "familysearch": rec.get("fs"),
                      "ancestry": None, "wikitree": None}
            record = {"cls": rec["cls"], "field": field, "values": values,
                      "severity": rec.get("severity") or SEV.get(rec["cls"], "med"),
                      "verdict": rec.get("verdict"), "next_record": rec.get("next_record"),
                      "note": note, "auto_close": auto_close,
                      "person_name": person.get("canonical_name")}
            seen += 1
            cls_counts[rec["cls"]] += 1
            if a.limit and seen > a.limit:
                break
            if a.apply:
                res = J.upsert_disagreement(root, pid, record, by="migration")
                actions[res["action"]] += 1
            else:
                actions["would_upsert"] += 1
                if len(samples) < 6:
                    samples.append({"pid": pid, "name": person.get("canonical_name"),
                                    "cls": rec["cls"], "field": field, "values": values,
                                    "auto_close": auto_close, "src": rec.get("src")})

    if a.apply and unresolved:
        (reports(root)).mkdir(parents=True, exist_ok=True)
        (reports(root) / "migration_unresolved.json").write_text(
            json.dumps(unresolved, indent=1, ensure_ascii=False) + "\n")

    out = {"repo": root.name, "mode": "apply" if a.apply else "dry-run",
           "gen_max": a.gen_max, "records_seen": seen,
           "by_class": dict(cls_counts.most_common()), "actions": dict(actions),
           "unresolved": len(unresolved), "unresolved_sample": unresolved[:8],
           "sample": samples}
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
