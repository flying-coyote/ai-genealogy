"""journal_io.py — the ONE write path for per-person research journals (frontmatter v2).

The journal is the single source of truth for observed platform claims, classified
disagreements, and research status (see methodology/07-cross-platform-reconciliation.md +
schema/journal.schema.json). EVERY producer (recon walk, migration, brick-wall pipeline,
conformance) writes disagreements through `upsert_disagreement` here; nothing authors a
journal's structured layer directly. Read paths (the derived index) call `parse`.

Two policies are enforced here (user-confirmed):
  * Mechanical-only auto-close — a producer may move None->open and refresh values, and may
    auto-close ONLY a mechanical case (person_gone, or the tree value now equals the source
    value) with an audit-note trail entry. A judgment close (resolved/held/disproven on a
    LIVE conflict) is human / gated-apply via `set_status`, and a producer can never
    overwrite a human-set status.
  * The confidence cap (an open high-severity disagreement caps tree confidence) is enforced
    downstream by the conformance gate (JOUR-1) reading status_summary — not here.

LOCAL-ONLY: stdlib + PyYAML, no network. Symlinked into each repo's scripts/; resolves its
own real path so the okf reader import works regardless of which repo the symlink lives in.
"""
from __future__ import annotations

import os
import sys
import datetime
from pathlib import Path

import yaml

# Reuse the hub's frontmatter splitter (single definition); fall back if unreachable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "okf"))
try:
    from okf import split_frontmatter as _okf_split  # type: ignore
except Exception:  # pragma: no cover
    _okf_split = None

import re
_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# ---------------------------------------------------------------- lifecycle DAG
# open -> researching -> lead_found -> contributed -> resolved | held | disproven
LIFECYCLE: dict[str, set[str]] = {
    "open":        {"researching", "lead_found", "contributed", "resolved", "held", "disproven"},
    "researching": {"lead_found", "contributed", "resolved", "held", "disproven", "open"},
    "lead_found":  {"contributed", "resolved", "held", "disproven", "researching"},
    "contributed": {"resolved", "held", "disproven"},
    "resolved":    set(),
    "held":        {"open", "researching", "resolved", "disproven"},
    "disproven":   set(),
}
ALL_STATUSES = set(LIFECYCLE)
# A producer must never overwrite any of these — they reflect human / judgment decisions.
HUMAN_OWNED = {"researching", "lead_found", "contributed", "held", "disproven", "resolved"}
SEV_RANK = {"high": 3, "med": 2, "low": 1}


# ---------------------------------------------------------------- path resolver
def journal_path(root, pid: str, must_exist: bool = False) -> Path | None:
    """Resolve the journal file for a tree id, absorbing the @I123@.md vs I123.md hazard.

    On-disk journals use the raw @-form (@I123@.md); some writers historically computed the
    @-stripped form (I123.md). We probe both and (when creating) prefer the @-form."""
    jdir = Path(root) / "research" / "journals"
    raw = pid
    stripped = pid.strip("@")
    cands = [jdir / f"{raw}.md", jdir / f"{stripped}.md"]
    for c in cands:
        if c.exists():
            return c
    if must_exist:
        return None
    return cands[0]  # canonical @-form for new files


# ---------------------------------------------------------------- parse / write
def split_frontmatter(text: str) -> tuple[dict, str]:
    if _okf_split is not None:
        return _okf_split(text)
    m = _FM.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        fm = None
    return (fm if isinstance(fm, dict) else {}), text[m.end():]


def parse(path) -> dict:
    """Return {path, exists, frontmatter, body, disagreements, status_summary}."""
    p = Path(path)
    if not p.exists():
        return {"path": p, "exists": False, "frontmatter": {}, "body": "",
                "disagreements": [], "status_summary": {}}
    text = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    fm = fm or {}
    return {"path": p, "exists": True, "frontmatter": fm, "body": body,
            "disagreements": fm.get("disagreements") or [],
            "status_summary": fm.get("status_summary") or {}}


def _dump_frontmatter(fm: dict) -> str:
    return yaml.safe_dump(fm, sort_keys=False, default_flow_style=False,
                          allow_unicode=True, width=1000)


def write(path, frontmatter: dict, body: str) -> None:
    """Atomically re-emit `---\\n{yaml}---\\n{body}`. Body is preserved verbatim."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    out = "---\n" + _dump_frontmatter(frontmatter) + "---\n" + body
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(out)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


# ---------------------------------------------------------------- status summary
def recompute_status_summary(disagreements: list[dict]) -> dict:
    counts = {k: 0 for k in ("open", "researching", "lead_found", "contributed",
                             "resolved", "held", "disproven")}
    high_open = 0
    worst = None
    for d in disagreements:
        st = d.get("status", "open")
        if st in counts:
            counts[st] += 1
        if st in ("open", "researching", "lead_found"):  # not-yet-settled
            sev = d.get("severity", "low")
            if sev == "high":
                high_open += 1
            if worst is None or SEV_RANK.get(sev, 0) > SEV_RANK.get(worst, 0):
                worst = sev
    counts["high_open"] = high_open
    counts["worst_open_severity"] = worst
    return counts


# ---------------------------------------------------------------- frontmatter scaffolding
_FM_ORDER = ["type", "schema_version", "person", "canonical_name", "gedcom_id",
             "generation", "lineage_part", "lineage_branch", "confidence", "status",
             "platform_identity"]


def _ensure_v2(fm: dict, pid: str) -> dict:
    fm.setdefault("type", "ResearchJournal")
    fm["schema_version"] = 2
    fm.setdefault("gedcom_id", pid)
    fm.setdefault("status", fm.get("status", "ACTIVE"))
    fm.setdefault("disagreements", fm.get("disagreements") or [])
    # stable-ish ordering: known scalars first, then extras, disagreements + summary last
    ordered = {}
    for k in _FM_ORDER:
        if k in fm:
            ordered[k] = fm[k]
    for k, v in fm.items():
        if k in ordered or k in ("disagreements", "status_summary"):
            continue
        ordered[k] = v
    ordered["disagreements"] = fm["disagreements"]
    ordered["status_summary"] = fm.get("status_summary") or {}
    return ordered


def _find(disagreements: list[dict], cls: str, field: str):
    for i, d in enumerate(disagreements):
        if d.get("cls") == cls and d.get("field") == field:
            return i
    return None


def _today() -> str:
    return os.environ.get("JOURNAL_IO_TODAY") or datetime.date.today().isoformat()


# ---------------------------------------------------------------- the write API
def upsert_disagreement(root, pid: str, record: dict, by: str, today: str | None = None) -> dict:
    """Idempotently upsert one disagreement (keyed by cls+field) into a person's journal.

    record: {cls, field, values{...}, severity, verdict?, next_record?, status?, auto_close?}
      - status defaults to 'open' for a new record; a producer should NOT pass a human-owned
        status. auto_close in {'person_gone','value_matched'} mechanically resolves an OPEN
        record with an audit note.
    Returns {action: created|updated|protected|auto_closed|noop, journal: path}.
    """
    today = today or _today()
    path = journal_path(root, pid)
    st = parse(path)
    fm = _ensure_v2(dict(st["frontmatter"]), pid) if st["exists"] else _ensure_v2(
        {"type": "ResearchJournal", "person": record.get("person_name"),
         "gedcom_id": pid, "status": "ACTIVE"}, pid)
    diss = list(fm["disagreements"])
    body = st["body"] if st["exists"] else f"\n# Research Journal: {record.get('person_name') or pid}\n"

    cls, field = record["cls"], record["field"]
    idx = _find(diss, cls, field)
    action = "noop"

    def trail_entry(note):
        return {"date": today, "by": by, "note": note}

    if idx is None:
        rec = {
            "cls": cls, "field": field,
            "values": record.get("values") or {},
            "status": record.get("status", "open"),
            "severity": record.get("severity", "med"),
            "verdict": record.get("verdict"),
            "next_record": record.get("next_record"),
            "first_seen": today, "last_checked": today,
            "trail": [trail_entry(record.get("note") or f"opened by {by}")],
        }
        if record.get("status") in HUMAN_OWNED:  # producers may not open-as-closed
            rec["status"] = "open"
        if record.get("auto_close"):
            rec["status"] = "resolved"
            rec["trail"].append(trail_entry(f"auto-closed (mechanical): {record['auto_close']}"))
        diss.append(rec)
        action = "auto_closed" if record.get("auto_close") else "created"
    else:
        rec = diss[idx]
        changed = False
        new_vals = record.get("values")
        if new_vals and new_vals != rec.get("values"):
            rec["values"] = new_vals
            changed = True
        for k in ("severity", "verdict", "next_record"):
            if record.get(k) is not None and record.get(k) != rec.get(k):
                rec[k] = record[k]
                changed = True
        rec["last_checked"] = today
        if rec.get("status") in HUMAN_OWNED:
            # protected: refresh values only, never touch status; trail only if changed
            if changed:
                rec.setdefault("trail", []).append(trail_entry(f"values refreshed by {by} (status protected)"))
            action = "protected"
        elif record.get("auto_close"):
            rec["status"] = "resolved"
            rec.setdefault("trail", []).append(trail_entry(f"auto-closed (mechanical): {record['auto_close']}"))
            action = "auto_closed"
        elif changed:
            rec.setdefault("trail", []).append(trail_entry(f"updated by {by}"))
            action = "updated"

    fm["disagreements"] = diss
    fm["status_summary"] = recompute_status_summary(diss)
    write(path, fm, body)
    return {"action": action, "journal": str(path)}


def set_status(root, pid: str, cls: str, field: str, new_status: str, by: str,
               note: str = "", today: str | None = None) -> dict:
    """Human / gated-apply status transition (validates the lifecycle DAG)."""
    if new_status not in ALL_STATUSES:
        raise ValueError(f"unknown status {new_status!r}")
    today = today or _today()
    path = journal_path(root, pid, must_exist=True)
    if path is None:
        raise FileNotFoundError(f"no journal for {pid}")
    st = parse(path)
    fm = _ensure_v2(dict(st["frontmatter"]), pid)
    diss = list(fm["disagreements"])
    idx = _find(diss, cls, field)
    if idx is None:
        raise KeyError(f"no disagreement {cls}/{field} on {pid}")
    cur = diss[idx].get("status", "open")
    if new_status != cur and new_status not in LIFECYCLE.get(cur, set()):
        raise ValueError(f"illegal transition {cur} -> {new_status} for {pid} {cls}/{field}")
    diss[idx]["status"] = new_status
    diss[idx]["last_checked"] = today
    diss[idx].setdefault("trail", []).append(
        {"date": today, "by": by, "note": note or f"status {cur} -> {new_status}"})
    fm["disagreements"] = diss
    fm["status_summary"] = recompute_status_summary(diss)
    write(path, fm, st["body"])
    return {"action": "status_set", "from": cur, "to": new_status, "journal": str(path)}
