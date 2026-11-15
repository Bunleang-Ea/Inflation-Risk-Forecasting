# Contributing & Workflow — Inflation Risk Forecasting

**Purpose:** keep `main` deployable, avoid branch drift, and make LLM-assisted work safe to merge.  
**Repo:** https://github.com/Bunleang-Ea/Inflation-Risk-Forecasting  
**Deadline:** Nov 18, 2026 — deploy `main` to Streamlit Community Cloud

> Read [`CONTRACT.md`](./CONTRACT.md) first. It defines paths, data/model/UI interfaces, and handoff schemas. Code to the contract.

---

## 1. Branching model

- **`main` = source of truth / always runnable / deployable.** Only reviewed, working code lands here.
- **Prefer short-lived task branches off `main`** (not permanent per-role branches):
  - Examples: `data/ingest-clean`, `data/lag-features`, `ui/sidebar`, `ml/baseline-rf`, `integration/wire-model`, `viz/altair-chart`, `chore/requirements`
  - Naming: `<area>/<short-task>` where area is `data|ui|ml|integration|viz|deploy|docs|fix`
- **Merge back quickly** at each handoff (same day). Open a PR → get a quick review → merge → branch again from updated `main`.
- **If you must keep a personal/role branch:** treat it as a workspace only. **Sync from `main` daily and open a PR into `main` at every handoff** (end of Nov 14, 15, 16, 17). Never let a branch diverge until the end.

## 2. Handoffs & schedule (align PRs to these)

| When | Role | Merge/handoff expectation |
|---|---|---|
| Nov 13–14 | Data Engineer | PR with processed datasets + updated `CONTRACT.md` §2 (features/target/split). Notify team. |
| Nov 13–14 | Streamlit UI Dev | PR with `app.py` skeleton, widget var names & chart slots documented in `CONTRACT.md` §4. |
| Nov 15 | ML Engineer | PR with `models/model.pkl` + `CONTRACT.md` §3 (feature order/dtypes, metrics). |
| Nov 16 | Integration Engineer | PR wiring widgets → model → predictions; outputs documented for Viz. |
| Nov 17 | Visualization Specialist | PR with Altair charts embedded; verify responsive updates with UI. |
| Nov 18 | Entire Team | Final cleanup, pinned `requirements.txt`, deploy `main`, smoke test live URL. |

## 3. PR checklist (required before merge)

- [ ] **Runs locally** (`streamlit run app.py` where applicable) — no crashes on the touched path.
- [ ] **Matches `CONTRACT.md`** (paths, column/feature names & order, widget vars, output schema). If changed, contract updated in the same PR.
- [ ] **Small & focused** — one task/handoff per PR when possible; easier to review and revert.
- [ ] **No junk** — remove debug prints, commented-out experiments, unused imports, stray notebooks/output not needed.
- [ ] **Artifacts in agreed locations** (e.g. `data/processed/*.csv`, `models/model.pkl`).
- [ ] **Handoff note in PR description:** what changed, how to run/test, anything downstream needs to know.

## 4. Working with LLMs (to avoid drift)

- **Prompt against the contract:** include relevant `CONTRACT.md` sections (paths, feature names/order, widget/output names) in your prompt so generated code matches interfaces.
- **Don’t paste giant blind dumps.** Generate/review in small chunks you understand; verify shapes, column names, and file paths.
- **Test before PR.** Run the code, check outputs (no NaN leakage, correct feature order, model loads, chart renders).
- **Commit readable diffs.** Keep generated code tidy; don’t rename/move agreed paths unless updating the contract.

## 5. Integration basics

- Pull/rebase from latest `main` before starting work: `git fetch origin && git rebase origin/main` (or merge).
- Don’t wait until “role complete” to integrate — push usable artifacts/interfaces early so downstream can wire against real shapes.
- If you hit a version conflict (e.g. scikit-learn/joblib), coordinate in the PR and pin agreed versions in `requirements.txt`.

## 6. Suggested quick start

```bash
git clone https://github.com/Bunleang-Ea/Inflation-Risk-Forecasting.git
cd Inflation-Risk-Forecasting
git checkout -b data/lag-features   # example task branch
# ... do work, test ...
git add -A && git commit -m "data: add lag features and train/test split"
git push -u origin data/lag-features
# open PR -> review -> merge to main
```

---
*Keep `main` green, keep PRs small, keep the contract updated.*