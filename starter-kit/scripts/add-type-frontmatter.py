#!/usr/bin/env python3
"""Idempotently add a Tolaria `type:` field to markdown notes.

Tolaria groups notes by a frontmatter `type:` key. This backfills it without
disturbing existing content:

- File already opens with a `---` YAML block: insert `type: <TYPE>` as the first
  key (skip if a `type:` key is already present -> idempotent).
- No frontmatter: prepend a minimal block (`type:` + `title:` derived from the
  first H1, falling back to the filename).

Safety:
- Never follows symlinks (skips symlinked files/dirs). This matters because the
  tree repos carry `docs/lessons-shared -> ../../ai-genealogy/lessons`; we must
  not rewrite the shared methodology files through that link.
- Non-recursive by default (operate on one note class at a time).
- `--dry-run` writes nothing and prints a per-action tally.

Usage:
    add-type-frontmatter.py --type ResearchJournal --dry-run research/journals
    add-type-frontmatter.py --type ResearchJournal           research/journals
    add-type-frontmatter.py --type Philosophy PHILOSOPHY.md
    add-type-frontmatter.py --type StarterKit --recursive starter-kit
"""
import argparse
import os
import re
import sys

FM_OPEN = re.compile(r"^---[ \t]*\r?\n")
FM_CLOSE = re.compile(r"\r?\n---[ \t]*\r?\n")
H1 = re.compile(r"^#\s+(.*\S)\s*$")
TYPE_KEY = re.compile(r"^type:\s", re.MULTILINE)


def split_frontmatter(text):
    """Return (fm_block_with_fences, body) if text opens a closed YAML block, else None."""
    if not FM_OPEN.match(text):
        return None
    m = FM_CLOSE.search(text, 3)  # search after the opening fence
    if not m:
        return None
    return text[: m.end()], text[m.end():]


def first_h1(text):
    for line in text.splitlines():
        m = H1.match(line)
        if m:
            return m.group(1)
        if line.strip() and not line.startswith(("#", ">", "-", "*")):
            # bail once real prose starts; H1 should be near the top
            break
    return None


def yaml_quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def process(path, typ, dry):
    if os.path.islink(path):
        return "skip-symlink"
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    parts = split_frontmatter(text)
    if parts:
        fm, _body = parts
        if TYPE_KEY.search(fm):
            return "skip-has-type"
        open_end = FM_OPEN.match(text).end()  # exact opening fence length (handles ---\r\n)
        new = "---\n" + f"type: {typ}\n" + text[open_end:]
        action = "insert"
    else:
        title = first_h1(text) or os.path.splitext(os.path.basename(path))[0]
        block = f"---\ntype: {typ}\ntitle: {yaml_quote(title)}\n---\n\n"
        new = block + text
        action = "create"
    if not dry:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
    return action


def collect(target, recursive):
    if os.path.isfile(target):
        return [target] if target.endswith(".md") and not os.path.islink(target) else []
    files = []
    if recursive:
        for root, dirs, names in os.walk(target):
            # prune symlinked dirs (e.g. lessons-shared) so we never descend them
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for n in sorted(names):
                p = os.path.join(root, n)
                if n.endswith(".md") and not os.path.islink(p):
                    files.append(p)
    else:
        for n in sorted(os.listdir(target)):
            p = os.path.join(target, n)
            if os.path.isfile(p) and n.endswith(".md") and not os.path.islink(p):
                files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser(description="Backfill Tolaria `type:` frontmatter.")
    ap.add_argument("targets", nargs="+", help="markdown files or directories")
    ap.add_argument("--type", dest="typ", required=True, help="type value to set")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--recursive", action="store_true", help="descend into subdirs")
    args = ap.parse_args()

    tally = {"insert": 0, "create": 0, "skip-has-type": 0, "skip-symlink": 0}
    total = 0
    for target in args.targets:
        if not os.path.exists(target):
            print(f"  ! missing: {target}", file=sys.stderr)
            continue
        for path in collect(target, args.recursive):
            total += 1
            tally[process(path, args.typ, args.dry_run)] += 1

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(
        f"[{mode}] type={args.typ} files={total} "
        f"insert={tally['insert']} create={tally['create']} "
        f"skip-has-type={tally['skip-has-type']} skip-symlink={tally['skip-symlink']}"
    )


if __name__ == "__main__":
    main()
