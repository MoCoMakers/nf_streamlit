#!/usr/bin/env python3
"""load_tp53_raw.py — load the staged NCI TP53 Database (R21) CSVs into the warehouse.

Naming convention: raw_nci_tp53_<datatype>. All TP53 files are narrow, so they load
AS-IS (every column TEXT, like load_depmap_raw.py). Idempotent: DROP then recreate.
SELECT is granted to compbio_dw_readonly (the dw-toolbox read-only role).

Relevant subset loaded (functional-classification + cell-line context for the R2.8
TP53 dominant-negative-vs-null work):
  MutationView_r21.csv   -> raw_nci_tp53_mutationview  (per-variant annotations incl. DNE_LOFclass)
  FunctionDownload_r21.csv-> raw_nci_tp53_function      (per-assay functional measurements)
  CellLineDownload_r21.csv-> raw_nci_tp53_cellline      (cell lines with TP53 status / LOH)

Run INSIDE the nf_streamlit container after docker-cp'ing the CSVs to /tmp/tp53/.
Read-WRITE account (comp_bio_u2).
"""
import csv
import psycopg
from psycopg import sql

DB = dict(host="dmvpetridishdatastore.dev", port=5432, dbname="data_warehouse",
          user="comp_bio_u2", password="SPrime555NF&&work",
          autocommit=True, connect_timeout=30)

SRC = "/tmp/tp53"
READONLY_ROLE = "compbio_dw_readonly"

# (csv path, table name, name for an empty first-column header)
ASIS = [
    (f"{SRC}/MutationView_r21.csv",    "raw_nci_tp53_mutationview", "col_0"),
    (f"{SRC}/FunctionDownload_r21.csv","raw_nci_tp53_function",     "col_0"),
    (f"{SRC}/CellLineDownload_r21.csv","raw_nci_tp53_cellline",     "col_0"),
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
    try:
        cur.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(
            sql.Identifier(table), sql.Identifier(READONLY_ROLE)))
    except Exception as e:                       # role may differ in some envs
        print(f"  (warning: GRANT to {READONLY_ROLE} failed: {e})")
    cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))
    print(f"  {table}: {cur.fetchone()[0]:,} rows x {len(cols)} cols (as-is)")


def main():
    with psycopg.connect(**DB) as conn, conn.cursor() as cur:
        print("AS-IS loads:")
        for path, table, first in ASIS:
            load_asis(cur, path, table, first)
        cur.execute("""SELECT table_name FROM information_schema.tables
                       WHERE table_schema='public' AND table_name LIKE 'raw_nci_tp53_%'
                       ORDER BY table_name""")
        print("\nraw_nci_tp53_* tables now present:")
        for (t,) in cur.fetchall():
            print("  -", t)


if __name__ == "__main__":
    main()
