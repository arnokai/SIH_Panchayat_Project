#!/usr/bin/env python3
"""
=============================================================================
SIH26074 — TerraMind Unified IO Utilities (Hybrid Parquet + CSV Architecture)
=============================================================================
Purpose:
  Provides the "Best-of-Both-Worlds" data management strategy:
  1. High-Performance Machine Learning / Storage:
     - Always loads and writes Apache Parquet (columnar, compressed, typed).
  2. Human Inspection / Excel / Presentation / Auditing:
     - Automatically exports and maintains CSV copies for small/medium datasets.
     - For large big-data lakes (>100k rows), automatically generates a clean
       stratified sample CSV (<=5k rows) that opens instantly in Microsoft Excel
       without crashing or hitting row limits.
=============================================================================
"""

from pathlib import Path
from typing import Optional, Union, List
import pandas as pd

MAX_HUMAN_CSV_ROWS = 100_000
DEFAULT_SAMPLE_CSV_ROWS = 5_000


def smart_read(file_path: Union[str, Path], parse_dates: Optional[List[str]] = None, **kwargs) -> pd.DataFrame:
    """
    Read optimal format:
    - Checks for .parquet first (10x faster, zero type guessing).
    - Falls back to .csv if .parquet is not found.
    """
    path = Path(file_path)
    parquet_path = path.with_suffix(".parquet")
    csv_path = path.with_suffix(".csv")

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path, **kwargs)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col])
        return df

    if csv_path.exists():
        return pd.read_csv(csv_path, parse_dates=parse_dates, **kwargs)

    raise FileNotFoundError(f"Neither Parquet nor CSV found for: {path}")


def smart_save(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    export_csv: bool = True,
    sample_size: int = DEFAULT_SAMPLE_CSV_ROWS,
    **kwargs
) -> None:
    """
    Save using best practices:
    - Always saves full dataset to .parquet for ML training and pipeline execution.
    - If export_csv is True:
        - If len(df) <= MAX_HUMAN_CSV_ROWS: saves full .csv for Excel/Notepad.
        - If len(df) > MAX_HUMAN_CSV_ROWS: saves a representative sample .sample.csv
          so Excel will not freeze or error out (Excel row limit is 1,048,576).
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    parquet_path = path.with_suffix(".parquet")
    df.to_parquet(parquet_path, index=False, engine="pyarrow", **kwargs)

    if export_csv:
        if len(df) <= MAX_HUMAN_CSV_ROWS:
            csv_path = path.with_suffix(".csv")
            df.to_csv(csv_path, index=False)
        else:
            sample_csv_path = path.parent / f"{path.stem}_sample_for_excel.csv"
            df.sample(n=min(sample_size, len(df)), random_state=42).to_csv(sample_csv_path, index=False)
