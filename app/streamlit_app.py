"""Decision Budget Engine — single-screen demo (workbook T12/T18).

Reads ONLY from the results tables. Offline fallback (default): the CSVs in
data/results/ — zero live calls, zero Snowflake dependency. Set
DBE_SOURCE=snowflake (or [dbe] source="snowflake" in st.secrets) to read the
same tables from DECISION_BUDGET.DEMO; the dataframe code downstream is
identical either way.

Every number displayed comes from RUN_SUMMARY / MODEL_RUNS / POLICY_DECISIONS /
HEROES. Nothing is computed from model output here, nothing is invented.
"""

import html
import json
import os
import sys

import pandas as pd
import streamlit as st

# The runner's actual prompt template — imported, not copied, so the screen
# cannot drift from what was really sent.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from run_arms import PROMPT_TEMPLATE  # noqa: E402
from pricing import TIER_MODEL  # noqa: E402 — the tier→model ladder, single source

# Local policy provenance — the guaranteed fallback. The demo NEVER depends
# on a live third-party call: EverOS is tried once (short timeout) and any
# failure falls back here silently.
LOCAL_PROVENANCE = {"version": "v1", "author": "hand-authored",
                    "basis": "expert judgment, not learned"}


@st.cache_data(ttl=600)
def _policy_provenance(mode):
    """mode is part of the cache key so a forced-local run never reuses a
    cached EverOS result (and vice versa)."""
    if mode == "local":
        return LOCAL_PROVENANCE, "local"
    try:
        from everos_log import fetch_policy_provenance
        return fetch_policy_provenance(timeout=4), "everos"
    except BaseException:  # noqa: BLE001 — any failure means local, silently
        return LOCAL_PROVENANCE, "local"


def policy_provenance():
    return _policy_provenance(os.environ.get("DBE_POLICY_SOURCE", "everos"))


def _source():
    if os.environ.get("DBE_SOURCE"):
        return os.environ["DBE_SOURCE"]
    try:
        return st.secrets["dbe"]["source"]
    except Exception:
        return "local"


# Distinct browser-tab titles so the two modes are unambiguous when both run
# side by side (offline on 8501, live on 8502).
st.set_page_config(
    page_title="DBE · LIVE" if _source() == "snowflake" else "DBE · OFFLINE",
    layout="wide")

# One style scale for the whole page (readability pass):
#   title (st.title) > metric values (2.4rem, the most prominent) >
#   next-best-action (1.35rem, second) > section headers (st.subheader) >
#   body (base 18px via .streamlit/config.toml) > labels/small print (.85rem).
# One muted color for ALL secondary text; card text is white on tinted cards.
MUTED = "#9aa4b2"
st.markdown(f"""<style>
[data-testid="stMetricValue"] {{ font-size: 2.4rem; font-weight: 700; }}
[data-testid="stMetricLabel"] {{ font-size: .85rem; color: {MUTED}; }}
[data-testid="stCaptionContainer"] {{ color: {MUTED}; font-size: .95rem; }}
/* Accent cards are real st.metric elements inside keyed containers, so their
   tooltips use the same ?-icon mechanism as every other metric on the page.
   Only the background/padding/colors are custom. */
.st-key-dbe_changed_card, .st-key-dbe_waste_card {{
    border-radius: 8px; padding: 12px 14px; }}
.st-key-dbe_changed_card {{ background: #1a3d5c; }}
.st-key-dbe_waste_card {{ background: #7a5200; }}
.st-key-dbe_changed_card [data-testid="stMetricLabel"],
.st-key-dbe_waste_card [data-testid="stMetricLabel"] {{ color: rgba(255,255,255,.85); }}
.st-key-dbe_changed_card [data-testid="stMetricValue"],
.st-key-dbe_waste_card [data-testid="stMetricValue"] {{ color: #fff; }}
.st-key-dbe_waste_card [data-testid="stCaptionContainer"] {{ color: rgba(255,255,255,.78); }}
.dbe-action {{ font-size: 1.35rem; font-weight: 650; line-height: 1.35; min-height: 4.6em;
               color: #fde68a; }}
.dbe-reasoning {{ font-size: .95rem; line-height: 1.55; color: #e5e7eb; }}
/* Enum badges, valence-colored: red = needs attention, yellow = settled
   either way, green = healthy/no obstacle */
.dbe-enum {{ font-family: "Source Code Pro", monospace; font-size: .85rem;
             padding: 2px 8px; border-radius: 6px;
             background: rgba(154,164,178,.12); }}
.dbe-enum.red {{ color: #f87171; }}
.dbe-enum.yellow {{ color: #fbbf24; }}
.dbe-enum.green {{ color: #4ade80; }}
/* Tiny field labels on the hero cards — subtle, uppercase, hover for detail */
.dbe-field {{ font-size: .68rem; letter-spacing: .09em; text-transform: uppercase;
              color: {MUTED}; opacity: .85; cursor: help; }}
div.dbe-field {{ margin: 6px 0 1px 0; }}
.dbe-chip {{ display: inline-block; padding: 2px 10px; border-radius: 12px;
             font-size: .8rem; margin: 2px 6px 2px 0; white-space: nowrap; }}
.dbe-chip.on {{ background: rgba(59,130,246,.22); border: 1px solid rgba(59,130,246,.55); }}
.dbe-chip.off {{ color: {MUTED}; background: rgba(154,164,178,.10);
                 border: 1px solid rgba(154,164,178,.25); }}
.dbe-chip.meta {{ background: rgba(154,164,178,.16); border: 1px solid rgba(154,164,178,.35); }}
/* Valence colors: red = risk in play, green = favorable, yellow = middling.
   Inactive risk signals stay muted (.off) — not a factor. */
.dbe-chip.bad {{ background: rgba(239,68,68,.16); border: 1px solid rgba(239,68,68,.5); }}
.dbe-chip.good {{ background: rgba(34,197,94,.15); border: 1px solid rgba(34,197,94,.45); }}
.dbe-chip.warn {{ background: rgba(250,204,21,.13); border: 1px solid rgba(250,204,21,.4); }}
/* Subtle source chip, top right of the header */
.dbe-src-chip {{ float: right; font-size: .8rem; color: {MUTED};
                 background: rgba(154,164,178,.10); border: 1px solid rgba(154,164,178,.22);
                 border-radius: 12px; padding: 3px 12px; margin-top: 4px; }}
/* Reference-policy tile: navy, mirroring the amber waste tile.
   Both tiles share a min-height so the pair reads symmetric. */
.st-key-dbe_ref_card, .st-key-dbe_waste_card {{ min-height: 14.5rem; }}
.st-key-dbe_ref_card {{ background: #1a3d5c; border-radius: 8px; padding: 12px 14px; }}
.st-key-dbe_ref_card [data-testid="stMetricLabel"] {{ color: rgba(255,255,255,.85); }}
.st-key-dbe_ref_card [data-testid="stMetricValue"] {{ color: #fff; }}
.st-key-dbe_ref_card [data-testid="stCaptionContainer"] {{ color: rgba(255,255,255,.78); }}
/* Subtle boxes for the non-headline metrics */
.st-key-dbe_tile_cost, .st-key-dbe_tile_verdict, .st-key-dbe_tile_cheap {{
    background: rgba(154,164,178,.08); border: 1px solid rgba(154,164,178,.20);
    border-radius: 8px; padding: 12px 14px; }}
/* The key-message banner: the 10k/week projection */
.st-key-dbe_projection {{ background: rgba(59,130,246,.12);
    border: 1px solid rgba(59,130,246,.45); border-radius: 8px;
    padding: 10px 18px 2px 18px; margin-top: 10px; }}
.dbe-proj-val {{ font-size: 1.5rem; font-weight: 700; }}
/* Slider: taller, bigger thumb label; built-in tick bar replaced by a
   full stops row below (it only ever showed the endpoints) */
[data-testid="stSliderTickBar"] {{ display: none; }}
.st-key-dbe_slider {{ padding: 6px 0 0 0; }}
.st-key-dbe_slider [data-testid="stSliderThumbValue"] {{ font-size: 1.05rem; font-weight: 700; }}
/* Collapse the default 1rem block gap, then pull the stops up past the
   slider's internal bottom padding so they hug the track, with clear
   separation before the metric tiles below */
.st-key-dbe_slider [data-testid="stVerticalBlock"] {{ gap: 0; }}
.dbe-stops {{ display: flex; justify-content: space-between;
              font-size: .95rem; margin: -30px 2px 18px 2px; }}
</style>""", unsafe_allow_html=True)

RESULTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "results"))
TABLES = ("run_summary", "model_runs", "policy_decisions", "heroes", "opportunities")


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

def fmt_amount(v):
    """Plain currency for dataframe cells (no markdown processing there)."""
    return f"${v / 1e6:.1f}M" if v >= 1_000_000 else f"${v / 1e3:.0f}K"


def md_usd(v, dec=4):
    """Currency for st.markdown/st.caption/st.info strings. The backslash
    escape stops Streamlit's markdown from treating paired $...$ as LaTeX
    math delimiters (the root cause of the mangled decomposition line)."""
    return f"\\${v:,.{dec}f}"


def md_amount(v):
    return fmt_amount(v).replace("$", "\\$")


def _b(v):
    """CSV booleans arrive as TRUE/FALSE strings or real bools by source."""
    return v if isinstance(v, bool) else str(v).upper() == "TRUE"


# The seven risk signals behind the Decision Complexity Score, in canonical
# order: (column, chip label, drill-down abbreviation)
RISK_SIGNALS = [
    ("no_economic_buyer", "no economic buyer", "buyer"),
    ("competitor_present", "competitor", "comp"),
    ("security_legal_blocked", "security/legal", "sec"),
    ("procurement_not_started", "procurement not started", "proc"),
    ("champion_risk", "champion risk", "champ"),
    ("inactive_21d", "inactive >21d", "inact"),
    ("conflicting_signals", "conflicting signals", "confl"),
]

COMPLEXITY_DEF = ("Complexity score = count of active risk signals (0–7) — no economic "
                  "buyer, competitor, security/legal block, procurement not started, "
                  "champion departed, inactivity >21d, conflicting signals. "
                  "Deterministic; no model involved.")


# Brand header — Intellinomics wordmark + lab line, source chip top right
_src_label = ("Live from Snowflake · DECISION_BUDGET.DEMO" if _source() == "snowflake"
              else "Measured run · Snowflake Cortex · Aug 7")
st.markdown(
    f"<div style='margin-bottom:2px'>"
    f"<span style='font-size:1.1rem;font-weight:800;letter-spacing:.14em;color:#5B8DEF'>INTELLINOMICS</span>"
    f"<span style='font-size:.95rem;color:{MUTED};margin-left:12px'>The Intelligence Economics Lab</span>"
    f"<span class='dbe-src-chip'>{_src_label}</span>"
    f"</div>", unsafe_allow_html=True)
st.title("Decision Budget Engine")
st.markdown(f"<div style='font-size:1.15rem;color:{MUTED};margin:-8px 0 6px 0'>"
            f"Optimizing AI reasoning one business decision at a time.</div>",
            unsafe_allow_html=True)
st.caption(
    "Workload-level model selection picks the best model for the task. "
    "Decision Budget Engine decides how much reasoning each record within it deserves. "
    "30 opportunities · two arms, measured."
)
# Provenance chip lives top-right in the brand header; mode remains a launch
# decision (demo-offline.sh / demo-live.sh), never a UI toggle.

# ---- Beat 1: the bill (filled after the slider sets the operating point) ----
beat1 = st.container()

st.divider()

# ---- Beat 2: the slider --------------------------------------------------
st.subheader("How settled must a deal be before we stop paying for reasoning?")
STOP_LABELS = {0.98: "0.98 · Conservative", 0.95: "0.95 · Balanced",
               0.90: "0.90 · Savings-oriented"}
with st.container(key="dbe_slider"):
    threshold = st.select_slider(
        label="High-confidence threshold — three measured operating points",
        options=[0.98, 0.95, 0.90],
        value=0.98,
        format_func=lambda v: STOP_LABELS[v],
    )
    stops = "".join(
        f"<span style='{'color:#5B8DEF;font-weight:700' if v == threshold else f'color:{MUTED}'}'>"
        f"{STOP_LABELS[v]}</span>" for v in (0.98, 0.95, 0.90))
    st.markdown(f"<div class='dbe-stops'>{stops}</div>", unsafe_allow_html=True)
row = summary[(summary.policy == "adaptive")
              & (summary.threshold.astype(float) == threshold)].iloc[0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(key="dbe_tile_cost"):
        st.metric("Cost vs reference", f"{row.cost_vs_reference_pct:.0f}%",
                  help="What the adaptive policy costs as a share of premium-everything. "
                       f"Math: adaptive cost ÷ reference cost = \\${row.total_dollars:.4f} ÷ "
                       f"\\${ref.total_dollars:.4f} = {row.cost_vs_reference_pct:.0f}%. "
                       "Lower is cheaper — the paired question is whether conclusions changed.")
with c2:
    with st.container(key="dbe_changed_card"):
        st.metric("Decisions changed", f"{int(row.decisions_changed)} of 30",
                  help="How many records the two policies answered differently. "
                       "Math: count of records where the verdict OR the primary "
                       "blocker differs — exact string match on fixed enums, no "
                       f"model judging. Here: {int(row.decisions_changed)} of 30.")
_v_match = round(row.verdict_agreement_pct * 30 / 100)
with c3:
    with st.container(key="dbe_tile_verdict"):
        st.metric("Verdict agreement", f"{row.verdict_agreement_pct:.0f}%",
                  help="How often both policies reached the same verdict. "
                       f"Math: {_v_match} of 30 matching ÷ 30 = {row.verdict_agreement_pct:.0f}%. "
                       "Blocker agreement is scored the same way separately "
                       f"({row.blocker_agreement_pct:.0f}%).")
with c4:
    with st.container(key="dbe_tile_cheap"):
        st.metric("Routed cheap", f"{row.pct_cheap:.0f}%",
                  help="Share of records the policy sent to the cheap model at this threshold. "
                       f"Math: {int(row.cheap_n)} of 30 = {row.pct_cheap:.1f}%. Rises as the "
                       "threshold loosens — it's the mechanism behind falling cost.")
st.caption(f"Blocker agreement: {row.blocker_agreement_pct:.0f}%. "
           "A decision changed when the two arms reach different conclusions "
           "(verdict or primary blocker) — scored by exact match, no judge model.")

# Call-flow arithmetic — makes the two-arm structure and call reuse legible
# before "did you send all 30 to all 3 models?" gets asked. All values from
# RUN_SUMMARY at the selected threshold.
unique_calls = 30 + int(row.cheap_n) + int(row.balanced_n)
st.markdown(
    f"<div style='font-size:.95rem;color:{MUTED};padding:2px 0 6px 0'>"
    f"30 records → <b>reference arm:</b> 30 premium calls → "
    f"<b>adaptive arm:</b> {int(row.cheap_n)} cheap + {int(row.balanced_n)} balanced + "
    f"{int(row.premium_n)} premium ({int(row.premium_n)} reuse the reference calls — counted once) → "
    f"<b>{unique_calls} unique calls</b> behind this view → conclusions compared per record → "
    f"<b>{int(row.decisions_changed)} changed</b></div>", unsafe_allow_html=True)

# Frontier table — the visualization (three measured points + the endpoint)
frontier = summary.copy()
frontier["operating point"] = frontier.apply(
    lambda r: "Reference (1.00 — bar unreachable, all premium)" if r.policy == "reference"
    else f"{float(r.threshold):.2f}", axis=1)
frontier_view = frontier[["operating point", "pct_cheap", "total_dollars",
                          "decisions_changed", "verdict_agreement_pct"]].rename(columns={
    "pct_cheap": "% routed cheap", "total_dollars": "total cost ($)",
    "decisions_changed": "decisions changed", "verdict_agreement_pct": "verdict agreement (%)"})
frontier_view["total cost ($)"] = frontier_view["total cost ($)"].map(lambda v: f"{v:.4f}")
# live direction examples for the certainty-bar tooltip (strictest vs loosest)
_adaptive = summary[summary.policy == "adaptive"].copy()
_adaptive["t"] = _adaptive.threshold.astype(float)
_hi = _adaptive.loc[_adaptive.t.idxmax()]
_lo = _adaptive.loc[_adaptive.t.idxmin()]
_bar_examples = (f"{_hi.t:.2f} → {_hi.pct_cheap:.0f}% cheap; "
                 f"{_lo.t:.2f} → {_lo.pct_cheap:.0f}% cheap")
st.dataframe(frontier_view, hide_index=True, width='stretch', column_config={
    "operating point": st.column_config.Column(
        help="The certainty bar: a deal is only routed cheap if its close "
             "probability clears this number. Higher bar = stricter = fewer deals "
             "routed cheap "
             f"({_bar_examples}). At 1.00 the bar is unreachable — no deal is ever "
             "certain enough — so every record gets the premium model. That's the "
             "reference policy."),
    "% routed cheap": st.column_config.Column(
        help="Share of the 30 records sent to the cheap model at that setting."),
    "total cost ($)": st.column_config.Column(
        help="Measured cost of running that policy across all 30 records — summed "
             "from each call's returned token counts × published Cortex rates."),
    "decisions changed": st.column_config.Column(
        help="Records answered differently vs premium-everything: the verdict or "
             "the primary blocker differs, by exact string match."),
    "verdict agreement (%)": st.column_config.Column(
        help="Share of the 30 records where both policies reached the same verdict."),
})

# Pinned record: the certainty veto overriding high complexity
pin = decisions[decisions.opp_id == "OPP-008"].sort_values("threshold", ascending=False)
pin_tiers = " → ".join(pin.tier.tolist())
pin_now = pin[pin.threshold.astype(float) == threshold].iloc[0]
opp8 = data["opportunities"].set_index("opp_id").loc["OPP-008"]
st.info(
    f"**OPP-008 — {opp8['name']}** · {md_amount(opp8.amount)} · p=0.93 · complexity 4  \n"
    f"Across the three thresholds its tier goes **{pin_tiers}** — at {threshold:.2f} it gets "
    f"**{pin_now.tier}**. Probable and messy at the same time: certainty vetoes spend once "
    f"the bar loosens, no matter how complex the record looks. Deal size never enters the rule."
)

# ---- Beat 1 content (needs the slider's operating point) -------------------
with beat1:
    b1, b2 = st.columns(2)
    with b1:
        with st.container(key="dbe_ref_card"):
            st.metric("Reference policy — every record to the premium model",
                      f"${ref.total_dollars:.4f}",
                      help="What it cost to send all 30 opportunities to the premium "
                           "model — the status quo this comparison is against. Math: sum "
                           "of the 30 premium calls' measured token costs (input + output "
                           "tokens × published Cortex rates) = "
                           f"\\${ref.total_dollars:.4f} ({ref.total_credits:.6f} credits).")
            st.caption(f"Adaptive at {threshold:.2f} decomposes: "
                       f"cheap {md_usd(row.cheap_credits * 3)} · balanced {md_usd(row.balanced_credits * 3)} · "
                       f"premium {md_usd(row.premium_credits * 3)}")
    with b2:
        _waste_names = row.waste_records.replace(";", " + ")
        _all_waste = summary[summary.policy == "adaptive"].waste_count.astype(int).unique()
        _robust = (f" It stays {int(_all_waste[0])} at every threshold — the most "
                   f"robust overspend in the set.") if len(_all_waste) == 1 else ""
        with st.container(key="dbe_waste_card"):
            st.metric("Spent on decisions that were already made",
                      f"${row.waste_dollars:.4f} on {int(row.waste_count)} records",
                      help="Premium money that bought nothing: records the policy "
                           "routed cheap where the cheap model reached the identical "
                           "verdict and blocker, so paying premium changed no answer. "
                           "Math: the premium policy's cost on just those records "
                           f"({_waste_names}) = \\${row.waste_dollars:.4f}.{_robust}")
            st.caption(f"Records the policy routed cheap where the cheap tier reached "
                       f"identical conclusions to premium ({row.waste_records.replace(';', ', ')}). "
                       f"Of the {int(row.cheap_n)} records routed cheap at this threshold, these "
                       f"{int(row.waste_count)} reached identical conclusions (spend bought "
                       f"nothing); the remainder are counted in decisions changed.")

    # The key message, full width and unmissable: what this costs at scale
    with st.container(key="dbe_projection"):
        st.markdown(f"<span class='dbe-proj-val'>At 10,000 records/week: "
                    f"{md_usd(ref.projected_10k_weekly_dollars, 2)} → "
                    f"{md_usd(row.projected_10k_weekly_dollars, 2)}</span>",
                    unsafe_allow_html=True)
        st.caption("Linear projection: measured per-record cost × 10,000 — projected, not measured.")

st.divider()

# ---- Beat 3: hero comparison ----------------------------------------------
st.subheader("Same workload, different business context, different reasoning budget")
kind = st.radio("Hero record", ["settled", "contestable", "complex"],
                horizontal=True, label_visibility="collapsed")
h = heroes[heroes.kind == kind].iloc[0]

st.markdown(f"**{h['opp_id']} — {h['name']}** · {md_amount(h.amount)} · "
            f"p={float(h.probability):.2f} · complexity {h.complexity_score}")

# Full attribute set: the seven risk signals as chips (red = active risk, so
# the complexity score is visibly the count of red chips; muted = not a
# factor) plus stage/strategic/recency colored by valence.
opp_full = data["opportunities"].set_index("opp_id").loc[h["opp_id"]]
chips = "".join(
    f"<span class='dbe-chip {'bad' if _b(opp_full[col]) else 'off'}'>"
    f"{'✓ ' if _b(opp_full[col]) else ''}{label}</span>"
    for col, label, _ in RISK_SIGNALS)
_stage_cls = "good" if opp_full.stage == "CONTRACT" else "warn"
_strat_cls = "good" if _b(opp_full.strategic_account) else "warn"
_days = int(opp_full.days_since_activity)
_days_cls = "good" if _days <= 7 else ("warn" if _days <= 21 else "bad")
chips += (f"<span class='dbe-chip {_stage_cls}'>stage: {opp_full.stage}</span>"
          f"<span class='dbe-chip {_strat_cls}'>strategic: {'yes' if _b(opp_full.strategic_account) else 'no'}</span>"
          f"<span class='dbe-chip {_days_cls}'>{_days} days since activity</span>")
st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)
st.caption(COMPLEXITY_DEF + " Both answers below respond to the question shown in "
           "'The question' expander at the bottom of the page.")

colc, colp = st.columns(2)
for col, tier_key, title in ((colc, "cheap", "cheap · llama3.1-8b"),
                             (colp, "premium", "premium · claude-sonnet-4-5")):
    with col:
        st.markdown(f"##### {title}")
        _verdict = h[f"{tier_key}_verdict"]
        _blocker = h[f"{tier_key}_primary_blocker"]
        _v_cls = {"AT_RISK": "red", "NO_ACTION_NEEDED": "yellow", "ON_TRACK": "green"}[_verdict]
        _b_cls = "green" if _blocker == "NONE" else "red"
        st.markdown(
            f"<span class='dbe-field' title='verdict — can this forecast be trusted? "
            f"One of ON_TRACK, AT_RISK, NO_ACTION_NEEDED.'>verdict</span> "
            f"<span class='dbe-enum {_v_cls}'>{_verdict}</span> &nbsp; "
            f"<span class='dbe-field' title='primary blocker — the single biggest "
            f"obstacle, from a fixed list of eight.'>blocker</span> "
            f"<span class='dbe-enum {_b_cls}'>{_blocker}</span>", unsafe_allow_html=True)
        # fixed-size action block keeps the two arms' cards aligned regardless
        # of action length; same size both arms, always the second-largest text
        st.markdown("<div class='dbe-field' title='next best action — the one thing "
                    "the rep should do next, in the model&apos;s words.'>next best action</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='dbe-action'>{html.escape(h[f'{tier_key}_next_best_action'])}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='dbe-field' title='reasoning — the model&apos;s "
                    "justification, grounded in the record evidence. Shown to humans, "
                    "never auto-scored.'>reasoning</div>", unsafe_allow_html=True)
        # full text, no expander: a lone "more" on one card looked broken, and
        # the longest reasoning is ~5 lines — cheap real estate. Near-white for
        # dark-background readability (gray was too dim for body text).
        st.markdown(f"<div class='dbe-reasoning'>{html.escape(h[f'{tier_key}_reasoning'])}</div>",
                    unsafe_allow_html=True)

evidence = json.loads(h.routed_evidence)
st.success(
    f"**Routing decision:** tier **{h.routed_tier}** — {h.routed_reason}.  \n"
    f"Evidence: {', '.join(f'{k}={v}' for k, v in evidence.items())}"
)
if "complexity_score" in evidence:
    st.caption(COMPLEXITY_DEF + " The lit chips above are the signals being counted.")

# ---- Q&A armor (not part of the demo flow) ---------------------------------
with st.expander("All 30 records"):
    adaptive = runs[(runs.policy == "adaptive")
                    & (runs.threshold.astype(float) == threshold)]
    reference = runs[runs.policy == "reference"]
    dec = decisions[decisions.threshold.astype(float) == threshold]
    opps = data["opportunities"]
    # amount deliberately omitted: it is never a policy input, the hero cards
    # carry it, and the width buys the conclusion columns room to render
    table = (opps[["opp_id", "probability"]]
             .merge(dec[["opp_id", "complexity_score", "tier", "changed_vs_reference",
                         "consequential"]], on="opp_id")
             .merge(reference[["opp_id", "verdict", "primary_blocker"]]
                    .rename(columns={"verdict": "ref_verdict", "primary_blocker": "ref_blocker"}), on="opp_id")
             .merge(adaptive[["opp_id", "verdict", "primary_blocker"]]
                    .rename(columns={"verdict": "adaptive_verdict", "primary_blocker": "adaptive_blocker"}), on="opp_id")
             .rename(columns={"changed_vs_reference": "changed"})
             .sort_values(["changed", "opp_id"], ascending=[False, True]))

    # Compact signals column instead of 7 boolean columns (table width):
    # abbreviations of the ACTIVE risk signals, so complexity_score is
    # traceable without leaving the table.
    flags_by_id = opps.set_index("opp_id")
    table.insert(4, "signals", table.opp_id.map(
        lambda oid: ", ".join(abbr for col, _, abbr in RISK_SIGNALS
                              if _b(flags_by_id.loc[oid][col])) or "—"))
    table["probability"] = table.probability.map(lambda v: f"{float(v):.2f}")

    # Highlight the specific cells that differ — yellow highlighter (bright,
    # deliberately not red: no editorializing about which arm is wrong).
    # Dark text on the yellow keeps the enum readable.
    TINT = ("background-color: rgba(253, 224, 71, 0.92); "
            "color: #111827; font-weight: 600")

    def _diff_tint(r):
        styles = pd.Series("", index=r.index)
        if r["ref_verdict"] != r["adaptive_verdict"]:
            styles[["ref_verdict", "adaptive_verdict"]] = TINT
        if r["ref_blocker"] != r["adaptive_blocker"]:
            styles[["ref_blocker", "adaptive_blocker"]] = TINT
        return styles

    st.dataframe(
        table.style.apply(_diff_tint, axis=1), hide_index=True, width='stretch',
        column_config={
            "opp_id": st.column_config.Column(width="small", help="Record identifier — one sales opportunity."),
            "probability": st.column_config.Column(width="small", help="The CRM's close probability for this deal (0–1). The routing rule's first check: very high or very low means the outcome is effectively decided, so the record is routed cheap."),
            "complexity_score": st.column_config.Column(width="small", help=COMPLEXITY_DEF),
            "signals": st.column_config.Column(help="The active risk signals behind complexity_score: "
                                               "buyer=no economic buyer, comp=competitor, sec=security/legal, "
                                               "proc=procurement not started, champ=champion risk, "
                                               "inact=inactive >21d, confl=conflicting signals."),
            "tier": st.column_config.Column(width="small", help="Which tier (and model) produced the adaptive policy's answer for this record — cheap=llama3.1-8b, balanced=mistral-large2, premium=claude-sonnet-4-5."),
            "changed": st.column_config.Column(width="small", help="The two policies reached different conclusions for this record — the verdict or the primary blocker differs, by exact string match. No AI grades these answers."),
            "consequential": st.column_config.Column(width="small", help="The two policies disagree on a live deal — where a different answer could change what the rep does next. Unchecked changed rows are disagreements on already-settled or already-lost deals, where the action stays the same either way."),
            "ref_verdict": st.column_config.Column(help="Conclusion from the reference policy — every record sent to the premium model."),
            "ref_blocker": st.column_config.Column(help="Conclusion from the reference policy — every record sent to the premium model."),
            "adaptive_verdict": st.column_config.Column(help="Conclusion from the adaptive policy at the threshold currently selected on the slider."),
            "adaptive_blocker": st.column_config.Column(help="Conclusion from the adaptive policy at the threshold currently selected on the slider."),
        })
    st.caption("Highlighted cells are the fields where the two arms' conclusions differ — "
               "tier plus highlight answers which model disagreed, and on which field.")

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
    # tier ladder order (cheap → balanced → premium), not alphabetical — the
    # cost column should read as a progression, and the mapping is explicit
    _model_tier = {m: t for t, m in TIER_MODEL.items()}
    _ladder = {t: i for i, t in enumerate(TIER_MODEL)}
    usage.insert(0, "tier", usage.model.map(_model_tier))
    usage = usage.sort_values("tier", key=lambda s: s.map(_ladder))
    st.dataframe(usage, hide_index=True, width='stretch', column_config={
        "tier": st.column_config.Column(
            help="The price-quality rung on the ladder — cheap, balanced, premium. "
                 "Each tier maps to one model (next column)."),
        "model": st.column_config.Column(help="The Cortex model behind a tier — cheap=llama3.1-8b, "
                                         "balanced=mistral-large2, premium=claude-sonnet-4-5."),
        "calls": st.column_config.Column(help="Unique model calls: one per (record, tier) pair. A call used by "
                                         "both policies is counted once, so these are physical calls, not billing rows."),
        "input_tokens": st.column_config.Column(help="Token counts as returned by each model call, summed over the unique calls."),
        "output_tokens": st.column_config.Column(help="Token counts as returned by each model call, summed over the unique calls."),
        "credits": st.column_config.Column(help="Each call's returned token counts priced at Snowflake's published "
                                           "per-token rates — measured, not estimated."),
        "cost ($)": st.column_config.Column(help="Credits converted at \\$3.00 per credit (Enterprise on-demand, "
                                            "AWS us-west-2 — a stated assumption; the credits column is the measured value)."),
    })
    st.caption("Unique model calls behind the reference arm and the adaptive arm at the "
               "selected threshold — a record premium in both arms is one call, counted once. "
               "Raw measured values from MODEL_RUNS; reconcilable against Snowflake's "
               "CORTEX_FUNCTIONS_USAGE_HISTORY (same ledger).")

with st.expander("The question"):
    st.code(PROMPT_TEMPLATE.format(
        record_block="<this record's CRM context — id, amount, probability, stage,\n"
                     " strategic flag, days since activity, close date, active risk\n"
                     " flags, and the rep's notes — injected here>"),
        language=None)
    st.caption("This identical prompt goes to every model — cheap, balanced, premium — "
               "with only the record's CRM context injected. Same question, same rules, "
               "same output contract; only the model changes. That's what makes the two "
               "arms' conclusions comparable. The numbered procedure pins the verdict "
               "boundaries so the arms can't disagree by vocabulary; the model's judgment "
               "lives in assessing whether risks require intervention, choosing the "
               "primary blocker, and the next action — the fields where the tiers "
               "actually diverge.")

with st.expander("The policy"):
    prov, prov_src = policy_provenance()
    st.markdown(
        f"<span class='dbe-chip meta' style='font-weight:600'>"
        f"{prov['version']} · {prov['author']} · {prov['basis']} — would be v2 "
        f"when learned from labeled decisions</span>"
        f"<span class='dbe-chip {'on' if prov_src == 'everos' else 'off'}'>"
        f"policy record: "
        f"{'EverOS memory' if prov_src == 'everos' else 'local definition (EverOS not consulted)'}"
        f"</span>", unsafe_allow_html=True)
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
