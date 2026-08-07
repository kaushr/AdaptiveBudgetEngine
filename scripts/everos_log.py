"""EverOS integration hook (event requirement): log routing decisions as memory.

Additive, not load-bearing — reads the already-written results tables and
records one message per routing decision (signals in, tier out, agreement
result) into an EverOS session, then flushes extraction so the decisions are
retrievable. EverOS distills recorded activity into episodes/facts (and, as
patterns repeat, Cases -> Skills) — the memory substrate for the Layer 3
learning loop in the judge prep.

Usage:
    python3 everos_log.py            # log the 0.98 operating point's 30 decisions
    python3 everos_log.py --search "which records routed premium"
"""

import argparse
import csv
import json
import os
import time
import urllib.request

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
ENV_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "local", "evermind.env"))
BASE = "https://api.evermind.ai/api/v2/memory"
USER_ID = "decision-budget-engine"
SESSION_ID = "dbe-run-2026-08-06-t098"
THRESHOLD = 0.98


def api_key():
    with open(ENV_PATH) as fh:
        for line in fh:
            if line.startswith("EVERMIND_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(f"EVERMIND_API_KEY not found in {ENV_PATH}")


def post(endpoint, payload):
    req = urllib.request.Request(
        f"{BASE}/{endpoint}", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def decision_message(d, run_row):
    changed = d["changed_vs_reference"] == "True"
    outcome_txt = ("its conclusions DIFFERED from the reference arm"
                   if changed else "its conclusions matched the reference arm")
    return (f"Routing decision for {d['opp_id']}: signals were close probability "
            f"{d['probability']}, decision complexity score {d['complexity_score']}, "
            f"strategic account {d['strategic_account']}. The policy selected the "
            f"{d['tier']} tier because: {d['reason']}. When evaluated, {outcome_txt} "
            f"(verdict {run_row['verdict']}, primary blocker {run_row['primary_blocker']}).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", help="retrieval demo: search the decision log")
    args = ap.parse_args()

    if args.search:
        out = post("search", {"query": args.search, "user_id": USER_ID})
        eps = out["data"]["episodes"]
        print(f"{len(eps)} episodes for: {args.search!r}")
        for e in eps[:5]:
            print(f"  [{e['score']:.2f}] {e['summary'][:160]}")
            for f in e.get("atomic_facts", [])[:8]:
                print(f"      - {f['content'][:200]}")
        return

    with open(os.path.join(RESULTS_DIR, "policy_decisions.csv")) as fh:
        decisions = [d for d in csv.DictReader(fh)
                     if float(d["threshold"]) == THRESHOLD]
    with open(os.path.join(RESULTS_DIR, "model_runs.csv")) as fh:
        runs = {r["opp_id"]: r for r in csv.DictReader(fh)
                if r["policy"] == "adaptive" and r["threshold"]
                and float(r["threshold"]) == THRESHOLD}

    now_ms = int(time.time() * 1000)
    messages = [{"role": "user", "sender_id": USER_ID, "timestamp": now_ms + i,
                 "content": decision_message(d, runs[d["opp_id"]])}
                for i, d in enumerate(decisions)]

    for i in range(0, len(messages), 10):  # modest batches
        out = post("add", {"session_id": SESSION_ID, "user_id": USER_ID,
                           "messages": messages[i:i + 10]})
        print(f"add [{i}-{i + len(messages[i:i + 10]) - 1}]: {out['data']['status']}")

    out = post("flush", {"session_id": SESSION_ID, "user_id": USER_ID})
    print("flush:", out["data"]["status"])
    print(f"logged {len(messages)} routing decisions to EverOS "
          f"(session {SESSION_ID}, user {USER_ID})")


if __name__ == "__main__":
    main()
