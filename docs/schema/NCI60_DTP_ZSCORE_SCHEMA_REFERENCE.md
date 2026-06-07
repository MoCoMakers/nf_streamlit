# Schema Reference — `raw_nci_dtp_nci_zscore`

Raw load of the **CellMiner / DTP NCI-60 compound activity z-score** matrix — one row per
compound (NSC), with z-scored mean activity across the 60 NCI-60 cell lines as columns.

- **Table:** `public.raw_nci_dtp_nci_zscore`
- **Source:** `data/DTP_NCI60_ZSCORE/output/DTP_NCI60_ZSCORE.xlsx`, sheet `all`
- **Provenance:** CellMiner Database **v2.15**, Human Genome **HG-19**, dated **09-17-2025** (from the workbook preamble, rows 1–5)
- **Grain:** one row per compound (`nsc`)
- **Size:** 25,731 rows × 68 columns, all `text`
- **Converter:** [`scripts/convert_nci60_zscore_xlsx.py`](scripts/convert_nci60_zscore_xlsx.py) (skips the 8-row CellMiner preamble; header = row 9)
- **Column map:** `data/DTP_NCI60_ZSCORE/output/DTP_NCI60_ZSCORE_column_map.csv` (original `PANEL:CellName` header → sql column)
- **Loader:** [`scripts/csv_to_datawarehouse.py`](scripts/csv_to_datawarehouse.py)
- **Built / verified:** 2026-06-01

> **Raw load:** all columns are `TEXT`. Numeric z-scores are stored as text and **missing
> values are the literal string `na`** (not NULL/empty). Cast with
> `NULLIF(col,'na')::numeric` before arithmetic.

---

## What this table is (and is not)

The z-score is the **average of a compound's activity across QC-passing NCI-60 experiments**,
standardized per the CellMiner pipeline (see `output/documentation/Drug_data_explained.xls`).
Higher/lower z = relatively more/less active in that cell line vs. the compound's profile.

- **It is a compound × cell-line activity matrix.** Cell lines appear only as **column headers**
  (`BR:MCF7`, `LC:A549/ATCC`, …) — there are **no ACH-#### or Cellosaurus CVCL identifiers** here.
  This table does **not** bridge NCI-60 names to DepMap `ACH-…`; that still needs Cellosaurus.
- The compound metadata columns **do** form a usable NSC ↔ PubChem SID ↔ name ↔ SMILES crosswalk.

---

## Column groups

### A. Compound metadata (columns 1–6)

| Column | Source header | Definition |
| --- | --- | --- |
| `nsc` | `NSC # b` | NCI compound identifier (grain). |
| `drug_name` | `Drug name` | Common/trivial drug name. `-` where none. |
| `fda_status` | `FDA status` | FDA status flag. `-` where none. |
| `mechanism_of_action` | `Mechanism of action c` | MOA label (see `Drug_data_explained.xls`). `-` where none. |
| `pubchem_sid` | `PubChem SID` | PubChem **substance** ID (compound, not cell line). |
| `smiles` | `SMILES d` | SMILES structure, from DTP. |

### B. Cell-line z-scores (columns 7–66, 60 cell lines)

One column per NCI-60 line, named `{panel}_{cellname}` (lowercased, non-alphanumerics → `_`).
Panel prefixes: `br` breast, `cns` CNS, `co` colon, `le` leukemia, `me` melanoma, `lc` lung,
`ov` ovarian, `pr` prostate, `re` renal.

| Example sql column | Original header |
| --- | --- |
| `br_mcf7` | `BR:MCF7` |
| `lc_a549_atcc` | `LC:A549/ATCC` |
| `ov_nci_adr_res` | `OV:NCI/ADR-RES` |
| `me_mda_n` | `ME:MDA-N` |

Full list in the column-map CSV. Values are z-scores as text, or `na` if absent.

### C. Experiment counts (columns 67–68)

| Column | Source header | Definition |
| --- | --- | --- |
| `total_experiments` | `Total experiments e` | NCI-60 experiments performed on this compound. |
| `total_after_qc` | `Total after quality control f` | Experiments that passed QC (basis for the z-score average). |

---

## Usage notes

- **Wide → long** for joins/analysis:
  ```sql
  -- one (nsc, cell_line, zscore) row per value, ignoring 'na'
  SELECT nsc, 'br_mcf7' AS cell_col, NULLIF(br_mcf7,'na')::numeric AS zscore
  FROM raw_nci_dtp_nci_zscore WHERE br_mcf7 <> 'na'
  -- ... UNION ALL across the 60 columns, or use a crosstab/unpivot helper.
  ```
- **Cell-line column names** are lossy (`/`, `-` collapsed to `_`). Always resolve back through the
  column-map CSV to the canonical `PANEL:CellName`.
- The cell-line names here match the NCI-60 set used in `raw_nci_nci60_doseresp.cell_name` — useful
  for cross-referencing, but join on a cleaned name, not the sanitized column label.

---

## Compound-name quality vs. `im_nci_nsc_compounds` (measured)

Question raised: are these `drug_name` values "better" than the names already loaded in
`im_nci_nsc_compounds.preferred_name`? Measured with PostgreSQL `pg_trgm` (extension installed
2026-06-01), comparing **lowercased** strings on the 9,107 NSCs present in both tables:

| Metric | Value |
| --- | ---: |
| NSCs joined & named in both | 9,107 |
| Avg trigram `similarity(lower,lower)` | **0.709** |
| Exact match (lowercased) | 3,581 (39%) |
| Very different (`similarity < 0.3`) | 1,345 (15%) |

**Verdict:** neither source is uniformly "better" — they are **complementary**:

- z-score `drug_name` tends to be the **common/trivial** name (`tolylquinone`, `Cactinomycin`,
  `Nitrogen mustard`, `8-Azaguanine`).
- `im_nci_nsc_compounds.preferred_name` tends to be the **systematic/registry** name
  (`TOLUQUINONE (VAN)`, `3-[2-(3,5-DIMETHYL-2-OXOCYCLOHEXYL)…]GLUTARIMIDE`, `CHLORAMINE (VAN)`).
- Some z-score entries are **not real names** at all (e.g. NSC 1012 → `wln: t66 bnj…`, a Wiswesser
  line notation; NSC 1026 → `acpc`, an abbreviation), so don't blindly prefer either.

Recommendation: keep both; for human-facing display prefer z-score `drug_name` when it is
alphabetic and `similarity > ~0.3`, else fall back to `preferred_name`. Treat sub-0.3 rows as
review candidates rather than auto-replacing.

### Reusable lowercase similarity check

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- one time

SELECT z.nsc,
       z.drug_name        AS zscore_name,
       c.preferred_name   AS existing_name,
       round(similarity(lower(z.drug_name), lower(c.preferred_name))::numeric, 3) AS sim
FROM raw_nci_dtp_nci_zscore z
JOIN im_nci_nsc_compounds c ON c.nsc = z.nsc
WHERE z.drug_name <> '-' AND c.preferred_name <> ''
ORDER BY sim;          -- lowest similarity = biggest disagreements first
```

`similarity()` returns 0–1 (≈ percent trigram overlap); `lower()` makes it case-insensitive.
For edit-distance instead, `fuzzystrmatch` is also available (`levenshtein()`).

---

## Related tables

- `raw_nci_nci60_doseresp` and endpoint tables — raw NCI-60 dose-response (long form).
- `im_nci_nsc_compounds`, `raw_nci_nsc_chemical_names` — existing NSC compound-name sources.
- Cellosaurus (pending) — the resource needed for the cell-line name ↔ `ACH-####` bridge.

**Last updated:** 2026-06-01 — loaded and verified against local `data_warehouse`; name-quality comparison measured via `pg_trgm`.
