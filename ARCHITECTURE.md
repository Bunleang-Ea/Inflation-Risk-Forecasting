# Project Architecture & Contract — Inflation Risk Forecasting

**Repo:** Bunleang-Ea/Inflation-Risk-Forecasting  
**Goal:** Streamlit + ML app forecasting inflation risk using `cambodia_inflation_2005_2025.csv`  
**Deadline:** Nov 18, 2026 (deploy `main` to Streamlit Community Cloud)  

> **Read this before touching the project.** This is the source of truth for architecture, repo layout, and handoff interfaces. Everyone (and your LLM prompts) must code to this contract. If something must change, update this file in a PR *before* changing code.

---

## 1. Repo layout (agreed paths)

```text
.
├── data/
│   ├── raw/
│   │   └── cambodia_inflation_2005_2025.csv
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
│   ├── 1_Historical_Trends.py 
│   ├── 2_Risk_Forecast.py     
│   └── 3_Model_Metrics.py     
├── app.py                         # Streamlit entrypoint (Home/Landing page)
├── utils.py                       # Shared functions (data loading, model loading)
├── requirements.txt               # Pinned versions for deploy
├── ARCHITECTURE.md
└── CONTRIBUTING.md

## 2. Data contract (Data Engineer → downstream)

**Source:** `data/raw/cambodia_inflation_2005_2025.csv`

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
- Date column name & format: `Date` — `m/d/yyyy` (e.g. `12/1/2005` is 1 Dec 2005; the day field is always `1`).
  **Corrected by Integration Engineer (Nov 18):** this file was documented as `dd/mm/yyyy`, but the
  raw CSV is month-first. Parsing it as `dd/mm/yyyy` silently turns every row into January of its
  year. `utils.DATE_FORMAT = "%m/%d/%Y"` now parses it explicitly; Data Engineer to confirm.
- Feature columns (exact names, in order): `Date, CPI_all_item, MoM_Change_CPI_all_item, YoY_Change_CPI_all_item, CPI_3_Month_Moving_Avg, CPI_12_Month_Moving_Avg, YoY_3_Month_Avg, YoY_12_Month_Avg`
- Target column name & meaning (e.g. `risk_label` 1/0, threshold rule): Suggested `risk_label` = 1 when `YoY_Change_CPI_all_item` > team-agreed risk threshold, else 0. Threshold value: `TBD` (Data Engineer + ML Engineer agree in PR).
- Split point/date: `TBD` (Data Engineer decides, must be chronological — earlier dates train, later dates test).
- Rows dropped/imputed due to lags: `TBD` (after lag feature engineering; document count).

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

**Integration adapter (implemented in `utils.py`, PR from Integration Engineer):**

The app does not hard-code the feature order. At startup `utils.get_feature_names(model)` reads
`model.feature_names_in_` (recorded automatically by scikit-learn when the model is fitted on a
DataFrame) and only falls back to `utils.FEATURES` when that attribute is absent. **The ML Engineer
should therefore fit on a named DataFrame** so the contract is carried by the artifact itself.

| Step | Function | Behaviour |
|---|---|---|
| Load | `load_model()` | `joblib.load`, `@st.cache_resource`, pickle fallback |
| Format | `build_feature_frame(inputs, names, history)` | One row, exact column order, `float`, raises listing unresolved features |
| Predict | `predict_risk(inputs, model, history, threshold)` | `predict_proba` → `predict` → regressor output; rule-based fallback |
| Output | `build_forecast(...)` → `Forecast` | Chart-ready history + forecast frame |

Feature resolution order per column: widget input → latest observed value → lag column
`"<base>_t-<n>"` computed from history. Lag names must follow that pattern for the adapter to
resolve them; otherwise supply the value as a widget input.

**Interim behaviour (until `models/model.pkl` lands):** `predict_risk` returns a rule-based
logistic score `1 / (1 + exp(-(value - threshold) / RISK_SPREAD))`, and `build_forecast` projects the
metric from the last observation toward the sidebar scenario rate with an exponential decay
(`DECAY_MONTHS = 6`). Both are labelled `source="rule"` in the UI and are replaced automatically when
the artifact and a matching feature contract exist.

## 4. UI & integration contract (UI ↔ Integration ↔ Viz)

**Entry points:** `app.py` (Landing), `pages/1_Historical_Trends.py`, `pages/2_Risk_Forecast.py`, `pages/3_Model_Metrics.py`
**Shared Utilities:** `utils.py`

**UI Developer provides (stable names — agree Day 1):**
- Landing page structure in `app.py`.
- Shared layout conventions across the `pages/` directory.
- Sidebar container: `st.sidebar` in `2_Risk_Forecast.py`.
- Widget variables (name → type/widget → meaning), live on `pages/2_Risk_Forecast.py`:
  - `forecast_horizon` → `st.slider` (3–24, default 12) → months projected in the forecast view.
  - `scenario_rate` → `st.slider` (observed range ±1, step 0.1) → hypothetical inflation rate (% YoY) the projection reverts toward. **Added by Integration**; UI Developer to own the styling.
  - `risk_threshold` → `st.slider` (0–max+1, step 0.1) → high-risk reference level (% YoY).
- Main layout: `st.columns()` placeholders/slots for metrics and charts.

**Integration Engineer provides:**
- Shared data/model caching functions in `utils.py`.
- Cached model load: `model = joblib.load("models/model.pkl")` via `@st.cache_resource` in `utils.py`.
- Captures live widget values in `2_Risk_Forecast.py` → formats into DataFrame/NumPy array matching **Section 3 feature order/dtypes exactly**.
- Runs `model.predict(...)` (and `predict_proba` if applicable).
- **Exposes clean, documented prediction outputs for Viz (stable names):**

  ```python
  prediction = utils.predict_risk(scenario_inputs, model=model, history=df, threshold=risk_threshold)
  forecast   = utils.build_forecast(df, horizon=horizon, scenario_rate=scenario_rate,
                                    threshold=risk_threshold, model=model)
  forecast_df = forecast.frame
  ```

  `forecast_df` columns (do not rename):

  | Column | dtype | Meaning |
  |---|---|---|
  | `Date` | datetime64 | Month, sorted ascending |
  | `YoY_Change_CPI_all_item` | float | Inflation metric (% YoY) — plotted on y-axis |
  | `type` | str | `"Historical"` or `"Forecast"` |
  | `risk_prob` | float | P(high risk), 0–1 |
  | `risk_label` | int | 1 = high risk, 0 = not high risk |
  | `high_risk` | bool | `YoY > risk_threshold` (for colour encoding) |

  Also available: `forecast.history`, `forecast.forecast` (same columns filtered by `type`),
  `forecast.peak_value`, `forecast.peak_date`, `forecast.source`, plus
  `prediction.value` / `.probability` / `.label` / `.source`.

**Metric note:** the plotted metric is `YoY_Change_CPI_all_item`, not the CPI index, so thresholds
are expressed in % YoY (default `RISK_THRESHOLD = 3.0`). Change `utils.VALUE_COL` if the team prefers CPI.

**Visualization Specialist provides:**
- Reads historical data + live prediction outputs from Integration in the respective `pages/` files.
- Altair charts (`alt.Chart`), date on x-axis, inflation/risk on y-axis; historical vs forecast layered; high-risk threshold breaches clearly highlighted.
- Renders via `st.altair_chart(chart, use_container_width=True)` into the agreed UI slots on `1_Historical_Trends.py` and `2_Risk_Forecast.py`.

## 5. Deployment contract (Team, Nov 18)

- Clean unused imports/commented dummy code; clear docs.
- Ensure `.gitkeep` files are not causing issues, and `env/` is strictly ignored in `.gitignore`.
- `requirements.txt` with **pinned versions** (e.g. `pandas==...`, `scikit-learn==...`, `streamlit==...`, `altair==...`) matching what trained/ran the model.
- Deploy **`main`** branch to Streamlit Community Cloud.
- Smoke test live public URL on multiple devices (laptop/phone).

## 6. Change control

- Don’t silently change paths, column names, feature order, widget var names, or output schema. **Update this contract in the same PR** and tag affected roles.
- When in doubt, check this file first — it’s the source of truth for handoffs.

## 7. Branch protection (owner only)

**`main` should be protected** so nobody can push to it directly — only via PR. This makes the "don't break main" rule real, not just a suggestion.

**Owner (`Bunleang-Ea`) sets this in the repo UI:**
1. Go to `Settings` → `Branches` → `Branch protection rules`
2. Select `main`
3. Enable **Require a pull request review before merging** (1 reviewer)
4. Enable **Restrict who can push to this branch** (or leave it for the team)
5. Save

*Note: branch protection requires **admin** permission on the repo. If you're a collaborator without admin, ask the repo owner (`Bunleang-Ea`) to apply it.*