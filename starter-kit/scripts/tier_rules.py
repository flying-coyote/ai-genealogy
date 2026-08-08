#!/usr/bin/env python3
"""Shared tier and confidence rules for validate-tree.py.

The three project validators are forks — genealogy's is 597 lines, dry-cross's 389,
kindred's 331 — and two of them contained no tier logic whatsoever, so a tree lead
stored at tier 1 was not merely invisible there, it was affirmatively counted as the
evidence satisfying the VERIFIED check. This module holds the one implementation all
three import, on the same reasoning that made conformance-report.py a symlink: the
copied checkers drifted, so the rule lives in one file.

Canonical standard: methodology/02-evidence-standards.md, §Source Tier Hierarchy and
§Confidence Rules. This module must agree with conformance-report.py; where the two
disagree, conformance-report.py is the gate and wins.

Usage in a fork:

    import tier_rules
    result = tier_rules.evaluate(person)
    errors.extend(result["errors"])
    warnings.extend(result["warnings"])
"""

import re

# Mirrors conformance-report.py.
VERIFIED_MIN_TIER2_SOURCES = 2
CONCLUDED = ("VERIFIED", "PROBABLE")

# Tier 4 is family documents and undocumented lineage compilations; Tier 5 is member
# trees. Neither supports a concluded label.
LEAD_TIER_FLOOR = 4


def _asdict(x):
    return x if isinstance(x, dict) else {}


def _aslist(x):
    return x if isinstance(x, list) else []


def _asstr(x):
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return " ".join(str(i) for i in x)
    return str(x) if x else ""


def tier_major(source):
    """Leading digit of the tier field, or None.

    Handles int, the documented-but-unwritable '2a'/'2b', 'T3', and the junk the trees
    actually contain — dry-cross stores the literal strings 'record' and 'church_record'
    in the tier field, and kindred writes tier 0 deliberately for audit pointers.
    """
    t = source.get("tier")
    if isinstance(t, bool):
        return None
    if isinstance(t, int):
        return t if 1 <= t <= 5 else None
    m = re.search(r"[1-5]", _asstr(t))
    return int(m.group()) if m else None


def source_identity(source):
    """Key two source objects share when they describe the same source.

    The standard requires >=2 *independent* sources for VERIFIED, and the trees hold
    literal duplicates — one genealogy parent side carries 71 identical copies of a
    single tree assertion — so counting rows lets one source satisfy a two-source rule.
    """
    loc = (_asstr(source.get("ark")) or _asstr(source.get("url"))).strip().lower()
    if loc:
        return loc
    return (_asstr(source.get("name") or source.get("title")).strip().lower(),
            _asstr(source.get("tier")))


def distinct(sources):
    """De-duplicated source list, first occurrence wins."""
    seen = {}
    for s in sources:
        if isinstance(s, dict):
            seen.setdefault(source_identity(s), s)
    return list(seen.values())


def is_flagged_lead(source):
    """True if the source declares itself a research lead rather than evidence.

    Since 2026-08-08 a Tier 5 source may sit in evidence.sources when flagged this way:
    recording that a claim was examined and what it rests on beats moving it out of
    sight. Without a flag it is still an error, because an unflagged tree row reads as
    evidence to every consumer.
    """
    if source.get("lead") is True or source.get("is_lead") is True:
        return True
    for key in ("evidence_type", "type", "role", "status"):
        if "lead" in _asstr(source.get(key)).lower():
            return True
    return "lead" in _asstr(source.get("proves")).lower()


def person_sources(person):
    """Sources that support the PERSON-level confidence label.

    Deliberately excludes validation.parent_confidence.<side>.sources. Those support the
    edge label, not the person: folding them in is what let one mis-tiered row be counted
    twice (see @I132594540360@ De Coursey, whose single misattached christening row was
    stored in both containers and cited as "2 sources, 2 Tier 1-2" to justify VERIFIED).
    conformance-report.py's CONF-1 has always counted only this container; this makes the
    validator agree with the gate instead of being 5x more permissive than it.
    """
    return _aslist(_asdict(_asdict(person.get("validation")).get("evidence")).get("sources"))


def legacy_sources(person):
    """Rows in the pre-schema containers that no checker or scorer reads.

    12 rows in genealogy, 116 in dry-cross, 182 in kindred at last count. They are inert:
    they inflate nothing, but they are also entirely unaudited.
    """
    out = list(_aslist(person.get("sources")))
    out += list(_aslist(_asdict(person.get("evidence")).get("sources")))
    return out


def parent_sides(person):
    """(side, block) for each populated parent_confidence side."""
    pc = _asdict(_asdict(person.get("validation")).get("parent_confidence"))
    for side in ("father", "mother"):
        blk = pc.get(side)
        if isinstance(blk, dict) and blk:
            yield side, blk


def evaluate(person):
    """Return {"errors": [...], "warnings": [...]} of human-readable strings."""
    pid = person.get("id") or person.get("person_id") or "<no-id>"
    errors, warnings = [], []

    confidence = _asstr(_asdict(person.get("validation")).get("confidence")).upper()
    srcs = person_sources(person)

    # --- source-level tier hygiene -------------------------------------------------
    for i, s in enumerate(srcs):
        if not isinstance(s, dict):
            errors.append(f"Person {pid}: source[{i}] is not an object")
            continue
        raw = s.get("tier")
        major = tier_major(s)
        if raw is None:
            warnings.append(f"Person {pid}: source[{i}] has no tier — it will be read as a lead")
        elif major is None:
            errors.append(f"Person {pid}: source[{i}] has an unusable tier {raw!r} "
                          f"(expected an integer 1-5)")
        elif not isinstance(raw, int):
            warnings.append(f"Person {pid}: source[{i}] tier {raw!r} is not an integer; "
                            f"read as {major}. The schema types tier as integer 1-5")
        if major == 5 and not is_flagged_lead(s):
            errors.append(f"Person {pid}: source[{i}] is Tier 5 (member tree) in "
                          f"evidence.sources but is not flagged as a lead")

    for s in legacy_sources(person):
        if isinstance(s, dict):
            warnings.append(
                f"Person {pid}: source stored in a legacy container "
                f"(person.sources / person.evidence.sources) that no checker or scorer "
                f"reads — migrate it to validation.evidence.sources")
            break

    # --- person-level confidence floor ---------------------------------------------
    uniq = distinct(srcs)
    tier12 = [s for s in uniq if (tier_major(s) or 9) <= 2]
    majors = [tier_major(s) for s in srcs if tier_major(s)]

    if confidence == "VERIFIED":
        if len(srcs) < 2:
            errors.append(f"Person {pid}: VERIFIED but only {len(srcs)} sources documented "
                          f"(need >=2)")
        if len(tier12) < VERIFIED_MIN_TIER2_SOURCES:
            errors.append(f"Person {pid}: VERIFIED but only {len(tier12)} distinct Tier 1-2 "
                          f"source(s) (need >={VERIFIED_MIN_TIER2_SOURCES})")
    elif confidence == "PROBABLE":
        if not srcs:
            warnings.append(f"Person {pid}: PROBABLE with no sources documented")
        elif not [s for s in uniq if (tier_major(s) or 9) <= 3]:
            warnings.append(f"Person {pid}: PROBABLE but no Tier 1-3 source")

    if confidence in CONCLUDED and majors and min(majors) >= LEAD_TIER_FLOOR:
        errors.append(f"Person {pid}: {confidence} but every source is Tier "
                      f"{min(majors)} or weaker (Tier 4-5 only caps at POSSIBLE)")

    # --- parent-side labels ---------------------------------------------------------
    # Nothing validated these before 2026-08-08. Person-level evidence does not
    # substitute: a well-documented person can have undocumented parentage, which is
    # the reason parent_confidence is tracked separately in the first place.
    for side, blk in parent_sides(person):
        side_conf = _asstr(blk.get("confidence")).upper()
        if side_conf not in CONCLUDED:
            continue
        side_uniq = distinct(_aslist(blk.get("sources")))
        if side_conf == "VERIFIED":
            n12 = len([s for s in side_uniq if (tier_major(s) or 9) <= 2])
            if n12 < VERIFIED_MIN_TIER2_SOURCES:
                warnings.append(f"Person {pid}: {side} side is VERIFIED but carries "
                                f"{n12} distinct Tier 1-2 source(s) on that side "
                                f"(need >={VERIFIED_MIN_TIER2_SOURCES})")
        elif not [s for s in side_uniq if (tier_major(s) or 9) <= 3]:
            warnings.append(f"Person {pid}: {side} side is PROBABLE but carries no "
                            f"Tier 1-3 source on that side")

    return {"errors": errors, "warnings": warnings}
