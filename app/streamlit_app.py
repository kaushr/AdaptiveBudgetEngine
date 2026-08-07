"""Decision Budget Engine — single-screen demo (workbook T12/T18).

Reads ONLY from the results tables. Offline fallback (default): the CSVs in
data/results/ — zero live calls, zero Snowflake dependency. Set
DBE_SOURCE=snowflake (or [dbe] source="snowflake" in st.secrets) to read the
same tables from DECISION_BUDGET.DEMO; the dataframe code downstream is
identical either way.

Every number displayed comes from RUN_SUMMARY / MODEL_RUNS / POLICY_DECISIONS /
HEROES. Nothing is computed from model output here, nothing is invented.
"""

import json
import os

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Decision Budget Engine", layout="wide")

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
TABLES = ("run_summary", "model_runs", "policy_decisions", "heroes", "opportunities")


def _source():
    if os.environ.get("DBE_SOURCE"):
        return os.environ["DBE_SOURCE"]
    try:
        return st.secrets["dbe"]["source"]
    except Exception:
        return "local"


@st.cache_data
def load_tables(source):
    if source == "snowflake":
        conn = st.connection("snowflake")
        return {t: conn.query(f"SELECT * FROM {t.upper()}", ttl=600).rename(
            columns=str.lower) for t in TABLES}
    return {t: pd.read_csv(os.path.join(RESULTS_DIR, f"{t}.csv"))
            for t in TABLES}


data = load_tables(_source())
summary = data["run_summary"]
runs = data["model_runs"]
decisions = data["policy_decisions"]
heroes = data["heroes"]

ref = summary[summary.policy == "reference"].iloc[0]

st.title("Decision Budget Engine")
st.caption(
    "Workload-level model selection picks the best model for the task. "
    "This decides how much reasoning each record within the task deserves. "
    f"Source: {'Snowflake' if _source() == 'snowflake' else 'results table (offline fallback)'} · "
    "30 opportunities · two arms, measured."
)

# ---- Beat 1: the bill (filled after the slider sets the operating point) ----
beat1 = st.container()

st.divider()

# ---- Beat 2: the slider --------------------------------------------------
st.subheader("How settled must a deal be before we stop paying for reasoning?")
threshold = st.select_slider(
    label="High-confidence threshold — three measured operating points",
    options=[0.98, 0.95, 0.90],
    value=0.98,
    format_func=lambda v: {0.98: "0.98 · Conservative", 0.95: "0.95 · Balanced",
                           0.90: "0.90 · Savings-oriented"}[v],
)
row = summary[(summary.policy == "adaptive")
              & (summary.threshold.astype(float) == threshold)].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cost vs reference", f"{row.cost_vs_reference_pct:.0f}%")
with c2:
    st.markdown(
        f"<div style='background:#1a3d5c;border-radius:8px;padding:10px 14px;text-align:center'>"
        f"<div style='font-size:0.8rem;color:#cfe3f5'>Decisions changed</div>"
        f"<div style='font-size:2.4rem;font-weight:700;color:#fff'>{int(row.decisions_changed)} of 30</div>"
        f"</div>", unsafe_allow_html=True)
c3.metric("Verdict agreement", f"{row.verdict_agreement_pct:.0f}%")
c4.metric("Routed cheap", f"{row.pct_cheap:.0f}%")
st.caption(f"Blocker agreement: {row.blocker_agreement_pct:.0f}%. "
           "A decision changed when the two arms reach different conclusions "
           "(verdict or primary blocker) — scored by exact match, no judge model.")

# Frontier table — the visualization (three measured points + the endpoint)
frontier = summary.copy()
frontier["operating point"] = frontier.apply(
    lambda r: "Reference (1.00 — nothing is ever settled)" if r.policy == "reference"
    else f"{float(r.threshold):.2f}", axis=1)
frontier_view = frontier[["operating point", "pct_cheap", "total_dollars",
                          "decisions_changed", "verdict_agreement_pct"]].rename(columns={
    "pct_cheap": "% routed cheap", "total_dollars": "total cost ($)",
    "decisions_changed": "decisions changed", "verdict_agreement_pct": "verdict agreement (%)"})
frontier_view["total cost ($)"] = frontier_view["total cost ($)"].map(lambda v: f"{v:.4f}")
st.dataframe(frontier_view, hide_index=True, width='stretch')

# Pinned record: the certainty veto overriding high complexity
pin = decisions[decisions.opp_id == "OPP-008"].sort_values("threshold", ascending=False)
pin_tiers = " → ".join(pin.tier.tolist())
pin_now = pin[pin.threshold.astype(float) == threshold].iloc[0]
opp8 = data["opportunities"].set_index("opp_id").loc["OPP-008"]
st.info(
    f"**OPP-008 — {opp8['name']}** · ${opp8.amount / 1e6:.1f}M · p=0.93 · complexity 4  \n"
    f"Across the three thresholds its tier goes **{pin_tiers}** — at {threshold:.2f} it gets "
    f"**{pin_now.tier}**. Probable and messy at the same time: certainty vetoes spend once "
    f"the bar loosens, no matter how complex the record looks. Deal size never enters the rule."
)

# ---- Beat 1 content (needs the slider's operating point) -------------------
with beat1:
    b1, b2 = st.columns(2)
    with b1:
        st.metric("Reference policy — every record to the premium model",
                  f"${ref.total_dollars:.4f}",
                  help=f"{ref.total_credits:.6f} credits · 30 premium calls")
        st.caption(f"Adaptive at {threshold:.2f} decomposes: "
                   f"cheap ${row.cheap_credits * 3:.4f} · balanced ${row.balanced_credits * 3:.4f} · "
                   f"premium ${row.premium_credits * 3:.4f}")
        st.caption(f"At 10,000 records/week: **${ref.projected_10k_weekly_dollars:.2f} → "
                   f"${row.projected_10k_weekly_dollars:.2f}** "
                   f"(projected from measured per-record cost)")
    with b2:
        st.markdown(
            f"<div style='background:#7a5200;border-radius:8px;padding:14px'>"
            f"<div style='font-size:0.85rem;color:#ffe9b8'>Spent on decisions that were already made</div>"
            f"<div style='font-size:1.8rem;font-weight:700;color:#fff'>${row.waste_dollars:.4f} "
            f"on {int(row.waste_count)} records</div>"
            f"<div style='font-size:0.8rem;color:#ffe9b8'>Records the policy routed cheap where the "
            f"cheap tier reached identical conclusions to premium ({row.waste_records.replace(';', ', ')})</div>"
            f"</div>", unsafe_allow_html=True)

st.divider()

# ---- Beat 3: hero comparison ----------------------------------------------
st.subheader("Same workload, different business context, different reasoning budget")
kind = st.radio("Hero record", ["settled", "contestable", "complex"],
                horizontal=True, label_visibility="collapsed")
h = heroes[heroes.kind == kind].iloc[0]

st.markdown(f"**{h['opp_id']} — {h['name']}** · ${h.amount / 1e6:.2f}M · "
            f"p={h.probability} · complexity {h.complexity_score}")
colc, colp = st.columns(2)
for col, tier_key, title in ((colc, "cheap", "cheap · llama3.1-8b"),
                             (colp, "premium", "premium · claude-sonnet-4-5")):
    with col:
        st.markdown(f"##### {title}")
        st.markdown(f"`{h[f'{tier_key}_verdict']}` · `{h[f'{tier_key}_primary_blocker']}`")
        st.markdown(f"### {h[f'{tier_key}_next_best_action']}")
        st.caption(h[f"{tier_key}_reasoning"])

evidence = json.loads(h.routed_evidence)
st.success(
    f"**Routing decision:** tier **{h.routed_tier}** — {h.routed_reason}.  \n"
    f"Evidence: {', '.join(f'{k}={v}' for k, v in evidence.items())}"
)

# ---- Q&A armor (not part of the demo flow) ---------------------------------
with st.expander("All 30 records"):
    adaptive = runs[(runs.policy == "adaptive")
                    & (runs.threshold.astype(float) == threshold)]
    reference = runs[runs.policy == "reference"]
    dec = decisions[decisions.threshold.astype(float) == threshold]
    opps = data["opportunities"]
    table = (opps[["opp_id", "amount", "probability"]]
             .merge(dec[["opp_id", "complexity_score", "tier", "changed_vs_reference",
                         "consequential"]], on="opp_id")
             .merge(reference[["opp_id", "verdict", "primary_blocker"]]
                    .rename(columns={"verdict": "ref_verdict", "primary_blocker": "ref_blocker"}), on="opp_id")
             .merge(adaptive[["opp_id", "verdict", "primary_blocker"]]
                    .rename(columns={"verdict": "adaptive_verdict", "primary_blocker": "adaptive_blocker"}), on="opp_id")
             .rename(columns={"changed_vs_reference": "changed"})
             .sort_values(["changed", "opp_id"], ascending=[False, True]))
    st.dataframe(table, hide_index=True, width='stretch')

with st.expander("Usage detail"):
    # Token-economy accounting per model. MODEL_RUNS repeats shared calls
    # across arms (a record premium in both arms was one physical call) —
    # dedupe on (opp_id, tier) so tokens bought once are counted once.
    arms = pd.concat([
        runs[runs.policy == "reference"],
        runs[(runs.policy == "adaptive") & (runs.threshold.astype(float) == threshold)],
    ]).drop_duplicates(subset=["opp_id", "tier"])
    usage = (arms.groupby("model", as_index=False)
             .agg(calls=("opp_id", "count"), input_tokens=("input_tokens", "sum"),
                  output_tokens=("output_tokens", "sum"), credits=("credits", "sum")))
    usage["cost ($)"] = (usage.credits * 3.00).map(lambda v: f"{v:.4f}")
    usage["credits"] = usage.credits.map(lambda v: f"{v:.6f}")
    st.dataframe(usage, hide_index=True, width='stretch')
    st.caption("Unique model calls behind the reference arm and the adaptive arm at the "
               "selected threshold — a record premium in both arms is one call, counted once. "
               "Raw measured values from MODEL_RUNS; reconcilable against Snowflake's "
               "CORTEX_FUNCTIONS_USAGE_HISTORY (same ledger).")

with st.expander("The policy"):
    st.code(
        f"if probability >= {threshold:.2f}:   # settled — certainty vetoes spend\n"
        f"    return CHEAP\n"
        f"if probability <= 0.10:   # already lost\n"
        f"    return CHEAP\n"
        f"if decision_complexity_score >= 4:\n"
        f"    return PREMIUM\n"
        f"if strategic_account:     # floor, never a bypass\n"
        f"    return BALANCED\n"
        f"return BALANCED",
        language="python")
    st.caption("This is the entire runtime policy. Moving the slider rewrites the first "
               "line — everything else is held constant, so any difference in the numbers "
               "above is attributable to that one threshold.")

st.caption("Methodology: the premium arm is a reference implementation, not truth. "
           "Conclusions are scored by exact match on fixed enums between arms; where they "
           "differ we say the decision **changed** — measured, not asserted. "
           "In production, arms would be evaluated against expert labels and business outcomes.")
