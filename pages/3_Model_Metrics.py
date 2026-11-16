"""Model performance metrics page (page 3).

Displays ML model evaluation metrics once the ML Engineer pushes
`models/model.pkl` and records them in ARCHITECTURE.md §3.
"""

import streamlit as st
from ui import apply_theme, page_intro

st.set_page_config(page_title="Model Metrics", layout="wide")
apply_theme()
page_intro("Model Metrics", "Review the model's evaluation results and feature contract once training is complete.")

st.info(
    "Model evaluation is not connected yet. You can still use Historical Trends and the forecast display while the model artifact is prepared."
)

st.markdown("### Evaluation summary")
m1, m2, m3, m4 = st.columns(4)
m1.metric("F1 score", "Pending")
m2.metric("RMSE", "Pending")
m3.metric("Accuracy / R²", "Pending")
m4.metric("Model status", "Pending")

st.markdown("### Model information")
st.table({"Item": ["Problem type", "Features", "Test period", "Evaluation date"], "Status": ["Pending", "Pending", "Pending", "Pending"]})

st.markdown(
    """
### Expected content (per ARCHITECTURE.md)

| Item | Source | Status |
|---|---|---|
| Problem type | ML Engineer (§3 model card) | Pending |
| Test metric(s) | ML Engineer (§3 model card) | Pending |
| Feature order & dtypes | ML Engineer (§3 model card) | Pending |
| Model artifact | `models/model.pkl` | Pending |

Until then this page is a placeholder. Once landed, replace this file with
real metric charts (e.g. confusion matrix, residual plot, feature importance).
"""
)
