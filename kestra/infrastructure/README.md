# Kestra server infrastructure (comp)

Live compose: **`~/Projects/kestra/docker-compose.yml`** on `comp` — not run from this repo.

This folder documents **what to add** to that file for large static datasets. Do not
replace the whole compose file; merge the two additions below into your existing YAML.

See also [../docs/KESTRA_STRATEGY_AND_TECHNIQUES.md](../docs/KESTRA_STRATEGY_AND_TECHNIQUES.md) §6.6
for the full standard-practice guide (three tiers, two-phase flows, validation).

---

## Path mapping

| Layer | Host (backup this) | Inside script containers | Lifetime |
|-------|-------------------|--------------------------|----------|
| Tier 1 scratch | `/tmp/kestra-wd/tmp/{executionId}/` | same | **One execution** |
| **Tier 2 cache** | `/var/lib/kestra/nf-datasets` | `/datasets/nf-streamlit` | Until wipe or Drive refresh |
| Tier 3 warehouse | — | — | Postgres `raw_nci_*` / `im_*` |

---

## One-time host setup

```bash
sudo mkdir -p /var/lib/kestra/nf-datasets
```

---

## Addition 1 — `kestra` service `volumes:`

Find your existing block:

```yaml
    volumes:
      - kestra-data:/app/storage
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/kestra-wd:/tmp/kestra-wd
```

Add **one line** after `/tmp/kestra-wd`:

```yaml
      - /var/lib/kestra/nf-datasets:/datasets/nf-streamlit:rw
```

---

## Addition 2 — `KESTRA_CONFIGURATION` → under `kestra:`

Find:

```yaml
          tasks:
            tmp-dir:
              path: /tmp/kestra-wd/tmp
          url: https://pipeline.comp.mocomakers.com
```

Insert **before** `ports:` (same indentation as `tasks:` / `url:`):

```yaml
          plugins:
            configurations:
              - type: io.kestra.plugin.scripts.runner.docker.Docker
                values:
                  volume-enabled: true
```

Restart:

```bash
cd ~/Projects/kestra
sudo docker compose down && sudo docker compose up -d
sudo docker compose logs kestra | tail -30
```

---

## Flow requirements (repo — not compose)

Script tasks need the same bind on `taskRunner` (sibling containers do not inherit
the Kestra service mount automatically):

```yaml
taskRunner:
  type: io.kestra.plugin.scripts.runner.docker.Docker
  volumes:
    - /var/lib/kestra/nf-datasets:/datasets/nf-streamlit:rw
```

Flows: `00_download_datasets.yml`, `01_load_raw_data.yml`, `99_volume_mount_test.yml`.

---

## Confirmatory test (validated 2026-06-07)

After compose changes, run `prod.nci60.volume_mount_test`:

```bash
# Write marker file to Tier 2
curl -u USER:PASS -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/volume_mount_test' \
  -F 'mode=write'

# Read marker in a NEW execution (proves cross-run persistence)
curl -u USER:PASS -X POST \
  'https://pipeline.comp.mocomakers.com/api/v1/main/executions/prod.nci60/volume_mount_test' \
  -F 'mode=read'
```

Expect `WRITE OK` then `READ OK` with the same `volume-ok-…` timestamp.

Example successful runs: write `3MWNmg6md5eyjRqR69Rm9S`, read `757F5qmp5qXzBXLEiALzYO`.

---

## Backup

```bash
sudo tar -czf nf-datasets-$(date +%Y%m%d).tar.gz -C /var/lib/kestra nf-datasets
```

---

## Optional snapshot

[docker-compose.reference.yml](docker-compose.reference.yml) is an optional full-file
snapshot for diffing — **merge additions manually**; do not blind-copy over live secrets.
