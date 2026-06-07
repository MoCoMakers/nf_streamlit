-- Build im_nci_cell_line_xref: bridge from NCI-60 raw cell_name values to
-- Cellosaurus CVCL primary IDs (and onward to DepMap ACH), using only
-- conservative matching (no edit-distance fuzzy).
--
-- Match levels, highest-confidence first:
--     1 nci_dtp_exact            cell_name = any value in nci_dtp_name (|-split)
--     2 name_exact               cell_name = Cellosaurus display name
--     3 synonym_exact            cell_name = any value in synonyms (|-split)
--     4 normalized_nci_dtp       norm_key matches at the nci_dtp_name level
--     5 normalized_name          norm_key matches at the name level
--     6 normalized_synonym       norm_key matches at the synonym level
--
-- norm_key = lowercase, strip [- _ . / and whitespace].
-- Each cell_name is assigned to the lowest-numbered (highest-confidence)
-- level that produces any match. If that level has >1 distinct CVCL hit,
-- match_source = 'ambiguous_<level>' and cvcl_id is NULL; n_matches and
-- candidate_cvcls let an operator review the ambiguity.

DROP TABLE IF EXISTS im_nci_cell_line_xref;

CREATE TABLE im_nci_cell_line_xref AS
WITH our_cells AS (
    SELECT DISTINCT cell_name
    FROM raw_nci_nci60_doseresp
    WHERE cell_name IS NOT NULL
      AND cell_name <> ''
),
-- Expand Cellosaurus into one (cvcl_id, candidate_string, source) row per
-- match candidate.
cello_candidates AS (
    SELECT cvcl_id, name AS cellosaurus_name, name AS candidate, 'name'::text AS src
    FROM raw_cellosaurus_celllines
    WHERE name <> ''
  UNION ALL
    SELECT cvcl_id, name,
           unnest(string_to_array(nci_dtp_name, '|')),
           'nci_dtp'::text
    FROM raw_cellosaurus_celllines
    WHERE nci_dtp_name <> ''
  UNION ALL
    SELECT cvcl_id, name,
           unnest(string_to_array(synonyms, '|')),
           'synonym'::text
    FROM raw_cellosaurus_celllines
    WHERE synonyms <> ''
),
-- All hits with their priority levels.
ranked AS (
    SELECT o.cell_name, c.cvcl_id, c.cellosaurus_name, c.src, c.candidate,
           CASE c.src
                WHEN 'nci_dtp' THEN 1
                WHEN 'name'    THEN 2
                WHEN 'synonym' THEN 3
           END AS lvl
    FROM our_cells o
    JOIN cello_candidates c ON c.candidate = o.cell_name

  UNION ALL

    SELECT o.cell_name, c.cvcl_id, c.cellosaurus_name, c.src, c.candidate,
           CASE c.src
                WHEN 'nci_dtp' THEN 4
                WHEN 'name'    THEN 5
                WHEN 'synonym' THEN 6
           END AS lvl
    FROM our_cells o
    JOIN cello_candidates c
      ON lower(regexp_replace(c.candidate, '[[:space:]._/-]+', '', 'g'))
       = lower(regexp_replace(o.cell_name, '[[:space:]._/-]+', '', 'g'))
    WHERE c.candidate <> o.cell_name        -- skip pairs already caught by levels 1-3
),
best_level AS (
    SELECT cell_name, MIN(lvl) AS best_lvl
    FROM ranked
    GROUP BY cell_name
),
best_hits AS (
    SELECT r.cell_name, r.cvcl_id, r.cellosaurus_name, r.src, r.lvl, r.candidate
    FROM ranked r
    JOIN best_level b USING (cell_name)
    WHERE r.lvl = b.best_lvl
),
agg AS (
    SELECT cell_name,
           MIN(lvl)                            AS lvl,
           COUNT(DISTINCT cvcl_id)             AS n_cvcl,
           string_agg(DISTINCT cvcl_id,           '|' ORDER BY cvcl_id)           AS cvcls,
           string_agg(DISTINCT cellosaurus_name, '|' ORDER BY cellosaurus_name)   AS cellosaurus_names,
           string_agg(DISTINCT src,               '|' ORDER BY src)               AS srcs
    FROM best_hits
    GROUP BY cell_name
)
SELECT
    o.cell_name,
    CASE WHEN a.n_cvcl = 1 THEN a.cvcls END                                AS cvcl_id,
    CASE WHEN a.n_cvcl = 1 THEN c.depmap_ach END                           AS depmap_ach,
    CASE
        WHEN a.cell_name IS NULL THEN 'unmatched'
        WHEN a.n_cvcl > 1 THEN 'ambiguous_lvl' || a.lvl
        WHEN a.lvl = 1 THEN 'nci_dtp_exact'
        WHEN a.lvl = 2 THEN 'name_exact'
        WHEN a.lvl = 3 THEN 'synonym_exact'
        WHEN a.lvl = 4 THEN 'normalized_nci_dtp'
        WHEN a.lvl = 5 THEN 'normalized_name'
        WHEN a.lvl = 6 THEN 'normalized_synonym'
    END                                                                    AS match_source,
    COALESCE(a.n_cvcl, 0)                                                  AS n_matches,
    a.cvcls                                                                AS candidate_cvcls,
    a.cellosaurus_names                                                    AS candidate_names
FROM our_cells o
LEFT JOIN agg a ON a.cell_name = o.cell_name
LEFT JOIN raw_cellosaurus_celllines c
    ON a.n_cvcl = 1 AND c.cvcl_id = a.cvcls;

CREATE UNIQUE INDEX ux_im_nci_cell_line_xref_cell_name
    ON im_nci_cell_line_xref (cell_name);
