"""Shared data / model loading and the prediction bridge.

Contract (see ARCHITECTURE.md §2–§4):
- raw dataset:      data/raw/cambodia_inflation_2005_2025.csv
- serialized model: models/model.pkl

Everything needed to go from sidebar widgets -> model -> chart-ready frames
lives here, so the UI, Visualization and Integration pages share one
implementation and one output schema.

Output schema handed to the Visualization Specialist (see §4):

    fc = build_forecast(df, horizon=..., scenario_rate=...)

    fc.frame        DataFrame with columns
                    [Date, YoY_Change_CPI_all_item, type, risk_prob,
                     risk_label, high_risk]
                    type is "Historical" or "Forecast".
    fc.history      Historical rows only (same columns).
    fc.forecast     Forecast rows only (same columns).
    fc.source       Human-readable caption describing the forecast source.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve repo root from this file's location: utils.py -> project root
REPO_ROOT = Path(__file__).resolve().parent

DATA_PATH = REPO_ROOT / "data" / "raw" / "cambodia_inflation_2005_2025.csv"
TRAIN_PATH = REPO_ROOT / "data" / "processed" / "train.csv"
TEST_PATH = REPO_ROOT / "data" / "processed" / "test.csv"
MODEL_PATH = REPO_ROOT / "models" / "model.pkl"

# --- Column contract (ARCHITECTURE.md §2) ----------------------------------
DATE_COL = "Date"
VALUE_COL = "YoY_Change_CPI_all_item"  # inflation metric shown and scored (%, YoY)

DATE_COL_CANDIDATES = [DATE_COL, "date", "DATE"]
VALUE_COL_CANDIDATES = [VALUE_COL, "inflation", "Inflation", "CPI"]

# The raw file is m/d/yyyy (month first), not dd/mm/yyyy. Every row has day = 1
# and month cycling 1..12, so an ambiguous parse silently collapses all rows
# into January. Verified against ARCHITECTURE §2 in the Integration PR.
DATE_FORMAT = "%m/%d/%Y"

# --- Risk scoring ----------------------------------------------------------
# Provisional until the Data/ML Engineers fix the threshold in ARCHITECTURE.md §2.
RISK_THRESHOLD = 3.0  # % YoY considered "high risk"
RISK_SPREAD = 0.75  # width of the logistic transition band, in percentage points
RISK_CUTOFF = 0.5
DECAY_MONTHS = 6.0  # mean-reversion speed of the fallback projection

# --- Feature contract (ARCHITECTURE.md §3) ---------------------------------
# PROPOSED default, used only when the serialized model does not expose
# ``feature_names_in_``. The ML Engineer owns the real list; ``get_feature_names``
# always prefers what the model itself was trained on.
FEATURES = [
    "CPI_all_item",
    "MoM_Change_CPI_all_item",
    "YoY_Change_CPI_all_item",
    "CPI_3_Month_Moving_Avg",
    "CPI_12_Month_Moving_Avg",
    "YoY_3_Month_Avg",
    "YoY_12_Month_Avg",
]

# Matches lag columns named like "<base>_t-1" / "<base>_t-12".
LAG_PATTERN = re.compile(r"^(?P<base>.+)_t-(?P<lag>\d+)$")


@st.cache_data(show_spinner="Loading inflation dataset...")
def load_data(path=DATA_PATH):
    """Load the raw Cambodia inflation CSV, parse dates, sort chronologically."""
    path = Path(path)
    if not path.exists():
        return None
    df = pd.read_csv(path)

    date_col = next((c for c in DATE_COL_CANDIDATES if c in df.columns), None)
    if date_col is None:
        for c in df.columns:
            try:
                df[c] = pd.to_datetime(df[c], dayfirst=True, errors="raise")
                date_col = c
                break
            except Exception:
                continue
    if date_col is not None:
        # Explicit format first so the month/day order can never flip, with a
        # lenient fallback for future exports that switch to ISO dates.
        try:
            parsed = pd.to_datetime(df[date_col], format=DATE_FORMAT, errors="raise")
        except (ValueError, TypeError):
            parsed = pd.to_datetime(df[date_col], errors="coerce")
        df[date_col] = parsed
        df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)

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
    """Return (date_col, value_col) for a dataframe, preferring the contract names."""
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


# ---------------------------------------------------------------------------
# Integration: widgets -> feature frame -> model
# ---------------------------------------------------------------------------


def get_feature_names(model=None):
    """Feature order/dtypes the model expects, in training order.

    Prefers ``model.feature_names_in_`` (recorded by scikit-learn) and falls
    back to the provisional ``FEATURES`` list in ARCHITECTURE.md §3.
    """
    names = getattr(model, "feature_names_in_", None)
    if names is not None and len(names):
        return [str(n) for n in names]
    return list(FEATURES)


def latest_inputs(df, feature_names=None):
    """Latest observed value of every model feature (sidebar widget defaults)."""
    if df is None:
        return {}
    feature_names = feature_names or FEATURES
    row = df.iloc[-1]
    return {
        name: float(row[name])
        for name in feature_names
        if name in df.columns and pd.notna(row[name])
    }


def build_feature_frame(inputs, feature_names=None, history=None):
    """Build a single-row DataFrame in the exact order the model expects.

    ``inputs`` wins over history (that is where the widget values land), then
    falls back to the latest observed value, then to lag columns named
    ``"<base>_t-<n>"`` computed from ``history``. Raises ``ValueError`` listing
    anything that could not be resolved, instead of sending a bad frame to
    ``predict()``.
    """
    feature_names = list(feature_names or get_feature_names())
    values = {}
    missing = []

    for name in feature_names:
        if inputs and name in inputs and inputs[name] is not None:
            values[name] = float(inputs[name])
            continue

        if history is not None and name in history.columns:
            values[name] = float(history[name].iloc[-1])
            continue

        match = LAG_PATTERN.match(name)
        if match and history is not None and match["base"] in history.columns:
            lag = int(match["lag"])
            series = history[match["base"]]
            if len(series) > lag:
                values[name] = float(series.iloc[-1 - lag])
                continue

        missing.append(name)

    if missing:
        raise ValueError(
            "Cannot build the model input frame; missing values for: "
            + ", ".join(missing)
        )

    return pd.DataFrame([values], columns=feature_names, dtype=float)


def score_risk(value, threshold=RISK_THRESHOLD, spread=RISK_SPREAD):
    """Probability of a high-risk month, as a logistic function of the value."""
    return 1.0 / (1.0 + math.exp(-(float(value) - float(threshold)) / float(spread)))


def risk_label(probability, cutoff=RISK_CUTOFF):
    """Binary risk class (1 = high risk) from a probability."""
    return int(probability >= cutoff)


@dataclass(frozen=True)
class Prediction:
    """One model prediction for the current sidebar scenario."""

    value: float  # inflation metric the prediction refers to
    probability: float  # P(high risk) in [0, 1]
    label: int  # 1 = high risk, 0 = not high risk
    source: str  # "model" or "rule"
    detail: str = ""

    def as_dict(self):
        return {
            "value": self.value,
            "probability": self.probability,
            "label": self.label,
            "source": self.source,
            "detail": self.detail,
        }


def predict_risk(inputs, model=None, history=None, threshold=RISK_THRESHOLD):
    """Run the model on the widget inputs, falling back to the rule-based score.

    Never raises: if the artifact is missing or its feature contract cannot be
    satisfied, the rule-based score is returned with ``source="rule"`` and a
    human-readable reason, so the page still renders.
    """
    scenario_value = float(inputs.get(VALUE_COL, 0.0))
    reason = "No model at models/model.pkl yet (rule-based score)."

    if model is not None:
        try:
            frame = build_feature_frame(inputs, get_feature_names(model), history)
        except Exception as exc:  # contract mismatch, not a crash
            reason = f"Model input unavailable ({type(exc).__name__}: {exc}); rule-based score."
        else:
            try:
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(frame)[0]
                    probability = float(proba[-1]) if len(proba) > 1 else float(proba[0])
                    label = int(model.predict(frame)[0])
                    return Prediction(
                        scenario_value,
                        probability,
                        label,
                        "model",
                        f"predict_proba / predict on {len(frame.columns)} features",
                    )

                out = float(model.predict(frame)[0])
                if 0.0 <= out <= 1.0:  # classifier exposing predict() only
                    return Prediction(
                        scenario_value,
                        out,
                        risk_label(out),
                        "model",
                        f"predict on {len(frame.columns)} features",
                    )
                # regressor: its output is the forecast value
                probability = score_risk(out, threshold)
                return Prediction(
                    out,
                    probability,
                    risk_label(probability),
                    "model",
                    "regressor output treated as the forecast value",
                )
            except Exception as exc:
                reason = f"Model call failed ({type(exc).__name__}: {exc}); rule-based score."

    probability = score_risk(scenario_value, threshold)
    return Prediction(scenario_value, probability, risk_label(probability), "rule", reason)


# ---------------------------------------------------------------------------
# Integration: predictions -> chart-ready frame
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Forecast:
    """Chart-ready history + forecast, shared with the Visualization Specialist."""

    frame: pd.DataFrame
    history: pd.DataFrame
    forecast: pd.DataFrame
    scenario_rate: float
    threshold: float
    source: str

    @property
    def peak_value(self):
        return float(self.forecast[VALUE_COL].max())

    @property
    def peak_date(self):
        return self.forecast.loc[self.forecast[VALUE_COL].idxmax(), DATE_COL]


def _scored(dates, values, kind, threshold):
    """Attach risk_prob / risk_label / high_risk to one branch of the frame."""
    out = pd.DataFrame({DATE_COL: pd.to_datetime(dates), VALUE_COL: values, "type": kind})
    out["risk_prob"] = out[VALUE_COL].map(lambda v: score_risk(v, threshold))
    out["risk_label"] = out["risk_prob"].map(risk_label)
    out["high_risk"] = out[VALUE_COL] > float(threshold)
    return out


def build_forecast(
    history_df,
    horizon=12,
    scenario_rate=None,
    threshold=RISK_THRESHOLD,
    model=None,
    decay_months=DECAY_MONTHS,
):
    """Project the inflation metric ``horizon`` months ahead and score every row.

    The projection reverts from the last observation toward ``scenario_rate``
    (the sidebar's hypothetical inflation rate) with an exponential decay, so
    the curve is a documented scenario simulation rather than a fitted
    forecast. When a model that consumes the projected inputs becomes
    available this is the single place to swap in ``model.predict``.

    Returns a :class:`Forecast` whose ``frame`` is ready for charting.
    """
    if history_df is None:
        raise ValueError("build_forecast() needs the loaded history dataframe.")

    date_col, value_col = infer_columns(history_df)
    hist = history_df[[date_col, value_col]].dropna().sort_values(date_col)
    if hist.empty:
        raise ValueError("History dataframe has no usable date/value rows.")

    last_date = hist[date_col].max()
    last_value = float(hist[value_col].iloc[-1])
    scenario_rate = last_value if scenario_rate is None else float(scenario_rate)

    horizon = int(horizon)
    future_dates = pd.date_range(
        start=last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS"
    )
    projected = [
        scenario_rate + (last_value - scenario_rate) * math.exp(-step / float(decay_months))
        for step in range(1, horizon + 1)
    ]

    hist_frame = _scored(hist[date_col], hist[value_col], "Historical", threshold)
    fcst_frame = _scored(future_dates, projected, "Forecast", threshold)

    if model is not None:
        source = (
            "Scenario projection from the latest observation toward the selected "
            "rate; `models/model.pkl` was loaded and scores the current risk."
        )
    else:
        source = (
            "Model not available yet (`models/model.pkl`), so the forecast uses the "
            "documented mean-reversion scenario projection and a rule-based risk score."
        )

    return Forecast(
        frame=pd.concat([hist_frame, fcst_frame], ignore_index=True),
        history=hist_frame,
        forecast=fcst_frame,
        scenario_rate=scenario_rate,
        threshold=float(threshold),
        source=source,
    )
