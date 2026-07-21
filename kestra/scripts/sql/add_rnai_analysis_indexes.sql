-- Supporting indexes for the generalized DEMETER RNAi driver/target/tissue
-- analysis (build_im_depm_demeter_rnai_pool_members.sql,
-- run_demeter_rnai_analysis.py).
--
-- Without these, even a single-driver/single-target lookup takes minutes:
-- im_dep_sprime_damaging_mutations is 33.8M rows with no index on gene_id or
-- cell_line, and the historical join pattern (cell_line = ANY(string_to_array(
-- depmap_ach, '|'))) cannot use an index at all. The pool-members build below
-- replaces that pattern with a plain equality join against an unnested ACH
-- list, which these indexes make cheap.
--
-- IF NOT EXISTS everywhere: safe to run on every flow execution.

CREATE INDEX IF NOT EXISTS idx_dep_sprime_damaging_mutations_gene_id
    ON im_dep_sprime_damaging_mutations (gene_id);

CREATE INDEX IF NOT EXISTS idx_dep_sprime_damaging_mutations_cell_line
    ON im_dep_sprime_damaging_mutations (cell_line);

CREATE INDEX IF NOT EXISTS idx_demeter_gene_dep_scores_gene
    ON raw_depm_demeter_combined_gene_dep_scores (gene);

CREATE INDEX IF NOT EXISTS idx_demeter_gene_dep_scores_ccle_id
    ON raw_depm_demeter_combined_gene_dep_scores (ccle_id);
