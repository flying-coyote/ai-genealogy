"""Parse the tree.json source-field registry (single source of truth) and check
source records against the accepted key set. Defensive: every public function
no-ops (returns empty / accepts-all) if the registry can't be read, so a caller
in the pre-commit path can never be broken by this module.

Mirrors scripts/okf.py for markdown types, applied to validation.evidence.sources[].
"""
from __future__ import annotations

import re
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent / "source-field-registry.md"


def accepted_source_keys(registry_path: Path = REGISTRY) -> set[str]:
    """Backtick tokens between '## Accepted source keys' and '## Merge map'."""
    try:
        text = registry_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    start = text.find("## Accepted source keys")
    end = text.find("## Merge map")
    region = text[start:end] if start != -1 and end != -1 else ""
    keys: set[str] = set()
    for tok in re.findall(r"`([^`]+)`", region):
        tok = tok.strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", tok):
            keys.add(tok)
    return keys


def noncanonical_keys(source: dict, accepted: set[str] | None = None) -> list[str]:
    """Keys on a source record that aren't in the accepted set. Empty if the
    registry is unreadable (fail-open — never flag when we can't be sure)."""
    if not isinstance(source, dict):
        return []
    if accepted is None:
        accepted = accepted_source_keys()
    if not accepted:
        return []
    return sorted(k for k in source.keys() if k not in accepted)
