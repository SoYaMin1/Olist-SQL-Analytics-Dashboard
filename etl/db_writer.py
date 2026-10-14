"""Запись DataFrame в SQLite."""
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "olist.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")


def init_schema(engine):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        ddl = f.read()
    with engine.begin() as conn:
        for stmt in ddl.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))


def write_df(df: pd.DataFrame, table: str, engine, if_exists: str = "replace"):
    df.to_sql(table, engine, if_exists=if_exists, index=False)
    print(f"{table}: {len(df):,} строк записано")