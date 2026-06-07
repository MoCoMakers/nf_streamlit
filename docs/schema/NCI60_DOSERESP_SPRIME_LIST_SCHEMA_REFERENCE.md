# Schema Reference — `im_nci_nci60_doseresp_sprime_list`

Intermediate (`im`) warehouse table that reshapes the raw NCI-60 dose-response data into the
[sprime](https://github.com/MoCoMakers/sprime) **Path A list** layout — one row per
dose-response **curve**, with comma-separated `responses` / `concentrations` cells ready to
export for `sp.load(values_as="list", ...)`.

- **Table:** `public.im_nci_nci60_doseresp_sprime_list`
- **Built from:** `raw_nci_nci60_doseresp` (see [NCI60_DOSERESP_SCHEMA_REFERENCE.md](NCI60_DOSERESP_SCHEMA_REFERENCE.md))
- **Build script:** [`scripts/build_nci60_doseresp_sprime_list.sql`](scripts/build_nci60_doseresp_sprime_list.sql)
- **Plan:** [`GMM/docs-for-ai/plan-nci60-doseresp-to-sprime-list.md`](GMM/docs-for-ai/plan-nci60-doseresp-to-sprime-list.md)
- **sprime format spec:** [`GMM/docs-for-ai/sprime-raw-list-format.md`](GMM/docs-for-ai/sprime-raw-list-format.md)
- **Grain:** one row per **EXPID × NSC × panel_number × cell_number** (one fittable curve)
- **Built / verified:** 2026-06-01

---

## Build results (verified live)

| Metric | Value |
| --- | ---: |
| Total curves | 4,858,493 |
| `load_eligible = true` (≥ 4 points) | 4,832,820 |
| `load_eligible = false` (< 4 points) | 25,673 |
| Distinct compounds (`nsc`) | 59,375 |
| Distinct cell lines (`cell_line`) | 163 |
| Distinct experiments (`expid`) | 5,182 |
| Response/concentration length mismatches | 0 |

Source rows consumed: 24,280,072 (`concentration_unit = 'M'`) of 24,492,523 total. The
`u` (µg/ml, 198,292 rows) and `V` (volume, 14,159 rows) units are **excluded in v1**.

---

## Column dictionary

| # | Column | Type | sprime role | Source / rule |
| ---: | --- | --- | --- | --- |
| 1 | `expid` | text | (pass-through) | `expid` |
| 2 | `nsc` | text | (pass-through) | `nsc` |
| 3 | `prefix` | text | (pass-through) | `prefix` |
| 4 | `compound_id` | text | **Compound_ID** | `nsc` |
| 5 | `cell_line` | text | **Cell_Line** | `cell_name` |
| 6 | `panel_number` | text | (pass-through) | `panel_number` — part of grain |
| 7 | `cell_number` | text | (pass-through) | `cell_number` — part of grain (not globally unique) |
| 8 | `panel_name` | text | (pass-through) | `panel_name` |
| 9 | `panel_code` | text | (pass-through) | `panel_code` |
| 10 | `concentration_units` | text | **Concentration_Units** | constant `'microM'` (post-conversion) |
| 11 | `original_concentration_unit` | text | — | constant `'M'` (source unit of v1 rows) |
| 12 | `log_hi_concentration` | text | — | `max(log_hi_concentration)` (metadata; constant within a curve) |
| 13 | `release_date` | text | — | `max(release_date)` |
| 14 | `control_response` | text | **Control_Response** | `NULL` — DOSERESP ships no per-curve DMSO; see §Decisions |
| 15 | `n_points` | integer | — | count of valid dose points in the curve |
| 16 | `load_eligible` | boolean | — | `n_points >= 4` (sprime Hill-fit minimum) |
| 17 | `responses` | text | **Responses** | `string_agg(average_ptc, ',' ORDER BY concentration)` |
| 18 | `concentrations` | text | **Concentrations** | `string_agg(10^(concentration+6), ',' ORDER BY concentration)` — linear µM |

**Indexes:** `(nsc, expid, cell_line)` for lookup/export; `(load_eligible)` for filtering.

---

## Design decisions (important — these differ from a naive mapping)

1. **Response = PTC (`average_ptc`).** As requested. PTC = percent of treated-vs-control growth
   (the basis for IC50). 27,949 source points with blank PTC are dropped at the point level.

2. **Concentration = `concentration`, NOT `log_hi_concentration`.** The original request named
   `log_hi_concentration`, but that column is the **single highest dose** in the series and is
   **constant for every point in a curve** (e.g. `-4` repeated). The true per-point dose is the
   `concentration` column (e.g. `-8, -7, -6, -5, -4`). Using `log_hi_concentration` would assign
   every dose the same value. → We use `concentration`.

3. **Concentrations are unlogged to µM.** Source `concentration` is **log₁₀ molar**. Conversion:
   linear M = `10^concentration`; linear µM = `10^concentration * 1e6 = 10^(concentration+6)`.
   Verified: `concentration` `{-8,-7,-6,-5,-4}` → `{0.01, 0.1, 1, 10, 100}` µM.

4. **Curve grain = `(expid, nsc, panel_number, cell_number)`.** `cell_number` alone is **not**
   globally unique — e.g. `cell_number = 1` maps to 7 different cell lines across panels — so the
   panel + cell number together (plus nsc + expid) define one curve. `cell_name` is carried as the
   sprime `Cell_Line` label.

5. **`skip_control_response_normalization = True` (corrected from request).** The request said
   `=False`, but the sprime loader **requires a non-empty, non-zero `Control_Response` on every raw
   row** when this flag is `False`, and DOSERESP has **no per-curve DMSO/vehicle column**. With
   `=False` every row would fail validation. `=True` matches the stated intent ("no control
   normalization, revisit later") and the plan doc. `control_response` is therefore `NULL`.

6. **`response_normalization = "asymptote_normalized"`.** As requested. With
   `skip_control_response_normalization=True`, sprime does **not** divide by control or re-scale at
   process time; this value documents the intended interpretation of the response scale. (Open
   item: PTC is already a 0–100 control-relative scale — revisit whether asymptote normalization is
   the right choice in the Phase-C pilot.)

---

## sprime load configuration

When exporting rows from this table to a CSV (or list-of-dicts) for sprime, rename columns to the
exact sprime headers and load with:

```python
from sprime import SPrime as sp

raw_data, load_report = sp.load(
    "nci60_sprime_list.csv",
    values_as="list",
    skip_control_response_normalization=True,        # DOSERESP has no DMSO column
    response_normalization="asymptote_normalized",
)
screening_data, process_report = sp.process(raw_data)
```

Export only `load_eligible = true` rows. Keep a `Control_Response` column present (empty cells) so
the header validation passes under `skip_control_response_normalization=True`.

### Column → sprime header mapping for export

| This table | sprime CSV header |
| --- | --- |
| `compound_id` | `Compound_ID` |
| `cell_line` | `Cell_Line` |
| `concentration_units` | `Concentration_Units` |
| `responses` | `Responses` |
| `concentrations` | `Concentrations` |
| `control_response` (empty) | `Control_Response` |
| `nsc`, `expid`, `panel_code`, … | (optional pass-through metadata) |

---

## Example queries

```sql
-- Export-ready eligible curves for one panel (lung)
SELECT compound_id AS "Compound_ID",
       cell_line   AS "Cell_Line",
       concentration_units AS "Concentration_Units",
       ''          AS "Control_Response",
       responses   AS "Responses",
       concentrations AS "Concentrations"
FROM   im_nci_nci60_doseresp_sprime_list
WHERE  load_eligible AND panel_code = 'LNS';

-- One curve
SELECT responses, concentrations
FROM   im_nci_nci60_doseresp_sprime_list
WHERE  nsc = '726263' AND expid = '0303RS52' AND cell_number = '13';

-- Point-count distribution among eligible curves
SELECT n_points, count(*) FROM im_nci_nci60_doseresp_sprime_list
WHERE load_eligible GROUP BY n_points ORDER BY n_points;
```

---

## Open items / deferred (per plan)

- **Phase C smoke test:** export ~100–1,000 eligible rows, run `sp.load` + `sp.process`, review
  `CURVE_FIT` / `MISSING_DATA` warnings; confirm `asymptote_normalized` is appropriate for the PTC
  scale (or switch to `response_scale`).
- **Response choice revisit:** GIPRCNT (`average_giprcnt`) vs PTC (`average_ptc`) — currently PTC.
- **Non-molar units:** `u` (µg/ml) and `V` rows excluded; need MW-based conversion or a separate table.
- **Compound metadata:** join NSC → name / MOA / target from DTP chemical data.
- **Downstream:** store sprime S′ output as `im_nci_nci60_sprime`; ΔS′ once ref/test lines defined.
- **HTS384:** same pattern over `raw_nci_hts384_doseresp`.

**Last updated:** 2026-06-01 — table built and verified against local `data_warehouse`.
