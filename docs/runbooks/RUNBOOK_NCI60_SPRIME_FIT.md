# Runbook — NCI-60 sprime fit

End-to-end procedure for fitting Hill curves and populating S' across the
NCI-60 dose-response panel. Two starting points are supported:

* **Fast path** — restore a Postgres dump that already has the upstream tables
  and intermediate `im_*` tables built, then just run the fit script.
* **From-scratch** — rebuild every intermediate table from the raw NCI sources,
  for full bit-level reproducibility.

The fit writes back into `im_nci_nci60_doseresp_sprime_list` (one row per curve)
and is fully resumable: the script filters `WHERE fit_run_id IS NULL`, so a
killed or restarted process picks up exactly where the last commit ended.

---

## 1. What this produces

For each eligible curve in `im_nci_nci60_doseresp_sprime_list` the following
columns are populated:

| Column | Source |
|---|---|
| `s_prime` | `math.asinh((zero_asymptote − inf_asymptote) / ec50)` |
| `ec50`, `zero_asymptote`, `inf_asymptote`, `hill_slope`, `r_squared` | `sprime.hill_fitting.fit_hill_curve` (wraps `scipy.optimize.curve_fit`) |
| `fit_status` | `'ok'`, `'failed'`, or `'skipped'` |
| `fit_warnings` | `"ExceptionClass: message"` when the worker caught an exception, else `NULL` |
| `sprime_version` | installed via `infra/requirements.txt` (unpinned — always latest) |
| `fit_run_id` | tag for this run (uuid by default; settable via `--run-id`) |
| `fit_at` | UTC timestamp of the UPDATE |

"Eligible" = `load_eligible = TRUE`, which is set at table-build time to
`COUNT(valid points) >= 4`. See
`scripts/build_nci60_doseresp_sprime_list.sql`.

Approximate scale at time of writing: **4,832,820 eligible curves**.

---

## 2. Prerequisites

* Docker Desktop on Windows, or Docker Engine on Linux.
* ~50 GB free disk (Postgres data volume + working space).
* 16+ CPU cores recommended; the script defaults to `nproc − 2` workers.
* Repo checked out to `C:\Users\enact\Projects\nf_streamlit` on Windows
  (the path that the compose file bind-mounts into `/workspace`). On a Linux
  server, update the `volumes:` paths in `infra/docker-compose.yml`.
* `data/NSC_Compounds/*.csv` present locally only if you intend the
  from-scratch build (Section 6). The fast path doesn't need them — the
  Postgres dump already contains the loaded tables.

---

## 3. Fast path — restore dump and run the fit

### 3.1 Restore the Postgres dump

```bash
# Bring up postgres on its named volume
docker compose -f infra/docker-compose.yml up -d postgres

# Restore (custom-format dump assumed; adjust path)
docker exec -i nf_streamlit_postgres \
    pg_restore -U comp_bio_u2 -d data_warehouse \
    --no-owner --no-privileges \
    < /path/to/data_warehouse.dump
```

### 3.2 Build the tools image

```bash
docker compose -f infra/docker-compose.yml --profile tools build tools
```

### 3.3 Sanity-check the schema

The dump should contain everything below. If anything is missing, jump to
the relevant from-scratch step (Section 6) before continuing.

```sql
-- Required source tables
SELECT count(*) FROM raw_nci_nci60_doseresp;          -- ~24.5M
SELECT count(*) FROM im_nci_nsc_compounds;            -- ~332k
SELECT count(*) FROM im_nci_nci60_doseresp_sprime_list;  -- ~4.86M

-- Required fit columns on the list table
SELECT column_name FROM information_schema.columns
 WHERE table_name = 'im_nci_nci60_doseresp_sprime_list'
   AND column_name IN ('curve_id','s_prime','ec50','fit_status','fit_run_id');
```

### 3.4 Run the fit

```bash
mkdir -p logs
docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
    python scripts/run_sprime_fit.py --batch-size 5000 --workers 12 \
    > logs/sprime_fit.log 2>&1 &
```

Observed throughput on a 16-core host: ~130 rows/sec sustained → roughly
**10 hours of wall** for a full run on 4.83M curves. Run it overnight or on
a 24-hour server.

### 3.5 Watch progress

```bash
# Tail the log
tail -f logs/sprime_fit.log

# Live DB progress
docker exec -i nf_streamlit_postgres psql -U comp_bio_u2 data_warehouse <<'SQL'
SELECT
  count(*) FILTER (WHERE fit_run_id IS NOT NULL)              AS done,
  count(*) FILTER (WHERE load_eligible AND fit_run_id IS NULL) AS remaining,
  100.0 * count(*) FILTER (WHERE fit_run_id IS NOT NULL)
      / NULLIF(count(*) FILTER (WHERE load_eligible), 0)      AS pct_done
FROM im_nci_nci60_doseresp_sprime_list;
SQL
```

### 3.6 Verify results

```sql
-- Per-status counts
SELECT fit_status, count(*) FROM im_nci_nci60_doseresp_sprime_list
 WHERE fit_run_id IS NOT NULL GROUP BY fit_status;

-- Distribution of fit quality
SELECT
  count(*) FILTER (WHERE r_squared >= 0.9)               AS r2_ge_09,
  count(*) FILTER (WHERE r_squared >= 0.7 AND r_squared < 0.9) AS r2_07_09,
  count(*) FILTER (WHERE r_squared < 0.7)                AS r2_lt_07
FROM im_nci_nci60_doseresp_sprime_list WHERE fit_status = 'ok';

-- Spot-check a known drug (5-fluorouracil = NSC 19893)
SELECT cell_line, round(s_prime::numeric,3) AS s_prime,
       round(ec50::numeric,3) AS ec50_uM,
       round(r_squared::numeric,3) AS r2
FROM im_nci_nci60_doseresp_sprime_list
WHERE nsc = '19893' AND fit_status = 'ok'
ORDER BY cell_line LIMIT 10;
```

---

## 4. Scientific decisions baked into the pipeline

These are the parameters you should *not* change without recording the
reason. They are all enforced inside `scripts/run_sprime_fit.py`.

### 4.1 sprime configuration

```python
values_as = "list"                                  # one row per curve
skip_control_response_normalization = True          # see 4.2
response_normalization = "asymptote_normalized"     # label-only when skip=True
```

### 4.2 Why `skip_control_response_normalization = True`

NCI-60 DOSERESP ships no per-curve DMSO / vehicle reading. The `average_ptc`
values used as responses are already T₀/control-normalized upstream
("Percent T/C"). Sprime's `pipeline_asymptote_normalized` divides raw
responses by `Control_Response`; with no `Control_Response` available, that
step cannot run. Setting `skip=True` is correct semantically — re-normalizing
already-normalized data would double-count the control.

With `skip=True`, the `response_normalization` setting is documentation
only — the Hill fit consumes PTC values unmodified. The *fitted* asymptotes
end up as inputs to S', which is the "asymptote-normalized" property in
effect.

### 4.3 Hill fitter and S' formula

```python
hp = sprime.hill_fitting.fit_hill_curve(concentrations, responses)
s_prime = math.asinh((hp.zero_asymptote - hp.inf_asymptote) / hp.ec50)
```

These two calls match what
`SPrime.load() + RawDataset.to_screening_dataset()` would do internally;
they're reached directly so that a `multiprocessing.Pool` can drive them.

### 4.4 Compound name preference (for display only)

Picked in `scripts/build_nci_nsc_compounds.sql`:

```
COMMON > USAN > TRADE > VAN > GENERAL > 8CI 9CI > 9CI > 8CI > anything else
```

Fallback when no chemical name exists:

1. `pubchem_sid_{sid}` from `raw_nci_nsc_sid_cid`
2. `NSC-{nsc}` last resort (covers the ~0.2% of NSCs lacking even a SID)

The fit script joins this table only so log/debug output has a human name;
**no fit parameter depends on the name**.

### 4.5 Why grain includes `panel_number`

`cell_number` is **not** globally unique across NCI panels. The curve grain
is `(expid, nsc, prefix, panel_number, cell_number)`. See the build SQL.

### 4.6 Concentration source

`raw_nci_nci60_doseresp.concentration` (log₁₀ M, per dilution row), **not**
`log_hi_concentration` (constant per curve). Converted to linear µM via
`10^(concentration + 6)` inside the build SQL.

---

## 5. Resumability and crash recovery

* Each batch is fetched → fit → `UPDATE` → committed before the next batch
  starts. Crash loss is bounded by `--batch-size` rows.
* `fetch_rows` filters `WHERE load_eligible AND fit_run_id IS NULL`. Re-run
  the script to pick up wherever the last commit landed; rows already tagged
  with any `fit_run_id` are skipped.
* If you want to **re-fit** rows from a specific past run (e.g. after a bug
  fix), null them out first:
  ```sql
  UPDATE im_nci_nci60_doseresp_sprime_list
     SET fit_run_id = NULL, fit_status = NULL, fit_at = NULL,
         s_prime = NULL, ec50 = NULL, zero_asymptote = NULL,
         inf_asymptote = NULL, hill_slope = NULL, r_squared = NULL,
         fit_warnings = NULL, sprime_version = NULL
   WHERE fit_run_id = 'pilot-XXXXXXXX';
  ```

---

## 6. From-scratch build (full reproducibility)

Use this when you do **not** have a dump and want to rebuild every
intermediate table from raw sources.

### Inputs

* `raw_nci_nci60_doseresp` already loaded from NCI's DTP/CellMiner dose-
  response export (out of scope for this runbook — see
  `GMM/docs-for-ai/notes-on-nci-datasource.md`).
* `data/NSC_Compounds/` containing the five NCI compound metadata files:
  * `nsc_cas.csv`
  * `nsc_chemical_names.csv` *(has 117 stray `0xbf` bytes in 57 rows —
    pre-cleaned in step 6.2)*
  * `nsc_mw_mf.csv`
  * `nsc_sid_cid.csv`
  * `nsc_smiles.csv`

### 6.1 Build the dose-response sprime list

```bash
docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
    psql -h postgres -U comp_bio_u2 data_warehouse \
    -f scripts/build_nci60_doseresp_sprime_list.sql
```

Produces `im_nci_nci60_doseresp_sprime_list` (~4.86M curves; ~4.83M
`load_eligible = TRUE`).

### 6.2 Clean and load NSC compound metadata

```bash
# 6.2a Heuristic substitution for the ¿ (U+00BF) bytes in nsc_chemical_names
docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
    python scripts/clean_nsc_chemical_names.py
# -> writes data/NSC_Compounds/nsc_chemical_names.cleaned.csv
# Substitution rule: digit (ws?) BF (ws?) digit -> right arrow (glycoside
# linkage), every other BF -> ASCII apostrophe (prime). Original character
# was lost upstream; PubChem SID is the authoritative compound reference.
```

```bash
# 6.2b Load all five files
docker compose -f infra/docker-compose.yml --profile tools run --rm tools bash -c '
  cfg=infra/config.docker.yaml
  for pair in \
    nsc_cas.csv:raw_nci_nsc_cas \
    nsc_chemical_names.cleaned.csv:raw_nci_nsc_chemical_names \
    nsc_mw_mf.csv:raw_nci_nsc_mw_mf \
    nsc_sid_cid.csv:raw_nci_nsc_sid_cid \
    nsc_smiles.csv:raw_nci_nsc_smiles
  do
    f=${pair%%:*}; t=${pair##*:}
    python scripts/csv_to_datawarehouse.py "data/NSC_Compounds/$f" "$t" --config "$cfg"
  done'
```

### 6.3 Build the compound reference table

```bash
docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
    psql -h postgres -U comp_bio_u2 data_warehouse \
    -f scripts/build_nci_nsc_compounds.sql
```

Produces `im_nci_nsc_compounds`: one row per NSC with `preferred_name`,
`compound_name` (with pubchem/NSC fallback), plus pass-through `cas`, `mw`,
`mf`, `pubchem_sid`, `pubchem_cid`, `smiles`.

### 6.4 Add fit columns to the list table

```bash
docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
    psql -h postgres -U comp_bio_u2 data_warehouse \
    -f scripts/alter_sprime_list_add_fit_columns.sql
```

Adds `curve_id BIGSERIAL` and the 11 fit columns. Idempotent.

### 6.5 Run the fit

Same as **3.4**.

---

## 7. Producing a fresh dump for hand-off

Run on the source host once a fit completes:

```bash
docker exec nf_streamlit_postgres \
    pg_dump -U comp_bio_u2 -Fc --no-owner --no-privileges data_warehouse \
    > data_warehouse_$(date +%Y%m%d).dump
```

Custom format (`-Fc`) compresses and supports parallel restore.

---

## 8. File index (everything this runbook touches)

| Path | Role |
|---|---|
| `infra/Dockerfile` | Single Python 3.11-slim image used by both `tools` and `streamlit` services |
| `infra/requirements.txt` | `sprime`, `tqdm`, `pyyaml` (rest reused from `app/requirements.txt`) |
| `infra/docker-compose.yml` | `postgres`, `tools` (profile=tools), `streamlit` (profile=app) |
| `infra/config.docker.yaml` | DB config used inside the container (host = `postgres`) |
| `scripts/config.yaml` | DB config used from the host (host = `localhost`) |
| `scripts/csv_to_datawarehouse.py` | Generic CSV → Postgres bulk loader (`COPY`) |
| `scripts/clean_nsc_chemical_names.py` | One-shot `0xbf` cleanup for `nsc_chemical_names.csv` |
| `scripts/build_nci60_doseresp_sprime_list.sql` | Reshape raw doseresp into one-row-per-curve list |
| `scripts/build_nci_nsc_compounds.sql` | Union of 5 raw NSC tables → one row per NSC with preferred name |
| `scripts/alter_sprime_list_add_fit_columns.sql` | Add `curve_id` + fit-result columns to the list table |
| `scripts/run_sprime_fit.py` | The fit driver (multiprocessing, batched, resumable) |
| `RUNBOOK_NCI60_SPRIME_FIT.md` | This document |
| `NCI60_DOSERESP_SPRIME_LIST_SCHEMA_REFERENCE.md` | Full schema of the list table |
| `NCI60_DOSERESP_SCHEMA_REFERENCE.md` | Full schema of the upstream `raw_nci_nci60_doseresp` |

---

**Last updated:** 2026-06-01
