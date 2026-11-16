"""Risk forecast chart (page 2).

Layers historical inflation with forecast values and highlights high-risk
threshold breaches. Until the Integration Engineer wires the real model,
a deterministic stub forecast is used so the page renders end-to-end.
"""

import streamlit as st
import altair as alt
import pandas as pd

from utils import REPO_ROOT, DATA_PATH, MODEL_PATH, load_data, load_model, infer_columns
from ui import apply_theme, page_intro

st.set_page_config(page_title="Risk Forecast", layout="wide")
apply_theme()
page_intro("Inflation Risk Forecast", "Compare recent history with the current forecast and review the high-risk reference level.")

df = load_data(DATA_PATH)
model = load_model(MODEL_PATH)

if df is None:
    st.warning("Historical inflation data is not available yet, so this page cannot create a forecast.")
    st.stop()

date_col, value_col = infer_columns(df)
if date_col is None or value_col is None:
    st.error("This page could not identify the date and inflation columns needed for the forecast.")
    st.stop()

# ---- Forecast (stub until Integration Engineer wires model.predict) ----
with st.sidebar:
    st.header("Forecast settings")
    horizon = st.slider("Forecast horizon (months)", 3, 24, 12, key="forecast_horizon")
    risk_threshold = st.number_input("Reference threshold", min_value=0.0, value=round(float(df[value_col].quantile(0.9)), 2), step=0.1, key="risk_threshold")
    st.caption("These controls currently drive the display stub and will be connected to the model during integration.")

HORIZON = horizon
RISK_THRESHOLD = risk_threshold

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

latest_value = df[value_col].iloc[-1]
forecast_peak = max(forecast_values)
peak_date = future_dates[forecast_values.index(forecast_peak)]
if latest_value >= RISK_THRESHOLD:
    reference_status, status_color = "High", "#b42318"
elif latest_value >= RISK_THRESHOLD * 0.8:
    reference_status, status_color = "Medium", "#b54708"
else:
    reference_status, status_color = "Low", "#087443"
summary1, summary2 = st.columns(2)
summary1.metric("Latest observation", f"{latest_value:.2f}", help=f"Observed on {df[date_col].iloc[-1].strftime('%d %b %Y')}")
summary2.metric("Model status", "Loaded" if model is not None else "Pending")
f1, f2, f3 = st.columns(3)
f1.metric("Latest observed", f"{latest_value:.2f}")
f2.metric("Risk reference", f"{RISK_THRESHOLD:.2f}")
f3.metric("Forecast peak", f"{forecast_peak:.2f}")
st.markdown(
    f"""
    <div class="status-card" style="border-left-color: {status_color};">
      <div class="status-label">Current reference status</div>
      <div class="status-value" style="color: {status_color};">{reference_status}</div>
      <div class="muted">Based on the latest observed value compared with the current reference level.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
date_start = future_dates.min().strftime("%b %Y")
date_end = future_dates.max().strftime("%b %Y")
st.caption(f"Forecast period: {date_start} – {date_end} · Peak expected in {peak_date.strftime('%b %Y')} · Reference level is provisional.")
st.info("How to use this page: review Historical Trends first, then adjust the forecast horizon and reference threshold. The final risk label will be supplied by the integrated model.")

# ---- Chart: history line + forecast points + risk threshold ----
base = alt.Chart(combined).encode(
    x=alt.X(f"{date_col}:T", title="Date"),
    y=alt.Y(f"{value_col}:Q", title=value_col),
    color=alt.Color("type:N", scale=alt.Scale(domain=["Historical", "Forecast"], range=["#1f77b4", "#f28e2b"]), legend=alt.Legend(title="Series")),
    tooltip=[alt.Tooltip(f"{date_col}:T", title="Date"), alt.Tooltip(f"{value_col}:Q", title="Value", format=".2f"), alt.Tooltip("type:N", title="Series")],
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
