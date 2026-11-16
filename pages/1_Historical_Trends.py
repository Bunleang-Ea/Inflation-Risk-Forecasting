"""Historical inflation trend chart (page 1).

Reads `data/raw/cambodia_inflation_2005_2025.csv` via `utils.load_data`
and renders an Altair line chart: date on x-axis, inflation/CPI on y-axis.
"""

import streamlit as st
import altair as alt

from utils import REPO_ROOT, DATA_PATH, load_data, infer_columns
from ui import apply_theme, page_intro

st.set_page_config(page_title="Historical Trends", layout="wide")
apply_theme()
page_intro("Historical Inflation Trends", "Start here to understand Cambodia's monthly inflation pattern from 2005–2025.")

df = load_data(DATA_PATH)

if df is None:
    st.warning("Historical inflation data is not available yet. Please try again when the dataset is connected.")
else:
    date_col, value_col = infer_columns(df)
    if date_col is None or value_col is None:
        st.error("Could not auto-detect a date column and a numeric value column.")
    else:
        latest = df.iloc[-1]
        first = df.iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Latest value", f"{latest[value_col]:.2f}")
        m2.metric("First value", f"{first[value_col]:.2f}")
        m3.metric("Observations", f"{len(df):,}")
        st.markdown("### Trend over time")
        st.info("How to use this page: hover over the chart to inspect monthly values, then open Risk Forecast to explore the forward-looking view.")
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(f"{date_col}:T", title="Date"),
                y=alt.Y(f"{value_col}:Q", title=value_col),
                tooltip=[alt.Tooltip(f"{date_col}:T", title="Date"), alt.Tooltip(f"{value_col}:Q", title="Value", format=".2f")],
            )
            .properties(
                title=f"{value_col} over time",
            )
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

        st.caption(
            f"Source: `{DATA_PATH.relative_to(REPO_ROOT)}` | "
            f"rows: {len(df):,} | columns: {', '.join(df.columns)}"
        )
