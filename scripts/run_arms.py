"""Dual-arm runner (workbook T7/T8): real AI_COMPLETE calls via `snow sql`.

Call plan is deduplicated on (opp_id, tier): conclusions depend only on the
tier a record is served at, so the reference arm's premium call is reused
wherever the adaptive arm also routes premium. Heroes additionally get a
cheap call for the side-by-side comparison view.

Every call is cached incrementally in data/results/call_cache.json — re-runs
never re-spend. Strict JSON contract per workbook section 4: validate, one
retry, then error record.

Usage:
    python3 run_arms.py --heroes     # the three heroes only, print comparison
    python3 run_arms.py              # full plan
"""

import argparse
import json
import os
import re
import subprocess
import time

from dataset import OPPORTUNITIES, FLAGS, complexity_score
from policy import route, CHEAP, PREMIUM
from pricing import TIER_MODEL, call_credits

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
CACHE_PATH = os.path.join(RESULTS_DIR, "call_cache.json")

THRESHOLDS = (0.98, 0.95, 0.90)
HEROES = ("OPP-001", "OPP-002", "OPP-003")

VERDICTS = {"ON_TRACK", "AT_RISK", "NO_ACTION_NEEDED"}
BLOCKERS = {"ECONOMIC_BUYER", "SECURITY_LEGAL", "PROCUREMENT", "COMPETITION",
            "PRICING", "CHAMPION_LOSS", "INACTIVITY", "NONE"}


def build_prompt(r):
    active = [f for f in FLAGS if r[f]] or ["none"]
    return f"""You are a sales operations analyst reviewing one CRM opportunity. Answer the manager's question: can I trust this forecast, what is the biggest risk, and what should be done next?

Respond with ONLY a JSON object — no markdown, no code fences, no text before or after — with exactly these fields:
{{"verdict": "...", "primary_blocker": "...", "next_best_action": "...", "reasoning": "..."}}

Verdict decision procedure — apply these steps IN ORDER and use the first that matches:
1. If stage is CONTRACT AND active_risk_flags is "none" AND crm_close_probability is 0.9 or higher: verdict is NO_ACTION_NEEDED (the deal is effectively won; waiting for paperwork is not selling work).
2. If crm_close_probability is 0.1 or lower: verdict is NO_ACTION_NEEDED (the deal is effectively dead; no intervention changes the result).
3. If any active risk flag requires intervention now: verdict is AT_RISK.
4. Otherwise: verdict is ON_TRACK.

Field rules:
- verdict: exactly one of ON_TRACK, AT_RISK, NO_ACTION_NEEDED, chosen by the decision procedure above.
- primary_blocker: exactly one of ECONOMIC_BUYER, SECURITY_LEGAL, PROCUREMENT, COMPETITION, PRICING, CHAMPION_LOSS, INACTIVITY, NONE. Pick the single biggest obstacle; NONE only if no obstacle exists.
- next_best_action: one specific action, one sentence.
- reasoning: two or three sentences grounded in the record's evidence.
- Do not output probabilities or confidence scores anywhere.

Opportunity record:
- id: {r['opp_id']}  name: {r['name']}
- amount_usd: {r['amount']}  crm_close_probability: {r['probability']}  stage: {r['stage']}
- strategic_account: {r['strategic_account']}  days_since_activity: {r['days_since_activity']}  close_date: {r['close_date']}
- active_risk_flags: {', '.join(active)}
- notes: {r['notes']}"""


def snow_ai_complete(model, prompt):
    """One AI_COMPLETE call. Returns (parsed_response_dict, wall_ms)."""
    sql = (
        "SELECT AI_COMPLETE(model=>'{m}', prompt=>'{p}', "
        "model_parameters=>{{'temperature': 0}}, show_details=>TRUE) AS RESPONSE"
    ).format(m=model, p=prompt.replace("'", "''"))
    t0 = time.time()
    out = subprocess.run(
        ["snow", "sql", "-q", sql, "--format", "json"],
        capture_output=True, text=True, timeout=180,
    )
    wall_ms = int((time.time() - t0) * 1000)
    if out.returncode != 0:
        raise RuntimeError(f"snow sql failed: {out.stderr.strip()[:500]}")
    rows = json.loads(out.stdout)
    cell = rows[0]["RESPONSE"]
    if isinstance(cell, str):
        cell = json.loads(cell)
    return cell, wall_ms


def parse_output(detail):
    """Extract and validate the model's JSON answer. Raises ValueError."""
    text = detail["choices"][0]["messages"].strip()
    # tolerate accidental code fences despite instructions
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object in response")
    obj = json.loads(m.group(0))
    missing = {"verdict", "primary_blocker", "next_best_action", "reasoning"} - set(obj)
    if missing:
        raise ValueError(f"missing fields: {missing}")
    if obj["verdict"] not in VERDICTS:
        raise ValueError(f"bad verdict: {obj['verdict']}")
    if obj["primary_blocker"] not in BLOCKERS:
        raise ValueError(f"bad primary_blocker: {obj['primary_blocker']}")
    return obj


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as fh:
            return json.load(fh)
    return {}


def save_cache(cache):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(CACHE_PATH, "w") as fh:
        json.dump(cache, fh, indent=1)


def run_call(record, tier, cache):
    """Execute (or fetch cached) one (opp, tier) call. Returns result dict."""
    key = f"{record['opp_id']}|{tier}"
    if key in cache and not cache[key].get("error"):
        return cache[key]
    model = TIER_MODEL[tier]
    prompt = build_prompt(record)
    result = {"opp_id": record["opp_id"], "tier": tier, "model": model}
    attempts, last_err = 0, None
    while attempts < 2:
        attempts += 1
        try:
            detail, wall_ms = snow_ai_complete(model, prompt)
            usage = detail.get("usage", {})
            obj = parse_output(detail)
            result.update(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                credits=call_credits(model, usage.get("prompt_tokens", 0),
                                     usage.get("completion_tokens", 0)),
                latency_ms=wall_ms, attempts=attempts, error=None, **obj,
            )
            cache[key] = result
            save_cache(cache)
            return result
        except (ValueError, RuntimeError, KeyError, json.JSONDecodeError) as e:
            last_err = str(e)[:300]
            prompt_retry = prompt + "\n\nIMPORTANT: your previous response was invalid (" + last_err + "). Output ONLY the JSON object with the exact enum values listed."
            prompt = prompt_retry
    result.update(input_tokens=0, output_tokens=0, credits=0.0, latency_ms=0,
                  attempts=attempts, error=last_err,
                  verdict=None, primary_blocker=None,
                  next_best_action=None, reasoning=None)
    cache[key] = result
    save_cache(cache)
    return result


def call_plan():
    """Unique (opp_id, tier) pairs needed across both arms + hero comparisons."""
    plan = {}
    for r in OPPORTUNITIES:
        tiers = {PREMIUM}  # reference arm
        for t in THRESHOLDS:
            tiers.add(route(r, high_confidence_threshold=t)[0])
        if r["opp_id"] in HEROES:
            tiers.add(CHEAP)  # side-by-side comparison needs the cheap answer
        plan[r["opp_id"]] = sorted(tiers)
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heroes", action="store_true", help="run only the three heroes")
    args = ap.parse_args()

    cache = load_cache()
    plan = call_plan()
    records = {r["opp_id"]: r for r in OPPORTUNITIES}
    todo = [(oid, t) for oid, tiers in plan.items() for t in tiers
            if not args.heroes or oid in HEROES]
    pending = [k for k in todo if f"{k[0]}|{k[1]}" not in cache
               or cache[f"{k[0]}|{k[1]}"].get("error")]
    print(f"plan: {len(todo)} calls ({len(todo) - len(pending)} cached, {len(pending)} to run)")

    for i, (oid, tier) in enumerate(todo):
        res = run_call(records[oid], tier, cache)
        status = f"ERROR: {res['error']}" if res["error"] else \
            f"{res['verdict']} / {res['primary_blocker']} ({res['input_tokens']}+{res['output_tokens']} tok, {res['latency_ms']}ms)"
        print(f"[{i+1}/{len(todo)}] {oid} {tier:<9} {status}")

    if args.heroes:
        print("\n--- Hero comparison (cheap vs premium) ---")
        for oid in HEROES:
            c, p = cache.get(f"{oid}|cheap"), cache.get(f"{oid}|premium")
            if not (c and p):
                continue
            same = c["verdict"] == p["verdict"] and c["primary_blocker"] == p["primary_blocker"]
            print(f"\n{oid} (p={records[oid]['probability']}, cx={complexity_score(records[oid])}) "
                  f"-> conclusions {'IDENTICAL' if same else 'DIFFER'}")
            print(f"  cheap:   {c['verdict']} / {c['primary_blocker']} | {c['next_best_action']}")
            print(f"  premium: {p['verdict']} / {p['primary_blocker']} | {p['next_best_action']}")


if __name__ == "__main__":
    main()
