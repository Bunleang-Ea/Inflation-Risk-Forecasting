# Project Contract — Inflation Risk Forecasting

**Repo:** Bunleang-Ea/Inflation-Risk-Forecasting  
**Goal:** Streamlit + ML app forecasting inflation risk using `Cambodia'sInflationRate2005-2025.csv`  
**Deadline:** Nov 18, 2026 (deploy `main` to Streamlit Community Cloud)  
**Rule:** Everyone (and your LLM prompts) codes to this contract. If something must change, update this file in a PR *before* changing code.

---

## 1. Repo layout (agreed paths)

```
.
├── app.py                         # Streamlit entrypoint (UI + integration + viz embed)
├── data/
│   ├── raw/
│   │   └── Cambodia'sInflationRate2005-2025.csv
│   └── processed/
│       ├── train.csv
│       └── test.csv
├── models/
│   └── model.pkl                  # Serialized best model (joblib/pickle)
├── notebooks/                     # Optional exploration only (not used by app)
├── requirements.txt               # Pinned versions for deploy
├── CONTRACT.md
└── CONTRIBUTING.md
```

> If you need extra modules, keep them importable from `app.py` (e.g. `src/`), but don’t move/rename the contract paths above without a PR updating this doc.

## 2. Data contract (Data Engineer → downstream)

**Source:** `data/raw/Cambodia'sInflationRate2005-2025.csv`

**Processing rules:**
- Load with Pandas, convert `Date` to datetime, **sort chronologically**.
- Engineer lagged time-series features with `shift()` (e.g. `t-1`, `t-3`, `t-12` on CPI/YoY as decided) — document exact columns produced.
- Create the **target** (binary 1/0 for risk classification, or isolated future CPI column for regression) — name and definition must be recorded below.
- **Chronological train/test split** — **no random shuffling**, no future leakage.
- Handle NaNs introduced by lag shifts (drop or impute initial rows) and verify.

**Outputs (must exist at these paths):**
- `data/processed/train.csv`
- `data/processed/test.csv`

**To fill in when data work lands (Data Engineer updates via PR):**
- Date column name & format: `TBD`
- Feature columns (exact names, in order): `TBD`
- Target column name & meaning (e.g. `risk_label` 1/0, threshold rule): `TBD`
- Split point/date: `TBD`
- Rows dropped/imputed due to lags: `TBD`

## 3. Model contract (ML Engineer → Integration)

**Artifact:** `models/model.pkl` (serialized with `joblib` or `pickle`)

**Requirements:**
- Train baseline in Scikit-learn (e.g. LogisticRegression/RandomForest for classification, or LinearRegression for regression).
- Evaluate on the **chronological test set** (F1 for classification, RMSE for regression) — record metrics below.
- App must be able to load the model with `joblib.load()` under `@st.cache_resource` without version conflicts.

**Model card (ML Engineer fills in via PR):**
- Problem type: `classification | regression` — `TBD`
- Library/serializer: `joblib|pickle`, `scikit-learn==TBD`
- Metric(s) on test: `TBD`
- **Expected input features (EXACT order and dtypes):** `TBD`  
  *(Integration must build inputs to match this exactly.)*
- Prediction output: `TBD` (e.g. class label, probability, or numeric forecast value)

## 4. UI & integration contract (UI ↔ Integration ↔ Viz)

**Entry point:** `app.py`

**UI Developer provides (stable names — agree Day 1):**
- Sidebar container: `st.sidebar`
- Widget variables (name → type/widget → meaning): `TBD`  
  *(e.g. `horizon = st.selectbox(...)`, `scenario_rate = st.slider(...)`)*
- Main layout: `st.columns()` placeholders/slots for metrics and charts: `TBD`

**Integration Engineer provides:**
- Cached model load: `model = joblib.load("models/model.pkl")` via `@st.cache_resource`
- Captures live widget values → formats into DataFrame/NumPy array matching **Section 3 feature order/dtypes exactly**
- Runs `model.predict(...)` (and `predict_proba` if applicable)
- Exposes clean, documented prediction outputs for Viz: `TBD` (variable names/structure)

**Visualization Specialist provides:**
- Reads historical data + live prediction outputs from Integration
- Altair charts (`alt.Chart`), date on x-axis, inflation/risk on y-axis; historical vs forecast layered; high-risk threshold breaches clearly highlighted
- Renders via `st.altair_chart(chart, use_container_width=True)` into the agreed UI slots

## 5. Deployment contract (Team, Nov 18)

- Clean unused imports/commented dummy code; clear docs.
- `requirements.txt` with **pinned versions** (e.g. `pandas==...`, `scikit-learn==...`, `streamlit==...`, `altair==...`) matching what trained/ran the model.
- Deploy **`main`** branch to Streamlit Community Cloud.
- Smoke test live public URL on multiple devices (laptop/phone).

## 6. Change control

- Don’t silently change paths, column names, feature order, widget var names, or output schema. **Update this contract in the same PR** and tag affected roles.
- When in doubt, check this file first — it’s the source of truth for handoffs.
