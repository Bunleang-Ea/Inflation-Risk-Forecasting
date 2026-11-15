"""Home / landing page for the Inflation Risk Forecasting Streamlit app."""

import streamlit as st

st.set_page_config(page_title="Inflation Risk Forecasting", layout="wide")

st.title("Inflation Risk Forecasting")
st.write("Cambodia inflation data (2005–2025) — Streamlit + ML forecasting app.")

st.markdown(
    """
### Team workflow

- `main` = the real project (deployed to Streamlit Community Cloud).
- Each member works in their own role branch (sandbox) and lands work via PR.
- Visuals live in the `pages/` directory; shared loading logic is in `utils.py`.

### Pages

- `pages/1_Historical_Trends.py` — historical inflation trend.
- `pages/2_Risk_Forecast.py` — historical vs forecast with risk-threshold highlighting.
- `pages/3_Model_Metrics.py` — model performance metrics (to be wired by ML Engineer).
"""
)
