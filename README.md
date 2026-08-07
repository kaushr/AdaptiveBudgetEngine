# Decision Budget Engine

Workload-level model selection picks the best model for a task. Decision Budget
Engine decides how much reasoning each individual record within that task
deserves — routed on business signals (close probability, decision complexity),
never deal size.

Snowflake × Beta Fund × Evermind hackathon — Track 1, Cost of Intelligence.

**Live demo (hosted, offline mode): https://intellinomics.streamlit.app** —
reads the measured results committed in this repo; no warehouse connection,
exactly as labeled on the page.

## The measured result

Two arms over the same 30 sales opportunities: **reference** (every record →
premium model) vs **adaptive** (tier per record). A decision **changed** when
verdict or primary blocker differs between arms — exact match on fixed enums,
no judge model. 61 unique model calls; every number below is from the run.

| operating point | % routed cheap | total cost ($) | vs reference | decisions changed | verdict agreement |
|---|---|---|---|---|---|
| 0.98 · Conservative | 13% | 0.1147 | 53% | **4 of 30** | 90% |
| 0.95 · Balanced | 20% | 0.1090 | 51% | 6 of 30 | 83% |
| 0.90 · Savings-oriented | 30% | 0.0962 | 45% | 9 of 30 | 77% |
| Reference (1.00) | 0% | 0.2152 | 100% | — | — |

One threshold varies; all other policy logic held constant. The output is a
frontier an enterprise tunes to its risk tolerance — not a single correct
policy. We say *changed*, never *improved*: changed is measured.

## Run it

Offline (the demo path — reads measured results, zero live calls):

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
./demo-offline.sh
```

Live mode — same UI, same code path, reading the five result tables from
`DECISION_BUDGET.DEMO` instead of CSVs (still zero model calls; `AI_COMPLETE`
exists only in `scripts/run_arms.py`):

```bash
.venv/bin/pip install snowflake-connector-python   # once, live mode only
./demo-live.sh
```

Requires a `[connections.snowflake]` block in `.streamlit/secrets.toml`
(gitignored — account, user, key-pair auth; mirror `~/.snowflake/config.toml`).
The Source line under the title shows which mode is running — a launch
decision by design (no in-UI toggle): it's a provenance claim, not a view
preference. Ports are pinned (offline 8501, live 8502) so both modes run side
by side in two browser tabs — titled "DBE · OFFLINE" and "DBE · LIVE" — with
the offline tab as the instant fallback while presenting from live. Rebuilding everything
from scratch is `scripts/` in order (see repo map) — 61 short `AI_COMPLETE`
calls, pennies of credit.

## Repo map

| Path | What |
|---|---|
| `data/` | 30-record source dataset + schema; `data/results/` is the measured output and the offline fallback |
| `scripts/` | `dataset.py` → `policy.py` (dry-run) → `run_arms.py` (dual-arm calls) → `summarize.py` (scoring) → `load_snowflake.py` → `everos_log.py` (EverOS decision log) |
| `app/` | single-screen Streamlit demo |
| `00–05_*.md` | docs: [setup](00_Setup.md) · [build workbook](01_Build_Workbook.md) · [product brief](02_Product_Brief.md) · [judge prep](03_Judge_Questions.md) · [vocabulary](04_Terms_Vocabulary.md) · [demo script](05_Demo_Script.md) |

## Tiers

| Tier | Cortex model | AI credits per 1M tokens (in / out) |
|---|---|---|
| cheap | `llama3.1-8b` | 0.132 / 0.132 |
| balanced | `mistral-large2` | 1.20 / 3.60 |
| premium | `claude-sonnet-4-5` | 1.80 / 9.00 |

A tier is a price-quality point on an ordered ladder, not a model family —
three tiers is a demo choice, not an architectural limit.

## Event requirement (EverMind)

Every routing decision (signals in, tier out, agreement result) is logged to
EverOS — the memory/learning layer — and retrievable by search
(`scripts/everos_log.py`). Token and cost accounting lives in Snowflake
(`MODEL_RUNS`, `RUN_SUMMARY`), reconcilable against
`CORTEX_FUNCTIONS_USAGE_HISTORY`: Snowflake analyzing the token economy behind
the product.
