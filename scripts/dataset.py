# Decision Budget Engine — Intellinomics
# Built at the Snowflake x Beta Fund AI Token Economics Hackathon, Aug 2026
# MIT License — see LICENSE

"""Hand-authored 30-opportunity dataset (workbook T1-T3).

Every record is deliberate. Heroes are OPP-001 (settled), OPP-002 (complex),
OPP-003 (contestable). Distribution engineering per T3:
  - 5 records in the 0.90-0.98 probability band (OPP-006..010)
  - 2 records below 0.10 (OPP-004, OPP-005)
so that thresholds 0.98 / 0.95 / 0.90 produce distinct routing.

Language rule: decisions "change" between arms; nothing here claims a tier
is better -- see data/SCHEMA.md.
"""

FLAGS = [
    "no_economic_buyer",
    "competitor_present",
    "security_legal_blocked",
    "procurement_not_started",
    "champion_risk",
    "inactive_21d",
    "conflicting_signals",
]

COLUMNS = (
    ["opp_id", "name", "amount", "probability", "stage", "strategic_account"]
    + FLAGS
    + ["days_since_activity", "close_date", "notes"]
)


def rec(opp_id, name, amount, probability, stage, strategic, flags, days, close, notes):
    r = {
        "opp_id": opp_id,
        "name": name,
        "amount": amount,
        "probability": probability,
        "stage": stage,
        "strategic_account": strategic,
        "days_since_activity": days,
        "close_date": close,
        "notes": notes,
    }
    for f in FLAGS:
        r[f] = f in flags
    # Consistency: inactivity flag must agree with the day count
    assert r["inactive_21d"] == (days > 21), f"{opp_id}: inactive_21d vs days_since_activity mismatch"
    return r


OPPORTUNITIES = [
    # --- Heroes (T2) ---------------------------------------------------------
    rec("OPP-001", "Meridian Health -- Platform Renewal", 5_200_000, 0.99, "CONTRACT", True,
        [], 2, "2026-08-28",
        "Legal review complete, MSA redlines signed off 8/2. PO already raised in their "
        "system. CFO sponsored the renewal in the QBR. No competing vendor in the account. "
        "Rep expects countersignature this month."),
    rec("OPP-002", "Northwind Logistics -- Analytics Expansion", 400_000, 0.52, "PROPOSAL", False,
        ["no_economic_buyer", "competitor_present", "security_legal_blocked", "procurement_not_started"],
        9, "2026-10-30",
        "Security review stalled three weeks on data residency question, no ETA from their "
        "InfoSec. Champion (Dir of Ops) is enthusiastic but VP Finance has not joined any "
        "call. Procurement portal registration not started. DataRival named by procurement "
        "as a reference bid they intend to collect."),
    rec("OPP-003", "Castellan Insurance -- Claims AI Pilot", 750_000, 0.58, "NEGOTIATION", False,
        ["competitor_present", "champion_risk", "conflicting_signals"],
        5, "2026-11-13",
        "Stage says negotiation but no commercial terms have actually been discussed. "
        "Champion moved into a new role with narrower budget authority mid-cycle, and "
        "with that move nobody at Castellan currently owns the budget decision -- the "
        "Claims VP claims it, but spend of this size routes through an IT steering "
        "committee the Claims VP does not sit on. Claims VP wants full-department "
        "rollout; IT sponsor insists on a 10-seat pilot only -- the two have not "
        "reconciled scope. Incumbent vendor's renewal is running in parallel."),

    # --- Below 0.10 -- already lost, certainty veto fires low-side (T3) ------
    rec("OPP-004", "Quarry Steel -- Data Platform", 900_000, 0.05, "DISCOVERY", False,
        ["champion_risk", "inactive_21d"],
        44, "2026-09-25",
        "Champion resigned in June and joined a competitor. No response to three follow-ups "
        "since 6/23. Deal kept open at rep's request pending one final executive email."),
    rec("OPP-005", "Bluewater Resorts -- POS Analytics", 150_000, 0.08, "QUALIFICATION", False,
        ["no_economic_buyer", "inactive_21d"],
        31, "2026-09-18",
        "Initial demo went fine but budget owner never identified. Contact went quiet after "
        "7/6; two nudges unanswered. Seasonal business -- they may re-engage after peak "
        "season, not before close date."),

    # --- 0.90-0.98 band -- these records are why the frontier moves (T3) -----
    rec("OPP-006", "Halberd Financial -- License Renewal", 1_100_000, 0.97, "CONTRACT", False,
        [], 3, "2026-08-31",
        "Renewal paper with their legal for signature routing, expected back within two "
        "weeks. Usage grew 22% YoY, no open support escalations, no competitor activity."),
    rec("OPP-007", "Sierra Foods -- Renewal + Seat Expansion", 680_000, 0.96, "CONTRACT", True,
        [], 4, "2026-09-11",
        "Named strategic account. Renewal plus 40-seat expansion verbally agreed with the "
        "COO; order form in their signature queue. Pricing already approved on our side."),
    rec("OPP-008", "Atlas Freight -- Enterprise Rollout", 2_400_000, 0.93, "NEGOTIATION", True,
        ["competitor_present", "security_legal_blocked", "procurement_not_started", "conflicting_signals"],
        7, "2026-10-16",
        "Rep has probability at 93% after exec dinner, but security architecture review is "
        "unfinished, procurement intake not filed, and RivalCo was on-site last month -- "
        "the CRM optimism and the open blockers do not tell the same story. Probable and "
        "messy at the same time."),
    rec("OPP-009", "Pinnacle Media -- Contract Renewal", 320_000, 0.92, "CONTRACT", False,
        ["inactive_21d"],
        24, "2026-09-04",
        "Auto-renewal language in current contract; customer historically signs late with "
        "no drama. Nothing from their side in three-plus weeks, which matches last year's "
        "pattern rather than signaling a problem."),
    rec("OPP-010", "Redwood Biotech -- Data Cloud Renewal", 540_000, 0.91, "CONTRACT", False,
        [], 6, "2026-09-30",
        "Renewal confirmed verbally by IT director; waiting on their new fiscal-year budget "
        "code to process the order. Support tickets trending down, adoption steady."),

    # --- Settled, >= 0.98 besides the hero -----------------------------------
    rec("OPP-011", "Ironvale Mining -- Support Renewal", 210_000, 0.98, "CONTRACT", False,
        [], 8, "2026-08-21",
        "Flat renewal, same terms as last year. Customer confirmed in writing; invoice "
        "requested for their AP calendar. Formality at this point."),

    # --- High complexity (4+ signals) -- premium candidates (T3) -------------
    rec("OPP-012", "Concord Utilities -- Grid Analytics", 1_800_000, 0.45, "PROPOSAL", True,
        ["no_economic_buyer", "security_legal_blocked", "procurement_not_started", "inactive_21d"],
        28, "2026-12-11",
        "Regulated-utility security addendum still with their counsel, four weeks now. "
        "Economic buyer (VP Grid Ops) has delegated all calls to an analyst. Procurement "
        "says RFP may be required. No substantive contact since mid-July."),
    rec("OPP-013", "Vantage Retail -- Personalization Suite", 950_000, 0.60, "NEGOTIATION", False,
        ["no_economic_buyer", "competitor_present", "champion_risk", "conflicting_signals"],
        10, "2026-11-06",
        "CMO sponsor reorged into a regional role; replacement not named. Merchandising "
        "team pushing to close this quarter while finance asks why the project exists at "
        "all -- directly contradictory signals in the same week. PersonaLab ran a "
        "competing pilot in Q2."),
    rec("OPP-014", "Helios Energy -- Forecasting Platform", 1_250_000, 0.35, "PROPOSAL", False,
        ["no_economic_buyer", "competitor_present", "security_legal_blocked", "procurement_not_started", "inactive_21d"],
        26, "2026-12-18",
        "Five open risk signals. SOC2 addendum questions unanswered, no budget owner on "
        "record, procurement intake not started, incumbent forecasting vendor lobbying to "
        "extend, and the account has been dark for almost four weeks."),
    rec("OPP-015", "Argent Bank -- Risk Modeling Workbench", 3_100_000, 0.68, "NEGOTIATION", True,
        ["competitor_present", "security_legal_blocked", "procurement_not_started", "conflicting_signals"],
        6, "2026-11-27",
        "Model-risk-management review open with two rounds of questions outstanding. "
        "Procurement will not open intake until MRM clears. Business unit says signed by "
        "Thanksgiving; risk office says no vendor decisions before year-end -- both are in "
        "the CRM. QuantEdge shortlisted alongside us."),

    # --- Strategic accounts, mid probability -- floor, never a bypass --------
    rec("OPP-016", "Trailhead Apparel -- Customer 360", 880_000, 0.75, "PROPOSAL", True,
        ["competitor_present"],
        11, "2026-10-23",
        "Strategic logo for the retail vertical. Proposal well received; CDP incumbent "
        "responded with a discounted renewal offer. Exec sponsor engaged and responsive."),
    rec("OPP-017", "Keystone Manufacturing -- Supply Chain AI", 1_500_000, 0.66, "DISCOVERY", True,
        ["no_economic_buyer", "procurement_not_started"],
        13, "2026-12-04",
        "Named strategic account, early cycle. Plant-level buy-in is strong; corporate "
        "budget owner not yet identified. Long procurement runway typical for this "
        "account -- flagged early, not yet blocking."),

    # --- Balanced by default -- the middle of the book (T3) ------------------
    rec("OPP-018", "Lumen Studios -- Media Asset Search", 260_000, 0.40, "QUALIFICATION", False,
        ["no_economic_buyer"],
        14, "2026-11-20",
        "Post-production leads love the demo; nobody with budget authority has been in a "
        "meeting yet. Studio is mid-slate, decisions move slowly until wrap."),
    rec("OPP-019", "Copperline Telecom -- Churn Analytics", 620_000, 0.72, "PROPOSAL", False,
        ["competitor_present"],
        8, "2026-10-09",
        "Technical eval scored us first of three. TelcoMetrics remains in the process at "
        "the CIO's insistence. Commercial proposal delivered, awaiting their scoring "
        "committee."),
    rec("OPP-020", "Foxglove Pharma -- Trial Data Hub", 1_050_000, 0.55, "PROPOSAL", False,
        ["security_legal_blocked", "procurement_not_started"],
        12, "2026-11-27",
        "GxP validation questionnaire in progress with our compliance team, their QA has "
        "follow-ups queued. Procurement will not engage until QA signs off. Sponsor "
        "steady, timeline realistic for pharma."),
    rec("OPP-021", "Marlowe & Finch -- Legal Doc Intelligence", 190_000, 0.30, "DISCOVERY", False,
        ["no_economic_buyer", "inactive_21d"],
        25, "2026-12-11",
        "Two partners saw the demo, neither owns the tech budget. Firm is mid-trial on a "
        "major matter; contact said to circle back in September and has been quiet since."),
    rec("OPP-022", "Stonebridge Credit Union -- Fraud Scoring", 430_000, 0.85, "NEGOTIATION", False,
        [], 4, "2026-09-18",
        "Terms agreed in principle; final pricing memo with their CFO. Reference call with "
        "a peer credit union completed and went smoothly. No open objections."),
    rec("OPP-023", "Aurora Hospitality -- Guest Data Platform", 350_000, 0.25, "QUALIFICATION", False,
        ["no_economic_buyer", "competitor_present", "procurement_not_started"],
        16, "2026-12-18",
        "Early exploration driven by a new VP of Digital who has not yet secured budget. "
        "HotelTech incumbent has a multi-year contract with an early-exit clause under "
        "review. Procurement not aware of the initiative."),
    rec("OPP-024", "Granite Peak Builders -- Project Analytics", 780_000, 0.62, "PROPOSAL", False,
        ["champion_risk", "conflicting_signals"],
        9, "2026-10-30",
        "Champion (IT Director) survived a reorg but lost two of five direct reports. Ops "
        "leadership calls this a top-three initiative while the CFO's office lists it "
        "under discretionary spend eligible for deferral -- same week, different decks."),
    rec("OPP-025", "Silverbirch Education -- Enrollment Insights", 240_000, 0.48, "QUALIFICATION", False,
        ["inactive_21d"],
        23, "2026-11-13",
        "Positive pilot readout in early July, then summer break silence -- expected in "
        "education, admissions team returns mid-August. Pilot metrics already shared with "
        "their cabinet."),
    rec("OPP-026", "Harborview Health -- Imaging Archive", 1_400_000, 0.78, "NEGOTIATION", True,
        ["security_legal_blocked"],
        5, "2026-10-16",
        "Strategic healthcare account. BAA and HIPAA security rider in legal review -- "
        "normal cycle time for them is 3-4 weeks and we are in week two. Clinical and IT "
        "sponsors aligned."),
    rec("OPP-027", "Nimbus Gaming -- Player Telemetry", 165_000, 0.20, "DISCOVERY", False,
        ["no_economic_buyer", "competitor_present"],
        15, "2026-12-04",
        "Analytics lead ran a self-serve trial and liked it. Studio evaluating an "
        "open-source stack in parallel. No budget conversation yet; studio funding tied "
        "to next title milestone."),
    rec("OPP-028", "Cobalt Chemicals -- ESG Reporting", 510_000, 0.83, "PROPOSAL", False,
        ["procurement_not_started"],
        7, "2026-09-25",
        "Sustainability office selected us after a three-vendor bake-off. Procurement "
        "intake opens next cycle per their policy -- known, dated, and on their calendar. "
        "Sponsor responsive."),
    rec("OPP-029", "Wrenfield Logistics -- Route Optimization", 290_000, 0.15, "QUALIFICATION", False,
        ["no_economic_buyer", "champion_risk", "inactive_21d"],
        35, "2026-11-20",
        "Original champion moved to a competitor in July. Operations analyst who inherited "
        "the eval has no purchasing authority and has not replied in five weeks."),
    rec("OPP-030", "Juniper Robotics -- Fleet Data Platform", 830_000, 0.70, "PROPOSAL", False,
        ["conflicting_signals"],
        6, "2026-10-23",
        "Engineering VP calls us the presumptive choice; the same VP's staff meeting notes "
        "(shared by champion) list the project as paused pending Series C close. CRM "
        "probability reflects the VP's verbal, not the board timeline."),
]

assert len(OPPORTUNITIES) == 30, f"expected 30 records, got {len(OPPORTUNITIES)}"
assert len({r["opp_id"] for r in OPPORTUNITIES}) == 30, "duplicate opp_id"

# T3 distribution guarantees
_band = [r for r in OPPORTUNITIES if 0.90 <= r["probability"] < 0.98]
_lost = [r for r in OPPORTUNITIES if r["probability"] < 0.10]
assert 4 <= len(_band) <= 5, f"need 4-5 records in [0.90, 0.98), got {len(_band)}"
assert len(_lost) == 2, f"need 2 records below 0.10, got {len(_lost)}"


def complexity_score(r):
    """Decision Complexity Score: count of active risk signals (0-7)."""
    return sum(1 for f in FLAGS if r[f])


def write_csv(path):
    import csv

    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in OPPORTUNITIES:
            row = dict(r)
            for f in FLAGS:
                row[f] = "TRUE" if row[f] else "FALSE"
            row["strategic_account"] = "TRUE" if row["strategic_account"] else "FALSE"
            w.writerow(row)


if __name__ == "__main__":
    import os

    out = os.path.join(os.path.dirname(__file__), "..", "data", "opportunities.csv")
    write_csv(os.path.normpath(out))
    print(f"wrote {len(OPPORTUNITIES)} records")
