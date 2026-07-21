# Plan: Project Restructuring + Kestra Formalization
_Written: 2026-06-07 | Branch: feature/NCI60_

---

## Decisions Captured

| Decision | Answer |
|---|---|
| Rename scripts/? | No — keep `scripts/`. Migrate pipeline scripts into `kestra/scripts/` progressively, then archive/delete originals |
| Kestra script ownership | Kestra gets its own copies under `kestra/scripts/` as flows are authored |
| GMM/ fate | Move to `analysis/GMM/` — per-file review required before committing |
| SPRIME debug docs | Resolved. Delete row-traces + big bug report. Leave one brief historical note. sprime 0.3.0 requires full S' recompute via Kestra |
| Docker location | Move to `infra/` (or inside NCI60 workstream area — decision deferred to this commit) |
| Commit style | One big organized commit for all moves |

---

## Three Workstreams

This repo serves three distinct workstreams. Every file belongs to one:

1. **Streamlit app** — `app/` (unchanged)
2. **Data ETL pipeline** — Kestra + scripts (formalizing now)
3. **Documentation** — `docs/` (schema refs, runbooks, investigations)

Scripts in `scripts/` must be categorized as either ETL-pipeline (→ eventually `kestra/scripts/`) or Streamlit-support (→ stay in `scripts/` or move to `app/`).

---

## Target Directory Structure (post-commit)

```
/projects/nf_streamlit/
│
├── app/                              # Workstream 1: Streamlit app (no changes)
│   ├── Home.py
│   ├── pages/
│   │   ├── Delta_S_Prime.py
│   │   └── MIPE_3_0.py
│   ├── services/csv_manager.py
│   ├── utils/database_connection.py
│   └── views/data.py
│
├── analysis/                         # Research & exploration
│   ├── dbscan_clustering/            # (existing, no change)
│   └── GMM/                          # MOVED from root GMM/ — see per-file review below
│       ├── docs-for-ai/              # planning .md notes kept; PDFs → gitignored
│       ├── reference/GMM-Initial/    # pilot work (script.py, myfilename.csv, NOTES.txt)
│       └── glossary.md, notes-on-GMM.md, thoughts-on-gmm.md, *.png
│       # NOTE: reference/sprime/ inside GMM → DELETE (dup of references/sprime/)
│
├── docs/                             # Workstream 3: Documentation
│   ├── schema/                       # all *_SCHEMA_REFERENCE.md files
│   │   ├── CHEMBL37_SCHEMA_REFERENCE.md          (MOVED from root)
│   │   ├── NCI60_DOSERESP_SCHEMA_REFERENCE.md    (MOVED from root)
│   │   ├── NCI60_DOSERESP_SPRIME_LIST_SCHEMA_REFERENCE.md  (MOVED)
│   │   ├── NCI60_DTP_ZSCORE_SCHEMA_REFERENCE.md  (MOVED from root)
│   │   ├── im_omics_genes_schema_report.md       (MOVED from root)
│   │   └── [existing: DATABASE_SCHEMA_REFERENCE.md, GUIDE2PHARMA_SCHEMA_REFERENCE.md, etc.]
│   ├── runbooks/
│   │   └── RUNBOOK_NCI60_SPRIME_FIT.md           (MOVED from root)
│   ├── sessions/
│   │   └── SESSION_2026-06-01_NOTES.md           (MOVED from root)
│   └── investigations/
│       └── SPRIME_SIGN_CONVENTION_HISTORICAL_NOTE.md   (NEW — brief, replaces 3 files)
│       # DELETED: SPRIME_SIGN_CONVENTION_BUG_REPORT.md (42 KB)
│       # DELETED: SPRIME_ROW_TRACE.md
│       # DELETED: SPRIME_ROW_TRACE_curve26.md
│
├── infra/                            # NEW — local postgres dev environment
│   ├── Dockerfile                    # MOVED from scripts/ (update: sprime 0.3.0)
│   ├── docker-compose.yml            # MOVED from scripts/
│   ├── config.docker.yaml            # MOVED from scripts/
│   ├── config.yaml.example           # MOVED from scripts/
│   ├── requirements.txt              # MOVED from scripts/ (update: sprime→0.3.0)
│   └── create_readonly_role.sql      # MOVED from scripts/ (DB bootstrap, not pipeline)
│
├── kestra/                           # Workstream 2: ETL pipeline orchestration
│   ├── README.md                     # (existing — comprehensive guide)
│   ├── flows/
│   │   ├── infrastructure/
│   │   │   └── sync_git.yml          # FIX: deprecated trigger type + rotate webhook key
│   │   ├── example/
│   │   │   └── hello_world.yml       # FIX: malformed trigger block
│   │   └── nci60/                    # TO BE AUTHORED (see flow plan below)
│   │       ├── 01_load_raw_data.yml
│   │       ├── 02_build_tables.yml
│   │       ├── 03_run_sprime_fit.yml
│   │       ├── 04_build_cell_xref.yml
│   │       └── 05_enrich_compounds.yml
│   └── scripts/                      # ETL scripts (OWN copies, referenced by flows)
│       ├── run_sprime_fit.py         # COPY from scripts/ — sprime 0.3.0 target
│       ├── csv_to_datawarehouse.py   # COPY from scripts/
│       ├── build_cellosaurus_nci60_bridge.py  # COPY
│       ├── extract_cellosaurus_celllines.py   # COPY
│       ├── convert_nci60_zscore_xlsx.py       # COPY
│       ├── clean_nsc_chemical_names.py        # COPY
│       ├── enrich_chembl_compounds.py         # COPY
│       ├── pubchem_enrich.py                  # COPY
│       └── sql/
│           ├── build_nci60_doseresp_sprime_list.sql
│           ├── build_nci_nsc_compounds.sql
│           ├── build_nci_cell_line_xref.sql
│           └── alter_sprime_list_add_fit_columns.sql
│
├── scripts/                          # KEEP — rationalize but don't rename
│   │   # Pipeline scripts: COPIED to kestra/scripts/ above; originals archived after flows work
│   │   # Streamlit-support: mcp-toolbox.sh/.bat, deployment.sh — stay here
│   │   # Utility: csv_compare_and_combine.py — stays here
│   │   # test_upload.csv → DELETE (57 B smoke test, disposable)
│   ├── mcp-toolbox.sh                # (keep — Streamlit/MCP support)
│   ├── mcp-toolbox.bat               # (keep — Streamlit/MCP support)
│   ├── deployment.sh                 # (keep — Streamlit deployment)
│   ├── csv_compare_and_combine.py    # (keep — general utility)
│   └── average_delta_s_prime.py     # (MOVE from root — pairs with its CSV)
│   # Archive candidates (after kestra/scripts/ copies are working):
│   #   run_sprime_fit.py, csv_to_datawarehouse.py, build_cellosaurus_nci60_bridge.py,
│   #   extract_cellosaurus_celllines.py, convert_nci60_zscore_xlsx.py,
│   #   clean_nsc_chemical_names.py, enrich_chembl_compounds.py, pubchem_enrich.py,
│   #   all .sql files
│
├── data/                             # gitignored, 3 GB (no change)
├── logs/                             # gitignored — ADD to .gitignore (currently missing!)
├── references/                       # vendored repos (gitignored)
├── README.md                         # Update paths after moves
├── tools.yaml.example
└── .gitignore                        # ADD: logs/, infra/config.yaml, scripts/config.yaml
```

---

## GMM/ Per-File Review (required before moving)

The 33 MB GMM/ directory needs a per-file decision before moving to analysis/GMM/:

| File/Dir | Action | Reason |
|---|---|---|
| `glossary.md` (14 KB) | KEEP → `analysis/GMM/` | Useful ML/biotech terminology |
| `notes-on-GMM.md` (4.2 KB) | KEEP → `analysis/GMM/` | Design notes |
| `thoughts-on-gmm.md` (176 B) | KEEP → `analysis/GMM/` | Scratch notes |
| `docs-for-ai/*.md` | KEEP → `analysis/GMM/docs-for-ai/` | Planning docs, articles |
| `docs-for-ai/PDFs/` (7 papers) | GITIGNORE → `analysis/GMM/docs-for-ai/PDFs/` | Binary, heavy |
| `docs-for-ai/text-articles/` | KEEP or GITIGNORE | Text versions of PDFs |
| `docs-for-ai/example-script.py` | KEEP | Reference code |
| `reference/GMM-Initial/` | KEEP → `analysis/GMM/reference/GMM-Initial/` | Pilot work |
| `reference/sprime/` | **DELETE** | Duplicate of `references/sprime/` (154 MB) |
| `*.png` (3 images) | KEEP → `analysis/GMM/` | Visualizations |

---

## .gitignore Additions Required

```gitignore
# Runtime logs (already treated as gitignored but not listed)
logs/

# Local config with credentials (if not already)
scripts/config.yaml
infra/config.yaml

# GMM research assets (heavy binaries)
analysis/GMM/docs-for-ai/PDFs/
analysis/GMM/reference/sprime/

# Test artifacts
scripts/test_upload.csv
```

---

## Files to DELETE (no historical value)

| File | Size | Reason |
|---|---|---|
| `scripts/test_upload.csv` | 57 B | Smoke test fixture |
| `SPRIME_SIGN_CONVENTION_BUG_REPORT.md` | 42.9 KB | Bug resolved; replace with brief note |
| `SPRIME_ROW_TRACE.md` | ? | Too granular; resolved with sprime 0.3.0 upgrade |
| `SPRIME_ROW_TRACE_curve26.md` | ? | Same |
| `GMM/reference/sprime/` | ~154 MB | Duplicate of `references/sprime/` |

Brief replacement for the three SPRIME files → `docs/investigations/SPRIME_SIGN_CONVENTION_HISTORICAL_NOTE.md`:
> S' sign convention bug was investigated June 2026. Root cause: sprime <0.3.0 had incorrect sign handling for certain Hill curve fits. Resolution: upgrade to sprime 0.3.0 and recompute all S' values (planned as a full Kestra pipeline run). Detailed traces were recorded but removed as they're superseded by the library fix.

---

## Kestra Formalization — NCI60 Flow Plan

The NCI60 pipeline maps to these Kestra flows (namespace: `prod.nci60`):

### Flow 01: Load Raw Data
- Task: `io.kestra.plugin.scripts.python.Script` → `kestra/scripts/csv_to_datawarehouse.py`
- Input: NCI60 dose-response CSV, Z-score XLSX, NSC compound CSVs, Cellosaurus FTP
- Output: raw tables in postgres

### Flow 02: Build Tables (SQL transforms)
- Task: `io.kestra.plugin.jdbc.postgresql.Query` (×4, sequential)
  1. `build_nci60_doseresp_sprime_list.sql` → reshape to one-row-per-curve
  2. `alter_sprime_list_add_fit_columns.sql` → add fit columns (idempotent)
  3. `build_nci_nsc_compounds.sql` → compound reference
  4. `build_nci_cell_line_xref.sql` → cell line cross-reference

### Flow 03: Run Sprime Fit
- Task: `io.kestra.plugin.scripts.python.Script` → `kestra/scripts/run_sprime_fit.py`
- **Critical**: upgrade to sprime 0.3.0 (current is 0.2.2 — S' values invalid)
- Resumable: `WHERE fit_run_id IS NULL` filter — safe to re-trigger
- Scale: ~4.83M curves, ~10 hours wall at 130 rows/sec (12 workers)

### Flow 04: Build Cell Line XRef
- Task: Python → `kestra/scripts/build_cellosaurus_nci60_bridge.py`
- Then SQL: cell line cross-reference build

### Flow 05: Enrich Compounds
- Task: Python → `kestra/scripts/enrich_chembl_compounds.py`, `pubchem_enrich.py`
- ChEMBL 37 + PubChem CID/SID enrichment

### Kestra Infrastructure Fixes (pre-authoring nci60 flows)
1. Fix `sync_git.yml`: deprecated trigger type `io.kestra.core.models.triggers.types.Webhook` → current plugin path
2. Rotate webhook key `GoKeyGo432L` → use Kestra secrets
3. Fix `hello_world.yml`: malformed trigger block
4. Reconcile duplicate sync flows (kestra README mentions two — pick one)

---

## Implementation Sequence (one big commit)

### Phase 1: Deletes + gitignore ✅ DONE
1. ~~Delete `scripts/test_upload.csv`~~ done
2. ~~Delete `SPRIME_SIGN_CONVENTION_BUG_REPORT.md`, `SPRIME_ROW_TRACE.md`, `SPRIME_ROW_TRACE_curve26.md`~~ done
3. ~~Delete `GMM/reference/sprime/`~~ done (was 1.5 MB nested clone, not 154 MB — plan had wrong size)
4. ~~Update `.gitignore`~~ done: added `logs/`, `GMM/docs-for-ai/PDFs/`, `GMM/reference/`, `infra/config.yaml`
   - Note: paths corrected — GMM moves happen in Phase 3, so gitignore uses `GMM/` paths not `analysis/GMM/`

### Phase 2: Docs reorganization ✅ DONE
1. ~~Create `docs/schema/`~~ done — moved 7 schema refs (5 from root + 2 already in docs/)
2. ~~Create `docs/runbooks/`~~ done — moved `RUNBOOK_NCI60_SPRIME_FIT.md`
3. ~~`docs/sessions/`~~ DELETED instead — session notes are internal dev journals, not appropriate for a public repo; `docs/sessions/` gitignored
4. ~~Create `docs/investigations/SPRIME_SIGN_CONVENTION_HISTORICAL_NOTE.md`~~ done
5. Fixed stale link in `kestra/README.md` → `../docs/runbooks/RUNBOOK_NCI60_SPRIME_FIT.md`
6. Note: `GMM/docs-for-ai/*.md` have stale schema links — will fix in Phase 3 when GMM moves

### Phase 3: Research consolidation ✅ DONE
1. ~~Move `GMM/` → `analysis/GMM/`~~ done — `GMM/reference/sprime/` already gone from Phase 1; fixed stale `../../` relative links in 3 docs-for-ai files; updated `.gitignore` paths from `GMM/` to `analysis/GMM/`

### Phase 4: Infra extraction ✅ DONE
1. ~~Create `infra/`~~ done
2. ~~Move Docker/infra files from `scripts/`~~ done — Dockerfile, docker-compose.yml, config.docker.yaml, config.yaml.example, requirements.txt, create_readonly_role.sql all moved to `infra/`
3. ~~sprime version bump~~ CHANGED per user: kept `sprime` unpinned (always latest); Opus noted no pin existed anyway — 0.2.2 was only in comments
4. Fixed all `scripts/docker-compose.yml` / `scripts/Dockerfile` / `scripts/requirements.txt` references → `infra/` across runbook, fit script, GMM docs, schema refs

### Phase 5: scripts/ rationalize ✅ DONE
1. ~~Move `average_delta_s_prime.py`~~ deleted (orphan, no paired CSV)
2. Confirmed stays: `mcp-toolbox.sh`, `mcp-toolbox.bat`, `deployment.sh`, `csv_compare_and_combine.py`
3. ~~Write `scripts/README.md`~~ done — three-category table (pipeline/streamlit-support/utilities)

### Phase 6: Kestra infra fixes ✅ DONE
1. ~~Fix `sync_git.yml`~~ done — trigger type updated to `io.kestra.plugin.core.trigger.Webhook`; key replaced with `{{ secret('WEBHOOK_KEY') }}`; **GitHub webhook key still needs rotation** (GoKeyGo432L is in public git history)
2. ~~Fix `hello_world.yml`~~ not needed — no malformed trigger on disk; Opus confirmed this was stale docs
3. Reconciled stale "Known issues" section in `kestra/README.md`

### Phase 7: README updates ✅ DONE
1. ~~Update root `README.md`~~ done — layout table updated with `infra/`, `docs/schema/`, `docs/runbooks/`, `docs/investigations/`, `analysis/GMM/`

### Phase 8: Kestra scripts setup (pipeline copies)
1. Create `kestra/scripts/` and `kestra/scripts/sql/`
2. Copy ETL pipeline scripts from `scripts/` → `kestra/scripts/`
3. Copy SQL build scripts from `scripts/` → `kestra/scripts/sql/`

### Phase 9: Prepare for commit
1. Run `git status` and `git diff` — review everything staged vs unstaged
2. Stage all intended files (`git add`)
3. Run final checks: no credentials, no large binaries, no stale paths
4. Present a draft commit message for user to review and run

---

## sprime 0.3.0 Upgrade Note

All previously computed S' values (270,400 curves fit under 0.2.2) are **invalid** due to sign convention bug. The full Kestra pipeline run will recompute all ~4.83M curves from scratch. `alter_sprime_list_add_fit_columns.sql` is idempotent — a `TRUNCATE` of fit results + re-run is the cleanest path.

The Kestra flow for sprime fit should include:
- `WHERE fit_run_id IS NULL` filter (resumable)
- `sprime_version` column to track which version computed each row
- A pre-flight check that the installed sprime version is 0.3.0+

---

## Open Questions (deferred)

1. **Where exactly does Kestra run?** — Not yet live; need to confirm target host before authoring `prod.nci60` flows
2. **Cellosaurus 38 unmatched cell lines** — Manual curation deferred; 76.7% match rate is sufficient for initial run
3. **Heuristic columns** (`common_name`, `compound_class` on sprime list) — Drop, rename `_v0_heuristic`, or replace with PubChem? Deferred to post-fit review
4. **GMM text-articles/**: keep or gitignore? Light enough to track but not sure if needed
