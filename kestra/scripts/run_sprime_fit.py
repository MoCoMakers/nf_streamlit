"""
Fit Hill curves to NCI-60 dose-response data and populate sprime S' values into
im_nci_nci60_doseresp_sprime_list. Designed to run inside the project's tools
docker container.

WHAT THIS PRODUCES
    For each eligible row in im_nci_nci60_doseresp_sprime_list, the following
    columns are populated (added beforehand by
    scripts/alter_sprime_list_add_fit_columns.sql):

        s_prime, ec50, zero_asymptote, inf_asymptote, hill_slope, r_squared,
        fit_status, fit_warnings, sprime_version, fit_run_id, fit_at

    "Eligible" = curve has >= 4 valid concentration/response pairs (already
    encoded in the load_eligible boolean by the SQL build script).

SCIENTIFIC NOTES (reproducibility — please do not change without recording why)

    * sprime installed via pip install "sprime>=0.3.0" in the fit flow beforeCommands.
    * Hill fitter: sprime.hill_fitting.fit_hill_curve, which wraps
      scipy.optimize.curve_fit. This is the same code path that
      SPrime.load() + RawDataset.to_screening_dataset() would call, just
      reached directly so we can drive a multiprocessing pool.
    * S' formula: math.asinh((zero_asymptote - inf_asymptote) / ec50),
      matching DoseResponseProfile.calculate_s_prime in sprime/sprime.py.
    * sprime config recorded as documentation (this script does not load via
      SPrime.load):
          values_as = "list"
          skip_control_response_normalization = True   (NCI-60 DOSERESP has
              no per-curve DMSO/Control_Response column; PTC is already
              T0/control-normalized upstream)
          response_normalization = "asymptote_normalized"   (label only when
              skip=True; the asymptotes used in S' come from the Hill fit on
              raw PTC values, which is the asymptote-normalization in effect)
    * Compound names for sprime input are not required for fitting; we keep
      the LEFT JOIN to im_nci_nsc_compounds in fetch_rows() for ad-hoc
      inspection but it does not affect any fit parameter.

RESUMABILITY
    fetch_rows filters WHERE fit_run_id IS NULL, so a killed or restarted
    process picks up exactly where the prior commit left off. Each batch is
    fetched -> fit -> UPDATEd -> committed before the next batch starts; loss
    on a crash is bounded by --batch-size rows.

USAGE
    # Inside the tools container (host-side wrapper in the runbook):
    python scripts/run_sprime_fit.py                       # full run, defaults
    python scripts/run_sprime_fit.py --workers 12 --batch-size 5000
    python scripts/run_sprime_fit.py --limit 1000          # smoke test
    python scripts/run_sprime_fit.py --workers 0           # serial (debug)
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import multiprocessing as mp
import os
import sys
import time
import uuid
import warnings

import psycopg
import sprime
from sprime.hill_fitting import fit_hill_curve

LIST_TABLE = "im_nci_nci60_doseresp_sprime_list"


def db_connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def fetch_rows(conn: psycopg.Connection, limit: int) -> list[dict]:
    """Pull the next chunk of eligible, unfit curves.

    Joins im_nci_nsc_compounds for a preferred display name. The name is not
    used by the fit — it's surfaced only so log/debug output can refer to
    compounds in a human-friendly way.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                l.curve_id,
                l.cell_line,
                l.responses,
                l.concentrations,
                COALESCE(c.compound_name, 'NSC-' || l.nsc) AS compound_name
            FROM {LIST_TABLE} l
            LEFT JOIN im_nci_nsc_compounds c ON c.nsc = l.nsc
            WHERE l.load_eligible = TRUE
              AND l.fit_run_id IS NULL
            ORDER BY l.curve_id
            LIMIT %s
            """,
            (limit,),
        )
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


_EMPTY_FIT = {
    "s_prime": None,
    "ec50": None,
    "zero_asymptote": None,
    "inf_asymptote": None,
    "hill_slope": None,
    "r_squared": None,
    "fit_status": "failed",
    "fit_warnings": None,
}


def _fit_one(args: tuple[int, str, str]) -> tuple[int, dict]:
    """Worker: parse one curve's concentration/response CSV strings, fit Hill,
    compute S'. Top-level pure function so multiprocessing.Pool can pickle it.
    """
    cid, concs_csv, resps_csv = args
    record = dict(_EMPTY_FIT)
    try:
        concs = [float(x) for x in concs_csv.split(",")]
        resps = [float(x) for x in resps_csv.split(",")]
        # scipy.curve_fit on pathological curves emits noisy warnings every
        # call; suppress in the worker so logs aren't flooded.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            hp = fit_hill_curve(concs, resps)
        if hp is None or hp.ec50 in (None, 0):
            return cid, record
        s_prime = math.asinh((hp.zero_asymptote - hp.inf_asymptote) / hp.ec50)
        record.update(
            s_prime=s_prime,
            ec50=hp.ec50,
            zero_asymptote=hp.zero_asymptote,
            inf_asymptote=hp.inf_asymptote,
            hill_slope=getattr(hp, "steepness_coefficient", None),
            r_squared=getattr(hp, "r_squared", None),
            fit_status="ok",
        )
    except Exception as e:  # noqa: BLE001
        record["fit_warnings"] = f"{type(e).__name__}: {e}"[:500]
    return cid, record


def update_rows(
    conn: psycopg.Connection,
    expected_ids: list[int],
    fits: dict[int, dict],
    run_id: str,
    version: str,
) -> None:
    """Write a batch's fit results back. Rows that produced no fit dict are
    marked fit_status='skipped' so we don't re-fetch them next batch.
    """
    now = dt.datetime.now(dt.timezone.utc)
    payload = []
    for cid in expected_ids:
        f = fits.get(cid)
        if f is None:
            payload.append(
                (None, None, None, None, None, None,
                 "skipped", "no_profile_returned",
                 version, run_id, now, cid)
            )
        else:
            payload.append(
                (f["s_prime"], f["ec50"],
                 f["zero_asymptote"], f["inf_asymptote"],
                 f["hill_slope"], f["r_squared"],
                 f["fit_status"], f.get("fit_warnings"),
                 version, run_id, now, cid)
            )

    sql = f"""
        UPDATE {LIST_TABLE}
           SET s_prime        = %s,
               ec50           = %s,
               zero_asymptote = %s,
               inf_asymptote  = %s,
               hill_slope     = %s,
               r_squared      = %s,
               fit_status     = %s,
               fit_warnings   = %s,
               sprime_version = %s,
               fit_run_id     = %s,
               fit_at         = %s
         WHERE curve_id = %s
    """
    with conn.cursor() as cur:
        cur.executemany(sql, payload)
    conn.commit()


def process_batch(
    conn: psycopg.Connection,
    pool: "mp.pool.Pool | None",
    batch_size: int,
    run_id: str,
    version: str,
    chunksize: int,
) -> tuple[int, dict[int, dict]]:
    """Fetch up to batch_size eligible unfit rows, fit them (parallel via pool
    or serial when pool is None), write back. Returns (rows_processed, fits).
    rows_processed == 0 signals the table is fully fit.
    """
    rows = fetch_rows(conn, batch_size)
    if not rows:
        return 0, {}

    work = [(r["curve_id"], r["concentrations"], r["responses"]) for r in rows]
    fits: dict[int, dict] = {}
    if pool is None:
        for item in work:
            cid, rec = _fit_one(item)
            fits[cid] = rec
    else:
        for cid, rec in pool.imap_unordered(_fit_one, work, chunksize=chunksize):
            fits[cid] = rec

    expected_ids = [r["curve_id"] for r in rows]
    update_rows(conn, expected_ids, fits, run_id, version)
    return len(rows), fits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument(
        "--batch-size", type=int, default=5000,
        help="Rows fetched + fit + UPDATEd per iteration (committed between).",
    )
    ap.add_argument(
        "--max-batches", type=int, default=0,
        help="0 = run until no eligible unfit rows remain (default).",
    )
    ap.add_argument(
        "--limit", type=int, default=0,
        help="If >0, cap total rows processed (overrides --max-batches).",
    )
    ap.add_argument("--run-id", default=None, help="defaults to a fresh uuid")
    ap.add_argument(
        "--workers", type=int,
        default=max(1, (os.cpu_count() or 2) - 2),
        help="multiprocessing worker count; 0 = serial (no pool).",
    )
    ap.add_argument(
        "--chunksize", type=int, default=100,
        help="Pool.imap chunksize (items dispatched per worker round-trip).",
    )
    args = ap.parse_args()

    run_id = args.run_id or f"run-{uuid.uuid4().hex[:8]}"
    version = sprime.__version__ if hasattr(sprime, "__version__") else "unknown"

    print(f"sprime version : {version}")
    print(f"run_id         : {run_id}")
    print(f"batch_size     : {args.batch_size}")
    print(f"workers        : {args.workers}")
    print(f"chunksize      : {args.chunksize}")
    print(f"max_batches    : {'unlimited' if args.max_batches == 0 else args.max_batches}")
    if args.limit:
        print(f"limit (total)  : {args.limit}")

    total_processed = 0
    total_ok = 0
    total_failed = 0
    batch_idx = 0
    overall_start = time.perf_counter()

    pool: "mp.pool.Pool | None" = None
    if args.workers > 0:
        pool = mp.Pool(processes=args.workers)
    try:
        with db_connect() as conn:
            while True:
                if args.max_batches and batch_idx >= args.max_batches:
                    print(f"reached max_batches={args.max_batches}; stopping")
                    break

                this_batch = args.batch_size
                if args.limit:
                    remaining = args.limit - total_processed
                    if remaining <= 0:
                        print(f"reached limit={args.limit}; stopping")
                        break
                    this_batch = min(this_batch, remaining)

                t0 = time.perf_counter()
                n, fits = process_batch(
                    conn, pool, this_batch, run_id, version, args.chunksize
                )
                if n == 0:
                    print("no more eligible unfit rows; done")
                    break

                ok = sum(1 for f in fits.values() if f["fit_status"] == "ok")
                failed = n - ok
                total_processed += n
                total_ok += ok
                total_failed += failed
                batch_idx += 1
                elapsed_batch = time.perf_counter() - t0
                rate = n / elapsed_batch if elapsed_batch > 0 else 0.0

                print(
                    f"batch {batch_idx:>4d}  rows={n:>5d}  ok={ok:>5d}  "
                    f"failed={failed:>4d}  {elapsed_batch:>6.1f}s  "
                    f"{rate:>6.1f} rows/s  cum={total_processed:,}"
                )
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    elapsed = time.perf_counter() - overall_start
    print()
    print("=" * 60)
    print(f"run_id            : {run_id}")
    print(f"batches           : {batch_idx}")
    print(f"rows processed    : {total_processed:,}")
    print(f"  fit ok          : {total_ok:,}")
    print(f"  fit failed      : {total_failed:,}")
    print(f"elapsed           : {elapsed:.1f}s ({elapsed/60:.1f} min)")
    if total_processed:
        print(f"avg rate          : {total_processed / elapsed:.1f} rows/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
