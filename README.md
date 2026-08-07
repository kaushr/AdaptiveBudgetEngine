# Decision Budget Engine

Workload-level model selection picks the best model for a task. This decides how
much reasoning each individual record within that task deserves. Snowflake ×
Beta Fund × Evermind hackathon — Track 1, Cost of Intelligence.

Docs: [00_Setup.md](00_Setup.md) (environment) · [01_Build_Workbook.md](01_Build_Workbook.md)
(build plan) · [02_Product_Brief.md](02_Product_Brief.md) (product) ·
[03_Judge_Questions.md](03_Judge_Questions.md) (framing).

## Run the demo (offline — zero live calls)

```bash
/opt/homebrew/bin/python3.11 -m venv .venv        # once
.venv/bin/pip install streamlit pandas             # once
.venv/bin/streamlit run app/streamlit_app.py
```

Reads the measured results from `data/results/*.csv` (the fallback tables).
Set `DBE_SOURCE=snowflake` to read the same tables from `DECISION_BUDGET.DEMO`.

## Rebuild the results (spends pennies of Cortex credit)

```bash
cd scripts
python3 dataset.py            # regenerate data/opportunities.csv (30 records)
python3 policy.py             # dry-run: routing distributions, no model calls
python3 run_arms.py --heroes  # the three heroes first (workbook rule)
python3 run_arms.py           # full dual-arm plan (cached, resumable)
python3 summarize.py          # score arms, write data/results/*.csv
python3 load_snowflake.py     # load the four tables into DECISION_BUDGET.DEMO
```

Calls are cached in `data/results/call_cache.json` — re-runs never re-spend.

## Measurement

Two arms over the same 30 records: reference (all premium) vs adaptive
(cheap / balanced / premium per record, from business signals only — never deal
size). A decision **changed** when verdict or primary blocker differs between
arms — exact match on fixed enums, no judge model. We say *changed*, never
*improved*: changed is measured.
