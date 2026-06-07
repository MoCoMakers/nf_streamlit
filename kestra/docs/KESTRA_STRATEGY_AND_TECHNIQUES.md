# Kestra — learning, strategy, and techniques

A practical guide for how we use Kestra at MoCo Makers: mental models, deployment
patterns, API workflows, and lessons from standing up the NCI-60 pipeline on
`pipeline.comp.mocomakers.com`.

**Audience:** anyone authoring flows, debugging executions, or operating the
prod warehouse load. Assumes OSS Kestra (`kestra/kestra:latest`) on `comp` with
Postgres metadata and Docker task runners.

**Related docs**

| Doc | Purpose |
|-----|---------|
| [../README.md](../README.md) | Repo layout, namespaces, authoring conventions |
| [../../docs/runbooks/RUNBOOK_KESTRA_NCI60_DEPLOY.md](../../docs/runbooks/RUNBOOK_KESTRA_NCI60_DEPLOY.md) | Operational steps for NCI-60 on prod |
| [../../docs/runbooks/RUNBOOK_NCI60_SPRIME_FIT.md](../../docs/runbooks/RUNBOOK_NCI60_SPRIME_FIT.md) | Local Docker parity path (same scripts/SQL) |
| [../infrastructure/README.md](../infrastructure/README.md) | comp `docker-compose.yml` diffs for dataset volume |

---

## 1. Mental model — what Kestra is for us

Kestra is **orchestration**, not storage and not the data source.

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│  Google Drive   │     │  GitHub          │     │  Kestra (comp)          │
│  static CSVs    │     │  flows + scripts │     │  schedules / webhooks   │
└────────┬────────┘     └────────┬─────────┘     └────────────┬────────────┘
         │                       │                            │
         │  gdown at runtime     │  git.Clone at runtime      │  executes tasks
         v                       v                            v
              ┌──────────────────────────────────────────────────────┐
              │  Worker: Docker containers + shared WorkingDirectory │
              └──────────────────────────┬───────────────────────────┘
                                         │ COPY / psql
                                         v
                              ┌──────────────────────┐
                              │  data_warehouse      │
                              │  (dmvpetridish...)  │
                              └──────────────────────┘
```

| Layer | Source of truth | Notes |
|-------|-----------------|-------|
| **Flow definitions** | Git `kestra/flows/` long-term; API for live drafts | `sync_git_flows` pulls from `main` |
| **Python / SQL logic** | Git repo root (`scripts/`, `kestra/scripts/`) | Cloned per execution — **not** embedded in flow YAML |
| **Dataset files** | Google Drive [Datasets folder](https://drive.google.com/drive/folders/1e0_UQzU-LksJxMEN5zJRikL0QbsWrJej) | Staged once to host cache `/var/lib/kestra/nf-datasets`; load flows read `/datasets/nf-streamlit` |
| **Credentials** | Kestra secrets (`SECRET_*` via `.env_encoded`) | Never in git |
| **Kestra metadata** | `kestralivedb` on `comp` | Flows, executions, logs — separate from warehouse |

**Prod population path:** Drive CSVs → Kestra `prod.nci60.load_raw_nci60` → `raw_nci_*` on
`dmvpetridishdatastore.dev`. Local Docker Postgres is an optional dev mirror using the
same scripts; it is not what Kestra targets unless secrets point there.

---

## 2. Server topology — everything runs in Docker Compose

The **production Kestra stack is not in this repo**. It lives on `comp` at
`~/Projects/kestra/` as a self-contained `docker-compose.yml`. There is no
separate Kestra install outside that compose project — UI, API, worker, metadata
Postgres, local storage, and task-runner Docker access are all defined there.

```text
~/Projects/kestra/
├── docker-compose.yml    # postgres + kestra services (source of truth for server)
├── .env                  # flow/warehouse secrets (gitignored on server)
└── .env_encoded          # SECRET_* base64 lines → kestra service env_file
```

Public URL `https://pipeline.comp.mocomakers.com` is a **reverse proxy** in front
of the compose-published ports on `comp`.

### 2.1 Compose services

| Service | Image | Role |
|---------|-------|------|
| `postgres` | `postgres:18` | Kestra **metadata** only (`kestralivedb`) |
| `kestra` | `kestra/kestra:latest` | UI + API + worker (`server standalone`) |

| Mount / port | Purpose |
|--------------|---------|
| `postgres-data` volume | Persists flows, executions, settings |
| `kestra-data` → `/app/storage` | Kestra local file storage |
| `/var/run/docker.sock` | Worker spawns **sibling** containers for script tasks |
| `/tmp/kestra-wd` | `WorkingDirectory` scratch — **per-execution** subtree only |
| `/var/lib/kestra/nf-datasets` → `/datasets/nf-streamlit` | **Long-term static CSV cache** (host bind mount) |
| `7777:8080` | UI + REST API (what the proxy targets) |
| `7778:8081` | Management / internal port |

The `kestra` service runs as **`user: root`** in compose — required so the
container can talk to the host Docker socket. Script tasks use
`io.kestra.plugin.scripts.runner.docker.Docker` and run as separate containers on
the same host.

**Inline server config:** almost all Kestra behaviour is set in the
`KESTRA_CONFIGURATION` environment variable (multi-line YAML in
`docker-compose.yml`): datasource URL, `repository`, `queue`, `storage`, public
`url`, and **`server.basic-auth`** (see §2.2). After any edit:

```bash
cd ~/Projects/kestra
sudo docker compose down && sudo docker compose up -d
sudo docker compose logs -f kestra   # confirm no YAML parse errors
```

**Flow secrets** (warehouse `PG_*`, `WEBHOOK_KEY`, Drive IDs) are **not** in
`KESTRA_CONFIGURATION`. They come from `.env` → `.env_encoded` and are loaded via
`env_file` on the `kestra` service. Re-encode and restart compose after changing
`.env` (see §9).

### 2.2 Users, login, and agent API access (same password)

Kestra OSS uses **one shared administrator account** — not a multi-user directory.

| What | How |
|------|-----|
| **Web UI login** | Email + password at `https://pipeline.comp.mocomakers.com` |
| **REST API / curl** | **Same** email + password — HTTP Basic Auth on every request |
| **Cursor agent / scripts** | **Same** credentials — `curl -u 'email:password'` or equivalent |

There is no separate “API key” or “agent user.” If you can log into the UI, you
use that exact pair for `PUT` flows, `POST` executions, and log polling.

```bash
# UI login  →  matt@example.com / your-password
# Agent     →  identical:
curl -s -u 'matt@example.com:your-password' \
  'https://pipeline.comp.mocomakers.com/api/v1/main/flows/prod.nci60/load_raw_nci60'
```

**Where credentials are defined (precedence)**

1. **`KESTRA_CONFIGURATION` → `kestra.server.basic-auth`** in `docker-compose.yml`
   — **recommended for production**; config file wins over DB-stored values.
2. **First-start Setup page** — if `basic-auth` is omitted, Kestra prompts once and
   stores credentials in the metadata DB (`Settings` table). A later compose config
   **overrides** those values.

**Adding or changing users (OSS)**

| Goal | What to do |
|------|------------|
| **Change admin password** | Edit `basic-auth.username` / `basic-auth.password` in compose → restart |
| **Give a teammate access** | Share the admin credentials securely, or rotate password after |
| **Separate accounts per person** | **Not in OSS** — requires Kestra Enterprise (RBAC / SSO) |
| **Forgot password** | Fix `basic-auth` in `docker-compose.yml` and restart (config overrides DB) |

Password rules (OSS): username must be a **valid email**; password ≥ 8 chars with
uppercase and a number. Store real values only on `comp` — never commit them to
`nf_streamlit`.

Example fragment inside `KESTRA_CONFIGURATION` (indentation matters — wrong nesting
crashes Kestra on start):

```yaml
        kestra:
          server:
            basic-auth:
              username: admin@your-org.com
              password: ChangeMe1!
          repository:
            type: postgres
          # ... storage, queue, url, etc.
```

**Webhook vs UI auth:** GitHub webhooks hit
`/api/v1/main/executions/webhook/.../{WEBHOOK_KEY}` using the **path key**, not
Basic Auth. That is separate from the UI/API login above.

### 2.3 Two Postgres databases — do not confuse them

| Database | Where | Purpose |
|----------|-------|---------|
| `kestralivedb` | `postgres` service **inside compose** | Kestra flows, executions, logs |
| `data_warehouse` | `dmvpetridishdatastore.dev:5432` (external) | NCI pipeline target via `PG_*` secrets |

---

## 3. Repository layout and namespaces

```text
kestra/
├── docs/                          ← this guide
├── flows/
│   ├── sync/sync_git_flows.yml    → prod.sync  (active webhook sync)
│   ├── nci60/01_load_raw_data.yml → prod.nci60
│   ├── nci60/02_build_tables.yml  → prod.nci60
│   └── example/hello_world.yml    → prod.example (via includeChildNamespaces)
├── legacy/infrastructure/         → NOT synced (outside kestra/flows/)
├── scripts/                       → cloned at runtime with rest of repo
└── secrets.example.env            → template only
```

### Namespace conventions

| Namespace | Role |
|-----------|------|
| `prod.sync` | Git sync infrastructure (`sync_git_flows`) |
| `prod.nci60` | NCI-60 load + build (+ future fit) |
| `prod.example` | Example flows under `flows/example/` (child namespace mapping) |
| `dev.*` | Safe experiments |

Child namespaces inherit secrets from parents (`prod` → `prod.nci60`).

### Active git sync: `sync_git_flows`

```yaml
type: io.kestra.plugin.git.SyncFlows
gitDirectory: kestra/flows
targetNamespace: prod
includeChildNamespaces: true
```

Folder → namespace mapping:

| Git folder | Kestra namespace |
|------------|------------------|
| `flows/sync/` | `prod.sync` |
| `flows/nci60/` | `prod.nci60` |
| `flows/example/` | `prod.example` |

**Legacy flows** live under `kestra/legacy/` so sync does not import broken YAML on
every run (e.g. old `TenantSync` with deprecated `uri` field).

**Webhook URL pattern**

```text
https://pipeline.comp.mocomakers.com/api/v1/main/executions/webhook/prod.sync/sync_git_flows/{WEBHOOK_KEY}
```

---

## 4. Deployment strategies

We use **two complementary loops**. Know which one you are in.

### Strategy A — Git-first (durable, team-wide)

```text
edit kestra/flows/*.yml → push main → webhook → sync_git_flows → flows updated in UI
```

- Best for: merged, reviewed, stable flows
- Risk: `main` must be valid YAML; bad flow on `main` breaks sync for that file
- Scripts: still from **git clone at execution time** — pushing script fixes to `main`
  is required for load/build tasks to pick them up (unless using hotfix below)

### Strategy B — API-first (fast iteration, agent-friendly)

```text
PUT flow YAML to API → execute → debug logs → mirror `source` back to repo → push main
```

| Operation | HTTP |
|-----------|------|
| Update flow | `PUT /api/v1/main/flows/{namespace}/{id}` + `Content-Type: application/x-yaml` |
| Execute | `POST /api/v1/main/executions/{namespace}/{id}` + form inputs (`-F key=value`) |
| Poll | `GET /api/v1/main/executions/{executionId}` |
| Logs | `GET /api/v1/main/logs/{executionId}` |

Example (smoke load):

```bash
curl -u 'USER:PASS' -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/load_raw_nci60' \
  -F git_branch=main \
  -F only_tables=doseresp \
  -F skip_download=false \
  -F nci_only=false \
  -F dry_run=false
```

**Mirror back:** PUT/GET response includes a `source` field with canonical YAML —
copy into `kestra/flows/...` and commit so Strategy A does not overwrite your draft.

**Conflict rule:** whichever lands last wins. If you API-edit a flow but do not push
to `main`, the next `sync_git_flows` webhook **reverts** the live flow to git.

### Strategy C — Script hotfix at runtime (bridge until `main` catches up)

When `main` still has a broken script but the flow is already fixed:

- Add a `beforeCommands` step after `git.Clone` that patches the cloned file in-place
  (small Python one-liner or `sed`)
- Mirror the real fix into `kestra/scripts/` and push `main`
- Remove the hotfix block once `main` is good

Use sparingly; prefer merging script fixes quickly.

---

## 5. Git plugin cheat sheet (version pitfalls)

Our Kestra build uses **current** plugin property names. Older examples online may not.

| Wrong (deprecated) | Correct |
|--------------------|---------|
| `uri:` on Clone / TenantSync | `url:` |
| `directory:` on TenantSync | `gitDirectory:` |
| `cloneDirectory:` on Clone | `directory:` |
| `io.kestra.core.models.triggers.types.Webhook` | `io.kestra.plugin.core.trigger.Webhook` |

### SyncFlows vs TenantSync

| | **SyncFlows** | **TenantSync** |
|--|---------------|----------------|
| **Our use** | ✅ `sync_git_flows` | Legacy only (`kestra/legacy/`) |
| **Layout** | `kestra/flows/{folder}/*.yml` + `includeChildNamespaces` | `{gitDirectory}/{namespace}/flows/{id}.yaml` |
| **Extra config** | `targetNamespace`, optional `ignoreInvalidFlows` | `kestraUrl`, `auth`, `sourceOfTruth` |
| **Fit** | Matches our repo today | Requires full tree restructure |

### TenantSync expected layout (if we adopt later)

```text
kestra/
  prod.nci60/flows/load_raw_nci60.yaml
  prod.sync/flows/sync_git_flows.yaml
```

Not `kestra/flows/nci60/01_load_raw_data.yml`.

---

## 6. Flow authoring techniques

### 6.1 WorkingDirectory — share filesystem between tasks

**Problem:** `git.Clone` in task A and `python.Commands` in task B each ran in separate
Docker containers → `cd nf_streamlit` failed.

**Fix:** wrap clone + script in `io.kestra.plugin.core.flow.WorkingDirectory`:

```yaml
tasks:
  - id: workspace
    type: io.kestra.plugin.core.flow.WorkingDirectory
    tasks:
      - id: clone_repo
        type: io.kestra.plugin.git.Clone
        url: https://github.com/mocomakers/nf_streamlit
        branch: "{{ inputs.git_branch }}"
        directory: nf_streamlit
      - id: load_raw
        type: io.kestra.plugin.scripts.python.Commands
        # ...
```

### 6.2 Secrets in flows

```yaml
PGHOST: "{{ secret('PG_HOST') }}"
```

Secrets on `comp` come from `~/Projects/kestra/.env` → encoded `SECRET_*` in
`.env_encoded`. **Skip `#` comment lines** when encoding — they break Docker `env_file`
parsing.

| Secret | Used for |
|--------|----------|
| `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_DATABASE`, `PG_PASSWORD` | Warehouse |
| `GDRIVE_DATASETS_FOLDER_ID` | Drive download root |
| `GDRIVE_NCI_FOLDER_ID` | Optional; required if `nci_only=true` |
| `WEBHOOK_KEY` | `sync_git_flows` webhook |

### 6.3 Inputs for smoke vs full runs

**`prod.nci60.load_raw_nci60`**

| Input | Smoke test | Full raw rebuild |
|-------|------------|------------------|
| `only_tables` | `doseresp` | *(empty)* |
| `nci_only` | `false`* | `false`* |
| `skip_download` | `false` (script auto-skips if local OK) | `false` |
| `force_download` | `false` | `true` only to refresh from Drive |
| `data_cache_path` | `/datasets/nf-streamlit` | same |
| `nci_only` | `true` when download runs | `true` |
| `dry_run` | `false` | `false` |
| `git_branch` | `main` | `main` |

\* `nci_only=true` requires `GDRIVE_NCI_FOLDER_ID` secret; otherwise use `false` and
accept a larger Datasets download.

### 6.4 Idempotency and retries

- Raw load uses `replace: true` → `TRUNCATE` + `COPY`
- Build SQL uses `DROP TABLE IF EXISTS` / `ADD COLUMN IF NOT EXISTS`
- Long tasks: `timeout: PT6H` on load, `retry` on network steps

### 6.5 Labels and stable IDs

- Flow `id` is stable — renaming creates a new flow and orphans history
- Labels: `pipeline: nci60`, `stage: load` for filtering in UI

### 6.6 Large static datasets — standard practice

Kestra is the wrong place to **store** multi-GB CSV trees. Use it to **orchestrate**
movement from an external source (Drive) into durable tiers, then into Postgres.

#### Three durability tiers

```text
Tier 1 — Execution scratch     /tmp/kestra-wd/tmp/{executionId}/
         Lifetime: one execution. Use for: git clone, small temp files.

Tier 2 — Host dataset cache      /var/lib/kestra/nf-datasets  (in container: /datasets/nf-streamlit)
         Lifetime: until manual wipe or Drive refresh. Use for: large static CSVs.

Tier 3 — Warehouse               raw_nci_* / im_* on dmvpetridishdatastore.dev
         Lifetime: until next load/build replaces tables. Use for: queryable pipeline output.
```

**Rule:** never download multi-GB datasets into `{repo}/data` inside `WorkingDirectory`.
That path is Tier 1 and is reclaimed when the execution ends.

#### Two-phase flow pattern (download once, load many)

| Phase | Flow | Writes to | Frequency |
|-------|------|-----------|-----------|
| **A** | `download_nci60_datasets` | Tier 2 host cache | Once per Drive release, or after cache wipe |
| **B** | `load_raw_nci60` | Tier 3 Postgres (local-first; auto-skips download if cache hit) | Every rebuild / iteration |
| **B** | `build_nci60_tables` | Tier 3 `im_*` tables | After raw load |

Do **not** combine a full Drive download with a warehouse load in every execution unless
you enjoy repeating hours of gdown and hitting rate limits.

#### comp `docker-compose.yml` — two required additions

See [../infrastructure/README.md](../infrastructure/README.md) for exact placement. Summary:

1. **Bind mount** on `kestra` service volumes:
   `- /var/lib/kestra/nf-datasets:/datasets/nf-streamlit:rw`
2. **`volume-enabled: true`** under `kestra.plugins.configurations` for
   `io.kestra.plugin.scripts.runner.docker.Docker` in `KESTRA_CONFIGURATION`.

Create the host dir once: `sudo mkdir -p /var/lib/kestra/nf-datasets`

#### Flow YAML requirements (all three layers)

Mounting only on the Kestra service is **not enough**. Script tasks run in **sibling**
Docker containers spawned via `docker.sock`. Each script task must repeat the bind:

```yaml
taskRunner:
  type: io.kestra.plugin.scripts.runner.docker.Docker
  volumes:
    - /var/lib/kestra/nf-datasets:/datasets/nf-streamlit:rw
```

Use flow input `data_cache_path` default `/datasets/nf-streamlit` and pass
`--data-root` / `DATA_ROOT` to `load_nci60_raw.py`.

**`load_nci60_raw.py` download policy (default = local-first):**

| Flag / env | Behaviour |
|------------|-----------|
| *(none)* | Use local CSVs under `data_root`; download from Drive only for missing manifest entries |
| `--skip-download` / `SKIP_DOWNLOAD=true` | Never download; exit error if local CSVs missing |
| `--force-download` / `FORCE_DOWNLOAD=true` | Always re-download from Drive |

#### Drive download scope

| Approach | When | Risk |
|----------|------|------|
| `nci_only=true` + `GDRIVE_NCI_FOLDER_ID` | **Default for NCI pipeline** | Low — only NCI subtree |
| Full `GDRIVE_DATASETS_FOLDER_ID` | Avoid on Kestra | High — unrelated folders, hours of download, gdown `FileURLRetrievalError` |

#### Confirmatory test (validated on comp, 2026-06-07)

Flow `prod.nci60.volume_mount_test` (in repo as `99_volume_mount_test.yml`):

1. **Write** execution (`mode=write`) — creates `/datasets/nf-streamlit/.agent_volume_test`
2. **Read** execution (`mode=read`) — reads the same file in a **new** execution

Both succeeded — proves compose mount + `volume-enabled` + `taskRunner.volumes` work and
Tier 2 persists across executions.

```bash
curl -u USER:PASS -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/volume_mount_test' \
  -F 'mode=write'
# then -F 'mode=read' in a second POST
```

#### Backup Tier 2

```bash
sudo tar -czf nf-datasets-$(date +%Y%m%d).tar.gz -C /var/lib/kestra nf-datasets
```

---

## 7. NCI-60 pipeline strategy

### Stage map

| Stage | Flow | Output |
|-------|------|--------|
| 0. Download (rare) | `download_nci60_datasets` | Tier 2 cache `/datasets/nf-streamlit` |
| 1. Raw load | `load_raw_nci60` | 11 `raw_nci_*` tables |
| 2. Build | `build_nci60_tables` | `im_nci_nci60_doseresp_sprime_list`, `im_nci_nsc_compounds`, xref |
| 3. Fit | *(planned flow)* | S′ columns on list table |
| 4. Enrich | *(planned)* | ChEMBL / compound enrichment |

### Raw tables (manifest-driven)

Defined in `kestra/scripts/nci60_manifest.yaml`:

- NCI-60: `doseresp`, `gi50`, `tgi`, `lc50`, `ic50`, `oneconc`
- NSC: `nsc_cas`, `nsc_chemical_names`, `nsc_mw_mf`, `nsc_sid_cid`, `nsc_smiles`

Orchestrator: `kestra/scripts/load_nci60_raw.py` → `scripts/csv_to_datawarehouse.py`

### Execution order (prod)

**Two-phase model (download once, load many times)**

```text
Phase A (rare)     download_nci60_datasets  →  /var/lib/kestra/nf-datasets
                                              (container: /datasets/nf-streamlit)
Phase B (repeat)   load_raw_nci60 (local-first)  →  raw_nci_*
                   build_nci60_tables  →  im_*
```

| Phase | Flow | When |
|-------|------|------|
| **A — Download** | `prod.nci60.download_nci60_datasets` | Once after Drive update, or cache wiped |
| **B — Load** | `prod.nci60.load_raw_nci60` | Every rebuild; local-first (downloads only if CSVs missing) |
| **B — Build** | `prod.nci60.build_nci60_tables` | After raw load |

**Why a host cache path?** `WorkingDirectory` creates a **per-execution** temp dir under
`/tmp/kestra-wd/tmp/{executionId}/`. CSVs under `{repo}/data` there are **deleted when
the run ends**. Tier 2 uses a **fixed host bind mount** outside that subtree. See §6.6.

1. Confirm secrets and flows synced (`prod.nci60.*` visible in UI)
2. Set `GDRIVE_NCI_FOLDER_ID` and run **`download_nci60_datasets`** with
   `nci_only=true` (avoid full Datasets folder — unrelated Plexiform screens and
   gdown rate limits)
3. Smoke load: `load_raw_nci60` with `only_tables=doseresp` (uses cache if present)
4. Full raw: `load_raw_nci60` all tables (same local-first behaviour)
5. `build_nci60_tables`
6. Fit (manual runbook or future flow)

---

## 8. Debugging techniques

### 8.1 UI

Executions → select run → **Logs** per task. Gantt shows retry boundaries.

### 8.2 API (agent / script)

```bash
# State + per-task status
curl -s -u USER:PASS \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/{id}' \
  | jq '.state.current, .taskRunList[] | {task: .taskId, state: .state.current}'

# Tail logs (filter client-side)
curl -s -u USER:PASS \
  'https://pipeline.comp.mocomakers.com/api/v1/main/logs/{id}' \
  | jq '.[].message' | tail -50
```

### 8.3 Common failures we hit (playbook)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Unrecognized field "uri"` | Old git plugin YAML on `main` | Use `url:` / `gitDirectory:`; remove legacy from `kestra/flows/` |
| `can't cd to nf_streamlit` | Clone and script in separate containers | `WorkingDirectory` wrapper |
| `SyntaxError: global REPO_ROOT` | Python 3.11 + bad `global` placement | Fix `load_nci60_raw.py`; use local `repo_root` |
| `remaining_ok` gdown error | gdown 6.x API change | Remove `remaining_ok=True` from `download_gdrive_datasets.py` |
| `Cannot find secret for key` | Missing `.env_encoded` entry | Add secret, re-encode, restart compose |
| YAML parse on Kestra start | Bad indentation in `KESTRA_CONFIGURATION` | Align `kestra.server.basic-auth` under `kestra:` |
| Sync imports bad flow | File under `kestra/flows/` | Move to `kestra/legacy/` or fix YAML; `ignoreInvalidFlows: true` |
| 503 on UI | Kestra container crash-loop | `docker compose logs kestra` |
| Full Datasets download for hours | `nci_only=false` on full folder | `download_nci60_datasets` with `nci_only=true` |
| gdown `FileURLRetrievalError` | Full folder + rate limit / private file | NCI-only download; populate Tier 2 cache once |
| Re-download every run | Data under per-exec WorkingDirectory | Tier 2 cache; `load_nci60_raw.py` local-first; see §6.6 |
| Script container cannot see cache | Missing `volume-enabled` or `taskRunner.volumes` | Both required; run `volume_mount_test` |

### 8.4 Docker on worker

Script tasks use `io.kestra.plugin.scripts.runner.docker.Docker`. The Kestra
container runs as `root` with docker.sock mounted — required for spawning sibling
containers.

---

## 9. Secrets encoding (comp server)

```bash
cd ~/Projects/kestra
# Encode only KEY=value lines (skip comments and blanks)
grep -v '^#' .env | grep -v '^$' | grep '=' | while IFS='=' read -r k v; do
  echo "SECRET_${k}=$(printf '%s' "$v" | base64 -w0)"
done > .env_encoded

sudo docker compose down && sudo docker compose up -d
```

Template: `kestra/secrets.example.env` (names only — never commit values).

---

## 10. Security practices

- Never commit warehouse passwords, webhook keys, or `basic-auth` passwords
- Rotate keys that appeared in git history or chat
- Use `{{ secret('WEBHOOK_KEY') }}` in flows, not inline keys
- Treat the single OSS admin login as **full control** — UI, API, and agents share it
- Restrict who can reach `pipeline.comp.mocomakers.com` and warehouse `:5432`
- Prefer `basic-auth` in compose over ad-hoc Setup-page credentials so restarts are predictable

---

## 11. Local parity vs prod

| | **Local** (`infra/docker-compose.yml`) | **Prod (Kestra)** |
|--|----------------------------------------|-------------------|
| Orchestrator | Manual / docker `tools` profile | Kestra flows |
| Postgres | `localhost:5432`, `localdev` | `dmvpetridishdatastore.dev` |
| Data | Local `data/` or Drive download | Tier 2 host cache on comp; gdown in `download_nci60_datasets` only |
| Scripts | Same `kestra/scripts/`, `scripts/` | `git.Clone` on worker |

Same manifest, same SQL, same COPY logic — different runner and DB target.

---

## 12. Evolution roadmap

| Item | Status |
|------|--------|
| `sync_git_flows` + webhook | ✅ Active |
| `download_nci60_datasets` + Tier 2 host volume on comp | ✅ Validated (`volume_mount_test`) |
| `load_raw_nci60` + `build_nci60_tables` | ✅ In prod namespace (sync after git push) |
| Remove runtime hotfixes once `main` has script fixes | 🔄 In progress |
| `03_run_sprime_fit.yml` flow | 📋 Planned |
| Cellosaurus raw load in Kestra | 📋 Open (xref build dependency) |
| Restructure for `TenantSync` layout | ❓ Optional; not required with SyncFlows |
| Pre-baked worker image (skip apt/pip each run) | 💡 Performance idea |

---

## 13. Quick reference links

- Kestra API guide: https://kestra.io/docs/how-to-guides/api
- SyncFlows plugin: https://kestra.io/plugins/plugin-git/io.kestra.plugin.git.syncflows
- Git Clone plugin: https://kestra.io/plugins/plugin-git/io.kestra.plugin.git.clone
- WorkingDirectory: `io.kestra.plugin.core.flow.WorkingDirectory`
- Our UI: https://pipeline.comp.mocomakers.com

---

## 14. Glossary

| Term | Meaning |
|------|---------|
| **Tenant** | `main` — prefix in API paths `/api/v1/main/...` |
| **Flow revision** | Increments on each PUT/sync; executions record `flowRevision` |
| **includeChildNamespaces** | Maps subfolders of `gitDirectory` to `targetNamespace.{folder}` |
| **WorkingDirectory** | Shared temp dir on worker across child tasks (Tier 1 scratch) |
| **Tier 2 cache** | `/var/lib/kestra/nf-datasets` on host; `/datasets/nf-streamlit` in script containers |
| **source (API)** | Canonical YAML string returned after flow PUT — use to mirror to git |

---

*Last updated from production bring-up lessons (June 2026). Amend this doc when
plugin versions, sync strategy, or server topology change.*
