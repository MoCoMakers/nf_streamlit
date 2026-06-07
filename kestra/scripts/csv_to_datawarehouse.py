import argparse
import csv
import os
import sys
import time
from pathlib import Path

import psycopg
import yaml
from psycopg import sql

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "config.yaml"


def config_from_env():
    """Build config from PG* env vars (Kestra secrets → task env)."""
    host = os.environ.get("PGHOST")
    user = os.environ.get("PGUSER")
    password = os.environ.get("PGPASSWORD")
    dbname = os.environ.get("PGDATABASE")
    if not all([host, user, password, dbname]):
        return None
    db = {
        "host": host,
        "port": int(os.environ.get("PGPORT", "5432")),
        "name": dbname,
        "user": user,
        "password": password,
        "connect_timeout": int(os.environ.get("PGCONNECT_TIMEOUT", "30")),
    }
    if os.environ.get("PGSSLMODE"):
        db["sslmode"] = os.environ["PGSSLMODE"]
    return {"database": db}


def load_config(path=None):
    env_cfg = config_from_env()
    if env_cfg is not None:
        return env_cfg

    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print("Set PGHOST, PGUSER, PGPASSWORD, PGDATABASE env vars or pass --config.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_table_name(table_name):
    if "." in table_name:
        schema, table = table_name.split(".", 1)
    else:
        schema, table = "public", table_name
    return schema, table


def table_identifier(schema, table):
    if schema == "public":
        return sql.Identifier(table)
    return sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))


def read_csv_columns(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV file is empty: {csv_path}") from exc
    if not header:
        raise ValueError(f"CSV has no header row: {csv_path}")
    return [col.strip().lower() for col in header]


def connect(db):
    connect_kwargs = {
        "host": db["host"],
        "port": db["port"],
        "dbname": db["name"],
        "user": db["user"],
        "password": db["password"],
        "autocommit": True,
        "connect_timeout": db.get("connect_timeout", 30),
    }
    if "sslmode" in db:
        connect_kwargs["sslmode"] = db["sslmode"]

    print(f"Connecting to PostgreSQL at {db['host']}:{db['port']}/{db['name']}...")
    try:
        return psycopg.connect(**connect_kwargs)
    except psycopg.Error as exc:
        print(f"ERROR: Database connection failed: {exc}")
        print(
            "If the host is unreachable, connect to your office/VPN network and retry."
        )
        sys.exit(1)


def table_exists(cur, schema, table):
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        )
        """,
        (schema, table),
    )
    return cur.fetchone()[0]


def create_table(cur, schema, table, columns):
    col_defs = sql.SQL(", ").join(
        sql.SQL("{} TEXT").format(sql.Identifier(col)) for col in columns
    )
    create_sql = sql.SQL("CREATE TABLE {} ({})").format(
        table_identifier(schema, table),
        col_defs,
    )
    cur.execute(create_sql)
    print(f"Created table {schema}.{table} with {len(columns)} columns.")


def load_csv(csv_path, table_name, config, replace=False):
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        sys.exit(1)

    columns = read_csv_columns(csv_path)
    schema, table = parse_table_name(table_name)
    db = config["database"]
    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)

    with connect(db) as conn:
        with conn.cursor() as cur:
            exists = table_exists(cur, schema, table)

            if exists and replace:
                print(f"Truncating existing table: {schema}.{table}")
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}").format(
                        table_identifier(schema, table)
                    )
                )
            elif exists:
                print(f"Using existing table: {schema}.{table}")
            else:
                create_table(cur, schema, table, columns)

            print(
                f"Loading {file_size_mb:.1f} MB from {csv_path} "
                f"into {schema}.{table}..."
            )
            started = time.perf_counter()

            copy_sql = sql.SQL(
                "COPY {} FROM STDIN WITH (FORMAT csv, HEADER true)"
            ).format(table_identifier(schema, table))

            with open(csv_path, "r", encoding="utf-8") as f:
                with cur.copy(copy_sql) as copy:
                    while chunk := f.read(1024 * 1024):
                        copy.write(chunk)

            elapsed = time.perf_counter() - started
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(
                    table_identifier(schema, table)
                )
            )
            row_count = cur.fetchone()[0]

            print(
                f"Import completed: {row_count:,} rows loaded in {elapsed:.1f}s."
            )


def main():
    parser = argparse.ArgumentParser(
        description="Bulk load a CSV into PostgreSQL using psycopg3."
    )
    parser.add_argument("csv_path", help="Path to the CSV file to import")
    parser.add_argument("table_name", help="Target PostgreSQL table name")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Truncate the target table before loading (table must already exist)",
    )

    args = parser.parse_args()
    config = load_config(args.config)
    load_csv(args.csv_path, args.table_name, config, replace=args.replace)


if __name__ == "__main__":
    main()
