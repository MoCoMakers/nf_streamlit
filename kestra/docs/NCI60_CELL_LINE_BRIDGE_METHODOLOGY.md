# NCI-60 → DepMap (ACH) cell-line bridge — methodology & audit

**Scope.** How NCI-60 dose-response cell-line names are linked to DepMap `ACH-######`
identifiers (the join key the genotype / S′ tables use), every filter applied along the
way, and an audit of whether the process is *exacting, secure, and reproducible*.

**Status of this audit:** 2026-06-15. Bridge build SQL + flow exist and are sound; the
load step was wired this session. Verdict and required fixes are in §6.

---

## 1. Dataflow (end to end)

```
 ExPASy Cellosaurus flat file            Google Drive (NCI DTP bulk release)
 cellosaurus.txt  (v55, 2026-03)         DOSERESP.csv ...
        │                                        │
        │ extract_cellosaurus_celllines.py       │ load_nci60_raw.py + nci60_manifest.yaml
        ▼                                        ▼  (→ csv_to_datawarehouse.py, COPY)
 cellosaurus_celllines.csv                raw_nci_nci60_doseresp
  (cvcl_id,name,synonyms,                  (cell_name, panel_name, nsc, ...)
   depmap_ach,nci_dtp_name)                       │
        │ csv_to_datawarehouse.py                 │
        ▼  (→ raw_cellosaurus_celllines)          │
                    └──────────────┬──────────────┘
                                   ▼  build_im_cellosaurus_nci60_to_depmap_bridge.sql
                          im_cellosaurus_nci60_to_depmap_bridge
                          (cell_name → cvcl_id → depmap_ach, match_source, ambiguity)
                                   │  join on depmap_ach = cell_line
                                   ▼
                     im_dep_sprime_damaging_mutations   (genotypes, ACH-keyed)
                     im_nci_nci60_doseresp_sprime_list  (NCI-60 S′, cell_name-keyed)
```

**Backbone scripts (all present + documented):**

| Stage | Artifact | Role |
|---|---|---|
| Extract | `kestra/scripts/extract_cellosaurus_celllines.py` | Parse `cellosaurus.txt` → flat CSV; pulls `DR DepMap;` and `DR NCI-DTP;` xrefs |
| Download | `kestra/scripts/download_gdrive_datasets.py` | Fetch NCI-60 CSVs from the public Drive folder |
| Load | `kestra/scripts/csv_to_datawarehouse.py` | psycopg3 `COPY` loader (env-var creds, parameterized identifiers) |
| Orchestrate load | `kestra/scripts/load_nci60_raw.py` + `nci60_manifest.yaml` | Local-first download + bulk load of NCI raw tables |
| Build bridge | `kestra/scripts/sql/build_im_cellosaurus_nci60_to_depmap_bridge.sql` | Leveled **exact-only** matcher (levels 1–3) → `im_cellosaurus_nci60_to_depmap_bridge` |
| Pipeline | `kestra/flows/nci60/03_build_cell_xref.yml` | extract-if-needed → load `raw_cellosaurus_celllines` → run build SQL → verify |

> Superseded: an earlier `build_cellosaurus_nci60_bridge.py` (commit `d42a42e`) did a
> Python-side match. It is **deleted** — the SQL above is the single source of truth.
> Do not resurrect it; two competing bridges would diverge.

---

## 2. Every filter, in order

### 2.1 Cellosaurus extract (`extract_cellosaurus_celllines.py`)
- One row per Cellosaurus entry (`ID`…`//` block).
- `cvcl_id` ← `AC` line (primary accession).
- `synonyms` ← `SY` line, split on `;`, pipe-joined.
- `depmap_ach` ← every `DR   DepMap; <id>` line, pipe-joined. **Filter: only `DepMap` xrefs.**
- `nci_dtp_name` ← every `DR   NCI-DTP; <name>` line, pipe-joined. **Filter: only `NCI-DTP` xrefs.**
- **Guard:** if any name/synonym already contains the pipe `|` delimiter, the script
  **aborts** (loud failure, no silent escaping).
- Empty list fields are written as `""` (→ become NULL on CSV `COPY`, see §2.2).

### 2.2 Raw load (`csv_to_datawarehouse.py`)
- Table created with all columns `TEXT`, in CSV header order.
- `COPY ... WITH (FORMAT csv, HEADER true)`. **Empty unquoted fields → NULL.**
- `--replace` truncates an existing table (creates it if absent). Identifiers passed via
  `psycopg.sql.Identifier` — **no string interpolation** (injection-safe).

### 2.3 NCI-60 cell-name universe (`build_im_cellosaurus_nci60_to_depmap_bridge.sql`, `our_cells` CTE)
- `SELECT DISTINCT cell_name FROM raw_nci_nci60_doseresp`
- **Filter:** `cell_name IS NOT NULL AND cell_name <> ''`.
- This is the *full* DTP testing roster (163 distinct names), **including engineered
  constructs** (`A-CREB`, `A-FOS`, `*p53RE*`, `T47D ERE4`, `VDSO/CMV-*`, …) that are not
  catalogued cell lines and will never carry an ACH. The canonical NCI-60 panel is ~60.

### 2.4 Candidate expansion (`cello_candidates` CTE)
One `(cvcl_id, candidate, src)` row per matchable string:
- `name` (src=`name`)
- each `unnest(string_to_array(nci_dtp_name,'|'))` (src=`nci_dtp`)
- each `unnest(string_to_array(synonyms,'|'))` (src=`synonym`)

### 2.5 Match levels (EXACT only; highest-confidence first)
A `cell_name` is assigned to the **lowest-numbered** level that yields any hit. All three
levels are **exact string equality** — no normalization, no fuzzy / edit-distance matching:

| lvl | `match_source` | rule |
|---|---|---|
| 1 | `nci_dtp_exact` | `cell_name` = a `nci_dtp_name` value (exact) |
| 2 | `name_exact` | `cell_name` = Cellosaurus display name (exact) |
| 3 | `synonym_exact` | `cell_name` = a synonym (exact) |

- **Normalized levels removed (2026-06).** A prior version also ran levels 4–6
  (`lower()` + strip `[[:space:]._/-]`). An audit on Cellosaurus v55 showed they matched
  exactly **one** NCI-60 name and resolved **zero** ACH — no coverage, all the
  false-positive risk (normalization collisions, parental/subclone drift). Dropping them
  left the pan-tissue TP53 arm unchanged (43 mut / 24 WT) and made the bridge provably
  exact-only.
- The `/ATCC`, `/H.Fine` etc. suffixes still match because Cellosaurus already lists those
  exact forms as synonyms (e.g. `A549/ATCC` is a synonym of `CVCL_0023`), caught at level 3.
- **`synonym_exact` (level 3) is the only tier warranting a manual spot-check** — it is
  exact, but against a curated synonym rather than a primary/DTP name (~13 rows on v55;
  filter `match_source = 'synonym_exact'`).

### 2.6 Ambiguity rule
- If the best level produces **>1 distinct `cvcl_id`**, then `cvcl_id` and `depmap_ach`
  are **NULL** and `match_source = 'ambiguous_lvl<N>'`; `candidate_cvcls` / `candidate_names`
  preserve the options for human review. Only **unique** matches yield a usable ID.

### 2.7 ACH extraction (final SELECT)
- `depmap_ach` is pulled from the uniquely-matched Cellosaurus row **as stored**.
- A unique index enforces one row per `cell_name`.

### 2.8 Downstream genotype join (analysis-time, not in the bridge)
- `im_cellosaurus_nci60_to_depmap_bridge.depmap_ach = im_dep_sprime_damaging_mutations.cell_line`
- Genotype filter: `mutation_value` **0 = wild-type**, **1 = heterozygous (EXCLUDED)**,
  **2 = biallelic-damaging = mutant**. Gene IDs: TP53 7115, RB1 4890, PTEN 2239,
  CDKN2A 17047. *(Biallelic-damaging=mutant rule still `[confirm vs manuscript Methods]`.)*
- Tissue filter (lung-specific work): `im_sprime_solved_s_prime.ccle_name LIKE '%_LUNG'`.
  Pan-tissue analysis omits this filter (see coverage note §5).

---

## 3. Audit — exacting?

**Largely yes, with two call-outs.**
- ✅ Deterministic: pure set/string ops, `string_agg(... ORDER BY ...)` — stable output,
  no randomness, no seed needed.
- ✅ Conservative: exact-only (levels 1–3), no normalization, no fuzzy matching, ambiguity
  never silently resolved.
- ⚠️ **Merged-ACH not split (correctness gap).** 21 Cellosaurus rows hold pipe-joined ACH
  (`ACH-x|ACH-y`, retired/merged accessions). For a `cell_name` matching such a row,
  `depmap_ach` becomes the literal `"ACH-x|ACH-y"`, which **fails** the downstream
  `= cell_line` equality join. Affects a small number of NCI-60 lines (observed e.g.
  `ACH-000338|ACH-001665`). Fix: split and pick the live/primary ACH, or expand to rows.
- ⚠️ No `trim()` on `cell_name` before exact compare (level 1–3). Harmless today (no
  leading/trailing spaces observed) but not defended.

## 4. Audit — secure?

**Yes.**
- ✅ Credentials only from `PG*` env vars (Kestra secrets → task env). `config.yaml` is
  **absent** on disk — no hardcoded fallback creds.
- ✅ `tools.yaml` (MCP RW password) is gitignored; `data/NCI` gitignored.
- ✅ `csv_to_datawarehouse.py` uses `psycopg.sql.Identifier` and `COPY` — no SQL built by
  string concatenation; injection-safe even though table names are caller-supplied.
- ⚠️ Operational, not a leak: the build SQL issues **no `GRANT`**, so after a fresh build
  the read-only role (`compbio_dw_readonly`, used by the MCP/analysis) cannot `SELECT`
  `im_cellosaurus_nci60_to_depmap_bridge`. Add `GRANT SELECT ... TO compbio_dw_readonly;` (same pattern as
  the `raw_depm_*` tables).

## 5. Audit — 100% reproducible?

**Not yet — fixable.** The matching logic is deterministic, but the *inputs* are not pinned:

1. **Cellosaurus release is not captured.** The file is v55 (March 2026); ACH accessions
   merge/retire between releases, so a future re-run on a newer flat file can change the
   ACH mapping. Nothing records the release used. → Record the Cellosaurus version (parse
   the release line, or stamp it as a column / provenance row in `raw_cellosaurus_celllines`).
2. **NCI-60 release is not stamped** in `raw_nci_nci60_doseresp` (manifest comment says
   "April 2026 bulk release" — prose only).
3. **Unpinned dependencies.** The flow `pip install`s `psycopg[binary] pyyaml` with no
   version locks. → Pin exact versions.
4. **`--skip-if-exists` staleness.** If `cellosaurus.txt` is refreshed but the cached
   `cellosaurus_celllines.csv` remains, the extract is silently skipped and the stale CSV
   is loaded. → Compare mtimes/hash, or key the cache on the Cellosaurus version.
5. **No input checksum / provenance.** → Record a SHA-256 of both source files alongside
   the build for true bit-reproducibility.

## 6. Required fixes to reach "exacting + 100% reproducible"

- [ ] Split merged ACH (`ACH-x|ACH-y`) → live primary; re-test downstream join (§3).
- [ ] Add `GRANT SELECT ON im_cellosaurus_nci60_to_depmap_bridge TO compbio_dw_readonly;` to the build SQL (§4).
- [ ] Capture Cellosaurus version + source SHA-256 into a provenance column/table (§5.1, §5.5).
- [ ] Pin `pip` versions in `03_build_cell_xref.yml` (§5.3).
- [ ] Make the extract cache version-aware instead of bare `--skip-if-exists` (§5.4).
- [ ] Confirm the biallelic-damaging=mutant genotype rule against manuscript Methods (§2.8).

## 7. Verified coverage (Cellosaurus v55, this audit)

Exact-only (levels 1–3), Cellosaurus v55:

- 163 distinct NCI-60 `cell_name` → **~124 match a CVCL**, of which **~79 carry a usable
  ACH**; 0 ambiguous. The rest are engineered constructs / lines absent from DepMap.
- Match-level breakdown (names, with-ACH): L1 `nci_dtp_exact` 62/51; L2 `name_exact` 38/15;
  L3 `synonym_exact` 24/13. (Removed normalized levels would have added 1 name / 0 ACH.)
- Genotype arms (mutant / WT):
  - lung-only: TP53 6/6 (RB1/PTEN/CDKN2A dead).
  - pan-tissue, levels 1–3: **TP53 43/24, PTEN 15/59, RB1 4/70, CDKN2A 4/66**.
  - pan-tissue, levels 1–2 only (drop synonyms): TP53 38/19, PTEN 10/53 — i.e. the synonym
    tier adds ~5 TP53 and ~5 PTEN mutants over exact name/DTP alone.

