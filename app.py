"""Home / landing page for the Inflation Risk Forecasting Streamlit app."""

import streamlit as st

from ui import apply_theme

st.set_page_config(page_title="Inflation Risk Forecasting", layout="wide")
apply_theme()

st.markdown(
    """
    <div class="hero">
      <h1>Inflation Risk Forecasting</h1>
      <p>Explore Cambodia's inflation history and understand potential near-term risk.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info("Use the page menu on the left to explore historical trends, forecasts, and model performance.")

cols = st.columns(3)
cards = [
    ("Historical Trends", "See how CPI and inflation have changed since 2005."),
    ("Risk Forecast", "Review the forecast horizon and high-risk threshold."),
    ("Model Metrics", "Check model quality once evaluation results are available."),
]
for col, (heading, body) in zip(cols, cards):
    with col:
        st.markdown(f'<div class="section-card"><h3>{heading}</h3><p>{body}</p></div>', unsafe_allow_html=True)

st.markdown("### About this dashboard")
st.write("This dashboard turns monthly inflation data into clear charts and forecast context for quick review. Use the historical page to understand the baseline before interpreting the forecast.")
