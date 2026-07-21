# NCI-60 S' Pipeline — Implementation Plan

Working document for the `feature/NCI60` branch. Target output:
`public.im_nci_nci60_doseresp_sprime_list` in the `data_warehouse` PostgreSQL DB.

> **Architectural rule (do not violate):** Kestra flows are the canonical,
> reproducible implementation. All logic lives in `kestra/scripts/` (Python) and
> `kestra/scripts/sql/` (psql). Flows clone the repo from
> `https://github.com/mocomakers/nf_streamlit` on the worker and execute those
> scripts with warehouse credentials from Kestra secrets (`PG_HOST`, `PG_PORT`,
> `PG_USER`, `PG_DATABASE`, `PG_PASSWORD`, `PG_SSLMODE`). Local DB access is for
> investigation/scoping only — never the path of record. Anything run locally to
> scope a change must be folded back into a script and flow before it counts as done.

---

## 1. Objective

Produce a clean, queryable, scientifically-valued NCI-60 dose-response table with one
row per dose-response **curve** (`curve_id` surrogate PK; grain = `expid × nsc ×
prefix × panel_number × cell_number`). The table reshapes the 24.5M-row long-format
`raw_nci_nci60_doseresp` into ~4.86M curve rows carrying dose-ordered concentration
and response CSV strings. The two deliverables: (1) cell-line identity resolved to
DepMap `depmap_ach` for omics/mutation joins; (2) a fitted Hill curve per eligible
curve yielding `s_prime` and four Hill parameters. S' is the primary scientific
product — input to downstream GMM clustering and delta-S' analyses. All other
enrichment (names, ChEMBL, Cellosaurus) is lower priority.

---

## 2. Data lineage / traceability

Every transform step must preserve a clear audit trail from raw CSV to final S' value.

```
Google Drive (NCI-60 CSVs)
  └─ 00_download_datasets.yml
       └─ /datasets/nf-streamlit/  (host cache, persistent)
            └─ 01_load_raw_data.yml  (load_nci60_raw.py)
                 └─ raw_nci_nci60_doseresp        (24.5M rows, long format)
                    raw_nci_nsc_cas / _mw_mf / _smiles / _sid_cid / _names
                         └─ 02_build_nci60_tables.yml  (SQL transforms)
                              └─ im_nci_nci60_doseresp_sprime_list  (~4.86M curve rows)
                                 im_nci_nsc_compounds                (compound metadata)
                                      └─ 03_build_cell_xref.yml
                                           ├─ im_nci_cell_line_xref  (cell-line identity)
                                           └─ + merge_depmap_ach_into_sprime_list.sql
                                                └─ depmap_ach, cvcl_id columns populated
                                                     └─ 04_run_sprime_fit.yml
                                                          └─ s_prime, ec50, zero_asymptote,
                                                             inf_asymptote, hill_slope,
                                                             r_squared, fit_status, fit_run_id
```

### Traceability columns on `im_nci_nci60_doseresp_sprime_list`

| Column | Traces to |
|--------|-----------|
| `curve_id` | surrogate PK; stable across re-builds |
| `expid` | raw `expid` from `raw_nci_nci60_doseresp` |
| `nsc` | raw NSC compound identifier |
| `prefix` | raw `prefix` (experiment type) |
| `panel_number`, `cell_number` | raw cell-line position identifiers |
| `cell_line` | raw `cellname` |
| `concentration_unit_raw` | raw `concentration_unit` before conversion |
| `concentrations_umolar` | derived: `10^(raw_concentration + 6)` |
| `responses_ptc` | raw `average_ptc` (percent-of-control), dose-ordered |
| `depmap_ach` | from `im_nci_cell_line_xref.depmap_ach` via `cell_line = cell_name` |
| `cvcl_id` | from `im_nci_cell_line_xref.cvcl_id` (same join, free) |
| `fit_run_id` | UUID of the `04_run_sprime_fit` execution that wrote the fit |
| `sprime_version` | `sprime.__version__` at fit time |
| `fit_at` | timestamp when the fit was written |

### Column naming — unit-explicit names

The current schema uses generic names (`concentrations`, `responses`) that hide
units. The plan adopts **unit-explicit names** throughout:

| Current name        | Proposed name           | Unit / note |
|---------------------|-------------------------|-------------|
| `concentrations`    | `concentrations_umolar` | linear µM (10^(log10M + 6)) |
| `responses`         | `responses_ptc`         | percent-of-control (PTC) |

These names must be consistent across:
- Build SQL in `kestra/scripts/sql/` (SELECT aliases and table DDL)
- `run_sprime_fit.py` (column fetch in `fetch_rows()`)
- Any verify queries in flows
- Schema report `docs/schema/im_omics_genes_schema_report.md`

If the column rename touches the live table (i.e., table was already built with old
names), the migration SQL is:

```sql
ALTER TABLE im_nci_nci60_doseresp_sprime_list
    RENAME COLUMN concentrations TO concentrations_umolar;
ALTER TABLE im_nci_nci60_doseresp_sprime_list
    RENAME COLUMN responses TO responses_ptc;
```

Run via psql in `02_build_nci60_tables.yml`'s rebuild task, or as a one-time
migration script if the table is already loaded. Investigate current column names
before committing (Q1).

---

## 3. Cleanup task (must land before Stage 1)

`kestra/flows/nci60/01_load_raw_data.yml` lines 77–90 carry a `beforeCommands`
heredoc that patches `load_nci60_raw.py` at runtime. **The fix is already correct in
the committed script** (lines 229–235: `elif skip_download:` filters `missing` down
to `required` entries). The patch is now a no-op that prints `PATCH FAILED`.

**Action:**

1. Delete the heredoc step (lines 77–90) from `01_load_raw_data.yml`. Keep the two
   preceding `beforeCommands` lines (apt-get; pip install).
2. No script change needed — `load_nci60_raw.py` is already correct.
3. Commit:
   - `kestra/flows/nci60/01_load_raw_data.yml`
   - `kestra/scripts/load_nci60_raw.py` (confirm clean)
   - Any other locally-modified files ready to commit
   - Message: `nci60: remove runtime patch hack; skip_download fix is canonical in script`

**Acceptance:** `grep -n PYEOF kestra/flows/nci60/01_load_raw_data.yml` returns
nothing. `--skip-download` with required CSV absent → exit 1; with optional only
absent → exit 0.

---

## 4. Stage 1 — Core List Consolidation

**Goal:** clean curve-level list with confirmed µM concentration units and
`depmap_ach` + `cvcl_id` populated from `im_nci_cell_line_xref`.

### 4a. Units — verify and rename

Build SQL already converts: `10^(concentration + 6)` → linear µM. **Action:** rename
the column from `concentrations` → `concentrations_umolar` and `responses` →
`responses_ptc` in the build SQL and fitter. Add a spot-check to the verify task:
a `-4.0` log10 M point must appear as `100.0` in `concentrations_umolar`.

Also add `concentration_unit_raw` (copy of the raw `concentration_unit` value before
filtering) to the list table to preserve the audit trail for any re-investigation.

### 4b. Add and populate `depmap_ach` + `cvcl_id`

Neither column currently exists on the list table. Create
`kestra/scripts/sql/merge_depmap_ach_into_sprime_list.sql`:

```sql
-- Idempotent. Adds depmap_ach + cvcl_id and populates from im_nci_cell_line_xref.
-- Only fills unambiguous matches (n_matches = 1 by xref construction).
-- Safe to run before or after Stage 2 fit — preserves s_prime/fit_run_id.
ALTER TABLE im_nci_nci60_doseresp_sprime_list
    ADD COLUMN IF NOT EXISTS depmap_ach text,
    ADD COLUMN IF NOT EXISTS cvcl_id    text;

UPDATE im_nci_nci60_doseresp_sprime_list l
   SET depmap_ach = x.depmap_ach,
       cvcl_id    = x.cvcl_id
  FROM im_nci_cell_line_xref x
 WHERE x.cell_name = l.cell_line
   AND x.depmap_ach IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_nci60_sprime_list_depmap_ach
    ON im_nci_nci60_doseresp_sprime_list (depmap_ach);

CREATE INDEX IF NOT EXISTS ix_nci60_sprime_list_nsc
    ON im_nci_nci60_doseresp_sprime_list (nsc);
```

### 4c. Where it lives

Append to `kestra/flows/nci60/03_build_cell_xref.yml` as a step after the xref is
built. Add coverage check to the flow's verify query:

```sql
SELECT
  count(*)                                          AS total_curves,
  count(*) FILTER (WHERE depmap_ach IS NOT NULL)    AS depmap_ach_filled,
  round(100.0 * count(*) FILTER (WHERE depmap_ach IS NOT NULL) / count(*), 1)
                                                    AS depmap_ach_pct,
  count(*) FILTER (WHERE cvcl_id IS NOT NULL)       AS cvcl_id_filled
FROM im_nci_nci60_doseresp_sprime_list;
```

Dependency order: `00` → `01` → `02` → `03` (xref build + depmap merge) → `04` (fit).

### 4d. Acceptance criteria

- `depmap_ach`, `cvcl_id`, `concentrations_umolar`, `responses_ptc` columns exist.
- Coverage % recorded as new baseline (do not assume 88.9% — measure it; see Q1).
- Units spot-check passes.
- Merge script is idempotent.

---

## 5. Stage 2 — S' Fitting

**Goal:** populate `s_prime`, `ec50`, `zero_asymptote`, `inf_asymptote`,
`hill_slope`, `r_squared`, `fit_status`, `fit_warnings`, `sprime_version`,
`fit_run_id`, `fit_at` for every eligible unfit curve
(`load_eligible = TRUE AND fit_run_id IS NULL`).

Script: `kestra/scripts/run_sprime_fit.py`. Uses `sprime.hill_fitting.fit_hill_curve`
and computes `s_prime = asinh((zero_asymptote - inf_asymptote) / ec50)`.
**Do not change the fit math** — must stay bit-compatible with the reference S' data
in the reporting warehouse.

### 5a. New flow: `kestra/flows/nci60/04_run_sprime_fit.yml`

Structure: `WorkingDirectory` → `git.Clone` → `python.Commands`.

```yaml
containerImage: <tools-image-with-sprime>   # see Q2
env:
  PGHOST:     "{{ secret('PG_HOST') }}"
  PGPORT:     "{{ secret('PG_PORT') }}"
  PGUSER:     "{{ secret('PG_USER') }}"
  PGDATABASE: "{{ secret('PG_DATABASE') }}"
  PGPASSWORD: "{{ secret('PG_PASSWORD') }}"
  PGSSLMODE:  "{{ secret('PG_SSLMODE') }}"
commands:
  - cd nf_streamlit
  - python kestra/scripts/run_sprime_fit.py
      --workers {{ inputs.workers }}
      --batch-size {{ inputs.batch_size }}
      $( [ "{{ inputs.limit }}" != "0" ] && echo --limit {{ inputs.limit }} )
timeout: PT24H
retry:
  type: constant
  interval: PT5M
  maxAttempt: 2
```

Flow inputs:

| Input        | Type   | Default | Notes |
|--------------|--------|---------|-------|
| `git_branch` | STRING | `main`  | |
| `workers`    | INT    | `4`     | cap to worker CPU |
| `batch_size` | INT    | `5000`  | crash-loss window |
| `limit`      | INT    | `0`     | 0 = no limit; use 5000 for smoke test |
| `chunksize`  | INT    | `100`   | Pool.imap chunksize |

### 5b. Resumability (critical — run is many hours, interrupts expected)

`fetch_rows()` selects `WHERE load_eligible = TRUE AND fit_run_id IS NULL ORDER BY curve_id`.
Skipped/failed curves get a non-NULL `fit_run_id` — not re-fetched. **A flow retry is
idempotent.**

**Safe-resume with last-row redo:** A crash between the final `executemany` UPDATE
and its `conn.commit()` can leave the last batch uncommitted — those rows stay
`fit_run_id IS NULL` and are naturally re-fit on resume. This is already correct
behavior. To make it explicit and verifiable, `run_sprime_fit.py` should:

1. At startup, log the `MAX(curve_id) WHERE fit_run_id IS NOT NULL` (the last
   committed curve) so the operator knows exactly where the prior run stopped.
2. Optionally: null out the `fit_run_id` for the most-recently-committed batch
   (`WHERE curve_id > MAX - batch_size`) at startup before the main loop, so those
   rows are re-fit cleanly on resume (defends against partial-write edge cases).
   This "redo last batch" strategy means at most `batch_size` curves are re-computed
   on resume — a negligible cost against millions of rows.

Flow-level resume: Kestra's `retry` on the python task re-runs the script from
scratch, which is safe because of the above. For very long interrupted runs where
even the retry fails, the operator can re-trigger the flow manually — it will
continue from wherever `fit_run_id IS NULL` starts.

**Recommended `batch_size`:** 2000–5000 rows per commit. Smaller batches = more
frequent checkpoints = less redo on crash. Larger batches = fewer round-trips.
5000 is a good default; tune down to 1000 if commit latency is high.

Do not attempt multi-worker sharding in v1 (see Q3).

### 5c. Acceptance criteria

- Smoke run (`--limit 5000`) completes; `s_prime` + Hill params populated.
- Full run: `fit_run_id IS NULL AND load_eligible` drains to zero.
- Verify query reports ok/failed/skipped breakdown by `fit_status`.
- Re-run immediately after: 0 rows processed.
- Spot-check: `s_prime = asinh((zero_asymptote - inf_asymptote) / ec50)` for 5 rows.

---

## 6. Stage 3 (Later) — Downstream Enrichment

All are additive UPDATE/join passes. None block Stage 1 or 2.

### 6a. Gene-level damaging-mutation join

Source: remote read-only reporting warehouse `dmvpetridishdatastore.dev`,
`im_dep_sprime_damaging_mutations` (`cell_line` ACH, `gene_id`, `mutation_value`).
Join key: `list.depmap_ach = mut.cell_line`.

This is cross-database — cannot be a single psql join. Approach:
- New script `kestra/scripts/build_sprime_gene_mutation_join.py`: opens two
  connections, pulls mutations for the ACH set in our list, writes
  `im_nci_nci60_sprime_gene_mutations` (grain: `depmap_ach × gene_id`) to
  `data_warehouse`.
- New flow `05_join_damaging_mutations.yml`.
- Requires a separate Kestra secret set for reporting-warehouse credentials (Q4).

### 6b. `common_name` (PubChem)

Rate-limited (~3–4 hrs). Script: `kestra/scripts/pubchem_enrich.py`. Keep as a
manually-triggered flow (no schedule). Join: `im_nci_nsc_compounds.pubchem_cid →
PubChem REST → Title`.

### 6c. `cvcl_id`

Largely delivered for free in Stage 1. No further work unless ambiguous cell lines
require manual curation of `candidate_cvcls`/`candidate_names`.

### 6d. `compound_name`

If `im_nci_nsc_compounds` has a usable name column, fold into Stage 1 merge:
`UPDATE l SET compound_name = c.name FROM im_nci_nsc_compounds c WHERE c.nsc = l.nsc`.

---

## 7. Flow numbering / naming conventions

Directory: `kestra/flows/nci60/`. Two-digit ordered prefix = execution order.

| File                               | Flow id (`prod.nci60`)        | Purpose |
|------------------------------------|-------------------------------|---------|
| `00_download_datasets.yml`         | `download_nci60_datasets`     | Drive → host CSV cache |
| `01_load_raw_data.yml`             | `load_raw_nci60`              | host cache → `raw_nci_*` tables |
| `02_build_nci60_tables.yml`        | `build_nci60_tables`          | raw → list + fit cols + nsc compounds |
| `03_build_cell_xref.yml`           | `build_nci60_cell_xref`       | Cellosaurus xref + depmap_ach/cvcl_id merge |
| `04_run_sprime_fit.yml` (**new**)  | `run_sprime_fit`              | Hill fit → s_prime + params |
| `05_join_damaging_mutations.yml` (**future**) | `join_damaging_mutations` | ACH × gene mutations |

Conventions:
- `namespace: prod.nci60`, `labels: {pipeline: nci60, stage: <load|build|fit|enrich>}`.
- Every code-running flow: `WorkingDirectory` → `git.Clone` (url:
  `https://github.com/mocomakers/nf_streamlit`, branch: `{{ inputs.git_branch }}`,
  directory: `nf_streamlit`) → commands `cd nf_streamlit && ...`.
- `git_branch` input on every flow (default `main`).
- Credentials always via `{{ secret('PG_*') }}` — never inline, never local paths.
- Every flow ends with a `jdbc.postgresql.Query` verify task with baseline counts
  in the `description`.
- No `beforeCommands` source-patching. Fix the script and update the local file.
- `sprime` install: `pip install "sprime>=0.3.0"` in `beforeCommands` — not a
  prebuilt image dependency. Pin floor at 0.3.9.

## 8. Development workflow (no git commits during iteration)

**Dual-write rule:** every change goes to two places simultaneously —
the local file in `kestra/` *and* the live Kestra instance via API
(`PUT /api/v1/flows/{namespace}/{id}`). Never let them diverge.

```
Edit local file (kestra/flows/ or kestra/scripts/)
    │
    ├─► Save local file                  ← always first
    └─► PUT to Kestra API                ← immediately after
         (or psql-execute for SQL files)
```

Scripts (`kestra/scripts/`) are pulled by the flow at runtime via git clone of
the repo — so script changes require a git push to take effect in Kestra.
For **script iteration during development**, use the same `beforeCommands` inline
patch technique to test the logic live, then once stable:
1. Write the final version to the local script file.
2. Push to GitHub (the user does this, not Claude).
3. Remove the inline patch from the flow YAML; the live flow and local YAML stay identical.

**Alignment audit (pre-commit gate):**
Before the user does any `git push`, run:
```
for each file in kestra/flows/**/*.yml:
    GET /api/v1/flows/{namespace}/{id}/export
    diff local_file kestra_response
    report any divergence
```
If local files == Kestra state: `git push` is safe and what ran is exactly what gets committed. Any divergence is flagged for manual reconciliation before committing.

---

## 9. Open questions

- **Q1 — Re-measure baselines + current column names.** Run
  `SELECT column_name FROM information_schema.columns WHERE table_name = 'im_nci_nci60_doseresp_sprime_list'`
  against the live warehouse. Confirm whether columns are named `concentrations` /
  `responses` or already `concentrations_umolar` / `responses_ptc`. If the table
  exists with old names, the rename migration must run in `02_build_nci60_tables.yml`
  (idempotent `ALTER TABLE ... RENAME COLUMN IF EXISTS`). Also re-measure actual row
  count and `depmap_ach`/`s_prime` coverage — do not assume the prior figures.

- **Q2 — `sprime` install in the fit flow.** Is there a prebuilt Docker image with
  `sprime` + scipy available to the Kestra worker? If not, `04_run_sprime_fit.yml`
  must `pip install -r infra/requirements.txt` in `beforeCommands`. Memory references
  a "sprime 0.3.0 upgrade" — confirm target version and pin it for reproducibility.

- **Q3 — Single-worker throughput.** Run `--limit 5000` smoke test, read `rows/s`
  from script output, extrapolate wall-clock. Do not build horizontal sharding
  speculatively.

- **Q4 — Reporting-warehouse Kestra secrets.** Stage 3a reads
  `dmvpetridishdatastore.dev`. Confirm a separate Kestra secret set exists (distinct
  from `data_warehouse` `PG_*`). Out of scope until Stage 1/2 land.

- **Q5 — `02_build_tables.yml` current state.** Confirm it has run against the live
  warehouse, `curve_id` (bigserial) is populated, and `load_eligible` is correctly
  flagged. The fitter selects on both.

- **Q6 — depmap merge placement.** §4c recommends appending to
  `03_build_cell_xref.yml`. Confirm acceptable vs. a dedicated
  `04_consolidate` flow (which shifts the fit flow to `05`). Decide before
  numbering hardens.

- **Q7 — Dropped-unit rows.** Build SQL filters `concentration_unit = 'M'`,
  deferring `'u'`/`'V'`. Confirm how many curves are excluded and whether any are
  scientifically needed.
