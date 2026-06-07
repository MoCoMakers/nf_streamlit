-- Add sprime fit-result columns to im_nci_nci60_doseresp_sprime_list.
-- Idempotent: uses ADD COLUMN IF NOT EXISTS.
--
-- curve_id is a surrogate primary key. We pass it to sprime as Compound_ID
-- (with the real cell_line as Cell_Line) so that (Compound_ID, Cell_Line) is
-- guaranteed unique across the upload regardless of how many curves share an
-- nsc/cell_line combination -- and so we can join fit results back unambiguously.

ALTER TABLE im_nci_nci60_doseresp_sprime_list
    ADD COLUMN IF NOT EXISTS curve_id        bigserial,
    ADD COLUMN IF NOT EXISTS s_prime         double precision,
    ADD COLUMN IF NOT EXISTS ec50            double precision,
    ADD COLUMN IF NOT EXISTS zero_asymptote  double precision,
    ADD COLUMN IF NOT EXISTS inf_asymptote   double precision,
    ADD COLUMN IF NOT EXISTS hill_slope      double precision,
    ADD COLUMN IF NOT EXISTS r_squared       double precision,
    ADD COLUMN IF NOT EXISTS fit_status      text,
    ADD COLUMN IF NOT EXISTS fit_warnings    text,
    ADD COLUMN IF NOT EXISTS sprime_version  text,
    ADD COLUMN IF NOT EXISTS fit_run_id      text,
    ADD COLUMN IF NOT EXISTS fit_at          timestamptz;

CREATE UNIQUE INDEX IF NOT EXISTS ux_nci60_sprime_list_curve_id
    ON im_nci_nci60_doseresp_sprime_list (curve_id);

CREATE INDEX IF NOT EXISTS ix_nci60_sprime_list_fit_run
    ON im_nci_nci60_doseresp_sprime_list (fit_run_id, fit_status);
