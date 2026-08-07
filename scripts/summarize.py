"""Build results tables (T9/T10 scoring + T13 fallback) from the call cache.

Outputs (data/results/):
  model_runs.csv        one row per opportunity per arm (reference + adaptive@t)
  policy_decisions.csv  explainability record per opportunity per threshold
  run_summary.csv       aggregates per arm -- every UI number comes from here
  heroes.csv            cheap-vs-premium comparison rows for the three heroes
  opportunities.csv     copy of the source records (UI + Snowflake load share it)

Scoring: a decision CHANGED if verdict or primary_blocker differs between the
adaptive arm's answer and the reference arm's answer. Exact match on enums,
no judge model anywhere.
"""

import csv
import json
import os

from dataset import OPPORTUNITIES, FLAGS, complexity_score, write_csv
from policy import route, CHEAP, BALANCED, PREMIUM
from pricing import TIER_MODEL, DOLLARS_PER_CREDIT

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
THRESHOLDS = (0.98, 0.95, 0.90)
HEROES = {"OPP-001": "settled", "OPP-002": "complex", "OPP-003": "contestable"}

ANSWER_FIELDS = ["verdict", "primary_blocker", "next_best_action", "reasoning",
                 "input_tokens", "output_tokens", "credits", "latency_ms", "error"]


def load_calls():
    with open(os.path.join(RESULTS_DIR, "call_cache.json")) as fh:
        return json.load(fh)


def arm_label(threshold):
    return "reference" if threshold is None else f"adaptive_{threshold:.2f}"


def main():
    calls = load_calls()
    recs = {r["opp_id"]: r for r in OPPORTUNITIES}

    def call(opp_id, tier):
        c = calls[f"{opp_id}|{tier}"]
        assert not c.get("error"), f"error record in cache: {opp_id}|{tier}"
        return c

    model_runs, policy_decisions, summaries = [], [], []

    # Reference arm: every record -> premium, no exceptions
    for oid, r in recs.items():
        c = call(oid, PREMIUM)
        model_runs.append({"run_id": f"reference|{oid}", "opp_id": oid,
                           "policy": "reference", "threshold": "",
                           "tier": PREMIUM, "model": TIER_MODEL[PREMIUM],
                           **{k: c[k] for k in ANSWER_FIELDS}})

    ref = {oid: call(oid, PREMIUM) for oid in recs}
    ref_credits = sum(c["credits"] for c in ref.values())
    summaries.append({
        "policy": "reference", "threshold": "", "total_credits": ref_credits,
        "total_dollars": ref_credits * DOLLARS_PER_CREDIT,
        "cheap_n": 0, "balanced_n": 0, "premium_n": 30, "pct_cheap": 0,
        "cheap_credits": 0.0, "balanced_credits": 0.0, "premium_credits": ref_credits,
        "decisions_changed": 0, "verdict_agreement_pct": 100.0,
        "blocker_agreement_pct": 100.0,
        "waste_records": "", "waste_count": 0, "waste_credits": 0.0, "waste_dollars": 0.0,
        "cost_vs_reference_pct": 100.0,
    })

    for t in THRESHOLDS:
        counts = {CHEAP: 0, BALANCED: 0, PREMIUM: 0}
        tier_credits = {CHEAP: 0.0, BALANCED: 0.0, PREMIUM: 0.0}
        changed, verdict_agree, blocker_agree = [], 0, 0
        waste_records, waste_credits = [], 0.0

        for oid, r in recs.items():
            tier, reason, evidence = route(r, high_confidence_threshold=t)
            counts[tier] += 1
            c = call(oid, tier)
            tier_credits[tier] += c["credits"]

            v_same = c["verdict"] == ref[oid]["verdict"]
            b_same = c["primary_blocker"] == ref[oid]["primary_blocker"]
            verdict_agree += v_same
            blocker_agree += b_same
            if not (v_same and b_same):
                changed.append(oid)
            # Waste: reference premium spend on records the policy called
            # settled (routed cheap) where cheap reached identical conclusions
            if tier == CHEAP and v_same and b_same:
                waste_records.append(oid)
                waste_credits += ref[oid]["credits"]

            model_runs.append({"run_id": f"{arm_label(t)}|{oid}", "opp_id": oid,
                               "policy": "adaptive", "threshold": t,
                               "tier": tier, "model": TIER_MODEL[tier],
                               **{k: c[k] for k in ANSWER_FIELDS}})
            policy_decisions.append({
                "opp_id": oid, "policy": "adaptive", "threshold": t,
                "complexity_score": complexity_score(r),
                "probability": r["probability"],
                "strategic_account": r["strategic_account"],
                "tier": tier, "reason": reason,
                "evidence": json.dumps(evidence),
                "changed_vs_reference": oid in changed,
            })

        total = sum(tier_credits.values())
        summaries.append({
            "policy": "adaptive", "threshold": t, "total_credits": total,
            "total_dollars": total * DOLLARS_PER_CREDIT,
            "cheap_n": counts[CHEAP], "balanced_n": counts[BALANCED],
            "premium_n": counts[PREMIUM],
            "pct_cheap": round(100 * counts[CHEAP] / 30, 1),
            "cheap_credits": tier_credits[CHEAP],
            "balanced_credits": tier_credits[BALANCED],
            "premium_credits": tier_credits[PREMIUM],
            "decisions_changed": len(changed),
            "verdict_agreement_pct": round(100 * verdict_agree / 30, 1),
            "blocker_agreement_pct": round(100 * blocker_agree / 30, 1),
            "waste_records": ";".join(waste_records), "waste_count": len(waste_records),
            "waste_credits": waste_credits,
            "waste_dollars": waste_credits * DOLLARS_PER_CREDIT,
            "cost_vs_reference_pct": round(100 * total / ref_credits, 1),
        })
        print(f"t={t}: changed={len(changed)} {sorted(changed)}")

    heroes = []
    for oid, kind in HEROES.items():
        row = {"opp_id": oid, "kind": kind, "name": recs[oid]["name"],
               "amount": recs[oid]["amount"], "probability": recs[oid]["probability"],
               "complexity_score": complexity_score(recs[oid])}
        for tier in (CHEAP, PREMIUM):
            c = call(oid, tier)
            for f in ("verdict", "primary_blocker", "next_best_action", "reasoning"):
                row[f"{tier}_{f}"] = c[f]
        tier, reason, evidence = route(recs[oid], high_confidence_threshold=0.98)
        row.update(routed_tier=tier, routed_reason=reason, routed_evidence=json.dumps(evidence))
        heroes.append(row)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    for fname, rows in (("model_runs.csv", model_runs),
                        ("policy_decisions.csv", policy_decisions),
                        ("run_summary.csv", summaries),
                        ("heroes.csv", heroes)):
        with open(os.path.join(RESULTS_DIR, fname), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {fname} ({len(rows)} rows)")
    write_csv(os.path.join(RESULTS_DIR, "opportunities.csv"))

    print(f"\nreference arm: {ref_credits:.6f} credits (${ref_credits * DOLLARS_PER_CREDIT:.4f})")
    for s in summaries[1:]:
        print(f"adaptive@{s['threshold']}: {s['total_credits']:.6f} credits "
              f"(${s['total_dollars']:.4f}) = {s['cost_vs_reference_pct']}% of reference | "
              f"changed {s['decisions_changed']} | verdict {s['verdict_agreement_pct']}% | "
              f"blocker {s['blocker_agreement_pct']}% | cheap {s['pct_cheap']}% | "
              f"waste {s['waste_count']} recs {s['waste_credits']:.6f} cr")


if __name__ == "__main__":
    main()
