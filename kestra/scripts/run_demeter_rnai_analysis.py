"""
Populate fnl_depm_demeter_rnai_analysis: pooled DEMETER RNAi delta scores for
ALL driver genes x ALL DEMETER target genes x ALL tissues, generalizing
references/demeter/rnai_analysis.py (which hardcoded 4 driver genes and
LUNG only).

WHAT THIS PRODUCES
    For each usable (driver_gene, tissue) combo -- one with both a non-empty
    WT/reference pool (mutation_value=0) and a non-empty mutant pool
    (mutation_value=2) in im_depm_demeter_rnai_pool_members -- and for every
    DEMETER target gene except the driver itself:
        mean_ref_dep_score_for_target  = mean dep_score over the WT pool
        mean_mut_dep_score_for_target  = mean dep_score over the MUT pool
        delta_rnai_dep_score_driver_and_target = MUT_avg - WT_avg
    written into fnl_depm_demeter_rnai_analysis.

WHY BATCHED, NOT ONE QUERY
    A single query joining the full driver-gene universe against the full
    DEMETER target-gene panel (both ~17-19k genes) across ~700 cell lines
    produces a pre-aggregation join in the tens of billions of rows -- not
    something Postgres (or a Kestra task timeout) can push through at once.
    The reference script's 4-driver loop never hit this because each driver's
    join was tiny (~127 lung cell lines). Batching by (driver_gene, tissue)
    keeps each iteration's join to the same small shape the reference script
    always used, just parameterized instead of hardcoded.

RESUMABILITY
    im_depm_demeter_rnai_work_queue.analysis_run_id is the checkpoint,
    directly mirroring im_nci_nci60_doseresp_sprime_list.fit_run_id in
    run_sprime_fit.py. fetch_batch() filters WHERE analysis_run_id IS NULL, so
    a killed or restarted execution picks up exactly where the prior commit
    left off. Each batch is fetched -> inserted -> queue rows marked done ->
    committed before the next batch starts; loss on a crash is bounded by
    --batch-size (driver_gene, tissue) combos, not by run duration.

PREREQUISITES (must already be run, in order, against the warehouse):
    kestra/scripts/sql/add_rnai_analysis_indexes.sql
    kestra/scripts/sql/build_im_depm_demeter_rnai_pool_members.sql
    kestra/scripts/sql/build_im_depm_demeter_rnai_work_queue.sql
    kestra/scripts/sql/create_fnl_depm_demeter_rnai_analysis.sql

USAGE
    python run_demeter_rnai_analysis.py                      # full run, defaults
    python run_demeter_rnai_analysis.py --batch-size 50
    python run_demeter_rnai_analysis.py --limit 10            # smoke test: 10 combos total
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid

import psycopg

POOL_TABLE = "im_depm_demeter_rnai_pool_members"
QUEUE_TABLE = "im_depm_demeter_rnai_work_queue"
RESULT_TABLE = "fnl_depm_demeter_rnai_analysis"


def db_connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def fetch_batch(conn: psycopg.Connection, batch_size: int) -> list[tuple[int, str]]:
    """Claim the next batch_size unprocessed (driver_gene_id, tissue) combos.

    FOR UPDATE SKIP LOCKED so this is safe even if a batch were ever run
    concurrently (not done today, but costs nothing to allow).
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT driver_gene_id, tissue
            FROM {QUEUE_TABLE}
            WHERE analysis_run_id IS NULL
            ORDER BY driver_gene_id, tissue
            LIMIT %s
            FOR UPDATE SKIP LOCKED
            """,
            (batch_size,),
        )
        return [(row[0], row[1]) for row in cur.fetchall()]


def insert_batch_results(
    conn: psycopg.Connection, batch: list[tuple[int, str]], run_id: str
) -> int:
    """Run one set-based INSERT for the whole batch (not one query per combo).

    The join is restricted to this batch's (driver_gene_id, tissue) pairs via
    an inline VALUES list, so its size is bounded by --batch-size regardless
    of how large the full driver/target/tissue space is.
    """
    values_sql = ", ".join(["(%s::int, %s::text)"] * len(batch))
    values_params: list[object] = []
    for gene_id, tissue in batch:
        values_params.extend([gene_id, tissue])

    sql = f"""
        INSERT INTO {RESULT_TABLE} (
            driver_gene_id, driver_gene, tissue, target_gene,
            mean_ref_dep_score_for_target, mean_mut_dep_score_for_target,
            delta_rnai_dep_score_driver_and_target,
            ref_pool_cell_lines_for_driver, mut_pool_cell_lines_for_driver,
            ref_dep_score_observations_for_target,
            mut_dep_score_observations_for_target,
            analysis_run_id, analysis_at
        )
        SELECT
            pm.driver_gene_id,
            max(pm.driver_gene),
            pm.tissue,
            d.gene,
            avg(d.dep_score::double precision) FILTER (WHERE pm.genotype_pool = 'WT_REF'),
            avg(d.dep_score::double precision) FILTER (WHERE pm.genotype_pool = 'MUT'),
            (avg(d.dep_score::double precision) FILTER (WHERE pm.genotype_pool = 'MUT')
             - avg(d.dep_score::double precision) FILTER (WHERE pm.genotype_pool = 'WT_REF')),
            count(DISTINCT pm.demeter_ccle_id) FILTER (WHERE pm.genotype_pool = 'WT_REF'),
            count(DISTINCT pm.demeter_ccle_id) FILTER (WHERE pm.genotype_pool = 'MUT'),
            count(d.dep_score) FILTER (WHERE pm.genotype_pool = 'WT_REF'),
            count(d.dep_score) FILTER (WHERE pm.genotype_pool = 'MUT'),
            %s,
            now()
        FROM {POOL_TABLE} pm
        JOIN (VALUES {values_sql}) AS batch(driver_gene_id, tissue)
          ON batch.driver_gene_id = pm.driver_gene_id AND batch.tissue = pm.tissue
        JOIN raw_depm_demeter_combined_gene_dep_scores d
          ON upper(d.ccle_id) = pm.demeter_ccle_id
        WHERE d.dep_score IS NOT NULL
          AND regexp_replace(d.gene, '\\s*\\([0-9]+\\)$', '')
              <> regexp_replace(pm.driver_gene, '\\s*\\([0-9]+\\)$', '')
        GROUP BY pm.driver_gene_id, pm.tissue, d.gene
        HAVING count(d.dep_score) FILTER (WHERE pm.genotype_pool = 'WT_REF') > 0
           AND count(d.dep_score) FILTER (WHERE pm.genotype_pool = 'MUT')    > 0
        ON CONFLICT (driver_gene_id, tissue, target_gene) DO NOTHING
    """
    # Param order must match placeholder order in the SQL text above: the
    # VALUES list's (gene_id, tissue) pairs come first, then run_id (the
    # SELECT's lone %s).
    full_params = values_params + [run_id]
    with conn.cursor() as cur:
        cur.execute(sql, full_params)
        return cur.rowcount


def mark_batch_done(
    conn: psycopg.Connection, batch: list[tuple[int, str]], run_id: str
) -> None:
    values_sql = ", ".join(["(%s::int, %s::text)"] * len(batch))
    params: list[object] = [run_id]
    for gene_id, tissue in batch:
        params.extend([gene_id, tissue])

    sql = f"""
        UPDATE {QUEUE_TABLE} q
           SET analysis_run_id = %s,
               analysis_completed_at = now()
        FROM (VALUES {values_sql}) AS batch(driver_gene_id, tissue)
        WHERE q.driver_gene_id = batch.driver_gene_id
          AND q.tissue = batch.tissue
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)


def process_batch(
    conn: psycopg.Connection, batch_size: int, run_id: str
) -> tuple[int, int]:
    """Claim, compute, and commit one batch. Returns (combos_claimed, rows_written).

    combos_claimed == 0 signals the queue is fully drained.
    """
    batch = fetch_batch(conn, batch_size)
    if not batch:
        return 0, 0
    rows_written = insert_batch_results(conn, batch, run_id)
    mark_batch_done(conn, batch, run_id)
    conn.commit()
    return len(batch), rows_written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument(
        "--batch-size", type=int, default=25,
        help="(driver_gene, tissue) combos claimed + computed + committed per iteration.",
    )
    ap.add_argument(
        "--max-batches", type=int, default=0,
        help="0 = run until no unprocessed combos remain (default).",
    )
    ap.add_argument(
        "--limit", type=int, default=0,
        help="If >0, cap total combos processed (overrides --max-batches).",
    )
    ap.add_argument("--run-id", default=None, help="defaults to a fresh uuid")
    args = ap.parse_args()

    run_id = args.run_id or f"run-{uuid.uuid4().hex[:8]}"

    print(f"run_id      : {run_id}")
    print(f"batch_size  : {args.batch_size}")
    print(f"max_batches : {'unlimited' if args.max_batches == 0 else args.max_batches}")
    if args.limit:
        print(f"limit (total combos) : {args.limit}")

    total_combos = 0
    total_rows = 0
    batch_idx = 0
    overall_start = time.perf_counter()

    with db_connect() as conn:
        while True:
            if args.max_batches and batch_idx >= args.max_batches:
                print(f"reached max_batches={args.max_batches}; stopping")
                break

            this_batch = args.batch_size
            if args.limit:
                remaining = args.limit - total_combos
                if remaining <= 0:
                    print(f"reached limit={args.limit}; stopping")
                    break
                this_batch = min(this_batch, remaining)

            t0 = time.perf_counter()
            n_combos, n_rows = process_batch(conn, this_batch, run_id)
            if n_combos == 0:
                print("no more unprocessed (driver_gene, tissue) combos; done")
                break

            total_combos += n_combos
            total_rows += n_rows
            batch_idx += 1
            elapsed_batch = time.perf_counter() - t0
            rate = n_combos / elapsed_batch if elapsed_batch > 0 else 0.0

            print(
                f"batch {batch_idx:>4d}  combos={n_combos:>4d}  rows={n_rows:>7,d}  "
                f"{elapsed_batch:>6.1f}s  {rate:>5.2f} combos/s  "
                f"cum_combos={total_combos:,}  cum_rows={total_rows:,}"
            )

    elapsed = time.perf_counter() - overall_start
    print()
    print("=" * 60)
    print(f"run_id            : {run_id}")
    print(f"batches           : {batch_idx}")
    print(f"combos processed  : {total_combos:,}")
    print(f"rows written      : {total_rows:,}")
    print(f"elapsed           : {elapsed:.1f}s ({elapsed/60:.1f} min)")
    if total_combos:
        print(f"avg rate          : {total_combos / elapsed:.2f} combos/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
