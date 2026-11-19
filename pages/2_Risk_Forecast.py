"""Risk forecast page: sidebar widgets -> model -> chart-ready frame.

Integration Engineer owns this wiring (see ARCHITECTURE.md §4):

1. ``utils.load_model`` loads ``models/model.pkl`` once, cached with
   ``@st.cache_resource``.
2. The sidebar widgets below hold the live inputs. Their keys are part of the
   contract: ``forecast_horizon``, ``scenario_rate``, ``risk_threshold``.
3. ``utils.predict_risk`` formats those inputs into a frame matching the
   model's feature order and runs ``predict`` / ``predict_proba``.
4. ``utils.build_forecast`` returns ``forecast`` (a ``utils.Forecast``) whose
   ``.frame`` is the documented output schema for the Visualization Specialist.
"""

import altair as alt
import pandas as pd
import streamlit as st

from ui import apply_theme, page_intro
from utils import (
    DATA_PATH,
    DATE_COL,
    MODEL_PATH,
    REPO_ROOT,
    RISK_THRESHOLD,
    VALUE_COL,
    build_forecast,
    get_feature_names,
    infer_columns,
    latest_inputs,
    load_data,
    load_model,
    predict_risk,
)

st.set_page_config(page_title="Risk Forecast", layout="wide")
apply_theme()
page_intro(
    "Inflation Risk Forecast",
    "Compare recent history with a scenario forecast and review the high-risk reference level.",
)

df = load_data(DATA_PATH)
model = load_model(MODEL_PATH)

if df is None:
    st.warning("Historical inflation data is not available yet, so this page cannot create a forecast.")
    st.stop()

date_col, value_col = infer_columns(df)
if date_col is None or value_col is None:
    st.error("This page could not identify the date and inflation columns needed for the forecast.")
    st.stop()

# ---------------------------------------------------------------------------
# Live inputs (UI Developer provides these names; ARCHITECTURE.md §4)
# ---------------------------------------------------------------------------
feature_names = get_feature_names(model)
defaults = latest_inputs(df, feature_names)
latest_value = float(df[value_col].iloc[-1])
observed_min = float(df[value_col].min())
observed_max = float(df[value_col].max())

with st.sidebar:
    st.header("Forecast settings")
    horizon = st.slider(
        "Forecast horizon (months)",
        3,
        24,
        12,
        key="forecast_horizon",
    )
    scenario_rate = st.slider(
        "Hypothetical inflation rate (% YoY)",
        min_value=round(max(0.0, observed_min) - 1.0, 1),
        max_value=round(observed_max + 1.0, 1),
        value=round(latest_value, 1),
        step=0.1,
        key="scenario_rate",
        help="The rate the scenario projection reverts toward over the horizon.",
    )
    risk_threshold = st.slider(
        "High-risk threshold (% YoY)",
        min_value=0.0,
        max_value=round(observed_max + 1.0, 1),
        value=float(RISK_THRESHOLD),
        step=0.1,
        key="risk_threshold",
    )
    st.caption(
        "Inputs are passed to `utils.predict_risk()` and formatted to the model's "
        "feature order before prediction."
    )

# ---------------------------------------------------------------------------
# Prediction (tasks 2-4 of the Integration handoff)
# ---------------------------------------------------------------------------
scenario_inputs = dict(defaults)
scenario_inputs[value_col] = scenario_rate

prediction = predict_risk(
    scenario_inputs,
    model=model,
    history=df,
    threshold=risk_threshold,
)
forecast = build_forecast(
    df,
    horizon=horizon,
    scenario_rate=scenario_rate,
    threshold=risk_threshold,
    model=model,
)
forecast_df = forecast.frame  # documented output for the Visualization Specialist

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
summary1, summary2, summary3, summary4 = st.columns(4)
summary1.metric(
    "Latest observation",
    f"{latest_value:.2f}",
    help=f"Observed on {df[date_col].iloc[-1].strftime('%d %b %Y')}",
)
summary2.metric("Scenario rate", f"{scenario_rate:.2f}")
summary3.metric("Forecast peak", f"{forecast.peak_value:.2f}", help=f"Expected in {forecast.peak_date.strftime('%b %Y')}")
summary4.metric(
    "Risk probability",
    f"{prediction.probability * 100:.0f}%",
    help=prediction.detail,
)

status = "High" if prediction.label == 1 else "Low"
status_color = "#b42318" if prediction.label == 1 else "#087443"
st.markdown(
    f"""
    <div class="status-card" style="border-left-color: {status_color};">
      <div class="status-label">Scenario risk classification</div>
      <div class="status-value" style="color: {status_color};">{status}</div>
      <div class="muted">
        {prediction.source} prediction · threshold {risk_threshold:.2f}% YoY ·
        {prediction.detail}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if model is None:
    st.info(
        "`models/model.pkl` has not been pushed yet, so the page uses a rule-based risk "
        "score. Widgets, feature formatting and the output schema are already wired: "
        "drop the artifact in and the model path activates without further changes."
    )

# ---------------------------------------------------------------------------
# Chart: history line + forecast line/points + threshold rule
# ---------------------------------------------------------------------------
tooltip = [
    alt.Tooltip(f"{DATE_COL}:T", title="Date"),
    alt.Tooltip(f"{VALUE_COL}:Q", title="Inflation (% YoY)", format=".2f"),
    alt.Tooltip("type:N", title="Series"),
    alt.Tooltip("risk_prob:Q", title="Risk probability", format=".0%"),
]

history_chart = (
    alt.Chart(forecast_df)
    .transform_filter(alt.datum.type == "Historical")
    .mark_line(color="#1f77b4")
    .encode(
        x=alt.X(f"{DATE_COL}:T", title="Date"),
        y=alt.Y(f"{VALUE_COL}:Q", title="Inflation (% YoY)"),
        tooltip=tooltip,
    )
)

forecast_line = (
    alt.Chart(forecast_df)
    .transform_filter(alt.datum.type == "Forecast")
    .mark_line(color="#f28e2b", strokeDash=[5, 5])
    .encode(
        x=alt.X(f"{DATE_COL}:T", title="Date"),
        y=alt.Y(f"{VALUE_COL}:Q", title="Inflation (% YoY)"),
        tooltip=tooltip,
    )
)

forecast_points = (
    alt.Chart(forecast_df)
    .transform_filter(alt.datum.type == "Forecast")
    .mark_point(filled=True, size=70)
    .encode(
        x=alt.X(f"{DATE_COL}:T", title="Date"),
        y=alt.Y(f"{VALUE_COL}:Q", title="Inflation (% YoY)"),
        color=alt.Color(
            "high_risk:N",
            title="Above threshold",
            scale=alt.Scale(domain=[True, False], range=["#b42318", "#087443"]),
        ),
        tooltip=tooltip,
    )
)

risk_rule = (
    alt.Chart(pd.DataFrame({VALUE_COL: [float(risk_threshold)]}))
    .mark_rule(color="#b42318", strokeDash=[4, 4])
    .encode(y=alt.Y(f"{VALUE_COL}:Q"))
)

chart = (
    (history_chart + forecast_line + forecast_points + risk_rule)
    .properties(title=f"Historical vs scenario forecast — high risk above {risk_threshold:.2f}% YoY")
    .interactive()
)

st.altair_chart(chart, width="stretch")

st.caption(forecast.source)
st.caption(
    f"Source: `{DATA_PATH.relative_to(REPO_ROOT)}` | model: "
    f"`{MODEL_PATH.relative_to(REPO_ROOT)}` | horizon: {horizon} months | "
    f"features: {len(feature_names)} | output rows: {len(forecast_df):,}"
)

with st.expander("Prediction output (for visualization / debugging)"):
    st.write(
        {
            "scenario_rate": scenario_rate,
            "risk_threshold": risk_threshold,
            "risk_probability": round(prediction.probability, 4),
            "risk_label": prediction.label,
            "source": prediction.source,
            "features_sent": feature_names,
        }
    )
    st.dataframe(forecast_df.tail(horizon), width="stretch")
