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

# The VERIFIED rule is not the same in every project, and pretending otherwise is what
# this module exists to stop. methodology/02-evidence-standards.md records one named
# exception: the kindred tree scores VERIFIED at three or more distinct Tier 1-3 sources
# rather than two at Tier 1-2, because applying the cross-project rule would wrongly strip
# 34 profiles whose support is genuine published work. Until 2026-08-08 the checker applied
# the cross-project rule to kindred anyway, so the gate contradicted the standard it checks
# against and reported 41 violations, 36 of which are not violations under kindred's own
# documented rule. A project declares its rule in .conformance-profile.json; the fork then
# reads as a decision rather than as drift.
PROFILE_FILE = ".conformance-profile.json"
VERIFIED_RULES = {
    "standard": {"min_tier": 2, "min_count": 2,
                 "desc": ">=2 distinct sources at Tier 1-2"},
    "kindred_t13_ge3": {"min_tier": 3, "min_count": 3,
                        "desc": ">=3 distinct sources at Tier 1-3 (documented kindred fork, "
                                "02 §Confidence Rules)"},
}


def load_profile(root):
    """Name of the project's VERIFIED rule. Absent file or unknown name -> 'standard'."""
    import json
    import pathlib
    try:
        cfg = json.loads((pathlib.Path(root) / PROFILE_FILE).read_text())
        name = cfg.get("verified_rule")
        return name if name in VERIFIED_RULES else "standard"
    except Exception:
        return "standard"


def verified_ok(sources, rule="standard"):
    """Does this source list carry what VERIFIED claims, under the named rule?"""
    spec = VERIFIED_RULES.get(rule) or VERIFIED_RULES["standard"]
    qualifying = [s for s in distinct(sources)
                  if (tier_major(s) or 9) <= spec["min_tier"]]
    return len(qualifying) >= spec["min_count"]


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


# A locator naming a COLLECTION or a search rather than a record. 2,156 rows across the
# three trees carry one: `sse.dll?dbid=7249` is the whole Millennium File, not an entry in
# it. Treating those as identity merged genuinely different records — on genealogy
# @I132246180553@ Thomas Hardeman, "Virginia Soldiers of 1776", "American Civil War
# Soldiers" and the 1790 Federal Census all carry `sse.dll?dbid=9000`, so first-occurrence-
# wins kept a Tier 3 row and silently discarded the Tier 2 census.
_GENERIC_LOCATOR = re.compile(
    r"/collections/\d+/?$"            # a collection, with no /records/<id> after it
    r"|/hints?(/|\?|$)"               # a hint list: a suggestion, not a record
    r"|discoveryui-content/view/?$"   # a record viewer pointed at nothing
    r"|/search/?$",
    re.I,
)


def is_record_locator(loc):
    """True when a url/ark identifies one record rather than a collection or a search."""
    low = loc.lower()
    if "sse.dll" in low and not re.search(r"[?&](h|indiv|pid|recid)=", low):
        return False
    return not _GENERIC_LOCATOR.search(low)


def source_identity(source):
    """Key two source objects share when they describe the same source.

    The standard requires >=2 *independent* sources for VERIFIED, and the trees hold
    literal duplicates — two genealogy parent sides carry 71 byte-identical copies each of
    a single Legacy NFS assertion (@I132566338704@ Richard Thatcher IV and @I236648223271@
    Christopher Thomas, Jr.) — so counting rows lets one source satisfy a two-source rule.

    A collection-level locator is not identity: those rows fall back to title+tier like any
    other row carrying no pointer.
    """
    loc = (_asstr(source.get("ark")) or _asstr(source.get("url"))).strip().lower()
    if loc and is_record_locator(loc):
        # Normalise scheme and host prefix: @I29566154585@ Elizabeth Talbott carries
        # Richard Talbott's 1663 will twice, once as http://msa.maryland.gov/... and once
        # as https://, and counting one document as two independent sources is the exact
        # error this function exists to prevent.
        return re.sub(r"^https?://(www\.)?", "", loc)
    # Fall back to the citation when there is no name or title. Kindred stores whole
    # populations with name and title both None but a specific citation — "Daviess County,
    # Kentucky. Probate Records 1812-1896. Will of Adam Shoemaker", "Monongalia County
    # court summons, January 1843" — which are plainly different records, and keying them
    # on (None, tier) collapsed three deeds, a will and a tax list into one source.
    label = _asstr(source.get("name") or source.get("title")).strip().lower()
    if not label or label == "none":
        label = _asstr(source.get("citation")).strip().lower()[:160]
    return (label, _asstr(source.get("tier")))


def distinct(sources):
    """De-duplicated source list, first occurrence wins."""
    seen = {}
    for s in sources:
        if isinstance(s, dict):
            seen.setdefault(source_identity(s), s)
    return list(seen.values())


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


def evaluate(person, rule="standard"):
    """Return {"errors": [...], "warnings": [...]} of human-readable strings.

    `rule` names the project's VERIFIED rule (see VERIFIED_RULES); pass
    load_profile(project_root) to honor a documented fork.
    """
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
        # tier 0 is a deliberate convention, not junk: kindred's
        # classify-untiered-sources.py writes it on audit-pointer rows (Find A Grave,
        # Social Security, BillionGraves) to mean "catalogued, not evidence". Treat it
        # like an absent tier — a lead — rather than erroring on 49 rows that are doing
        # exactly what they were designed to do.
        if raw is None or raw == 0:
            warnings.append(f"Person {pid}: source[{i}] has no usable tier — "
                            f"it will be read as a lead")
        elif major is None:
            errors.append(f"Person {pid}: source[{i}] has an unusable tier {raw!r} "
                          f"(expected an integer 1-5)")
        elif not isinstance(raw, int):
            warnings.append(f"Person {pid}: source[{i}] tier {raw!r} is not an integer; "
                            f"read as {major}. The schema types tier as integer 1-5")
        # No error for Tier 5 in evidence.sources. It was one until 2026-08-08, which is
        # the sole reason every remediation demoted tree rows to Tier 4 instead of 5 and
        # thereby slipped past CONF-3. A first version of this module instead demanded an
        # explicit "lead" flag, which produced 1,372 errors in dry-cross for not adopting
        # a field invented the same day — and the flag was redundant anyway, since the
        # tier is itself the declaration. What matters is what a Tier 5 row can support,
        # and the concluded-label check below enforces that.

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
        if not verified_ok(srcs, rule):
            spec = VERIFIED_RULES.get(rule) or VERIFIED_RULES["standard"]
            have = len([s for s in uniq if (tier_major(s) or 9) <= spec["min_tier"]])
            errors.append(f"Person {pid}: VERIFIED but only {have} distinct Tier "
                          f"1-{spec['min_tier']} source(s) — {spec['desc']}")
    # The tier floor: every source at Tier 4-5 cannot support a concluded label.
    below_floor = bool(majors) and min(majors) >= LEAD_TIER_FLOOR
    if confidence in CONCLUDED and below_floor:
        errors.append(f"Person {pid}: {confidence} but every source is Tier "
                      f"{min(majors)} or weaker (Tier 4-5 only caps at POSSIBLE)")

    if confidence == "PROBABLE":
        if not srcs:
            warnings.append(f"Person {pid}: PROBABLE with no sources documented")
        elif not below_floor and not [s for s in uniq if (tier_major(s) or 9) <= 3]:
            # Suppressed when below_floor already fired: "every source is Tier 4+" and
            # "no Tier 1-3 source" are the same fact stated twice, and reporting both
            # inflated 20 genealogy persons into two findings each.
            warnings.append(f"Person {pid}: PROBABLE but no Tier 1-3 source")

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
