# Kestra — flows & best practices

This directory is the **source of truth for our Kestra flows**. Everything here is
versioned in git (`mocomakers/nf_streamlit`) and synced into Kestra automatically —
no flow should ever be authored only in the Kestra UI, because the next git sync
will overwrite or orphan it.

We are migrating the NCI-60 / sprime data-warehouse migrations (see
[`RUNBOOK_NCI60_SPRIME_FIT.md`](../docs/runbooks/RUNBOOK_NCI60_SPRIME_FIT.md) and
[`RUNBOOK_KESTRA_NCI60_DEPLOY.md`](../docs/runbooks/RUNBOOK_KESTRA_NCI60_DEPLOY.md))
from the manual runbook + `scripts/` into orchestrated Kestra flows.

**Deep dive:** [docs/KESTRA_STRATEGY_AND_TECHNIQUES.md](docs/KESTRA_STRATEGY_AND_TECHNIQUES.md)
— learning guide, **Docker Compose stack on `comp`**, **large static datasets (§6.6)**,
**single admin login (UI = API = agent curl)**, deployment strategies (git vs API-first),
sync plugin pitfalls, WorkingDirectory patterns, secrets, debugging playbook, and NCI pipeline strategy.

**Large datasets on comp:** [infrastructure/README.md](infrastructure/README.md) — two
compose additions for `/var/lib/kestra/nf-datasets`; download once via
`download_nci60_datasets`; `load_nci60_raw.py` is **local-first** (auto-skips download when cache hit).

---

## How flows reach Kestra (deployment model)

```
edit kestra/flows/**.yml  ->  git push origin main  ->  GitHub webhook
   ->  Kestra runs the sync flow  ->  flows appear/update under their namespace
```

1. **Git is authoritative long-term.** Flows live under `kestra/flows/`. For rapid
   iteration, flows can be updated live via the Kestra API (`PUT /api/v1/main/flows/{namespace}/{id}`
   with `Content-Type: application/x-yaml`), then mirrored back into this repo from the
   response `source` field. The next `sync_git_flows` run will overwrite live edits unless
   the same YAML is pushed to `main`.
2. **A GitHub webhook on `main` is already configured**, so a merge to `main`
   triggers the sync automatically. You should not need to run anything by hand.
3. Two git-sync flows coexist in the repo (see layout below). **Webhook target:**
   `flows/sync/sync_git_flows.yml` (`prod.sync.sync_git_flows`). Legacy
   `flows/infrastructure/sync_git.yml` (`prod.sync.sync_git`) is unchanged.

---

## Reference projects (git repositories)

Keep this list current. These are the git repos Kestra pulls from or that we use
as reference material for authoring flows. Add a row whenever we point a sync flow
or a `Clone`/`SyncNamespaceFiles` task at a new repo.

| Repository | Purpose | Synced by |
|---|---|---|
| `https://github.com/kestra-io/kestra.git` | Upstream Kestra — plugin source, blueprints, and example flows. Reference only; we do **not** deploy from it. | — (manual reference) |
| `https://github.com/mocomakers/nf_streamlit` | **This project.** Flows under `kestra/flows/` are synced to Kestra on push to `main`. | `flows/sync/sync_git_flows.yml`; legacy copy in `legacy/infrastructure/sync_git.yml` |

> When you add a repo here, also document *which flow* syncs it and *into which
> namespace*, so the mapping from git → Kestra stays traceable.

---

## Directory layout

```
kestra/
├── README.md                      # this file
├── docs/
│   └── KESTRA_STRATEGY_AND_TECHNIQUES.md
├── flows/
│   ├── sync/                      # active git sync (prod.sync.sync_git_flows)
│   │   └── sync_git_flows.yml
│   ├── example/
│   │   └── hello_world.yml
│   └── nci60/                     # NCI-60 pipeline (see RUNBOOK_KESTRA_NCI60_DEPLOY.md)
│       ├── 00_download_datasets.yml  # Drive → Tier 2 host cache (rare)
│       ├── 01_load_raw_data.yml      # Tier 2 → raw_nci_* tables
│       ├── 02_build_tables.yml       # SQL → im_* tables
│       ├── 03_run_sprime_fit.yml     # (planned)
│       └── 99_volume_mount_test.yml  # compose volume smoke test
├── infrastructure/                # comp docker-compose diffs (dataset volume)
│   └── README.md
├── legacy/                        # old flows — outside flows/ so sync_git_flows skips them
│   └── infrastructure/
│       └── sync_git.yml           # legacy TenantSync (prod.sync.sync_git)
├── resources/                     # shared SQL / config pulled in by flows
└── scripts/                       # Python invoked by script tasks (or reuse ../scripts)
```

Subfolders under `kestra/flows/` map to child namespaces via `includeChildNamespaces`:
`sync/` → `prod.sync`, `nci60/` → `prod.nci60`, etc. Legacy `sync_git.yml` lives under
`kestra/legacy/` so `sync_git_flows` does not try to import it on every run.

- One flow per file; **filename = flow `id`** (`sync_git_flows.yml` → `id: sync_git_flows`).
- Group by pipeline/domain folder; folder name = namespace suffix under `prod.*`.

---

## Namespace conventions

Namespaces are dotted and hierarchical; child namespaces inherit secrets/KV from
parents, so use the hierarchy deliberately.

| Namespace | Use |
|---|---|
| `prod.nci60` | The production migration pipeline (load, build, fit, enrich). |
| `prod.sync` | Infrastructure — `flows/sync/` (active webhook). Legacy flow in `legacy/infrastructure/`. |
| `dev.*` | Experiments and smoke tests. Safe to break. |
| `example` | Vendor/example flows. Nothing in `prod.*` may call into `example`. |

Pick **one** environment prefix scheme (`prod.` / `dev.`) and stick to it. Today
the repo mixes `example`, `system`, and `prod.sync` — converge on `prod.*` /
`dev.*` and reserve `system`/`example` for throwaways.

---

## Flow authoring best practices

### IDs & naming
- `id` is kebab/snake and stable — **renaming an `id` creates a new flow** and
  orphans run history. Choose well the first time.
- Task `id`s should read as steps: `load-doseresp`, `build-sprime-list`, `run-fit`.

### Secrets & connections — never hardcode
This is the most important rule for us, because the pipeline holds DB credentials.

- **Do not** put DB host/user/password in flow YAML. Our `scripts/config.yaml`
  pattern (real creds, gitignored) does **not** translate to Kestra — flows are in
  git.
- Store credentials as **Kestra Secrets** (env `SECRET_*`) or **KV store** values
  and reference them: `{{ secret('PG_PASSWORD') }}` / `{{ kv('PG_HOST') }}`.
- Webhook keys must come from `{{ secret(...) }}`, not be committed in plaintext.
  `sync_git.yml` now uses `{{ secret('WEBHOOK_KEY') }}`; rotate the old key on the
  GitHub webhook side — `GoKeyGo432L` is public in git history.

### Idempotency
Our build SQL is already idempotent (`DROP TABLE IF EXISTS`, `CREATE … AS`,
`ADD COLUMN IF NOT EXISTS`) — preserve that. A flow should be safe to re-run from
the top without manual cleanup. Prefer `Queries` with `CREATE OR REPLACE` /
`IF NOT EXISTS` over imperative one-shots.

### Resumability for long jobs
`run_sprime_fit.py` is already resumable (`WHERE fit_run_id IS NULL`, batched
commits). Keep that design when wrapping it: the fit task should be re-runnable and
simply pick up where it left off, rather than relying on Kestra to checkpoint a
10-hour task.

### Retries & timeouts
Put `retry` on anything touching the network or DB; set a `timeout` on the fit task
so a hung run is killed, not left forever.

```yaml
    retry:
      type: constant
      interval: PT30S
      maxAttempt: 3
    timeout: PT12H
```

### Reuse via subflows
Factor the repeating "load one CSV" step (we load ~18 raw tables the same way) into
a single subflow (`io.kestra.plugin.core.flow.Subflow`) called per table, instead of
copy-pasting the loader task.

### Inputs & labels
- Expose run-time knobs as `inputs` (e.g. `batch_size`, `workers`, `fit_run_id`,
  `dry_run`) with defaults — don't bury them in the script.
- Add `labels` (`pipeline: nci60`, `stage: fit`) so runs are filterable.

---

## Migrating the existing pipeline → flows

Map the runbook steps onto tasks. Reuse the existing `scripts/` (they're
bind-mounted / available in the tools image) rather than rewriting them.

| Runbook step | Script today | Flow task type |
|---|---|---|
| Load raw CSVs (×18) | `scripts/csv_to_datawarehouse.py` | `io.kestra.plugin.scripts.python.Commands` (subflow, one call per table) |
| Build sprime list | `build_nci60_doseresp_sprime_list.sql` | `io.kestra.plugin.jdbc.postgresql.Queries` |
| Build compound ref | `build_nci_nsc_compounds.sql` | `io.kestra.plugin.jdbc.postgresql.Queries` |
| Cell-line xref | `build_nci_cell_line_xref.sql` | `io.kestra.plugin.jdbc.postgresql.Queries` |
| Add fit columns | `alter_sprime_list_add_fit_columns.sql` | `io.kestra.plugin.jdbc.postgresql.Queries` |
| Run Hill fit | `run_sprime_fit.py` | `io.kestra.plugin.scripts.python.Commands` (long-running, resumable) |
| ChEMBL enrich | `enrich_chembl_compounds.py` | `io.kestra.plugin.scripts.python.Commands` |

> **Open dependency:** `im_chembl_nsc_map` has no committed build script, and the
> `chembl` foreign schema has no setup script. Resolve both before the enrich step
> can run from scratch on a fresh server — otherwise the flow will fail there.

---

## Plugin type reference

Kestra reorganized plugin type paths around 0.16. The **modern** `io.kestra.plugin.core.*`
paths are preferred; the old `io.kestra.core.models.*` paths are deprecated aliases.
**Verify these against the Kestra version we actually run** before relying on them.

| Purpose | Preferred type | Deprecated alias seen in repo |
|---|---|---|
| Webhook trigger | `io.kestra.plugin.core.trigger.Webhook` | `io.kestra.core.models.triggers.types.Webhook` (was in `sync_git.yml`, now fixed) |
| Schedule trigger | `io.kestra.plugin.core.trigger.Schedule` | — |
| Subflow | `io.kestra.plugin.core.flow.Subflow` | — |
| Postgres query / DDL | `io.kestra.plugin.jdbc.postgresql.Query`, `.Queries` | — |
| Python | `io.kestra.plugin.scripts.python.Script`, `.Commands` | — |
| Git sync | `io.kestra.plugin.git.SyncFlows` / `.TenantSync` | — |

---

## Known issues / cleanup

1. ~~**Two competing sync flows**~~ — resolved. Only `flows/infrastructure/sync_git.yml`
   exists; the second flow referenced in earlier notes was never on disk.

2. ~~**Malformed trigger in `hello_world.yml`**~~ — not present on disk. `hello_world.yml`
   has no trigger block; it is valid YAML. No fix needed.

3. ~~**Plaintext webhook key `GoKeyGo432L`** in `sync_git.yml`~~ — fixed in repo:
   trigger now uses `{{ secret('WEBHOOK_KEY') }}`. **Action still required**: rotate
   the old key on the GitHub webhook settings page — it is in public git history.

4. **Hardcoded repo URL in `sync_git.yml`.** The URI is hardcoded; fine for now, but
   credentials for private syncs must come from secrets.
