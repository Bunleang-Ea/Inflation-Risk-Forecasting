"""Risk forecast chart (page 2).

Layers historical inflation with forecast values and highlights high-risk
threshold breaches. Until the Integration Engineer wires the real model,
a deterministic stub forecast is used so the page renders end-to-end.
"""

import streamlit as st
import altair as alt
import pandas as pd

from utils import REPO_ROOT, DATA_PATH, MODEL_PATH, load_data, load_model, infer_columns

st.set_page_config(page_title="Risk Forecast", layout="wide")
st.title("Inflation Risk Forecast")

df = load_data(DATA_PATH)
model = load_model(MODEL_PATH)

if df is None:
    st.warning(
        f"Dataset not found at `{DATA_PATH}`. "
        "Ask the Data Engineer to add `cambodia_inflation_2005_2025.csv` to `data/raw/`."
    )
    st.stop()

date_col, value_col = infer_columns(df)
if date_col is None or value_col is None:
    st.error("Could not auto-detect a date column and a numeric value column.")
    st.stop()

# ---- Forecast (stub until Integration Engineer wires model.predict) ----
HORIZON = 12  # months ahead to forecast
RISK_THRESHOLD = df[value_col].quantile(0.9)  # high-risk threshold (TBD by team)

last_date = df[date_col].max()
future_dates = pd.date_range(start=last_date + pd.offsets.MonthBegin(1), periods=HORIZON, freq="MS")

if model is not None:
    # TODO(Integration Engineer): replace stub with real model.predict() on formatted inputs.
    # Expected input: DataFrame matching ARCHITECTURE.md §3 feature order & dtypes.
    forecast_values = [df[value_col].iloc[-1]] * HORIZON
    forecast_source = "Loaded model `models/model.pkl` (stub prediction — replace with real predict())"
else:
    forecast_values = [df[value_col].iloc[-1]] * HORIZON
    forecast_source = (
        "No model found at `models/model.pkl`. "
        "Ask the ML Engineer to push it. Using last-value stub forecast."
    )

forecast_df = pd.DataFrame({date_col: future_dates, value_col: forecast_values, "type": "Forecast"})
history_df = df[[date_col, value_col]].copy()
history_df["type"] = "Historical"

combined = pd.concat([history_df, forecast_df], ignore_index=True)
combined["high_risk"] = combined[value_col] > RISK_THRESHOLD

# ---- Chart: history line + forecast points + risk threshold ----
base = alt.Chart(combined).encode(
    x=alt.X(f"{date_col}:T", title="Date"),
    y=alt.Y(f"{value_col}:Q", title=value_col),
    color=alt.Color("type:N", legend=alt.Legend(title="Series")),
)

history_line = base.transform_filter("datum.type == 'Historical'").mark_line()
forecast_points = base.transform_filter("datum.type == 'Forecast'").mark_point(filled=True, size=60)
forecast_line = base.transform_filter("datum.type == 'Forecast'").mark_line(strokeDash=[5, 5])

risk_rule = alt.Chart(pd.DataFrame({value_col: [RISK_THRESHOLD]})).mark_rule(
    color="red", strokeDash=[4, 4]
).encode(y=alt.Y(f"{value_col}:Q"))

chart = (
    (history_line + forecast_line + forecast_points + risk_rule)
    .properties(
        title=f"Historical vs Forecast — high risk > {RISK_THRESHOLD:.2f} (red)",
        use_container_width=True,
    )
    .interactive()
)

st.altair_chart(chart, use_container_width=True)

st.caption(forecast_source)
st.caption(
    f"Source: `{DATA_PATH.relative_to(REPO_ROOT)}` | model: `{MODEL_PATH.relative_to(REPO_ROOT)}` | "
    f"rows: {len(df):,} | horizon: {HORIZON} months"
)

st.markdown(
    """
### Integration notes
- Replace the stub forecast above with `model.predict()` outputs from `utils.load_model()`.
- Format widget inputs into a DataFrame matching **ARCHITECTURE.md §3** (exact feature order & dtypes).
- `st.sidebar` widgets live in this file; predictions flow into this chart and into `3_Model_Metrics.py`.
"""
)
