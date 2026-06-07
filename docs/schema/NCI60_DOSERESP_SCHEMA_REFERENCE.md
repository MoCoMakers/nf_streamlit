# Schema Reference — `raw_nci_nci60_doseresp`

Formal schema reference for the NCI-60 **dose-response (DOSERESP)** raw table in the local
`data_warehouse` PostgreSQL database.

- **Table:** `public.raw_nci_nci60_doseresp`
- **Source:** NCI/DTP NCI-60 Growth Inhibition Data — DOSERESP bulk file (April 2026 release)
- **Grain:** one row per **NSC × EXPID × concentration × cell line**
- **Size:** 24,492,523 rows (~2.4 GB CSV) — verified live 2026-05-31
- **Column count:** 18, **all `text`, all nullable** (raw load — no type coercion applied)
- **Verified against live DB:** 2026-05-31 via MCP toolbox (`describe-table-columns`)

> **Provenance note.** This is a **raw** load: the loader (`scripts/csv_to_datawarehouse.py`)
> auto-creates every column as `TEXT` and lowercases the original CSV headers. Numeric values
> (concentrations, GIPRCNT, PTC, counts, std-devs) are stored as text and must be cast
> (`::numeric`, `::int`) before arithmetic. No primary key, indexes, or constraints are defined.

---

## Overview

The NCI-60 panel is the NCI Development Therapeutics Program (DTP) standard *in vitro*
anticancer cell-line screen. Compounds are identified by **NSC number** and assayed across a
fixed panel of human tumor cell lines at multiple concentrations. The DOSERESP file holds the
**underlying concentration/response measurements** — the raw curves from which the GI50, TGI,
LC50, and IC50 endpoint tables are interpolated.

Each record is tied to an individual experiment (**EXPID**), not aggregated across experiments.
Most experiments use **5 dilutions** at log (10-fold) intervals; some use **10 dilutions** at
half-log intervals.

---

## Column dictionary

| # | Column | Type | Null | Definition |
| ---: | --- | --- | :---: | --- |
| 1 | `release_date` | text | yes | Date of this data release. |
| 2 | `expid` | text | yes | Experiment identifier. Format `YYMMLLSS` (year, month, internal process letters, sequence). All cell lines for one EXPID are grown and assayed contemporaneously. |
| 3 | `prefix` | text | yes | NSC sequence prefix. Public data uses `S`. |
| 4 | `nsc` | text | yes | Numeric compound identifier (NSC number). Not guaranteed 1:1 with a unique chemical structure. |
| 5 | `concentration_unit` | text | yes | Concentration units: `M` (molar — small molecules), `u` (µg/ml — some biologics), `V` (volume-based — mixtures/extracts). |
| 6 | `log_hi_concentration` | text | yes | log₁₀ of the **highest** concentration in the dilution series for this experiment. |
| 7 | `concentration` | text | yes | log₁₀ of the concentration tested at **this** row. |
| 8 | `panel_number` | text | yes | Internal panel ID (cancer-type grouping). |
| 9 | `cell_number` | text | yes | Internal cell-line ID. |
| 10 | `panel_name` | text | yes | Human-readable cancer-type panel name. |
| 11 | `cell_name` | text | yes | Human-readable cell-line name (e.g. `A549`). |
| 12 | `panel_code` | text | yes | Panel abbreviation (e.g. `LU` = lung). |
| 13 | `count_giprcnt` | text | yes | Count of GIPRCNT values aggregated in this row (usually 1). |
| 14 | `average_giprcnt` | text | yes | Average **GIPRCNT** — growth inhibition percent vs. control, T₀-corrected. See scale below. |
| 15 | `stddev_giprcnt` | text | yes | Standard deviation of GIPRCNT (usually 0 at single-experiment grain). |
| 16 | `count_ptc` | text | yes | Count of PTC values aggregated in this row. |
| 17 | `average_ptc` | text | yes | Average **PTC** — percent of treated cell growth as a fraction of control. Recalculated for this release; may be null where only GIPRCNT exists. |
| 18 | `stddev_ptc` | text | yes | Standard deviation of PTC. |

---

## Core response metrics

### GIPRCNT (`average_giprcnt`)
**Growth inhibition percent relative to control**, corrected for the cell count at the time of
drug addition (T₀).

| Value | Meaning |
| ---: | --- |
| `100` | Control growth (no inhibition) |
| `0` | Complete inhibition of growth (cytostasis) |
| `-100` | Complete cell kill |

GI50, TGI, and LC50 endpoints are derived by **simple interpolation** of GIPRCNT values
crossing **50**, **0**, and **-50** respectively.

### PTC (`average_ptc`)
**Percent of Treated cell growth as a fraction of Control.** The **IC50** endpoint is
interpolated from PTC (not GIPRCNT). PTC was not stored historically and was recalculated for
this release; a few rows report GIPRCNT with a null PTC.

### Derived endpoints (in sibling tables)

| Endpoint | GIPRCNT target | Plain language | Table |
| --- | ---: | --- | --- |
| GI50 | 50 | Slowed growth to 50% of control | `raw_nci_nci60_gi50` |
| TGI | 0 | Total growth inhibition (no net growth) | `raw_nci_nci60_tgi` |
| LC50 | −50 | 50% lethal (net cell killing) | `raw_nci_nci60_lc50` |
| IC50 | from PTC | 50% inhibition on PTC scale | `raw_nci_nci60_ic50` |

Typical ordering when all three GIPRCNT-derived endpoints are measurable: **GI50 < TGI < LC50**
("slowed it down" → "stopped it" → "killed it").

---

## Keys & relationships

- **No declared keys.** The logical grain is `(nsc, expid, cell_number, concentration)`.
- **Cell-line identity:** `panel_number` + `cell_number` uniquely identify a cell line;
  `cell_name` / `panel_name` are labels; `panel_code` is the panel abbreviation.
- **Joins to endpoint tables** (`_gi50`, `_tgi`, `_lc50`, `_ic50`) on `nsc` + `expid` +
  `cell_number` (those tables share the same identity columns but carry one interpolated
  `average` per NSC × EXPID × cell line instead of per-concentration rows).

---

## Usage notes & caveats

- **Cast before computing.** All columns are `text`; e.g. `average_giprcnt::numeric`,
  `concentration::numeric`, `count_giprcnt::int`.
- **Concentrations are log₁₀.** `concentration` and `log_hi_concentration` are already log-scaled.
- **Nulls are expected** in `average_ptc` / `count_ptc` for some dilution points.
- **No release QC.** Lab-level QC was applied when experiments ran, but no additional QC or
  consistency checks were applied for the public release. Cancelled experiments are excluded
  (shipped separately as `*_Cancelled.csv`).
- **Replicates are rare.** At single-experiment grain, most rows have `count_* = 1` and
  `stddev_* = 0`.

---

## Example queries

```sql
-- Full dose-response curve for one compound × cell line × experiment
SELECT concentration::numeric        AS log_conc,
       average_giprcnt::numeric      AS giprcnt,
       average_ptc::numeric          AS ptc
FROM   raw_nci_nci60_doseresp
WHERE  nsc = '123127'
  AND  cell_name = 'SK-MEL-28'
  AND  expid = '0001MD02'
ORDER  BY concentration::numeric;

-- Distinct cell lines in the lung panel
SELECT DISTINCT cell_name
FROM   raw_nci_nci60_doseresp
WHERE  panel_code = 'LU'
ORDER  BY cell_name;

-- Concentration points per experiment for a compound (dilution-series length)
SELECT expid, count(*) AS conc_points
FROM   raw_nci_nci60_doseresp
WHERE  nsc = '123127'
GROUP  BY expid
ORDER  BY conc_points DESC;
```

---

## Sample row (live)

A representative row from the loaded table (verified 2026-05-31):

| Column | Value |
| --- | --- |
| `release_date` | `20210223` |
| `expid` | `0303RS52` |
| `prefix` | `S` |
| `nsc` | `726263` |
| `concentration_unit` | `M` |
| `log_hi_concentration` | `-4` |
| `concentration` | `-7` |
| `panel_number` | `9` |
| `cell_number` | `13` |
| `panel_name` | `Renal Cancer` |
| `cell_name` | `A498` |
| `panel_code` | `REN` |
| `count_giprcnt` | `1` |
| `average_giprcnt` | `108.3221` |
| `stddev_giprcnt` | `0` |
| `count_ptc` | `1` |
| `average_ptc` | `102.502` |
| `stddev_ptc` | `0` |

(Note `average_giprcnt` = 108.32 > 100 — i.e. growth *above* control at this low dose, a normal occurrence in raw data.)

---

## Lineage

| Aspect | Value |
| --- | --- |
| Upstream file | `...\NCI\NCI60\NCI60\DOSERESP\DOSERESP.csv` |
| Loader | `scripts/csv_to_datawarehouse.py` (auto-creates all columns as TEXT) |
| Local DB | `data_warehouse` (see `infra/docker-compose.yml`, `scripts/config.yaml`) |
| Naming convention | `raw_nci_nci60_{file}` — raw load · NCI source · NCI60 panel · file stem |
| Release | April 2026 NCI-60 Growth Inhibition bulk |

---

## References

- [NCI-60 Growth Inhibition Data (NCI DTP wiki)](https://wiki.nci.nih.gov/spaces/NCIDTPdata/pages/147193864/NCI-60+Growth+Inhibition+Data) — primary column definitions and release notes
- Project doc: `GMM/docs-for-ai/nci-60-growth-inhibition-data.md` — narrative dataset documentation
- Project doc: `GMM/docs-for-ai/notes-on-nci-datasource.md` — GI50 vs. EC50 / S′ cross-validation
- Boyd MR, Paull KD. *Some practical considerations and applications of the NCI in vitro anticancer drug discovery screen.* Drug Dev Res. 1995.

**Last updated:** 2026-05-31 — column list verified live against `data_warehouse.public.raw_nci_nci60_doseresp`; definitions aligned with the April 2026 bulk release.
