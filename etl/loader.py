"""Загрузка CSV в DataFrame."""
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл: {path}")
    return pd.read_csv(path, **kwargs)