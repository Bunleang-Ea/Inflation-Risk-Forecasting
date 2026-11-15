# Project Architecture & Contract — Inflation Risk Forecasting

**Repo:** Bunleang-Ea/Inflation-Risk-Forecasting  
**Goal:** Streamlit + ML app forecasting inflation risk using `Cambodia'sInflationRate2005-2025.csv`  
**Deadline:** Nov 18, 2026 (deploy `main` to Streamlit Community Cloud)  

> **Read this before touching the project.** This is the source of truth for architecture, repo layout, and handoff interfaces. Everyone (and your LLM prompts) must code to this contract. If something must change, update this file in a PR *before* changing code.

---

## 1. Repo layout (agreed paths)

```text
.
├── data/
│   ├── raw/
│   │   └── Cambodia'sInflationRate2005-2025.csv
│   └── processed/
│       ├── train.csv
│       └── test.csv
├── env/                           # Virtual environment folder (added to .gitignore)
├── models/
│   ├── .gitkeep                   # To preserve the empty folder in version control
│   └── model.pkl                  # Serialized best model (joblib/pickle)
├── notebooks/                     # Optional exploration only (not used by app)
│   └── .gitkeep                   # To preserve the empty folder in version control
├── pages/                         # Streamlit multi-page directory
│   ├── 1_📈_Historical_Trends.py 
│   ├── 2_🔮_Risk_Forecast.py     
│   └── 3_📊_Model_Metrics.py     
├── app.py                         # Streamlit entrypoint (Home/Landing page)
├── utils.py                       # Shared functions (data loading, model loading)
├── requirements.txt               # Pinned versions for deploy
├── ARCHITECTURE.md
└── CONTRIBUTING.md

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
- App must be able to load the model with `joblib.load()` under `@st.cache_resource` in `utils.py` without version conflicts.

**Model card (ML Engineer fills in via PR):**
- Problem type: `classification | regression` — `TBD`
- Library/serializer: `joblib|pickle`, `scikit-learn==TBD`
- Metric(s) on test: `TBD`
- **Expected input features (EXACT order and dtypes):** `TBD`
  *(Integration must build inputs to match this exactly.)*
- Prediction output: `TBD` (e.g. class label, probability, or numeric forecast value)

## 4. UI & integration contract (UI ↔ Integration ↔ Viz)

**Entry points:** `app.py` (Landing), `pages/1_📈_Historical_Trends.py`, `pages/2_🔮_Risk_Forecast.py`, `pages/3_📊_Model_Metrics.py`
**Shared Utilities:** `utils.py`

**UI Developer provides (stable names — agree Day 1):**
- Landing page structure in `app.py`.
- Shared layout conventions across the `pages/` directory.
- Sidebar container: `st.sidebar` in `2_🔮_Risk_Forecast.py`.
- Widget variables (name → type/widget → meaning): `TBD`
  *(e.g. `horizon = st.selectbox(...)`, `scenario_rate = st.slider(...)`)*

**Integration Engineer provides:**
- Shared data/model caching functions in `utils.py`.
- Cached model load: `model = joblib.load("models/model.pkl")` via `@st.cache_resource` in `utils.py`.
- Captures live widget values in `2_🔮_Risk_Forecast.py` → formats into DataFrame/NumPy array matching **Section 3 feature order/dtypes exactly**.
- Runs `model.predict(...)` (and `predict_proba` if applicable).
- Exposes clean, documented prediction outputs for Viz: `TBD` (variable names/structure).

**Visualization Specialist provides:**
- Reads historical data + live prediction outputs from Integration in the respective `pages/` files.
- Altair charts (`alt.Chart`), date on x-axis, inflation/risk on y-axis; historical vs forecast layered; high-risk threshold breaches clearly highlighted.
- Renders via `st.altair_chart(chart, use_container_width=True)` into the agreed UI slots on `1_📈_Historical_Trends.py` and `2_🔮_Risk_Forecast.py`.

## 5. Deployment contract (Team, Nov 18)

- Clean unused imports/commented dummy code; clear docs.
- Ensure `.gitkeep` files are not causing issues, and `env/` is strictly ignored in `.gitignore`.
- `requirements.txt` with **pinned versions** (e.g. `pandas==...`, `scikit-learn==...`, `streamlit==...`, `altair==...`) matching what trained/ran the model.
- Deploy **`main`** branch to Streamlit Community Cloud.
- Smoke test live public URL on multiple devices (laptop/phone).

## 6. Change control

- Don’t silently change paths, column names, feature order, widget var names, or output schema. **Update this contract in the same PR** and tag affected roles.
- When in doubt, check this file first — it’s the source of truth for handoffs.