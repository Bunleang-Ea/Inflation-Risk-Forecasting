"""Historical inflation trend chart (page 1).

Reads `data/raw/cambodia_inflation_2005_2025.csv` via `utils.load_data`
and renders an Altair line chart: date on x-axis, inflation/CPI on y-axis.
"""

import streamlit as st
import altair as alt

from utils import REPO_ROOT, DATA_PATH, load_data, infer_columns

st.set_page_config(page_title="Historical Trends", layout="wide")
st.title("Historical Inflation Trends")

df = load_data(DATA_PATH)

if df is None:
    st.warning(
        f"Dataset not found at `{DATA_PATH}`. "
        "Ask the Data Engineer to add `cambodia_inflation_2005_2025.csv` to `data/raw/`."
    )
else:
    date_col, value_col = infer_columns(df)
    if date_col is None or value_col is None:
        st.error("Could not auto-detect a date column and a numeric value column.")
    else:
        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X(f"{date_col}:T", title="Date"),
                y=alt.Y(f"{value_col}:Q", title=value_col),
                tooltip=[date_col, value_col],
            )
            .properties(
                title=f"{value_col} over time",
                use_container_width=True,
            )
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)

        st.caption(
            f"Source: `{DATA_PATH.relative_to(REPO_ROOT)}` | "
            f"rows: {len(df):,} | columns: {', '.join(df.columns)}"
        )
