#!/usr/bin/env python3
"""load_depmap_raw.py — load the staged DepMap CRISPR/RNAi CSVs into the warehouse.

Naming convention: raw_depm_<biogrid|demeter>_<snake_case_table>.
Most files load AS-IS (every column TEXT, like csv_to_datawarehouse.py). The three
BioGRID gene matrices are ~18,086 columns wide — past Postgres's 1,600-column limit —
so they are melted to long form (screen_id, gene, <value>) instead.

Run INSIDE the nf_streamlit container after docker-cp'ing the CSVs to /tmp/depm/.
Read-WRITE account (comp_bio_u2). Idempotent: DROP TABLE IF EXISTS then recreate.
"""
import csv, io, os, sys
import pandas as pd
import psycopg
from psycopg import sql


def db_from_env():
    """Credentials from PG* env vars (never hardcode — this file is git-tracked).
    Set PGHOST/PGUSER/PGPASSWORD/PGDATABASE (read-WRITE account for loading)."""
    need = ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE")
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: set env vars {missing} (read-write account) before running.")
    return dict(host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
                dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                password=os.environ["PGPASSWORD"], autocommit=True, connect_timeout=30)


DB = db_from_env()

BG = "/tmp/depm/biogrid"
DM = "/tmp/depm/demeter"

# (csv path, table name, name for an empty first-column header)
ASIS = [
    (f"{BG}/ScreenSequenceMap.csv",            "raw_depm_biogrid_screen_sequence_map",      "col_0"),
    (f"{DM}/sample_info.csv",                  "raw_depm_demeter_sample_info",              "col_0"),
    (f"{DM}/Hartposcontrols.csv",              "raw_depm_demeter_hart_pos_controls",        "col_0"),
    (f"{DM}/Hartnegcontrols.csv",              "raw_depm_demeter_hart_neg_controls",        "col_0"),
    (f"{DM}/CCLE_mutation_data.csv",           "raw_depm_demeter_ccle_mutation_data",       "col_0"),
]
# Wide score matrices melted to long (id, var, value). The DEMETER matrices fit the
# 1600-column limit but their 712 inline values overflow Postgres's 8 KB row size, so
# they melt too. (csv, table, id_col, var_col, value_col)
LONG = [
    # BioGRID: rows = screen, cols = gene
    (f"{BG}/ScreenGeneEffect.csv",            "raw_depm_biogrid_screen_gene_effect",             "screen_id", "gene", "gene_effect"),
    (f"{BG}/ScreenGeneEffectUncorrected.csv", "raw_depm_biogrid_screen_gene_effect_uncorrected", "screen_id", "gene", "gene_effect_uncorrected"),
    (f"{BG}/ScreenGeneDependency.csv",        "raw_depm_biogrid_screen_gene_dependency",         "screen_id", "gene", "gene_dependency"),
    # DEMETER2: rows = gene/seed, cols = cell line (CCLE id)
    (f"{DM}/D2_combined_gene_dep_scores.csv", "raw_depm_demeter_combined_gene_dep_scores", "gene", "ccle_id", "dep_score"),
    (f"{DM}/D2_combined_seed_dep_scores.csv", "raw_depm_demeter_combined_seed_dep_scores", "seed", "ccle_id", "dep_score"),
]


def norm(header, first_name):
    """lowercase, fill empty/dup names, keep CSV order."""
    out, seen = [], set()
    for i, c in enumerate(header):
        c = (c or "").strip().lower()
        if i == 0 and not c:
            c = first_name
        if not c:
            c = f"col_{i}"
        base, k = c, 1
        while c in seen:
            c = f"{base}_{k}"; k += 1
        seen.add(c); out.append(c)
    return out


def load_asis(cur, path, table, first_name):
    with open(path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    cols = norm(header, first_name)
    cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))
    cur.execute(sql.SQL("CREATE TABLE {} ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.SQL("{} TEXT").format(sql.Identifier(c)) for c in cols)))
    copy_sql = sql.SQL("COPY {} FROM STDIN WITH (FORMAT csv, HEADER true)").format(sql.Identifier(table))
    with open(path, "r", encoding="utf-8") as f, cur.copy(copy_sql) as cp:
        while chunk := f.read(1 << 20):
            cp.write(chunk)
    cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))
    print(f"  {table}: {cur.fetchone()[0]:,} rows x {len(cols)} cols (as-is)")


def load_long(cur, path, table, id_col, var_col, value_col):
    df = pd.read_csv(path)
    idc = df.columns[0]
    long = (df.melt(id_vars=[idc], var_name=var_col, value_name=value_col)
              .dropna(subset=[value_col])
              .rename(columns={idc: id_col}))[[id_col, var_col, value_col]]
    cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))
    cur.execute(sql.SQL("CREATE TABLE {} ({} TEXT, {} TEXT, {} DOUBLE PRECISION)").format(
        sql.Identifier(table), sql.Identifier(id_col), sql.Identifier(var_col), sql.Identifier(value_col)))
    tmp = "/tmp/_melt.csv"
    long.to_csv(tmp, index=False, header=False)          # to file → low memory for the big melts
    copy_sql = sql.SQL("COPY {} ({}, {}, {}) FROM STDIN WITH (FORMAT csv)").format(
        sql.Identifier(table), sql.Identifier(id_col), sql.Identifier(var_col), sql.Identifier(value_col))
    with open(tmp, "r", encoding="utf-8") as f, cur.copy(copy_sql) as cp:
        while chunk := f.read(1 << 20):
            cp.write(chunk)
    cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))
    print(f"  {table}: {cur.fetchone()[0]:,} rows (long: {id_col}, {var_col}, {value_col})")


def main():
    with psycopg.connect(**DB) as conn, conn.cursor() as cur:
        print("AS-IS loads:")
        for path, table, first in ASIS:
            load_asis(cur, path, table, first)
        print("LONG (melted) loads:")
        for path, table, id_col, var_col, vcol in LONG:
            load_long(cur, path, table, id_col, var_col, vcol)
        # summary
        cur.execute("""SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' AND table_name LIKE 'raw_depm_%' ORDER BY table_name""")
        print("\nraw_depm_* tables now present:")
        for (t,) in cur.fetchall():
            print("  -", t)


if __name__ == "__main__":
    main()
