from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parents[2] / "results"

def append(rows: list[dict], name: str) -> Path:
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"{name}.parquet"
    df = pd.DataFrame(rows)
    if path.exists():
        df = pd.concat([pd.read_parquet(path), df], ignore_index=True)
    df.to_parquet(path, index=False)
    return path

def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(RESULTS / f"{name}.parquet")