import pandas as pd
import numpy as np


def load_dataset(filepath: str) -> pd.DataFrame:
    """Load CSV or Excel file into a DataFrame."""
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the dataset: remove duplicates, empty columns, fill missing values."""
    # Remove duplicate rows
    df = df.drop_duplicates()

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    # Fill missing numeric values with column mean
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].mean())

    # Fill missing categorical values with 'Unknown'
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in cat_cols:
        df[col] = df[col].fillna("Unknown")

    return df


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Detect numeric, categorical, and time columns.
    Returns a dict with keys: 'numeric', 'categorical', 'datetime'.
    """
    numeric_cols = list(df.select_dtypes(include=[np.number]).columns)

    # Attempt to parse object columns as datetime
    datetime_cols = []
    remaining_cat = []
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="raise")
            df[col] = parsed
            datetime_cols.append(col)
        except Exception:
            remaining_cat.append(col)

    # Check dtype=datetime columns already detected by pandas
    for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
        if col not in datetime_cols:
            datetime_cols.append(col)

    return {
        "numeric": numeric_cols,
        "categorical": remaining_cat,
        "datetime": datetime_cols,
    }


def get_preview(df: pd.DataFrame, rows: int = 8) -> list[dict]:
    """Return first N rows as a list of dicts for JSON serialization."""
    return df.head(rows).to_dict(orient="records")


def compute_column_info(df: pd.DataFrame) -> dict:
    """Return basic column info: dtype and non-null count."""
    info = {}
    for col in df.columns:
        info[col] = {
            "dtype": str(df[col].dtype),
            "non_null": int(df[col].notna().sum()),
            "total": len(df),
        }
    return info
