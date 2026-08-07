"""Load the four project tables into DECISION_BUDGET.DEMO (workbook T11).

Generates one SQL script from the results CSVs and runs it via `snow sql -f`.
Re-runnable: CREATE OR REPLACE. The CSVs in data/results/ remain the offline
fallback -- the demo never needs these tables to render.
"""

import csv
import os
import subprocess

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))

DDL = """
USE DATABASE DECISION_BUDGET;
USE SCHEMA DEMO;
CREATE OR REPLACE TABLE OPPORTUNITIES (
  opp_id STRING, name STRING, amount NUMBER, probability FLOAT, stage STRING,
  strategic_account BOOLEAN, no_economic_buyer BOOLEAN, competitor_present BOOLEAN,
  security_legal_blocked BOOLEAN, procurement_not_started BOOLEAN, champion_risk BOOLEAN,
  inactive_21d BOOLEAN, conflicting_signals BOOLEAN, days_since_activity NUMBER,
  close_date DATE, notes STRING
);
CREATE OR REPLACE TABLE MODEL_RUNS (
  run_id STRING, opp_id STRING, policy STRING, threshold FLOAT, tier STRING,
  model STRING, verdict STRING, primary_blocker STRING, next_best_action STRING,
  reasoning STRING, input_tokens NUMBER, output_tokens NUMBER, credits FLOAT,
  latency_ms NUMBER, error STRING
);
CREATE OR REPLACE TABLE POLICY_DECISIONS (
  opp_id STRING, policy STRING, threshold FLOAT, complexity_score NUMBER,
  probability FLOAT, strategic_account BOOLEAN, tier STRING, reason STRING,
  evidence STRING, changed_vs_reference BOOLEAN, consequential BOOLEAN
);
CREATE OR REPLACE TABLE RUN_SUMMARY (
  policy STRING, threshold FLOAT, total_credits FLOAT, total_dollars FLOAT,
  cheap_n NUMBER, balanced_n NUMBER, premium_n NUMBER, pct_cheap FLOAT,
  cheap_credits FLOAT, balanced_credits FLOAT, premium_credits FLOAT,
  decisions_changed NUMBER, verdict_agreement_pct FLOAT, blocker_agreement_pct FLOAT,
  waste_records STRING, waste_count NUMBER, waste_credits FLOAT, waste_dollars FLOAT,
  cost_vs_reference_pct FLOAT, projected_10k_weekly_dollars FLOAT
);
CREATE OR REPLACE TABLE HEROES (
  opp_id STRING, kind STRING, name STRING, amount NUMBER, probability FLOAT,
  complexity_score NUMBER,
  cheap_verdict STRING, cheap_primary_blocker STRING,
  cheap_next_best_action STRING, cheap_reasoning STRING,
  premium_verdict STRING, premium_primary_blocker STRING,
  premium_next_best_action STRING, premium_reasoning STRING,
  routed_tier STRING, routed_reason STRING, routed_evidence STRING
);
"""


def sql_lit(v):
    if v is None or v == "":
        return "NULL"
    s = str(v)
    if s.upper() in ("TRUE", "FALSE"):
        return s.upper()
    try:
        float(s)
        return s
    except ValueError:
        return "'" + s.replace("'", "''") + "'"


def inserts(table, csv_name, date_cols=()):
    path = os.path.join(RESULTS_DIR, csv_name)
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    cols = list(rows[0].keys())
    values = []
    for r in rows:
        vals = []
        for c in cols:
            if c in date_cols and r[c]:
                vals.append(f"'{r[c]}'::DATE")
            else:
                vals.append(sql_lit(r[c]))
        values.append("(" + ", ".join(vals) + ")")
    return f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n" + ",\n".join(values) + ";\n"


def main():
    sql = [DDL]
    sql.append(inserts("OPPORTUNITIES", "opportunities.csv", date_cols=("close_date",)))
    sql.append(inserts("MODEL_RUNS", "model_runs.csv"))
    sql.append(inserts("POLICY_DECISIONS", "policy_decisions.csv"))
    sql.append(inserts("RUN_SUMMARY", "run_summary.csv"))
    sql.append(inserts("HEROES", "heroes.csv"))
    sql.append("SELECT 'OPPORTUNITIES' t, COUNT(*) n FROM OPPORTUNITIES UNION ALL "
               "SELECT 'MODEL_RUNS', COUNT(*) FROM MODEL_RUNS UNION ALL "
               "SELECT 'POLICY_DECISIONS', COUNT(*) FROM POLICY_DECISIONS UNION ALL "
               "SELECT 'RUN_SUMMARY', COUNT(*) FROM RUN_SUMMARY UNION ALL "
               "SELECT 'HEROES', COUNT(*) FROM HEROES;")

    script = os.path.join(RESULTS_DIR, "load.sql")
    with open(script, "w") as fh:
        fh.write("\n".join(sql))
    out = subprocess.run(["snow", "sql", "-f", script], capture_output=True, text=True)
    print(out.stdout[-1500:])
    if out.returncode != 0:
        raise SystemExit(out.stderr[-1500:])


if __name__ == "__main__":
    main()
