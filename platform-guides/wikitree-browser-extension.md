# WikiTree Browser Extension (WT BE) — Capability Reference

Centralized reference for the official WikiTree Browser Extension. Used
across the three sister genealogy projects (`genealogy`, `genealogy-kindred`,
`genealogy-dry-cross`) that share the `kurbyewiley@gmail.com` / `jeremy@wiley2.com`
WikiTree accounts.

Upstream: https://github.com/wikitree/WikiTree-Browser-Extension · MIT

## Why this extension matters for our workflow

Our mentor Lukas Murphy flagged (2026-04-21) three source-quality anti-patterns
in our contributions: WT profiles cited as sources, FS profile URLs instead
of record ARKs, and vague no-URL aggregator blobs. The extension's built-in
**Bio Check** feature (`src/features/bioCheck/`) encodes ~100 invalid-source
patterns as an executable `SourceRules` class — essentially the same rules
Lukas is teaching, in reusable form. Running Bio Check on a profile before
posting catches exactly the regressions he flagged.

The extension also integrates with `plus.wikitree.com` for per-profile error
lists (Error 305 mother-too-young, Error 406 date conflicts, etc.), which is
the suggestion-list Lukas pointed us at for cleanup priority.

## Install — stable Chrome blocks `--load-extension`

Google Chrome stable (v143+ verified) explicitly refuses the `--load-extension`
flag with `--load-extension is not allowed in Google Chrome, ignoring.` The
CDP `Extensions.loadUnpacked` method returns `Method not available` on the
WebSocket transport. You need one of these workarounds:

### Recommended: Playwright's Chromium for Testing

Playwright ships Chromium builds at `~/.cache/ms-playwright/chromium-<version>/
chrome-linux64/chrome` (e.g. `chromium-1208` = Chrome/145.0.7632.6). These
are Chromium for Testing, which accepts `--load-extension` normally.
User-data-dir format is Chrome-compatible — cookies + logged-in tabs preserve
when switching between stable Chrome and Chromium.

Build the extension from source:
```bash
cd <project>/vendor
git clone https://github.com/wikitree/WikiTree-Browser-Extension.git wikitree-browser-extension-src
cd wikitree-browser-extension-src
npm ci && npm run build
cp -r dist ../wikitree-be-dist
```

Commit `vendor/wikitree-be-dist/` (the built MV3 dist, ~8 MB, 180 files);
gitignore the source clone.

Then modify your `scripts/chrome-cdp.sh` to auto-select Chromium when the
dist is present:
```bash
CHROME="/opt/google/chrome/chrome"
CHROMIUM="/home/jerem/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
EXT_DIR="/home/<user>/<project>/vendor/wikitree-be-dist"

EXT_FLAGS=()
if [ -d "$EXT_DIR" ] && [ -x "$CHROMIUM" ]; then
    CHROME="$CHROMIUM"
    EXT_FLAGS=(--load-extension="$EXT_DIR" --disable-extensions-except="$EXT_DIR")
fi
# ... use CHROME + EXT_FLAGS in your CHROME_FLAGS array
```

### Alternative: Chrome Beta/Dev/Canary

`sudo apt install google-chrome-beta` — the beta/dev channels accept
`--load-extension`. Separate binary at `/opt/google/chrome-beta/chrome`.
Haven't tested in our workflow.

### Alternative: Enterprise Policy force-install

Drop a JSON at `/etc/opt/chrome/policies/managed/wtbe.json`:
```json
{
  "ExtensionSettings": {
    "ncjafpiokcjepnnlmgdaphkkjehapbln": {
      "installation_mode": "force_installed",
      "update_url": "https://clients2.google.com/service/update2/crx"
    }
  }
}
```
Requires sudo. Uses the stable Web Store extension ID
`ncjafpiokcjepnnlmgdaphkkjehapbln`. Stable Chrome then installs + auto-updates
from Web Store. Not compatible with CDP user-data-dir unless you switch Chrome
entirely.

## Verify install

After restart, the CDP `/json/list` endpoint should surface extension
service-worker targets:

```bash
curl -s http://localhost:9223/json/list | python3 -c "
import json, sys, re
tabs = json.load(sys.stdin)
ext = [t for t in tabs if re.match(r'chrome-extension://[a-p]{32}/', t.get('url',''))]
print('LOADED' if ext else 'NOT_LOADED')
for t in ext[:3]:
    print(f\"  {t.get('type')}: {t.get('url','')[:80]}\")
"
```

Expected (after load):
```
LOADED
  service_worker: chrome-extension://imdflchbmmlikjngjekjbeieoocfhbab/background.js
  page: chrome-extension://imdflchbmmlikjngjekjbeieoocfhbab/options.html
```

Unpacked-build extension IDs are deterministic per install path, so once
you've built the dist once, the ID `imdflchbmmlikjngjekjbeieoocfhbab` (or
whatever hash your path produces) will be stable across restarts as long as
you keep the same `vendor/wikitree-be-dist/` path.

### Extension IDs reference

| Build channel | Chrome Web Store ID |
|---|---|
| Stable | `ncjafpiokcjepnnlmgdaphkkjehapbln` |
| Preview | `ijipjpbjobecdgkkjdfpemcidfdmnkid` |
| Unpacked dev (our Chromium build) | `imdflchbmmlikjngjekjbeieoocfhbab` |

## Features are opt-in — enable these first

Install alone enables **nothing**. Open the options page in your CDP browser:
```
chrome-extension://imdflchbmmlikjngjekjbeieoocfhbab/options.html
```

For the Lukas-aligned source-quality workflow, enable these 5 first:

| Feature | Category | Why |
|---|---|---|
| **Bio Check** (`bioCheck`) | Editing | Validates bio before save: rejects patron-tree citations, bare collection names, invalid sources. The cornerstone for Lukas's feedback. |
| **Show Suggestions** (`showSuggestions`) | Editing | Surfaces plus.wikitree.com errors inline on each profile page (Error 305 etc.). Replaces manual plus.wikitree.com navigation. |
| **Auto Bio** (`autoBio`) | Editing/Add_Person | Skeleton bio from dates/places/census — reduces manual typing + enforces WT-idiomatic structure. Combine with our `wt-contribution-dispatch.py` for consistency. |
| **WikiTree+ Edit Helper** (`wtplus`) | Editing | Multiple editing conveniences; tightly integrated with plus.wikitree.com. |
| **Category Management** (`categoryManagement`) | Editing | Category edits come up constantly; saves clicks. |

Next tier (enable when you run into these scenarios):

| Feature | When to enable |
|---|---|
| Find A Grave Memorial Extractor | When attaching FAG sources — parses memorial pages into structured citations |
| Add FamilySearch ID | When populating FS IDs from a WT profile |
| Date Fixer | When working with non-US-format dates (DD-MM-YYYY etc.) |
| Shareable Sources | Cross-profile source reuse |
| Source Preview | Preview how source citations render before save |
| Family Timeline | Visual family timeline on profile submenu |
| Verify ID | Extra check when attaching a person by ID |
| Locations Helper | Location typeahead sanity |

## Full feature inventory (78 features with options, 25+ simple)

Grouped by category per the extension's own taxonomy. `✅` = default-on.
"Default" reflects upstream defaults; the options page lets you toggle any.

### Editing (17)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `bioCheck` | Bio Check | ✅ | Check biography sources and style |
| `categoryManagement` | Category Management | ✅ | Creating, filling, changing, emptying categories |
| `unnamedInfant` | Childless (Unnamed Infant) | ✅ | Standardize unnamed-infant naming |
| `copyBioChanges` | Copy Bio Changes | ✅ | Buttons to copy bio change deltas |
| `dateFixer` | Date Fixer | | MM-DD-YYYY ↔ DD-MM-YYYY etc. |
| `editorExpander` | Editor Expander | ✅ | Expand the bio editor to near full-screen |
| `enhancedEditorStyle` | Enhanced Editor Style | | Custom colors for Enhanced Editor |
| `familyStatusSync` | Family Status Sync | | Sync status flags across family |
| `imagePageOptions` | Image Page Options | | Tweak image-page template examples |
| `locationsHelper` | Locations Helper | ✅ | Highlight likely-correct locations in suggestions |
| `makeRadioButtonsDeselectable` | De-selectable Radio Buttons | ✅ | Clear a radio button by clicking it |
| `migrationCategoryHelper` | Migration Category Helper | ✅ | Auto-populate migration categories |
| `scissors` | Scissors | ✅ | Copy variants on Category/Image/Help/etc. pages |
| `shareableSources` | Shareable Sources | | Reuse sources across profiles |
| `stickyToolbar` | Sticky Toolbar | ✅ | Keep editor toolbar visible on scroll |
| `wikitableWizard` | Wikitable Wizard | ✅ | Create/edit wiki tables |
| `wtplus` | WikiTree+ Edit Helper | ✅ | Multiple editing features, plus.wikitree.com-integrated |

### Editing / Add Person (4)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `editFamilyData` | Dates and Locations on New Profile | ✅ | Auto-fill dates/locations from related profile |
| `sendToMerge` | Send to Merge | | Button to send to merge queue |
| `suggestedMatchesFilters` | Suggested Matches Filters | ✅ | Filter out bad suggested matches (location, name, date) |
| `verifyID` | Verify ID | ✅ | Confirm details when attaching a person by ID |

### Editing / Edit Profile (5)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `autoCategories` | Auto Categories | ✅ | Add categories to bio from available data |
| `editProfileRedesign` | Edit Profile Redesign | | Hide/show sections on edit page |
| `familyDropdown` | Family Dropdown | | Quick-copy family WikiLinks |
| `familyLists` | Family Lists | ✅ | Generate family list info into bio |
| `saveButtonsStyleOptions` | Save Buttons Style | | Convert Compare/Return links to buttons |

### Profile page (10)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `addFSId` | Add FamilySearch ID | | Button to attach FS ID to profile |
| `collapsibleDescendants` | Collapsible Descendants | ✅ | Collapse/expand descendants tree branches |
| `collapsibleProfiles` | Collapsible Profiles | ✅ | Collapse profile sections |
| `connectorImage` | Connector Image | | Connector Project jigsaw symbol |
| `distanceAndRelationship` | Distance and Relationship | ✅ | Show degree + relationship to profile person |
| `familyGroup` | Family Group | ✅ | Dates/locations of all family members |
| `familyTimeline` | Family Timeline | ✅ | Visual family timeline |
| `sortThemePeople` | Featured Connections Tables | ✅ | Sortable featured-connection tables |
| `reorderNames` | Reorder Names | | Reorder non-Latin-alphabet names |
| `unconnectedBranchTable` | Unconnected Branch Table | ✅ | List all people in an unconnected branch |

### Global (9)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `accessKeys` | Access Keys | ✅ | Keyboard shortcuts for common actions |
| `addSearchBoxes` | Add Search Boxes | | Google + Help search boxes at page bottom |
| `clipboardAndNotes` | Clipboard and Notes | | Persistent clipboard + notes |
| `extraWatchlist` | Extra Watchlist | ✅ | Second personal watchlist |
| `linksToNewTabs` | Links to New Tabs | | Open all links in new tab |
| `menuHover` | Menu Hover | | Show top menus on hover |
| `showSearch` | Show Search | | Start with search bar open |
| `spaceWatchlistSorter` | Space Watchlist Sorter | | Organize space pages in tabs |
| `textExpander` | Text Expander | | Abbreviation → full-text expansion |

### Global / Style (6)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `disableGIFs` | Disable GIFs | | Animated GIFs → static images |
| `highlightWBEFeatures` | Highlight WBE Features | | Cyan border on WBE-injected UI |
| `menuStyle` | Menu Style | | Remove underlines + visited colors from top menus |
| `spaceStyle` | Space Style | ✅ | Restyle space pages (sidebar removal etc.) |
| `stickyHeader` | Sticky Header | | WikiTree header sticks on scroll |
| `visitedLinks` | Visited Links | | Change color of visited links |

### Navigation (3 + 3 in Find Menu)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `akaNameLinks` | AKA Name Links | ✅ | Surname-page links in AKA section |
| `categoryFinderPins` | Category Finder Pins | ✅ | Pins on Category Finder results (edit page) |
| `myMenu` | My Menu | | Custom top menu |
| `cc7Changes` | CC7 Changes | | Track changes in your CC7 |
| `draftList` | Draft List | ✅ | Uncommitted drafts in Find menu |
| `appsMenu` | Submenus | ✅ | Sub-menus in Find/Help for Apps/Categories/etc. |

### Other (17)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `anniversariesTable` | Anniversaries Table | | Sortable/filterable anniversaries |
| `categoryFilters` | Category Filters | ✅ | Filter category pages (unconnected, orphaned) |
| `categoryTables` | Category Table | ✅ | People-in-category sortable table |
| `connectionFinderOptions` | Connection Finder Options | ✅ | Extra features on Connection Finder |
| `countdown` | Countdown | ✅ | Live countdowns on space/project pages |
| `dnaTable` | DNA Connections Table | ✅ | Birthplaces in DNA connections |
| `enumerateImageDetail` | Enumerate Image Detail | | Sort/number image detail lists |
| `feedHelper` | Feed Helper | | Anomaly/activity checks on Activity Feed |
| `findAGraveMemorialExtractor` | Find A Grave Memorial Extractor | | CSV export of FAG cemetery memorials |
| `help` | Help | ✅ | WBE options on WBE Help page |
| `myConnections` | My Connections | ✅ | Per-degree tables of connections |
| `pendingMergesFilters` | Pending Merges Filters | ✅ | Filter pre-1500/pre-1700/not-open |
| `removeFromWatchlist` | Remove from Watchlist | ✅ | Multi-select watchlist removal |
| `surnameTable` | Search/Watchlist Table Options | | Extra columns on Search/Watchlist |
| `watchlistFilter` | Watchlist Filter | | Filter options on Watchlist |
| `wikitreePlusHelper` | WikiTree+ Query Builder | ✅ | OR-groups + AND-conditions for WT+ queries |
| `wills` | Wills and Estates | | Category page tables for wills/estates |

### Community / Debug (4)

| ID | Name | Default | Description |
|---|---|:-:|---|
| `confirmThankYous` | Confirm Thank Yous | | Confirm before sending Thank You |
| `hideMyContributions` | Hide My Contributions | | Toggle visibility of own contributions |
| `sortBadges` | Sort Badges | ✅ | Sort/hide badges on badge management page |
| `debugProfileClasses` | Debug Profile Classes | | Highlight profile page sections (for dev) |

## Integration with our workflows

### Bio Check complements `scripts/fix-evidence-quality.py`

The extension's **Bio Check** runs client-side on WT profile pages; our
`fix-evidence-quality.py` runs server-side against `tree.json`. They share
the same source-quality vocabulary (invalid-source patterns mirror Lukas's
feedback). Use them together:

1. **Server-side (tree.json)**: run `fix-evidence-quality.py --dry-run --only <bucket>`
   to audit the tree's citation database before generating bios.
2. **Client-side (WT profile)**: enable Bio Check on the profile before
   saving — it catches new violations introduced during manual editing.

The extension has a JavaScript `SourceRules` class at
`src/features/bioCheck/SourceRules.js` with 100+ invalid-source patterns.
Porting these patterns to Python is a future improvement for the `narrative`
and `other` buckets in our triage classifier.

### WikiTree+ data — `scripts/wikitree-plus-fetch.py`

The extension's **Show Suggestions** feature consumes `plus.wikitree.com`
JSON endpoints inline. Our Python helper does the same thing out-of-browser
for programmatic analysis:

```bash
python3 scripts/wikitree-plus-fetch.py
# → data/reports/wt_plus_errors_<manager>_<date>.json
```

The extension uses `appID=apiExtWbe` per `docs/CallsTo wikitree.com.md`.
Our script should use `appID=apiSvc_genealogy_cleanup` when sending requests.

### Rate limiter — `scripts/wt-rate-check.py`

The extension does NOT enforce our project's custom rate limits (50/day,
150/week, 120s min-delay, 8/30min burst). **Before every WT edit, call
`python3 scripts/wt-rate-check.py`**. The extension is purely assistive;
rate limits are our policy.

### Contribution dispatch — `scripts/wt-contribution-dispatch.py`

The extension's **Auto Bio** generates skeleton bios from tree data in the
browser. Our dispatch pipeline generates paste-ready inline-ref blocks from
`tree.json`. Use the dispatch output as the source of truth (it enforces our
citation format) and the extension's Auto Bio only for supplemental
structuring.

## Centralized vs. per-project state

All three sister projects share the same extension install: each has its
own `vendor/wikitree-be-dist/` built from the same upstream commit (update
all three together when upgrading). Each project's `scripts/chrome-cdp.sh`
has its own `USER_DATA_DIR` pointing to a distinct Chrome profile
(`/home/jerem/.cache/ms-playwright/<project>-chrome`), so they don't share
extension storage. Extension options must be configured once per
user-data-dir.

## Known quirks

- **Stable Chrome ignores `--load-extension`** — use Chromium for Testing or
  Beta/Dev. See "Install" section above.
- **Unpacked extension IDs depend on install path**, not content. Keeping
  `vendor/wikitree-be-dist/` at the same path across all three projects keeps
  the extension ID stable, so plus.wikitree.com integrations and extension-scoped
  storage stay consistent.
- **Features are opt-in**. Fresh install does nothing. Set your preferences
  once per user-data-dir via the options page.
- **CDP cookie drop on navigation** — if you `page.goto()` to a WT edit URL
  in Playwright, session cookies drop silently. Use `fetch()` from an
  already-navigated page context (the extension does this too). See
  PROVISIONAL.md "WikiTree: CDP `fetch()` works; `page.goto()` drops auth state".
- **WT account rate-limit blocks persist** (~48+ days) — see PROVISIONAL.md
  "WikiTree account blocks are durable". The extension does not bypass the
  block; all extension features go through the same authenticated session.

## References

- Upstream repo: https://github.com/wikitree/WikiTree-Browser-Extension
- WT Help:WikiTree_Plus (deprecated Trtnik ext — the current official extension is separate):
  https://www.wikitree.com/wiki/Help:WikiTree_Plus
- WT BE space page: https://www.wikitree.com/wiki/Space:WikiTree_Browser_Extension
- Chrome Web Store (stable): https://chrome.google.com/webstore/detail/wikitree-browser-extensio/ncjafpiokcjepnnlmgdaphkkjehapbln
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/wikitree-browser-extension/
- Safari (Mac + iOS): https://apps.apple.com/us/app/wikitree-browser-extension/id6447643999

## Canonical source-of-truth section

This doc is the centralized capability reference for the extension across
all three sister projects. Updates here propagate to project-level CLAUDE.md
via the existing ai-genealogy pointer pattern. If you learn something
project-specific worth noting, add to PROVISIONAL.md first; promote here
once cross-project-confirmed.
