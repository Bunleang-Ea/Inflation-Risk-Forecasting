"""Shared data / model loading for the Inflation Risk Forecasting app.

Both UI pages import from here so every page reads the same contract paths:
- raw dataset:   data/raw/cambodia_inflation_2005_2025.csv
- serialized model: models/model.pkl
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve repo root from this file's location: utils.py -> project root
REPO_ROOT = Path(__file__).resolve().parent

DATA_PATH = REPO_ROOT / "data" / "raw" / "cambodia_inflation_2005_2025.csv"
TRAIN_PATH = REPO_ROOT / "data" / "processed" / "train.csv"
TEST_PATH = REPO_ROOT / "data" / "processed" / "test.csv"
MODEL_PATH = REPO_ROOT / "models" / "model.pkl"

# Date column / target column are filled in by the Data Engineer in ARCHITECTURE.md §2.
# Until then we auto-detect: first datetime-ish column, first numeric column.
DATE_COL_CANDIDATES = ["date", "Date", "DATE"]
VALUE_COL_CANDIDATES = ["cpi", "CPI", "inflation", "Inflation", "value", "Value"]


@st.cache_data(show_spinner="Loading inflation dataset...")
def load_data(path=DATA_PATH):
    """Load the raw Cambodia inflation CSV, parse dates, sort chronologically."""
    path = Path(path)
    if not path.exists():
        return None
    df = pd.read_csv(path)

    # Try to find a date column
    date_col = next((c for c in DATE_COL_CANDIDATES if c in df.columns), None)
    if date_col is None:
        # fallback: first column that parses as datetime
        for c in df.columns:
            try:
                parsed = pd.to_datetime(df[c], errors="raise")
                date_col = c
                df[date_col] = parsed
                break
            except Exception:
                continue
    if date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)

    return df


@st.cache_resource(show_spinner="Loading trained model...")
def load_model(path=MODEL_PATH):
    """Load the serialized model (joblib or pickle) from models/model.pkl."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        import joblib

        return joblib.load(path)
    except Exception:
        import pickle

        with open(path, "rb") as f:
            return pickle.load(f)


def infer_columns(df):
    """Return (date_col, value_col) auto-detected from a dataframe."""
    if df is None:
        return None, None
    date_col = next((c for c in DATE_COL_CANDIDATES if c in df.columns), None)
    if date_col is None:
        for c in df.columns:
            try:
                pd.to_datetime(df[c], errors="raise")
                date_col = c
                break
            except Exception:
                continue
    value_col = next((c for c in VALUE_COL_CANDIDATES if c in df.columns), None)
    if value_col is None:
        for c in df.columns:
            if c == date_col:
                continue
            if pd.api.types.is_numeric_dtype(df[c]):
                value_col = c
                break
    return date_col, value_col
