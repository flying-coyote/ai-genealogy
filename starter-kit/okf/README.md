---
type: RefDoc
title: "OKF (Open Knowledge Format) layer — genealogy knowledge graph"
created: 2026-06-19
tags: [okf, km, knowledge-graph, starter-kit]
---

# OKF layer (Open Knowledge Format) for genealogy KM

A local-file, no-network knowledge-format discipline over the genealogy vaults, adapted from the
Second-Brain OKF layer (2026-06-19 transfer brief). Promoted here so the **one** registry is shared
across the three tree repos + this hub, parsed by one reader.

## Pieces
- `_type-registry.md` — canonical markdown `type:` values (single source of truth; the reader parses it).
- `source-field-registry.md` — canonical `tree.json` `validation.evidence.sources[]` keys + merge map.
- `okf.py` — federation-ready reader (`load_notes(roots)`); registry parsed, never duplicated.
- `okf_health.py` — coverage / drift / gaps across roots (run on a cadence).
- `okf_signals.py` — the maturation queue, **derived** from the typed graph + each tree's `tree.json`.
- `okf_source_fields.py` + `okf_source_audit.py` — source-key parser + drift audit; a defensive,
  non-blocking `validate-tree.py` warning flags non-canonical source keys.

## Configure when adopting
The reader currently hardcodes machine-local roots (`okf.py:GENEALOGY_ROOTS`) and an absolute
`REGISTRY` path — point these at your checkout. Everything is local-file + local-script; never point
a hosted-egress step (graphify Pass 2, embedding indexers, hosted vector DBs) at the PII trees.

## Baselines (2026-06-19)
Markdown graph: 95.8% typed (8,713/9,097). Source-field drift: 1.4% of 74,508 sources carry a
non-canonical key. Bridge join (journal↔tree.json): genealogy 99.6%, dry-cross 100%, kindred 78.5%.
