-- Generalizes references/demeter/rnai_analysis.py's POOL_MEMBERS_SQL to ALL
-- driver genes and ALL tissues (the reference script hardcoded 4 driver genes
-- and LUNG only). Grain: one row per (driver_gene_id, tissue, ccle_id) with
-- its resolved 0/2 genotype pool.
--
-- mutation_value coding (im_dep_sprime_damaging_mutations): 0 = 0/2 alleles
-- damaged (WT/reference), 1 = 1/2 (heterozygous -- indeterminate, EXCLUDED),
-- 2 = 2/2 (biallelic damaging -- mutant). A cell line with conflicting 0-and-2
-- calls for the same gene (ambiguous source data) is discarded entirely, same
-- as the reference script's driver_conflicts logic.
--
-- Performance note: the reference script (and a naive generalization) joins
-- via cell_line = ANY(string_to_array(depmap_ach, '|')), which cannot use an
-- index and is what made even single-gene pilot queries take minutes. Here
-- the pipe-delimited depmap_ach is unnested ONCE into ach_expanded (a few
-- hundred rows), then joined to the mutation table with a plain equality
-- predicate -- run add_rnai_analysis_indexes.sql first so that join is an
-- index lookup, not a sequential scan.
--
-- Diagnostic/derived table only -- carries no pipeline state, so this is
-- safe to fully rebuild (DROP + CREATE AS) on every run.

DROP TABLE IF EXISTS im_depm_demeter_rnai_pool_members;

CREATE TABLE im_depm_demeter_rnai_pool_members AS
WITH demeter_cells AS (
    SELECT DISTINCT upper(ccle_id) AS ccle_id
    FROM raw_depm_demeter_combined_gene_dep_scores
),
mapped_cells AS (
    SELECT DISTINCT
        dc.ccle_id,
        b.tissue,
        b.depmap_ach,
        b.match_source
    FROM demeter_cells dc
    JOIN im_depm_demeter_cellosurus_to_ach_cellline_mapping b
      ON upper(b.ccle_id) = dc.ccle_id
    WHERE b.depmap_ach IS NOT NULL
),
ach_expanded AS (
    SELECT DISTINCT
        mc.ccle_id,
        mc.tissue,
        unnest(string_to_array(mc.depmap_ach, '|')) AS ach_id
    FROM mapped_cells mc
),
driver_status_raw AS (
    SELECT
        ae.ccle_id,
        ae.tissue,
        m.gene_id,
        m.mutation_value
    FROM ach_expanded ae
    JOIN im_dep_sprime_damaging_mutations m
      ON m.cell_line = ae.ach_id
    WHERE m.mutation_value IN (0, 2)
),
driver_conflicts AS (
    SELECT ccle_id, gene_id
    FROM driver_status_raw
    GROUP BY ccle_id, gene_id
    HAVING count(DISTINCT mutation_value) > 1
),
driver_status AS (
    SELECT
        dsr.ccle_id,
        dsr.tissue,
        dsr.gene_id,
        min(dsr.mutation_value) AS mutation_value
    FROM driver_status_raw dsr
    WHERE NOT EXISTS (
        SELECT 1 FROM driver_conflicts dc
        WHERE dc.ccle_id = dsr.ccle_id AND dc.gene_id = dsr.gene_id
    )
    GROUP BY dsr.ccle_id, dsr.tissue, dsr.gene_id
    HAVING count(DISTINCT dsr.mutation_value) = 1
)
SELECT
    ds.gene_id AS driver_gene_id,
    g.name     AS driver_gene,
    ds.tissue,
    ds.ccle_id AS demeter_ccle_id,
    ds.mutation_value,
    CASE ds.mutation_value WHEN 0 THEN 'WT_REF' WHEN 2 THEN 'MUT' END AS genotype_pool
FROM driver_status ds
LEFT JOIN im_omics_genes g ON g.id = ds.gene_id;

CREATE INDEX ON im_depm_demeter_rnai_pool_members (driver_gene_id, tissue);

GRANT SELECT ON im_depm_demeter_rnai_pool_members TO compbio_dw_readonly;
