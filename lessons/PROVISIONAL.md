# Provisional Patterns

Patterns discovered in only one sister project. Plausible and worth knowing, but not yet cross-validated. These may be promoted to LESSONS.md once another project confirms them, or may turn out to be project-specific.

---

## FS source description URLs can be patched via API

**Source**: dry-cross (2026-04-15)

`POST /platform/sources/descriptions/{sourceId}` with body `{"sourceDescriptions": [{"id": "...", "about": "https://..."}]}` updates the `about` URL on an existing source description. HTTP 204 = success. This lets you add or correct a source URL programmatically without going through the FS Source Linker browser UI.

**Needs confirmation in**: genealogy, genealogy-kindred

---

## FS source harvest: targeted calls beat bulk script for recently-added persons

**Source**: dry-cross (2026-04-15)

For persons added to the tree within the current session (e.g., via lineage extension), direct API calls per FS PID yield more new sources per minute than the sequential bulk harvest script. The bulk script processes persons in tree order, hitting well-sourced early-generation persons before reaching the newly-added ones.

**Needs confirmation in**: genealogy, genealogy-kindred

---

## Scope analysis: `ancestor_set()` to catch research drift

**Source**: dry-cross (2026-04-10)

Computing the explicit ancestor set of primary persons (via BFS traversal of father_id/mother_id) and comparing against all persons in tree.json identifies orphaned ancestors (stale-correction artifacts), collateral bleed-through (in-laws' lineage accidentally added), and contextual siblings. Running this after any bulk import or parent-link correction caught 15 out-of-scope persons in one session.

```python
def ancestors_of(root_id, person_index):
    result = set()
    stack = [root_id]
    while stack:
        cur = stack.pop()
        if cur in result or not cur: continue
        p = person_index.get(cur)
        if not p: continue
        result.add(cur)
        stack.append(p.get('father_id'))
        stack.append(p.get('mother_id'))
    return result
```

**Needs confirmation in**: genealogy, genealogy-kindred

---

## Journal cross-linking: back-references on parent journals

**Source**: dry-cross (2026-04-10)

When creating child-generation research journals in batch, also append a back-reference block to each parent's journal listing the new children with links. This allows researchers to navigate parent ↔ child without name search. A marker line in the parent journal (`## YYYY-MM-DD — Descendant journal cross-references`) prevents duplicate blocks on re-runs.

**Needs confirmation in**: genealogy, genealogy-kindred

---

## WikiTree: CDP `fetch()` works; `page.goto()` drops auth state

**Source**: genealogy (2026-04-15)

In Chrome CDP sessions, `fetch()` calls from browser context inherit session cookies. `page.goto()` to certain Ancestry or FS pages drops authentication state mid-navigation. Use `browser_evaluate` with `fetch()` for authenticated API calls rather than page navigation.

**Confirmed in**: genealogy  
**Needs confirmation in**: genealogy-kindred, dry-cross

---

## Generation cap on lineage extension: quality gates by era

**Source**: genealogy (2026-04-15)

Extending lineage beyond Gen 15 (pre-1600) requires ≥2 Tier 1-2 sources on both the child and the parent. Even if FS has parents listed for a Gen 16 person, the parents may have only Tier 5 community-tree sourcing. The dispatcher's `PRE_1700_GEN_THRESHOLD` enforces a stricter evidence filter at deeper generations. This architectural decision reflects that pre-1600 FamilySearch profiles are heavily conflated across community contributions.

**Needs confirmation in**: genealogy-kindred, dry-cross
