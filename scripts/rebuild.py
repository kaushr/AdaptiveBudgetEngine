"""Clean-slate rebuild: wipe → 61 calls → score → load → EverOS → verify → compare.

Narrates every step by default — the prompts, raw responses, INSERTs, and acks
printed are the actual ones, never simulated. Flags:
    --quiet          stage banners and outcomes only (for reruns)
    --full-prompts   print untruncated prompts during the call stage

Inputs are never touched: scripts/dataset.py (the authored source),
data/opportunities.csv, docs. Outputs wiped and regenerated: the five Snowflake
tables, data/results/*.csv, call_cache.json. The committed results CSVs are
backed up to data/results.pre-rebuild.bak/ first (git also has them:
`git checkout -- data/results/` restores offline mode after a failed rebuild).
"""

import argparse
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from dataset import OPPORTUNITIES, write_csv  # noqa: E402
import run_arms  # noqa: E402
import summarize  # noqa: E402
import load_snowflake  # noqa: E402
import everos_log  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(ROOT, "data", "results")
BACKUP = os.path.join(ROOT, "data", "results.pre-rebuild.bak")
TABLES = ["OPPORTUNITIES", "MODEL_RUNS", "POLICY_DECISIONS", "RUN_SUMMARY", "HEROES"]


def banner(title):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def snow(sql):
    out = subprocess.run(["snow", "sql", "-q", sql, "--format", "json"],
                         capture_output=True, text=True, timeout=180)
    if out.returncode != 0:
        raise RuntimeError(f"snow sql failed: {out.stderr.strip()[:400]}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return []


def stage_wipe(quiet):
    banner("STAGE 1/6 — WIPE (~30s)")
    if os.path.isdir(RESULTS):
        os.makedirs(BACKUP, exist_ok=True)
        for f in glob.glob(os.path.join(RESULTS, "*.csv")):
            shutil.copy2(f, BACKUP)
        print(f"backed up {len(glob.glob(os.path.join(BACKUP, '*.csv')))} result CSVs "
              f"→ {os.path.relpath(BACKUP, ROOT)}  (git has them too)")
    for t in TABLES:
        snow(f"DROP TABLE IF EXISTS DECISION_BUDGET.DEMO.{t}")
        print(f"DROP TABLE IF EXISTS {t} ✓")
    for f in sorted(glob.glob(os.path.join(RESULTS, "*.csv")) +
                    glob.glob(os.path.join(RESULTS, "*.json")) +
                    glob.glob(os.path.join(RESULTS, "*.sql"))):
        os.remove(f)
        print(f"deleted {os.path.relpath(f, ROOT)} ✓")
    print("NOT deleted: scripts/dataset.py (authored source), data/opportunities.csv "
          "(authored input), data/SCHEMA.md, docs.")


def stage_calls(quiet, full_prompts):
    banner("STAGE 2/6 — 61 MODEL CALLS (~6-8 min, ~$0.30)")
    write_csv(os.path.join(ROOT, "data", "opportunities.csv"))
    print("regenerated data/opportunities.csv from scripts/dataset.py (30 records)")
    cache = run_arms.load_cache()
    plan = run_arms.call_plan()
    records = {r["opp_id"]: r for r in OPPORTUNITIES}
    todo = [(oid, t) for oid, tiers in plan.items() for t in tiers]
    print(f"plan: {len(todo)} unique (record, tier) calls — heroes first\n")
    spend, t0 = 0.0, time.time()
    for i, (oid, tier) in enumerate(todo):
        res = run_arms.run_call(records[oid], tier, cache, verbose=not quiet,
                                full_prompts=full_prompts,
                                header=f"[call {i + 1}/{len(todo)}]")
        spend += res["credits"]
        line = (f"  running total: {i + 1}/{len(todo)} calls · spend so far: "
                f"${spend * 3:.4f} · elapsed {int(time.time() - t0)}s")
        print(line + ("\n" if not quiet else ""), flush=True)
        if res["error"]:
            print(f"  !! error record for {oid}|{tier} — will surface in scoring")
    errors = [k for k, v in cache.items() if v.get("error")]
    print(f"calls complete: {len(todo)} done, {len(errors)} error records, "
          f"total ${spend * 3:.4f} ({spend:.6f} cr)")
    if errors:
        raise SystemExit(f"error records present, fix before scoring: {errors}")


def stage_score(quiet):
    banner("STAGE 3/6 — SCORING (seconds, zero model calls)")
    summarize.main()
    with open(os.path.join(RESULTS, "run_summary.csv")) as fh:
        for s in csv.DictReader(fh):
            if s["policy"] == "adaptive":
                print(f"  {s['threshold']} → {s['cheap_n']}C/{s['balanced_n']}B/"
                      f"{s['premium_n']}P · {s['decisions_changed']} changed · "
                      f"verdict {s['verdict_agreement_pct']}% · "
                      f"cost {s['cost_vs_reference_pct']}% of reference")


def stage_load(quiet):
    banner("STAGE 4/6 — SNOWFLAKE LOAD (~30-60s)")
    load_snowflake.main()
    rows = snow(" UNION ALL ".join(
        f"SELECT '{t}' AS T, COUNT(*) AS N FROM DECISION_BUDGET.DEMO.{t}" for t in TABLES))
    for r in rows:
        print(f"  {r['T']} ← {r['N']} rows ✓")
    expected = {"OPPORTUNITIES": 30, "MODEL_RUNS": 120, "POLICY_DECISIONS": 90,
                "RUN_SUMMARY": 4, "HEROES": 3}
    got = {r["T"]: int(r["N"]) for r in rows}
    assert got == expected, f"row counts off: {got}"


def stage_everos(quiet):
    banner("STAGE 5/6 — EVEROS DECISION LOG (~1-2 min)")
    print(f"session: {everos_log.SESSION_ID}")
    # log the 30 decisions (prints each batch ack)
    sys.argv = ["everos_log.py"]
    everos_log.main()
    for attempt in range(4):
        out = everos_log.post("flush", {"session_id": everos_log.SESSION_ID,
                                        "user_id": everos_log.USER_ID})
        status = out["data"]["status"]
        print(f"flush attempt {attempt + 1}: {status}")
        if status == "extracted":
            break
        time.sleep(15)
    out = everos_log.post("search", {"query": "which records routed premium because of "
                                              "high decision complexity",
                                     "user_id": everos_log.USER_ID})
    eps = out["data"]["episodes"]
    print(f"retrieval smoke test: {len(eps)} episode(s)")
    for e in eps[:2]:
        print(f"  [{e['score']:.2f}] {e['summary'][:140]}")


def stage_compare(quiet):
    banner("STAGE 6/6 — VERIFY + COMPARE vs committed numbers")
    # fresh timestamps from Snowflake's own metadata
    rows = snow("SELECT table_name, created, last_altered FROM "
                "DECISION_BUDGET.DEMO.INFORMATION_SCHEMA.TABLES "
                "WHERE table_schema='DEMO' ORDER BY table_name")
    for r in rows:
        print(f"  {r['TABLE_NAME']}: created {r['CREATED']}")

    def load_csv(path):
        with open(path) as fh:
            return list(csv.DictReader(fh))

    old_sum = {("adaptive", s["threshold"]): s for s in load_csv(os.path.join(BACKUP, "run_summary.csv"))
               if s["policy"] == "adaptive"}
    new_sum = {("adaptive", s["threshold"]): s for s in load_csv(os.path.join(RESULTS, "run_summary.csv"))
               if s["policy"] == "adaptive"}

    # Routing must be IDENTICAL: deterministic policy over unchanged records.
    old_route = {(d["threshold"], d["opp_id"]): d["tier"]
                 for d in load_csv(os.path.join(BACKUP, "policy_decisions.csv"))}
    new_route = {(d["threshold"], d["opp_id"]): d["tier"]
                 for d in load_csv(os.path.join(RESULTS, "policy_decisions.csv"))}
    assert old_route == new_route, "ROUTING DRIFTED — policy or dataset changed, investigate"
    print("\nrouting: identical across all thresholds ✓ (deterministic policy, unchanged records)")

    # Conclusions MAY drift (LLMs at temp 0 are near- but not perfectly deterministic)
    print("\nfrontier — new vs committed:")
    drift = False
    for key in sorted(new_sum):
        o, n = old_sum[key], new_sum[key]
        for field, label in (("decisions_changed", "changed"),
                             ("verdict_agreement_pct", "verdict agr"),
                             ("blocker_agreement_pct", "blocker agr"),
                             ("pct_cheap", "% cheap")):
            same = o[field] == n[field]
            drift |= not same
            mark = "✓ unchanged" if same else f"→ DRIFTED (was {o[field]})"
            print(f"  t={key[1]} {label}: {n[field]} {mark}")
    old_runs = {r["run_id"]: r for r in load_csv(os.path.join(BACKUP, "model_runs.csv"))}
    new_runs = {r["run_id"]: r for r in load_csv(os.path.join(RESULTS, "model_runs.csv"))}
    flips = [(k, f"{old_runs[k]['verdict']}/{old_runs[k]['primary_blocker']}",
              f"{v['verdict']}/{v['primary_blocker']}")
             for k, v in new_runs.items()
             if k in old_runs and (v["verdict"] != old_runs[k]["verdict"]
                                   or v["primary_blocker"] != old_runs[k]["primary_blocker"])]
    if flips:
        print(f"\nconclusion flips vs committed run ({len(flips)}):")
        for k, was, now in sorted(flips):
            print(f"  {k}: {was} → {now}")
        print("If a flip moved a headline number: update 05_Demo_Script.md to match "
              "the screen (the script must say what the screen says), re-run the "
              "language/consistency sweep, and commit the new results CSVs.")
    else:
        print("\nno conclusion flips — every record's verdict/blocker matches the committed run")
    if not drift:
        print("\nRESULT: numbers identical to committed run — script and screen already agree ✓")
    else:
        print("\nRESULT: DRIFT detected — see above; demo script must match the screen exactly")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="banners and outcomes only")
    ap.add_argument("--full-prompts", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    stage_wipe(args.quiet)
    stage_calls(args.quiet, args.full_prompts)
    stage_score(args.quiet)
    stage_load(args.quiet)
    stage_everos(args.quiet)
    stage_compare(args.quiet)
    print(f"\nrebuild complete in {int((time.time() - t0) / 60)}m{int(time.time() - t0) % 60}s")


if __name__ == "__main__":
    main()
