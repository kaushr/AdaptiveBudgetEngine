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
import urllib.error
import urllib.request

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
ENV_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "local", "evermind.env"))
BASE = "https://api.evermind.ai/api/v2/memory"
USER_ID = "decision-budget-engine"
SESSION_ID = "dbe-run-" + time.strftime("%Y-%m-%d") + "-t098"  # fresh session per day
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
    agreement_txt = ("its conclusions DIFFERED from the reference arm"
                     if changed else "its conclusions matched the reference arm")
    return (f"Routing decision for {d['opp_id']}: signals were close probability "
            f"{d['probability']}, decision complexity score {d['complexity_score']}, "
            f"strategic account {d['strategic_account']}. The policy selected the "
            f"{d['tier']} tier because: {d['reason']}. When evaluated, {agreement_txt} "
            f"(verdict {run_row['verdict']}, primary blocker {run_row['primary_blocker']}).")


POLICY_SESSION = "dbe-policy-store"
POLICY_ARTIFACT = (
    "Routing policy artifact for the Decision Budget Engine. "
    "policy-version: v1. author: hand-authored. "
    "basis: expert judgment, not learned. "
    "Rules in order: (1) if close probability is at or above the "
    "high-confidence threshold (operating points 0.98, 0.95, 0.90) route "
    "CHEAP — certainty vetoes spend; (2) if probability is 0.10 or lower "
    "route CHEAP — already lost; (3) if decision complexity score is 4 or "
    "higher route PREMIUM; (4) strategic accounts get at least BALANCED — a "
    "floor, never a bypass; (5) otherwise BALANCED. "
    "This version was written by a human. Version v2 would be learned from "
    "labeled decisions accumulated in this memory.")


def publish_policy():
    """Write the active policy to EverOS as a versioned, provenance-stamped
    artifact. Honesty is the point: v1 is hand-authored and says so."""
    out = post("add", {"session_id": POLICY_SESSION, "user_id": USER_ID,
                       "messages": [{"role": "user", "sender_id": USER_ID,
                                     "timestamp": int(time.time() * 1000),
                                     "content": POLICY_ARTIFACT}]})
    print("publish:", out["data"]["status"])
    for attempt in range(4):
        out = post("flush", {"session_id": POLICY_SESSION, "user_id": USER_ID})
        print(f"flush attempt {attempt + 1}: {out['data']['status']}")
        if out["data"]["status"] == "extracted":
            break
        time.sleep(15)


def fetch_policy_provenance(timeout=4):
    """Fetch the active policy's provenance from EverOS. Returns a dict
    {version, author, basis, score} or raises — callers must fall back to
    the local definition; the demo never depends on this call."""
    import re
    req = urllib.request.Request(
        f"{BASE}/search",
        data=json.dumps({"query": "hand-authored policy-version v1 expert judgment "
                                  "not learned routing policy artifact",
                         "user_id": USER_ID}).encode(),
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read())
    for e in out["data"]["episodes"]:
        text = e.get("episode", "") + " " + e.get("summary", "") + " " + \
            " ".join(f.get("content", "") for f in e.get("atomic_facts", []))
        # extraction paraphrases: "policy-version: v1" comes back as
        # "The policy version is v1.0" — match both, normalize v1.0 -> v1
        m = re.search(r"policy[- ]version\s*(?:is|:)?\s*(v[\d.]+)", text, re.I)
        if m and "hand-authored" in text.lower():
            return {"version": "v" + m.group(1).lstrip("vV").split(".")[0],
                    "author": "hand-authored",
                    "basis": "expert judgment, not learned",
                    "score": e.get("score", 0.0)}
    raise LookupError("policy artifact not found in EverOS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", help="retrieval demo: search the decision log")
    ap.add_argument("--publish-policy", action="store_true",
                    help="write the versioned policy artifact to EverOS")
    args = ap.parse_args()

    if args.publish_policy:
        publish_policy()
        prov = fetch_policy_provenance()
        print(f"round trip: {prov['version']} · {prov['author']} · "
              f"{prov['basis']} (relevance {prov['score']:.2f})")
        return

    if args.search:
        # Q&A armor: readable over a shoulder, graceful when offline.
        try:
            out = post("search", {"query": args.search, "user_id": USER_ID})
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise SystemExit(
                f"\nEverOS unreachable ({getattr(e, 'reason', e)}).\n"
                "No network or the API is down — the decision log itself is fine; "
                "retry when connectivity returns.")
        eps = out["data"]["episodes"]
        print(f"\nEverOS retrieval — {len(eps)} episode(s) for: {args.search!r}\n")
        import textwrap
        for e in eps[:5]:
            print(f"  relevance {e['score']:.2f}")
            print(textwrap.fill(e["summary"], width=76,
                                initial_indent="  ", subsequent_indent="  "))
            for f in e.get("atomic_facts", [])[:6]:
                print(textwrap.fill("• " + f["content"], width=76,
                                    initial_indent="    ", subsequent_indent="      "))
            print()
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
