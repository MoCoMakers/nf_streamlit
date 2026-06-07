-- Build im_nci_nci60_doseresp_sprime_list
-- Reshapes raw_nci_nci60_doseresp (long: one row per dose point) into the sprime
-- "Path A list" intermediate (one row per NSC x EXPID x cell-line curve), ready to
-- export for sprime sp.load(values_as="list", ...).
--
-- Decisions baked in (see NCI60_DOSERESP_SPRIME_LIST_SCHEMA_REFERENCE.md):
--   * Response column        = average_ptc  (PTC, as requested)
--   * Concentration source   = concentration (log10 M) -> linear uM via 10^(c+6)
--                              (NOT log_hi_concentration, which is constant per curve)
--   * Curve grain            = (expid, nsc, prefix, panel_number, cell_number)
--                              cell_number is NOT globally unique; panel scopes it.
--   * v1 units               = molar ('M') only; 'u'/'V' deferred.
--   * Point validity         = numeric concentration AND numeric average_ptc.
--   * load_eligible          = TRUE when >= 4 valid points (sprime Hill-fit minimum).
--   * sprime load (documented, applied at export time, not here):
--        values_as="list",
--        skip_control_response_normalization=True,   -- DOSERESP has no DMSO column
--        response_normalization="asymptote_normalized"

DROP TABLE IF EXISTS im_nci_nci60_doseresp_sprime_list;

CREATE TABLE im_nci_nci60_doseresp_sprime_list AS
SELECT
    expid,
    nsc,
    prefix,
    nsc                                   AS compound_id,        -- sprime Compound_ID
    cell_name                             AS cell_line,          -- sprime Cell_Line
    panel_number,
    cell_number,
    panel_name,
    panel_code,
    'microM'                              AS concentration_units,-- sprime Concentration_Units (post-conversion)
    'M'                                   AS original_concentration_unit,
    max(log_hi_concentration)             AS log_hi_concentration,
    max(release_date)                     AS release_date,
    NULL::text                            AS control_response,   -- DOSERESP ships no per-curve DMSO
    count(*)                              AS n_points,
    (count(*) >= 4)                       AS load_eligible,
    -- sprime Responses: PTC values, dose-ordered low -> high
    string_agg(average_ptc, ','
               ORDER BY concentration::numeric)                 AS responses,
    -- sprime Concentrations: linear uM, dose-ordered to match Responses
    string_agg(
        trim_scale(round(power(10::numeric, concentration::numeric + 6), 10))::text,
        ',' ORDER BY concentration::numeric)                    AS concentrations
FROM raw_nci_nci60_doseresp
WHERE concentration_unit = 'M'
  AND concentration ~ '^-?[0-9]+(\.[0-9]+)?$'
  AND average_ptc    ~ '^-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?$'
GROUP BY expid, nsc, prefix, cell_name, panel_number, cell_number, panel_name, panel_code;

CREATE INDEX ix_nci60_sprime_list_lookup
    ON im_nci_nci60_doseresp_sprime_list (nsc, expid, cell_line);

CREATE INDEX ix_nci60_sprime_list_eligible
    ON im_nci_nci60_doseresp_sprime_list (load_eligible);
