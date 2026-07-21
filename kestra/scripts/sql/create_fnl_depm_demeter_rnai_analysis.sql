-- Final table. One row per (driver_gene_id, tissue, target_gene) with a
-- usable WT/MUT pool split -- the generalized, all-drivers/all-targets/
-- all-tissues successor to references/demeter/rnai_analysis.py's
-- rnai_delta_lung_driver_target.csv (validated to match it exactly for
-- TP53 x A1BG x LUNG before this was built).
--
-- INSERT-only: populated in batches by run_demeter_rnai_analysis.py, keyed
-- off im_depm_demeter_rnai_work_queue. NOT dropped/recreated on rerun -- rows
-- accumulate as the work queue drains, matching the resumable pattern in
-- run_sprime_fit.py.

CREATE TABLE IF NOT EXISTS fnl_depm_demeter_rnai_analysis (
    driver_gene_id                          INTEGER NOT NULL,
    driver_gene                             TEXT,
    tissue                                  TEXT NOT NULL,
    target_gene                             TEXT NOT NULL,
    mean_ref_dep_score_for_target           DOUBLE PRECISION,
    mean_mut_dep_score_for_target           DOUBLE PRECISION,
    delta_rnai_dep_score_driver_and_target  DOUBLE PRECISION,
    ref_pool_cell_lines_for_driver          INTEGER,
    mut_pool_cell_lines_for_driver          INTEGER,
    ref_dep_score_observations_for_target   INTEGER,
    mut_dep_score_observations_for_target   INTEGER,
    analysis_run_id                         TEXT,
    analysis_at                             TIMESTAMPTZ,
    PRIMARY KEY (driver_gene_id, tissue, target_gene)
);

GRANT SELECT ON fnl_depm_demeter_rnai_analysis TO compbio_dw_readonly;
