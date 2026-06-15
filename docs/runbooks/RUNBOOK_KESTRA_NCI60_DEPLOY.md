# Runbook — Deploy NCI-60 pipeline on Kestra

Operational guide for loading NCI-60 raw data from the public [MoCo Makers Datasets Google Drive folder](https://drive.google.com/drive/folders/1e0_UQzU-LksJxMEN5zJRikL0QbsWrJej) into PostgreSQL at `dmvpetridishdatastore.dev`, then building intermediate tables.

**Related docs**

- [kestra/README.md](../../kestra/README.md) — flow authoring conventions, secrets, namespaces
- [kestra/docs/KESTRA_STRATEGY_AND_TECHNIQUES.md](../../kestra/docs/KESTRA_STRATEGY_AND_TECHNIQUES.md) — comprehensive learning, strategy, API/git deployment, debugging playbook
- [RUNBOOK_NCI60_SPRIME_FIT.md](RUNBOOK_NCI60_SPRIME_FIT.md) — local Docker path (same SQL/scripts)
- [PLAN_RESTRUCTURE_KESTRA.md](../../PLAN_RESTRUCTURE_KESTRA.md) — reorg plan and full flow roadmap

---

## 1. Architecture (what runs where)

**Large static datasets:** download once into a **host cache** on `comp`, then load/transform
many times without re-fetching from Google Drive. See
[kestra/docs/KESTRA_STRATEGY_AND_TECHNIQUES.md](../../kestra/docs/KESTRA_STRATEGY_AND_TECHNIQUES.md) §6.6
and [kestra/infrastructure/README.md](../../kestra/infrastructure/README.md).

```
Google Drive (NCI subtree only — not full Datasets folder)
        │
        ▼  (rare — once per Drive release)
Kestra flow: prod.nci60.download_nci60_datasets
  └─ gdown → /var/lib/kestra/nf-datasets  (container: /datasets/nf-streamlit)
        │
        ▼  (repeat — local-first; no download if cache hit)
Kestra flow: prod.nci60.load_raw_nci60
  ├─ git.Clone → nf_streamlit repo (scripts + kestra/scripts/)
  ├─ load_nci60_raw.py --data-root /datasets/nf-streamlit  (local-first; auto-download if missing)
  ├─ COPY CSV → raw_nci_* tables
  └─ verify row counts
        │
        ▼
Kestra flow: prod.nci60.build_nci60_tables
  ├─ psql → build_nci60_doseresp_sprime_list.sql
  ├─ psql → alter_sprime_list_add_fit_columns.sql
  ├─ psql → build_nci_nsc_compounds.sql
  └─ psql → build_im_cellosaurus_nci60_to_depmap_bridge.sql
        │
        ▼
(Future) prod.nci60.run_sprime_fit → ~4.8M curves, ~10h
```

**Important:** `sync_git.yml` only syncs `kestra/flows/` into Kestra. Python lives in the **Git repo**; each flow **clones the repo** on the worker before running scripts. Do not author flows only in the UI.

---

## 2. Target database

| Setting | Value |
|---------|--------|
| Host | `dmvpetridishdatastore.dev` |
| Port | `5432` |
| Database | `data_warehouse` |
| User | `comp_bio_u2` |
| Password | *(your credential — Kestra secret only)* |

### Local test (same scripts, no Kestra)

```powershell
# Copy infra/config.yaml.example → scripts/config.yaml and fill password
$env:PGHOST = "dmvpetridishdatastore.dev"
$env:PGPORT = "5432"
$env:PGUSER = "comp_bio_u2"
$env:PGDATABASE = "data_warehouse"
$env:PGPASSWORD = "<password>"

pip install psycopg[binary] pyyaml gdown tqdm
python kestra/scripts/load_nci60_raw.py --only doseresp --dry-run
python kestra/scripts/load_nci60_raw.py --only doseresp
```

`csv_to_datawarehouse.py` now prefers **PG\*** env vars over `config.yaml` when set.

---

## 3. Kestra secrets (one-time setup)

Create these in **Kestra → Settings → Secrets** (names must match exactly):

| Secret name | Example value | Used by |
|-------------|---------------|---------|
| `PG_HOST` | `dmvpetridishdatastore.dev` | All DB tasks |
| `PG_PORT` | `5432` | All DB tasks |
| `PG_USER` | `comp_bio_u2` | All DB tasks |
| `PG_DATABASE` | `data_warehouse` | All DB tasks |
| `PG_PASSWORD` | *(your password)* | All DB tasks |
| `PG_SSLMODE` | `prefer` or empty | Optional TLS |
| `GDRIVE_DATASETS_FOLDER_ID` | `1e0_UQzU-LksJxMEN5zJRikL0QbsWrJej` | Drive download |
| `GDRIVE_NCI_FOLDER_ID` | *(optional subfolder id)* | `--nci-only` downloads |
| `WEBHOOK_KEY` | *(new random key)* | `prod.sync.sync_git_flows` |

Template: [kestra/secrets.example.env](../../kestra/secrets.example.env) — **never commit filled-in values**.

### Where secrets live

- **Not** in flow YAML, **not** in `scripts/config.yaml` (gitignored), **not** in Git.
- Kestra injects them at runtime via `{{ secret('PG_PASSWORD') }}`.
- Workers must reach `dmvpetridishdatastore.dev:5432` (VPN/office network if required).

---

## 3.5 Server dataset volume (comp — one-time)

Before the NCI pipeline, add the Tier 2 cache to `~/Projects/kestra/docker-compose.yml`
on `comp`. **Two additions only** — full instructions:
[kestra/infrastructure/README.md](../../kestra/infrastructure/README.md).

| What | Path |
|------|------|
| Host cache (backup) | `/var/lib/kestra/nf-datasets` |
| In script containers | `/datasets/nf-streamlit` |
| Do **not** store CSVs here | `/tmp/kestra-wd/tmp/{executionId}/` (ephemeral) |

**Validate** after compose restart:

```bash
curl -u USER:PASS -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/volume_mount_test' \
  -F 'mode=write'
curl -u USER:PASS -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/volume_mount_test' \
  -F 'mode=read'
```

Expect `WRITE OK` then `READ OK` with the same marker contents.

---

## 4. Sync flows to Kestra

1. Merge/push flow YAML under `kestra/flows/` to `main` (or your deploy branch).
2. GitHub webhook triggers `prod.sync.sync_git_flows` (see [sync_git_flows.yml](../../kestra/flows/sync/sync_git_flows.yml)).
3. In Kestra UI, confirm namespaces:
   - `prod.sync` — infrastructure (`sync_git_flows`)
   - `prod.nci60` — `download_nci60_datasets`, `load_raw_nci60`, `build_nci60_tables`

If webhook is not wired yet, run `sync_git_flows` manually once from the UI.

**Rotate** the old webhook key `GoKeyGo432L` on GitHub — it appears in git history.

---

## 5. Run the pipeline

### Step 0 — Download CSVs to host cache (once)

Flow: **`prod.nci60.download_nci60_datasets`**

Run when Tier 2 is empty or Google Drive data changed. **Not** on every load.

| Input | Value |
|-------|-------|
| `nci_only` | `true` (**required** — set `GDRIVE_NCI_FOLDER_ID` secret) |
| `data_cache_path` | `/datasets/nf-streamlit` (default) |
| `git_branch` | `main` |

Allow **PT12H** timeout for large gdown. After success, CSVs live on host at
`/var/lib/kestra/nf-datasets` until manually removed.

### Step A — Load raw CSVs

Flow: **`prod.nci60.load_raw_nci60`**

| Input | When to use |
|-------|-------------|
| `git_branch` | `main` (or feature branch until merged) |
| `skip_download` | `false` (default) — script uses Tier 2 cache first; downloads only if CSVs missing |
| `force_download` | `true` to re-fetch from Drive even when cache is populated |
| `data_cache_path` | `/datasets/nf-streamlit` (default) |
| `nci_only` | `true` (default) when a download is needed |
| `only_tables` | `doseresp` for smoke test; empty for full load |
| `dry_run` | `true` to validate paths without COPY |

**Smoke test (recommended first):**

- `only_tables` = `doseresp`
- `dry_run` = `false`
- Expect **~24.5M rows** in `raw_nci_nci60_doseresp` (verify task output).

**Full load:** clear `only_tables`, allow **PT6H** timeout (DOSERESP ~2.4 GB CSV).

### Step B — Build intermediate tables

Flow: **`prod.nci60.build_nci60_tables`**

Requires raw tables loaded. Produces:

| Table | Approx rows |
|-------|-------------|
| `im_nci_nci60_doseresp_sprime_list` | ~4.86M |
| `im_nci_nsc_compounds` | ~332k |
| `im_cellosaurus_nci60_to_depmap_bridge` | 163 lines (~124 CVCL, ~79 ACH) |

**Prerequisites for cell xref:** `raw_cellosaurus_celllines` must exist (Cellosaurus extract — not in Drive NCI folder; run `extract_cellosaurus_celllines.py` separately or load from Drive `Cellosaurus/` subfolder).

### Step C — Sprime fit (manual / future flow)

Not yet a Kestra flow. Use [RUNBOOK_NCI60_SPRIME_FIT.md](RUNBOOK_NCI60_SPRIME_FIT.md) or add `03_run_sprime_fit.yml` later.

---

## 6. Manifest and Drive layout

File mapping: [kestra/scripts/nci60_manifest.yaml](../../kestra/scripts/nci60_manifest.yaml)

Expected paths under Tier 2 cache (`/datasets/nf-streamlit` / host `nf-datasets/`):

```
NCI/NCI60/NCI60/DOSERESP/DOSERESP.csv  → raw_nci_nci60_doseresp
NCI/NCI60/NCI60/GI50.csv               → raw_nci_nci60_gi50
...
NCI/NSC_Compounds/nsc_*.csv            → raw_nci_nsc_*
```

If gdown produces a different tree, either:

1. Edit `relative_path` in the manifest, or  
2. Rely on basename `rglob` fallback (loader finds `DOSERESP.csv` uniquely).

List what landed:

```bash
find data -name '*.csv' | sort
```

---

## 7. Verification SQL

```sql
SELECT 'doseresp' AS tbl, count(*) FROM raw_nci_nci60_doseresp
UNION ALL
SELECT 'sprime_list', count(*) FROM im_nci_nci60_doseresp_sprime_list
UNION ALL
SELECT 'eligible', count(*) FROM im_nci_nci60_doseresp_sprime_list WHERE load_eligible;
```

Compare to local postgres golden counts in [NCI60_DOSERESP_SCHEMA_REFERENCE.md](../schema/NCI60_DOSERESP_SCHEMA_REFERENCE.md).

---

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| `Clone` task fails | Check worker outbound HTTPS; repo public or add deploy key |
| Drive download empty / quota | `download_nci60_datasets` with `nci_only=true`; never full Datasets folder on Kestra |
| gdown `FileURLRetrievalError` | Full Drive folder — use NCI subfolder only; see §5 Step 0 |
| CSVs missing on load | Run Step 0 first; confirm Tier 2 with `volume_mount_test` |
| Re-download every run | Data was under WorkingDirectory scratch — use Tier 2 cache; script auto-skips download |
| DB connection timeout | VPN; confirm host/port; test with `psql` from worker network |
| `CSV not found` | Fix manifest paths; run `find data -name DOSERESP.csv` |
| `build_cell_line_xref` fails | Load Cellosaurus raw table first |
| Plugin type not found | Confirm Kestra version; see plugin table in [kestra/README.md](../../kestra/README.md) |
| Docker runner missing | Install Docker on Kestra worker or switch taskRunner to `PROCESS` |

---

## 9. Files added for this pipeline

| Path | Role |
|------|------|
| `kestra/infrastructure/README.md` | comp compose diffs for dataset volume |
| `kestra/flows/nci60/00_download_datasets.yml` | One-time/rare Drive → Tier 2 cache |
| `kestra/flows/nci60/01_load_raw_data.yml` | Load flow (Tier 2 → Postgres) |
| `kestra/flows/nci60/99_volume_mount_test.yml` | Compose volume smoke test |
| `kestra/flows/nci60/02_build_tables.yml` | SQL build flow |
| `kestra/scripts/load_nci60_raw.py` | Download + load orchestrator |
| `kestra/scripts/download_gdrive_datasets.py` | gdown wrapper |
| `kestra/scripts/nci60_manifest.yaml` | CSV → table map |
| `kestra/secrets.example.env` | Secret name reference |
| `scripts/csv_to_datawarehouse.py` | PG\* env support for Kestra |

---

**Last updated:** 2026-06-07
