#!/usr/bin/env python3
"""reconcile-journal-frontmatter.py — one-time, lossless upgrade of every research journal
to frontmatter v2 (schema/journal.schema.json). Idempotent: re-running is a no-op on files
already at schema_version 2.

What it does per journal:
  * Normalizes the three trees' divergent frontmatter (genealogy minimal, dry-cross extended,
    kindred extended-or-NONE) into the v2 superset. Pre-v2 extra fields are KEPT verbatim.
  * Synthesizes frontmatter for kindred's no-frontmatter journals from the filename stem
    (the tree id) + the `# {name} ({pid})` body header — verified identity-safe.
  * Adds `platform_identity` sourced from tree.json (the authoritative conclusion), with
    verified:false; DROPS the stale scattered scalar id copies (fs_pid/wt_id/ancestry_id and
    kindred's familysearch/wikitree/findagrave/ancestry) so there is ONE id source, not two.
    (Confirmed: no tooling reads those journal fields; tree.json is the authority.)
  * Adds an empty `disagreements: []` + derived `status_summary` (P5 migration fills them).
  * Preserves the prose body byte-for-byte; asserts a parse round-trip fixpoint before writing.

Usage: reconcile-journal-frontmatter.py --repo PATH [--apply] [--limit N] [--report FILE]
Default is DRY-RUN (reports counts + a sample diff, writes nothing).
"""
from __future__ import annotations
import argparse, json, re, sys, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal_io as J

DROP = {"fs_pid", "wt_id", "ancestry_id", "familysearch", "wikitree", "findagrave",
        "ancestry", "geni", "person_id", "name"}
PLATS = ("familysearch", "wikitree", "ancestry", "findagrave", "geni")


def load_tree_index(root: Path):
    persons = json.loads((root / "data/tree.json").read_text()).get("persons", [])
    idx = {}
    for p in persons:
        idx[p["id"]] = p
        idx[p["id"].strip("@")] = p
    return idx


def resolve_pid(stem: str, fm: dict, idx: dict):
    for cand in (fm.get("gedcom_id"), fm.get("person_id"), stem, f"@{stem}@", f"@{stem.strip('@')}@"):
        if cand and cand in idx:
            return idx[cand]["id"], idx[cand]
    # not in tree (orphan journal); best-effort canonical id from the stem
    cid = stem if stem.startswith("@") else f"@{stem}@"
    return (fm.get("gedcom_id") or cid), None


def platform_identity_from_tree(person: dict, fm: dict) -> dict:
    pi = {}
    pl = (person or {}).get("platform_ids") or {}
    fs = pl.get("familysearch") or pl.get("fs_pid") or (fm.get("fs_pid") if not person else None)
    pairs = {"familysearch": fs, "wikitree": pl.get("wikitree") or (fm.get("wt_id") if not person else None),
             "ancestry": pl.get("ancestry") or (fm.get("ancestry_id") if not person else None),
             "findagrave": pl.get("findagrave"), "geni": pl.get("geni")}
    # kindred's own frontmatter form, only used when there's no tree person
    if not person:
        pairs["familysearch"] = pairs["familysearch"] or fm.get("familysearch")
        pairs["wikitree"] = pairs["wikitree"] or fm.get("wikitree")
        pairs["ancestry"] = pairs["ancestry"] or fm.get("ancestry")
        pairs["findagrave"] = pairs["findagrave"] or fm.get("findagrave")
    for k, v in pairs.items():
        if v:
            pi[k] = {"id": v, "verified": False}
    return pi


def body_header_name(body: str) -> str | None:
    m = re.search(r"^#\s+(?:Research Journal:\s*)?(.+?)\s*(?:\(@?[^)]*\))?\s*$", body, re.M)
    return m.group(1).strip() if m else None


def build_v2(stem: str, fm: dict, body: str, idx: dict):
    pid, person = resolve_pid(stem, fm, idx)
    name = (fm.get("person") or fm.get("canonical_name") or fm.get("name")
            or (person or {}).get("canonical_name") or body_header_name(body))
    out = {"type": "ResearchJournal", "schema_version": 2}
    if name:
        out["person"] = name
        out["canonical_name"] = (fm.get("canonical_name") or (person or {}).get("canonical_name") or name)
    out["gedcom_id"] = pid
    gen = fm.get("generation") if fm.get("generation") is not None else (person or {}).get("generation")
    if gen is not None:
        out["generation"] = gen
    for k in ("lineage_part", "lineage_branch", "confidence"):
        v = fm.get(k) if fm.get(k) is not None else (person or {}).get("validation", {}).get("confidence") if k == "confidence" else None
        if v is not None:
            out[k] = v
    out["status"] = fm.get("status") or "ACTIVE"
    pi = platform_identity_from_tree(person, fm)
    if pi:
        out["platform_identity"] = pi
    # keep every OTHER pre-v2 field except the dropped scalar-id aliases + things we set
    handled = set(out) | DROP | {"type", "schema_version"}
    for k, v in fm.items():
        if k in handled or k in ("disagreements", "status_summary"):
            continue
        out[k] = v
    out["disagreements"] = fm.get("disagreements") or []
    out["status_summary"] = J.recompute_status_summary(out["disagreements"])
    return J.jsonsafe(out), (person is not None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    idx = load_tree_index(root)
    jdir = root / "research" / "journals"
    files = sorted(jdir.glob("*.md"))
    if a.limit:
        files = files[: a.limit]

    n = {"total": len(files), "already_v2": 0, "normalized": 0, "no_frontmatter": 0,
         "orphan_no_tree": 0, "fixpoint_fail": 0}
    fails, orphans, sample = [], [], None
    for f in files:
        text = f.read_text(encoding="utf-8")
        fm, body = J.split_frontmatter(text)
        had_fm = bool(fm)
        if not had_fm:
            n["no_frontmatter"] += 1
        if fm.get("schema_version") == 2:
            n["already_v2"] += 1
            continue
        v2, in_tree = build_v2(f.stem, fm or {}, body, idx)
        if not in_tree:
            # orphan: not a per-person tree node (stale id, cluster note, geni-trial log,
            # junk stem). Do NOT impose the person schema — skip + report for human review.
            n["orphan_no_tree"] += 1
            orphans.append(f.stem)
            continue
        # round-trip fixpoint: re-parse what we'd write must equal the structure
        rendered = "---\n" + J._dump_frontmatter(v2) + "---\n" + body
        rfm, rbody = J.split_frontmatter(rendered)
        if rfm != v2 or rbody != body:
            n["fixpoint_fail"] += 1
            fails.append(f.stem)
            continue
        n["normalized"] += 1
        if sample is None and (not had_fm or in_tree):
            sample = {"file": f.name, "had_frontmatter": had_fm, "v2_frontmatter": v2}
        if a.apply:
            J.write(f, v2, body)

    out = {"repo": root.name, "mode": "apply" if a.apply else "dry-run", "counts": n,
           "fixpoint_failures": fails[:20], "orphan_sample": orphans[:20], "sample": sample}
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    if a.report:
        Path(a.report).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    main()
