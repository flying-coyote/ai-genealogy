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

---

## WikiTree contribution queue: filter pre-1700 at build time

**Source**: genealogy (2026-04-18)

WikiTree locks pre-1700 profiles behind a Pre-Genealogical Merit (PGM) project badge. Building a WT contribution queue without filtering birth year < 1700 (or generation > 15 when birth year is unknown) makes the majority of a deep pedigree queue unusable — 833 of 1,293 WT profiles in the Kurby tree were pre-1700. The rebuild script (`rebuild-wt-queue.py`) now enforces this filter. Attempting to edit a pre-1700 profile via the edit page returns a "This profile is protected" message with no textarea.

**Needs confirmation in**: genealogy-kindred, dry-cross

---

## WikiTree: additive bio injection for stale prepared edits

**Source**: genealogy (2026-04-18)

A prepared WT edit bio goes stale when other contributors enrich the live profile between the time the edit was prepared and the time it is posted. If the prepared bio is materially shorter than the current live bio (threshold: prepared < current - 200 chars), applying it as a full replacement causes a regression — stripping enrichment the community added. The correct strategy: extract new `<ref name="...">...</ref>` blocks from the prepared bio that aren't already present in the current bio (match by `name` attribute), then inject them immediately before `<references />` in the live bio. If there are no new refs to inject, skip and remove the prepared file. Implemented in `wt-playwright-post.py` via `_extract_new_refs()` + `_inject_refs_into_bio()`.

**Needs confirmation in**: genealogy-kindred, dry-cross

---

## WikiTree CDP posting: `wait_until="networkidle"` required for textarea read

**Source**: genealogy (2026-04-18)

When navigating to the WT edit page (`?action=edit`) via Playwright CDP and then reading `#wpTextbox1.value`, using `wait_until="domcontentloaded"` causes `Execution context was destroyed` errors — the page is still rendering when the query fires. `wait_until="networkidle"` waits until all XHR/fetch activity settles and reliably yields a populated textarea. Use `networkidle` for any WT edit page read in Playwright scripts.

**Needs confirmation in**: genealogy-kindred, dry-cross

---

## WikiTree CDP posting: `context.new_page()` for tab isolation

**Source**: genealogy (2026-04-18)

When using Chrome CDP with an active Playwright MCP session (which occupies pages[0]), automated posting scripts must call `context.new_page()` to get an isolated tab — using `pages[0]` directly clobbers the active MCP tab and disrupts the user's browser session. This is a refinement of the existing LESSONS.md rule ("use `pages[0]` after Chrome restart") — that rule targets restart-hang prevention; this rule targets concurrent MCP + script isolation. The two scenarios are mutually exclusive: after a restart there are no existing pages, so `new_page()` and `pages[0]` are equivalent.

**Needs confirmation in**: genealogy-kindred, dry-cross

---

## Canonical name in tree.json can diverge from WT profile identity

**Source**: genealogy (2026-04-18)

WT ID assignment is an identity-match operation, not a name-sync operation. A person's canonical name in tree.json may be incorrect while their assigned WT ID is correct. Primary sources are authoritative for name: if 50+ Tier 1-2 sources consistently identify a person as "Matthew Grant" but tree.json has "William Grant", the name in tree.json is the error — not the WT ID. When researching a blocked_mismatch queue item, check source text before concluding the WT ID is wrong. Name correction is a separate step from platform ID assignment and requires a `data_correction` contribution_log entry.

**Needs confirmation in**: genealogy-kindred, dry-cross

---

## Convergence-aware generation validator: `parent.gen != child.gen + 1` is WARN when parent has 2+ children at different gens

**Source**: dry-cross (2026-04-19)

Multi-lineage convergence (primary descendant reaching a deep ancestor via multiple paths of different lengths) is a real phenomenon in a well-researched tree — e.g. Shell convergence, Howard triple descent. A strict `parent.gen == child.gen + 1` rule treats these as errors. The convergence-aware variant detects them: if an ancestor has two or more children stored at different `generation` values, the diff != 1 at each child is a convergence artifact (WARN). Everything else is ERROR. This distinguishes documented multi-lineage descent from actual import bugs. See `scripts/validate-tree.py` step `[5/5]` in dry-cross.

```python
convergence_ancestors = {pid for pid, gens in parent_child_gens.items() if len(gens) > 1}
# For each parent-child edge with diff != 1:
#   if parent in convergence_ancestors → WARN
#   else → ERROR
```

**Needs confirmation in**: genealogy, genealogy-kindred

---

## Background-script checkpoints: persist after every item, not at batch end

**Source**: dry-cross (2026-04-19)

Long-running batch scripts (e.g. Playwright triage of 50+ items, bulk API harvests) should save their progress file after each completed item, not accumulate results in memory for a single end-of-batch write. When the browser or API crashes mid-batch (common with Playwright `Execution context was destroyed` or token expiry), all completed work is lost otherwise. Pattern:

```python
for item in batch:
    try:
        result = process(item)
        log['sessions'][-1]['items'].append(result)
        save_log(log)          # ← every iteration, not outside the loop
    except Exception as e:
        log['sessions'][-1]['errors'].append({"item": item['id'], "error": str(e)})
        save_log(log)
        continue               # ← don't let one bad item kill the batch
```

In dry-cross `scripts/ancestry-auto-triage.py` commit `8f8bfe0`, this pattern converted "lose 10 accepts on crash" into "lose the one failing item; everything else preserved." Verified against the exact `query_selector_all` crash that motivated the patch.

**Needs confirmation in**: genealogy, genealogy-kindred

---

## Hardcoded-generation anti-pattern in bulk-add scripts

**Source**: dry-cross (2026-04-19)

Scripts that write `"generation": N` as a hardcoded literal (e.g. `add-generation.py`, `add-gen7-persons.py`) introduce systematic gen-offset bugs at import boundaries. When a user manually adds a new ancestor at their "intuitive" gen number (e.g. "this is my great-grandfather's great-grandfather, so Gen 7") without computing from the existing child's stored gen, any off-by-one error cascades through all previously-imported ancestors of that person.

In dry-cross, 510 persons ended up stored +1 off canonical shortest-path-to-Christy because @I711@ Miles Grady Martin was inserted at `"generation": 5` while his child @I4@ Mary Blanche Martin was at 3 (should be parent=4). The offset compounded through all 77 Martin ancestors, plus 376 Sanders ancestors after @I712@ was inserted similarly, plus 3 Griffith ancestors inserted 2026-04-19. The validator's strict diff=1 check only fires at 2 boundary edges; the 508 internal edges all have diff=1 because everyone is equally wrong.

**Mitigation**: always compute `generation = persons[child_id]["generation"] + 1` (or the inverse when adding children). Fail loudly if child has no generation rather than silently picking a literal.

**Recovery**: surgical fix requires per-person path enumeration to avoid corrupting legitimate convergence anchors (some Martin ancestors also appear via Cross/Smith paths through deep convergence). Simple bulk decrement creates new bad edges.

**Needs confirmation in**: genealogy, genealogy-kindred
