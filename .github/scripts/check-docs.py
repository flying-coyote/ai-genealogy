#!/usr/bin/env python3
"""
check-docs.py — Lightweight documentation validator for the ai-genealogy hub.

Run from the repo root. Catches the kind of drift that has slipped in before
(broken cross-references, stale links) without needing any third-party deps.

Checks
------
ERROR (fails CI)
  - broken internal links: [text](path) or [text](path#anchor) where `path`
    is a repo-relative file that does not exist
WARNING (reported, does not fail unless --strict)
  - broken in-repo anchors: #anchor that matches no heading in the target file
  - a .md file missing `type:` / `title:` YAML frontmatter

External links (http/https/mailto), pure protocol-relative links, and image
embeds are not fetched — this is an offline structural check only.

Usage
-----
  python3 .github/scripts/check-docs.py
  python3 .github/scripts/check-docs.py --strict   # warnings also fail
"""

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
SLUG_STRIP = re.compile(r"[^\w\s-]")


def slugify(heading: str) -> str:
    """Approximate GitHub's heading-anchor slug algorithm."""
    s = heading.strip().lower()
    s = SLUG_STRIP.sub("", s)        # drop punctuation except word chars, space, hyphen
    s = s.replace(" ", "-")
    return s


def headings_slugs(text: str) -> set[str]:
    slugs: dict[str, int] = {}
    out: set[str] = set()
    for h in HEADING_RE.findall(text):
        base = slugify(h)
        # GitHub disambiguates repeats with -1, -2, ...
        n = slugs.get(base, 0)
        out.add(base if n == 0 else f"{base}-{n}")
        slugs[base] = n + 1
    return out


def has_frontmatter_fields(text: str) -> bool:
    if not text.startswith("---"):
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    front = parts[1]
    return "type:" in front and "title:" in front


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate hub docs (links + frontmatter).")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    md_files = sorted(p for p in root.rglob("*.md") if ".git" not in p.parts)

    # Cache heading slugs per file
    slug_cache: dict[Path, set[str]] = {}

    def slugs_for(path: Path) -> set[str]:
        if path not in slug_cache:
            try:
                slug_cache[path] = headings_slugs(path.read_text(encoding="utf-8"))
            except OSError:
                slug_cache[path] = set()
        return slug_cache[path]

    errors: list[str] = []
    warnings: list[str] = []

    for md in md_files:
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(root)

        if not has_frontmatter_fields(text):
            warnings.append(f"{rel}: missing `type:`/`title:` frontmatter")

        for target in LINK_RE.findall(text):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:", "//", "tel:")):
                continue

            file_part, _, anchor = target.partition("#")

            if file_part == "":
                # pure in-page anchor
                if anchor and slugify(anchor) not in slugs_for(md):
                    warnings.append(f"{rel}: in-page anchor '#{anchor}' has no matching heading")
                continue

            dest = (md.parent / file_part).resolve()
            if not dest.exists():
                errors.append(f"{rel}: broken link '{target}' -> {file_part} not found")
                continue

            if anchor and dest.suffix == ".md":
                if slugify(anchor) not in slugs_for(dest):
                    warnings.append(
                        f"{rel}: link '{target}' -> file exists but anchor '#{anchor}' not found"
                    )

    print(f"=== check-docs.py — scanned {len(md_files)} markdown files ===\n")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")

    if errors:
        return 1
    if args.strict and warnings:
        print("(--strict: warnings count as failures)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
