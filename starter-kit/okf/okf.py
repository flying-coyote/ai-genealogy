"""Shared OKF (Open Knowledge Format) reader for the genealogy knowledge graph.

Federation-ready: load_notes() takes a list of roots, so the same coverage / drift /
signal logic runs across all three tree repos plus the ai-genealogy hub with no change.

Single source of truth for the canonical type list is the registry doc itself
(research/_type-registry.md) — parsed, not duplicated, so a guard can never disagree
with the human-readable registry.

LOCAL-ONLY by design: pathlib + json + (optional) PyYAML, no network. SKIP_DIRS excludes
data/, backups/, and caches so the reader structurally cannot walk tree.json or per-record
PII. Adapted from the Second Brain OKF layer (~/project1) per the 2026-06-19 transfer brief.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# The registry lives in the coordinator repo (promote to ai-genealogy hub when ready).
# Configure via GENEALOGY_HOME env var (default: your home dir). Registry sits next to these scripts.
import os
_BASE = Path(os.environ.get("GENEALOGY_HOME", str(Path.home())))
REGISTRY = Path(__file__).resolve().parent / "_type-registry.md"

# One OKF graph across the three trees + the shared methodology hub.
GENEALOGY_ROOTS = [
    _BASE / "genealogy",
    _BASE / "genealogy-dry-cross",
    _BASE / "genealogy-kindred",
    _BASE / "ai-genealogy",
]

# Dirs that hold structured data / history / generated / non-graph content — never the graph.
# Note: iter_markdown only globs *.md, so tree.json (.json) is never read regardless. We skip
# backups/caches (huge, stale) and the per-project memory dir (.claude — its own nested
# metadata.type convention), but DO walk data/reports/*.md so they can be typed as Report.
SKIP_DIRS = frozenset({
    "backups", "cache", ".cache", "exports", "imports", "vendor",
    "wt_prepared_edits", "wt_prepared_comments", "ancestry_prepared_edits",
    "b1_harvest", "chancery", ".claude", ".playwright-mcp", "output",
    ".archive", "archive", "05-archives",
    ".venv", "venv", "node_modules", ".git", "__pycache__", "dist", "_site", "build",
})

# Untyped files that are legitimately NOT knowledge nodes (navigation / status / front-door).
_NON_GRAPH_STEM = re.compile(
    r"^(INDEX|README|CHANGELOG|PLAN|ARCHITECTURE|CLAUDE|AGENTS|MEMORY|CONTRIBUTING|"
    r"PHILOSOPHY|TOOLS-TRACKER|LICENSE|.*_INDEX|.*-PROPOSAL|_type-.*)$",
    re.IGNORECASE,
)

_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SCALAR_LINE = re.compile(r"^([A-Za-z][\w-]*):[ \t]*(.*?)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class OKFNote:
    path: Path
    root: Path
    type: str | None
    frontmatter: dict

    @property
    def rel(self) -> str:
        try:
            return str(self.path.relative_to(self.root))
        except ValueError:
            return str(self.path)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Empty dict when there's no frontmatter.
    Falls back to a scalar/inline-list parse if PyYAML isn't installed."""
    m = _FM.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    if yaml is not None:
        try:
            fm = yaml.safe_load(block)
            if isinstance(fm, dict):
                return fm, text[m.end():]
        except yaml.YAMLError:
            pass
    fm: dict = {}
    for key, raw in _SCALAR_LINE.findall(block):
        val = raw.strip().strip("\"'")
        if val.startswith("[") and val.endswith("]"):
            fm[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        elif val:
            fm[key] = val
    return fm, text[m.end():]


def type_of(text_or_fm) -> str | None:
    """Normalize a note's top-level `type` to a string (or None)."""
    fm = text_or_fm if isinstance(text_or_fm, dict) else split_frontmatter(text_or_fm)[0]
    t = fm.get("type")
    return None if t is None else (t if isinstance(t, str) else str(t))


def load_canonical_types(registry_path: Path = REGISTRY) -> set[str]:
    """Parse the canonical type set from the registry doc (the single source of truth).

    Reads only the region between the "Canonical types" and "Merge map" headings, keeping
    backtick tokens that look like a type name (excludes `*.md`, `_type-*` stubs, paths)."""
    if not registry_path.exists():
        return set()
    text = registry_path.read_text(encoding="utf-8")
    start = text.find("## Canonical types")
    end = text.find("## Merge map")
    region = text[start:end] if start != -1 and end != -1 else text
    canon: set[str] = set()
    for tok in re.findall(r"`([^`]+)`", region):
        tok = tok.strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", tok):
            canon.add(tok)
    return canon


def iter_markdown(root: Path):
    for p in Path(root).rglob("*.md"):
        if SKIP_DIRS.intersection(p.parts):
            continue
        yield p


def load_notes(roots) -> list[OKFNote]:
    """Load every markdown file under each root (typed or not), federation-ready."""
    notes: list[OKFNote] = []
    for root in roots:
        root = Path(root).expanduser()
        if not root.exists():
            continue
        for p in iter_markdown(root):
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm, _ = split_frontmatter(text)
            notes.append(OKFNote(p, root, type_of(fm), fm if isinstance(fm, dict) else {}))
    return notes


def is_graph_candidate(note: OKFNote) -> bool:
    """True if an untyped file *should* carry a type (not a nav/front-door file)."""
    return not _NON_GRAPH_STEM.match(note.path.stem)
