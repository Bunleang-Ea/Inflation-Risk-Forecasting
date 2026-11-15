"""Model performance metrics page (page 3).

Displays ML model evaluation metrics once the ML Engineer pushes
`models/model.pkl` and records them in ARCHITECTURE.md §3.
"""

import streamlit as st

st.set_page_config(page_title="Model Metrics", layout="wide")
st.title("Model Metrics")

st.info(
    "Waiting for the ML Engineer to push `models/model.pkl` and record test-set "
    "metrics (F1 / RMSE) in ARCHITECTURE.md §3."
)

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
