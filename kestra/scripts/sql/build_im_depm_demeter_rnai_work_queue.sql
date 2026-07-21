-- Work-queue / checkpoint table driving run_demeter_rnai_analysis.py's
-- batches. One row per USABLE (driver_gene_id, tissue) combo -- i.e. a combo
-- with a non-empty WT_REF pool AND a non-empty MUT pool in
-- im_depm_demeter_rnai_pool_members. That "usable" gate is what keeps the
-- work queue to real candidates instead of the full driver x tissue cross
-- product (most combos have an empty pool on one side or the other).
--
-- analysis_run_id / analysis_completed_at are the resumability checkpoint,
-- directly mirroring im_nci_nci60_doseresp_sprime_list.fit_run_id in
-- run_sprime_fit.py: a killed or restarted execution picks back up on
-- WHERE analysis_run_id IS NULL.
--
-- UNLIKE the pool-members table, this one is NOT dropped/recreated -- it
-- carries process state across runs. Re-running this script only ADDS
-- newly-usable combos (ON CONFLICT DO NOTHING); it never resets progress on
-- combos already queued or completed.

CREATE TABLE IF NOT EXISTS im_depm_demeter_rnai_work_queue (
    driver_gene_id         INTEGER NOT NULL,
    driver_gene            TEXT,
    tissue                 TEXT NOT NULL,
    ref_pool_cell_lines    INTEGER NOT NULL,
    mut_pool_cell_lines    INTEGER NOT NULL,
    analysis_run_id        TEXT,
    analysis_completed_at  TIMESTAMPTZ,
    PRIMARY KEY (driver_gene_id, tissue)
);

INSERT INTO im_depm_demeter_rnai_work_queue
    (driver_gene_id, driver_gene, tissue, ref_pool_cell_lines, mut_pool_cell_lines)
SELECT
    driver_gene_id,
    max(driver_gene) AS driver_gene,
    tissue,
    count(*) FILTER (WHERE genotype_pool = 'WT_REF') AS ref_pool_cell_lines,
    count(*) FILTER (WHERE genotype_pool = 'MUT')    AS mut_pool_cell_lines
FROM im_depm_demeter_rnai_pool_members
GROUP BY driver_gene_id, tissue
HAVING count(*) FILTER (WHERE genotype_pool = 'WT_REF') > 0
   AND count(*) FILTER (WHERE genotype_pool = 'MUT')    > 0
ON CONFLICT (driver_gene_id, tissue) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_rnai_work_queue_unclaimed
    ON im_depm_demeter_rnai_work_queue (driver_gene_id, tissue)
    WHERE analysis_run_id IS NULL;

GRANT SELECT ON im_depm_demeter_rnai_work_queue TO compbio_dw_readonly;
