# scripts/

Operational support scripts for the nf_streamlit project.

Pipeline (ETL) scripts have been moved to [`kestra/scripts/`](../kestra/scripts/) where they
are the authoritative copies used by Kestra flows. Originals are archived in `deprecated-scripts/`
(gitignored, local reference only).

## Streamlit-support / operational (stay here)

| Script | Purpose |
|--------|---------|
| `deployment.sh` | Git-pull deploy script for the Streamlit server. |
| `mcp-toolbox.sh` | Manage the MCP Toolbox Docker container (Linux/macOS). |
| `mcp-toolbox.bat` | Manage the MCP Toolbox Docker container (Windows). |

## Utilities (stay here)

| Script | Purpose |
|--------|---------|
| `csv_compare_and_combine.py` | One-off helper to overlay/merge dose-response CSVs. |

## Local config (not committed)

`config.yaml` holds local PostgreSQL connection settings and is **gitignored**.
Create it locally from `infra/config.yaml.example`.
