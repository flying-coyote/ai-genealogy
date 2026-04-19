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

---

## FS `/platform/records/search` endpoint returns 404 — deprecated

**Source**: genealogy (2026-04-19)

The record-level search API `GET /platform/records/search?q=<query>` at `api.familysearch.org` returns HTTP 404 regardless of query params or auth. Confirmed in the Gen 9-11 weak-target research batch where a Sonnet agent tested all documented parameter combinations. No known alternative bulk record discovery path remains via API alone.

Effect on pipelines: any automation that attempted record-level search (rather than per-person `/platform/tree/persons/{PID}/sources`) now needs to either (a) use the FS Full-Text Search API for handwritten record OCR, or (b) accept manual browser-driven search for record discovery. The documented URL works in a browser at `www.familysearch.org/search/record/results?q=...` but the API path is gone.

**Needs confirmation in**: genealogy-kindred, genealogy-dry-cross

---

## FS HTTP 204 on persons/{PID}/sources — GEDCOM-import profiles have zero attached sources

**Source**: genealogy (2026-04-19)

When `GET /platform/tree/persons/{PID}/sources` returns HTTP 204 (no content), the profile exists on FamilySearch but has no sources attached. In the genealogy Gen 9-11 batch, **15 of 25 FS-ID targets returned 204** — these profiles were created by mass GEDCOM import without source attachment. This is the normal state for the majority of collateral/deep-ancestor profiles on FS, not an error condition.

Operational implications:
- Don't treat 204 as a retry candidate; it is the final answer for that profile in the API.
- The "correct" fix is not code — it is either (a) attaching sources from tree.json via `batch-fs-source-attach.py` or (b) accepting the profile is source-sparse and pursuing records via archive paths.
- If a harvest script reports "profiles checked: N, new sources found: 0", 204 responses are the dominant reason at Gen 9+.

**Needs confirmation in**: genealogy-kindred, genealogy-dry-cross

---

## WikiTree account blocks are durable and account-wide, not action-scoped

**Source**: genealogy (2026-04-19)

When a WikiTree account triggers Error 2562 (automation rate limiting), the block persists for **48+ days** and applies to *every* action on that account — UI edits, API reads, and logins all fail with Error 2562 or `?errcode=blocked`. Observed pattern for Wiley-6910 (tree manager account for ~165 profiles): block initiated 2026-03-02 after ~993 automated edits in 5 days; 48 days later (2026-04-19) still blocked. Contact with `info@wikitree.com` has not yielded resolution.

Mitigation adopted: use a separate account (Wiley-6998) assigned to a mentor (Lukas Murphy), with all edits via browser UI (no automation) at ≤50/day / ≥120s min-delay / ≤8/30min burst. Rate limiter script: `scripts/wt-rate-check.py` with shared lockfile `~/.wikitree-contribution-log.jsonl` across all sister projects.

Implication: any automation architecture must assume blocks are irrecoverable and plan for clean-account rotation rather than trying to unblock.

**Needs confirmation in**: genealogy-kindred, genealogy-dry-cross

---

## Loop-research saturates at Gen 49 (Merovingian frontier) on FS-Tier-5 parents

**Source**: genealogy (2026-04-19)

The recursive parent-extension loop (`scripts/loop-research-dispatch.py`) drains at the Gen 49 Merovingian dynasty frontier. Beyond Gen 49 on the Kurby Wiley tree, FS profiles for claimed parents are either (a) absent (profile not on FS), (b) Tier-5-only (patron-submitted trees, not attachable per our T5 external rule), or (c) present with zero sources (HTTP 204 pattern above).

At that frontier, further extension requires:
- Scholarly genealogies (Settipani, Medieval Lands Project) — usually paywalled or subscription-only
- Primary records (chronicles, annals, royal charters) — archive access required
- Aristocratic lineage studies — not a pure-API path

Operational rule: once `loop-research-dispatch.py` exits code 2 (queue drained) twice in succession on the same tree, do not restart. The queue is not going to refill itself; the remaining frontier is ONSITE research.

**Needs confirmation in**: genealogy-kindred, genealogy-dry-cross

---

## Weak-person FS ID mismatch gate — ~36% of untriaged FS IDs fail identity check

**Source**: genealogy (2026-04-19)

In a Gen 9-11 weak-target audit (25 persons with FS IDs but POSSIBLE/UNVERIFIED confidence), **9 of 25 failed the identity gate**: either the birth year differed by >3 years, the birth country differed, or descendancy was time-impossible (e.g., FS profile death pre-dates subject's required existence). This suggests that for persons with weak-confidence + FS IDs assigned via GEDCOM bulk import, roughly 1 in 3 FS IDs are *wrong*, not merely under-sourced.

Recommended gate (applied in the April 2026 batch):
- Name overlap: ≥2 normalized tokens (excludes titles)
- Birth year: within ±3 years (tighten to ±1 when both dates have source attribution)
- Spouse match: ≥1 spouse-name token overlap OR spouse absent both sides
- Country match: required for pre-1900 persons
- Descendancy check: subject's required life window must overlap with FS lifespan

Persons failing the gate should have the FS ID *removed* rather than sources attached. Attaching records to the wrong profile compounds the error and propagates to child/spouse profiles via FS's relationship links.

**Needs confirmation in**: genealogy-kindred, genealogy-dry-cross
