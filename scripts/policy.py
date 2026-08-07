"""Adaptive Business Policy (workbook section 3) + dry-run harness (section 6).

Pure arithmetic -- zero model calls. Run before any AI_COMPLETE spend to
confirm the three high-confidence thresholds produce distinct routing.

Policy order is the product philosophy: certainty vetoes spend, complexity
escalates, strategic importance sets a floor but never bypasses certainty.
Deal size appears nowhere.
"""

from dataset import OPPORTUNITIES, complexity_score

CHEAP, BALANCED, PREMIUM = "cheap", "balanced", "premium"

LOW_CONFIDENCE_THRESHOLD = 0.10   # held constant
COMPLEXITY_THRESHOLD = 4          # held constant (4+ = high per workbook)


def route(record, high_confidence_threshold,
          low_confidence_threshold=LOW_CONFIDENCE_THRESHOLD,
          complexity_threshold=COMPLEXITY_THRESHOLD):
    """Returns (tier, reason, evidence) -- every decision is explainable."""
    p = record["probability"]
    score = complexity_score(record)
    thresholds = {
        "high_confidence_threshold": high_confidence_threshold,
        "low_confidence_threshold": low_confidence_threshold,
        "complexity_threshold": complexity_threshold,
    }

    if p >= high_confidence_threshold:
        return CHEAP, "settled: probability at or above high-confidence threshold", {
            "probability": p, **thresholds}
    if p <= low_confidence_threshold:
        return CHEAP, "already lost: probability at or below low-confidence threshold", {
            "probability": p, **thresholds}
    if score >= complexity_threshold:
        return PREMIUM, "high decision complexity: unresolved evidence to synthesize", {
            "complexity_score": score, **thresholds}
    if record["strategic_account"]:
        return BALANCED, "strategic account floor (floor, never a bypass)", {
            "strategic_account": True, "complexity_score": score, **thresholds}
    return BALANCED, "default tier: contested but not high-complexity", {
        "complexity_score": score, **thresholds}


def dry_run(thresholds=(0.98, 0.95, 0.90)):
    """Frontier dry-run: tier distribution per threshold. Reference Policy is
    the same curve at threshold 1.00 -- shown as the endpoint, not a baseline."""
    rows = []
    for t in list(thresholds) + [1.00]:
        counts = {CHEAP: 0, BALANCED: 0, PREMIUM: 0}
        routing = {}
        for r in OPPORTUNITIES:
            if t == 1.00:  # Reference Policy: every record -> premium, no exceptions
                tier = PREMIUM
            else:
                tier, _, _ = route(r, high_confidence_threshold=t)
            counts[tier] += 1
            routing[r["opp_id"]] = tier
        rows.append({"threshold": t, "counts": counts, "routing": routing})
    return rows


if __name__ == "__main__":
    rows = dry_run()
    adaptive = [r for r in rows if r["threshold"] != 1.00]

    print(f"{'threshold':>10} {'cheap':>6} {'balanced':>9} {'premium':>8} {'% cheap':>8}")
    for row in rows:
        c = row["counts"]
        label = f"{row['threshold']:.2f}" if row["threshold"] != 1.00 else "1.00*"
        print(f"{label:>10} {c[CHEAP]:>6} {c[BALANCED]:>9} {c[PREMIUM]:>8} "
              f"{100 * c[CHEAP] // 30:>7}%")
    print("* Reference Policy endpoint (nothing ever settled enough to spend less on)")

    # Collapse check (workbook section 6): distributions must be distinct
    signatures = [tuple(sorted(r["routing"].items())) for r in adaptive]
    if len(set(signatures)) != len(signatures):
        raise SystemExit("FAIL: thresholds produced identical routing -- fix record probabilities")
    print("\nPASS: all three thresholds produce distinct routing")

    # Per-record movement across the frontier (the records that make it move)
    print("\nRecords whose tier changes across thresholds:")
    for opp_id in sorted(adaptive[0]["routing"]):
        tiers = [r["routing"][opp_id] for r in adaptive]
        if len(set(tiers)) > 1:
            prob = next(r["probability"] for r in OPPORTUNITIES if r["opp_id"] == opp_id)
            print(f"  {opp_id} (p={prob:.2f}): " + " -> ".join(tiers))

    # Hero sanity (T2 intended routing at the 0.98 operating point)
    t98 = adaptive[0]["routing"]
    assert t98["OPP-001"] == CHEAP, "settled hero must route cheap"
    assert t98["OPP-002"] == PREMIUM, "complex hero must route premium"
    assert t98["OPP-003"] == BALANCED, "contestable hero must route balanced"
    print("\nHero routing at 0.98: OPP-001 cheap / OPP-002 premium / OPP-003 balanced -- as designed")
