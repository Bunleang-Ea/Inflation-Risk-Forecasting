# Inflation Risk Forecasting

Streamlit + Machine Learning app to forecast inflation risk using Cambodia inflation data (2005–2025).

- **Dataset:** `data/raw/Cambodia'sInflationRate2005-2025.csv`
- **Deadline:** Nov 18, 2026
- **Deploy target:** Streamlit Community Cloud (`main` branch)

## Team workflow (read before coding)

- **[`CONTRACT.md`](./CONTRACT.md)** — source of truth for paths, data/model/UI interfaces, and handoff schemas. Everyone (and LLM prompts) must follow it.
- **[`CONTRIBUTING.md`](./CONTRIBUTING.md)** — branching, PR/handoff rules, and LLM hygiene to avoid drift.

**TL;DR:** `main` stays deployable. Use short-lived task branches off `main`, open small PRs at each handoff, and keep the contract updated when interfaces change.

## Project schedule (WBS)

| Role | Dates | Key output |
|---|---|---|
| Data Engineer | Nov 13–14 | Cleaned/lagged features, chronological train/test split → `data/processed/` |
| Streamlit UI Developer | Nov 13–14 | `app.py` skeleton, sidebar widgets, layout placeholders |
| Machine Learning Engineer | Nov 15 | Baseline model + metrics → `models/model.pkl`, feature spec |
| Streamlit Integration Engineer | Nov 16 | Wire widgets → model → predictions |
| Visualization Specialist | Nov 17 | Altair charts (history + forecast, risk thresholds) in app |
| Entire Team | Nov 18 | Cleanup, pinned `requirements.txt`, deploy `main`, smoke test |

## Quick start (local)

```bash
# clone
git clone https://github.com/Bunleang-Ea/Inflation-Risk-Forecasting.git
cd Inflation-Risk-Forecasting

# (after requirements.txt exists)
pip install -r requirements.txt
streamlit run app.py
```

## Repo structure (target)

```
app.py
data/raw/                  # source CSV
data/processed/            # train.csv, test.csv
models/                    # model.pkl
CONTRACT.md                # interface contract
CONTRIBUTING.md            # workflow rules
requirements.txt           # pinned deps (for deploy)
```
