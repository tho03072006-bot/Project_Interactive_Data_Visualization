from __future__ import annotations

import hashlib
import json
import os
import tarfile
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd


def find_project_root(start: Path | None = None) -> Path:
    """Tìm project_remake mà không phụ thuộc notebook được mở từ thư mục nào."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "data" / "raw").exists() and (candidate / "scripts").exists():
            return candidate
    raise FileNotFoundError("Không tìm thấy project_remake có data/raw và scripts.")


ROOT = find_project_root()
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
STAGING = PROCESSED / "staging"
TABLES = PROCESSED / "tables"
QUALITY = PROCESSED / "quality_reports"
FIGURES = PROCESSED / "eda_figures"


def ensure_output_dirs() -> None:
    for path in (STAGING, TABLES, QUALITY, FIGURES):
        path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_coinmetrics(archive: Path | None = None) -> Iterator[tuple[str, pd.DataFrame]]:
    """Đọc trực tiếp từng CSV trong archive, không phụ thuộc file giải nén bên ngoài."""
    archive = archive or RAW / "crypto" / "coinmetrics_raw.tar.gz"
    if not archive.exists():
        raise FileNotFoundError(archive)
    with tarfile.open(archive, "r:gz") as tar:
        members = sorted(
            (m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith(".csv")),
            key=lambda m: m.name,
        )
        for member in members:
            stream = tar.extractfile(member)
            if stream is None:
                raise OSError(f"Không đọc được {member.name}")
            yield Path(member.name).stem.upper(), pd.read_csv(stream, low_memory=False)


def assert_unique_key(df: pd.DataFrame, key: Iterable[str], table: str) -> None:
    key = list(key)
    missing_cols = sorted(set(key) - set(df.columns))
    if missing_cols:
        raise AssertionError(f"{table}: thiếu cột khóa {missing_cols}")
    null_rows = int(df[key].isna().any(axis=1).sum())
    duplicate_rows = int(df.duplicated(key, keep=False).sum())
    if null_rows or duplicate_rows:
        raise AssertionError(
            f"{table}: khóa {key} có {null_rows} dòng null và {duplicate_rows} dòng thuộc khóa trùng"
        )


def numeric_no_infinity(df: pd.DataFrame, table: str) -> None:
    numeric = df.select_dtypes(include=[np.number])
    count = int(np.isinf(numeric.to_numpy(dtype=float, na_value=np.nan)).sum())
    if count:
        raise AssertionError(f"{table}: có {count} giá trị vô cực")


def write_csv_atomic(df: pd.DataFrame, path: Path, *, float_format: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    is_gzip = path.suffix.lower() == ".gz"
    temp = path.with_name(path.name + (".tmp.gz" if is_gzip else ".tmp"))
    df.to_csv(
        temp,
        index=False,
        encoding="utf-8",
        compression="gzip" if is_gzip else None,
        float_format=float_format,
    )
    os.replace(temp, path)


def write_json_atomic(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(temp, path)


def table_quality(df: pd.DataFrame, name: str, key: Iterable[str]) -> dict:
    key = list(key)
    assert_unique_key(df, key, name)
    numeric_no_infinity(df, name)
    return {
        "table": name,
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "key": key,
        "duplicate_keys": int(df.duplicated(key).sum()),
        "null_key_rows": int(df[key].isna().any(axis=1).sum()),
        "missing_cells": int(df.isna().sum().sum()),
    }


def last_complete_month(last_date: pd.Timestamp) -> pd.Timestamp:
    last_date = pd.Timestamp(last_date).normalize()
    period = last_date.to_period("M")
    if last_date < period.end_time.normalize():
        period -= 1
    return period.to_timestamp("M")


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """q-value Benjamini-Hochberg, giữ nguyên index và xử lý NaN."""
    result = pd.Series(np.nan, index=p_values.index, dtype=float)
    valid = p_values.dropna().astype(float).sort_values()
    if valid.empty:
        return result
    m = len(valid)
    adjusted = (valid.to_numpy() * m / np.arange(1, m + 1))[::-1]
    adjusted = np.minimum.accumulate(adjusted)[::-1]
    result.loc[valid.index] = np.minimum(adjusted, 1.0)
    return result

