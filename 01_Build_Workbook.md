# Decision Budget Engine — Build Workbook

**Use this Friday. Everything else is reference.**

Feature filter, on the whiteboard:

> Does this help prove that different business decisions within the same workload deserve different amounts of intelligence?

If no, don't build it.

---

## 0. Before Friday (do not defer)

| Item | Done when |
|---|---|
| Snowflake auth verified | You can create a table from your laptop, on your own network |
| Model access confirmed | You have called cheap / balanced / premium tiers successfully |
| **Tier → model mapping fixed** | Each of the three tiers names one specific available model. No "balanced TBD" on Friday. |
| Pricing constants written down | Per-million input and output token rates for all three tiers |
| Function Studio availability | Asked in Discord — yes/no answer recorded |
| Repo scaffolded | Empty script runs, reads a CSV, writes a table |
| **Fallback mechanism built** | UI reads from a results table with dummy rows and never calls a model. Friday only swaps in real data. |

**Exit condition:** no environment or authentication decisions remain for Friday.

---

## 1. Timeline

| Time | Focus | Exit condition |
|---|---|---|
| 11:00–12:00 | Dataset | 3 hero records hand-authored, 27 generated |
| 12:00–1:00 | Dual-policy runner | Both arms run end-to-end on 3 records |
| 1:00–2:00 | Policy, scoring, full run | Measured outputs for all 30, three frontier points |
| 2:00–2:30 | Snowflake + fallback | Data queryable live and offline |
| **2:30** | **HARD STOP** | No new features. Demo-blocking defects only. |
| 2:30–3:15 | One screen + script | Four beats visible and timed |
| 3:15–4:00 | Rehearse, stabilize, submit | Three clean runs under 2:45 |

---

## 2. Task board

### P0 — demo does not exist without these

| # | Task | Done when |
|---|---|---|
| T1 | Opportunity schema + blocker enum | Fields and enum values documented |
| T2 | Three hero opportunities | Settled / complex / contestable produce intended routing |
| T3 | Remaining 27 records | Deliberate edge cases present, notes have texture, **and 4–5 records sit between 0.90 and 0.98 probability plus 2 below 0.10** so every threshold and branch actually fires |
| T4 | Structured prompt | Model returns valid JSON matching schema |
| T5 | Decision Complexity Score | Deterministic, testable, parameterized threshold |
| T6 | Adaptive Business Policy | Certainty first, strategic floor, returns explanation |
| T7 | Dual-policy runner | One script, both arms, 3 records end-to-end |
| T8 | Usage capture | Tokens, cost, latency, model, output stored per call |
| T9 | Exact-match scoring | Verdict and blocker agreement computed automatically |
| T10 | Decisions Changed | Count of records where verdict or blocker differs |
| T11 | Snowflake tables | All four tables load |
| T12 | Comparison view | One query feeds the results screen |
| T13 | Offline fallback — populate | Real results loaded into the pre-built fallback table; demo runs with zero live calls |
| T14 | Three-minute script | Four beats and exact closing line written |
| T15 | Rehearse | Three runs under 2:45 |

### P1 — only if P0 is complete

| # | Task |
|---|---|
| T16 | Low-value premium spend summary |
| T17 | Three threshold runs → frontier |
| T18 | Slider + hero comparison UI |

**Split for two builders:** one owns T1–T3 + T11–T13 (data and persistence), the other owns T4–T10 (policy and measurement). T14–T15 together.

---

## 3. Policy specification

```
if probability >= high_confidence_threshold:      # settled
    return CHEAP
if probability <= low_confidence_threshold:       # already lost
    return CHEAP
if decision_complexity_score >= complexity_threshold:
    return PREMIUM
if strategic_account:
    return BALANCED
return BALANCED
```

**Order is the product philosophy.** Certainty vetoes spend. Strategic importance sets a floor, never a bypass. There is no direct multiplier on deal size anywhere in the policy.

**Decision Complexity Score** — count of active risk signals, distinct from CRM probability:

- No economic buyer engaged
- Competitor present
- Security or legal blocked
- Procurement not started
- Champion departed or weakened
- No activity > 21 days
- Conflicting notes or stage signals

0–1 low · 2–3 medium · 4+ high. Threshold parameterized.

**Every routing decision returns:** selected tier, reason, business evidence used, thresholds applied. No ROI number — the system does not compute financial return from reasoning.

---

## 4. AI task contract

**Question:** Can I trust this forecast, what's the biggest risk, and what should I do next?

**Output schema:**

| Field | Values | Purpose |
|---|---|---|
| `verdict` | ON_TRACK, AT_RISK, NO_ACTION_NEEDED | Categorical agreement scoring |
| `primary_blocker` | ECONOMIC_BUYER, SECURITY_LEGAL, PROCUREMENT, COMPETITION, PRICING, CHAMPION_LOSS, INACTIVITY, NONE | Exact-match scoring |
| `next_best_action` | Free text, one action | Business value; shown largest in UI |
| `reasoning` | Free text, grounded in evidence | Makes tier quality difference visible |

**Constraint:** the model does not output a confidence score. CRM probability is a policy input only. Two confidence numbers on screen invites a question you can't win.

---

## 5. Snowflake tables

| Table | Purpose | Key fields |
|---|---|---|
| `OPPORTUNITIES` | Source business context | id, name, amount, probability, stage, risk flags, strategic, notes, timeline |
| `MODEL_RUNS` | One row per opportunity per policy | run_id, opp_id, policy, tier, in/out tokens, cost, latency, verdict, blocker, action, reasoning, error |
| `POLICY_DECISIONS` | Explainability record | opp_id, policy, thresholds, complexity score, tier, reason, signals used |
| `RUN_SUMMARY` | Demo aggregates | policy, total cost, verdict agreement, blocker agreement, decisions changed, low-value premium spend |

---

## 6. Measurement rules

**Headline:** `ONLY X OF 30 DECISIONS CHANGED WHEN WE BOUGHT MORE REASONING`

- A decision *changed* if verdict or primary blocker differs between arms. Automated.
- Next-action differences shown for hero records only, not automated.
- Say **changed**, never **improved** or **benefited**. Changed is measured. Improved is not.
- Every number on screen comes from a run. If agreement is 88%, show 88%.
- **No LLM-as-judge anywhere in scoring, by design.** A judge model would make the headline number carry a second model's biases and hand judges the "AI grading AI" attack. Exact match on contractually-forced enums is reproducible by anyone with the two output tables.
- **Conclusions vs outcomes.** The arms reach *conclusions* (verdict, blocker); deals have *outcomes* (closed, stalled, died) — reserve "outcome" for the real world. The metric counts records where conclusions differ, symmetrically: neither arm is a baseline-of-truth the other deviated from.
- **Two kinds of numbers on screen, and only two.** Measured numbers appear unlabeled. Projections (e.g. the 10k records/week scaling of measured per-record cost) are always labeled "projected." Nothing else — no estimates, no illustrative figures.

**Frontier:** vary `high_confidence_threshold` **only** — 0.98 / 0.95 / 0.90, labelled Conservative / Balanced / Savings-Oriented. Hold `complexity_threshold` and every other rule constant. Two dials moving at once means you can't attribute the change to either.

The Reference Policy is the same curve at threshold 1.00 — nothing is ever settled enough to spend less on. Present it as the endpoint, not a separate baseline.

Frontier table columns: policy · threshold · **% routed cheap** · total cost · decisions changed · verdict agreement. The % cheap column is free to compute and makes the mechanism visible — without it, falling cost looks like magic.

**Dry-run the policy function against the dataset before any model calls.** Pure arithmetic, two minutes. If all three thresholds produce identical routing, the frontier collapses into three identical rows and you'll find out at 1:45 with no time to fix the data.

**Say aloud in the demo:** *"For this prototype, the premium model is our reference implementation, not truth. In production we'd evaluate against expert labels and actual business outcomes."*

**Cost reconciliation (cheap, do it):** our measured token counts should agree with Snowflake's own cost surface by construction. After a run:

```sql
-- Ours (from show_details capture in MODEL_RUNS)
SELECT model, SUM(input_tokens + output_tokens) AS our_tokens
FROM MODEL_RUNS GROUP BY model
-- Theirs (Snowflake's governed spend surface)
-- SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY: tokens + token_credits by model
SELECT model_name, SUM(tokens) AS their_tokens, SUM(token_credits) AS credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY
WHERE function_name ILIKE '%COMPLETE%' GROUP BY model_name;
```

View verified queryable on our account. **Caveat: ACCOUNT_USAGE lags up to a few hours** — run Friday's reconciliation against the morning's calls, not the run you just finished; don't demo it live expecting instant agreement. If numbers match (ours ⊆ theirs for the run window), say so in one line: routing decisions and their spend live in the same ledger.

---

## 7. Risks

| Risk | Guardrail |
|---|---|
| WiFi or auth fails on stage | Fallback table built and tested Thursday, not Friday |
| Invalid JSON | Strict schema, validate, one retry, then error record |
| All models agree everywhere | Test heroes first; add conflicting evidence to the contestable record |
| Premium output not visibly better | Revise the contestable opportunity, not the concept |
| Agreement lower than hoped | Show it. The frontier makes any number a tunable operating point. |
| "Isn't this an if statement?" | "Intentionally rules-based so every decision is explainable. Production policy would be learned from expert labels and observed outcomes." |
| Features creep after 2:30 | Feature filter on the whiteboard |

---

## 8. Go / no-go

- [ ] Snowflake auth verified before Friday
- [ ] Three heroes produce intended routing
- [ ] Both arms run in one script
- [ ] Every displayed number from a measured run
- [ ] Blocker enum scoring automated
- [ ] Decisions Changed is the headline
- [ ] Workload-vs-per-record diagram in the demo
- [ ] Routing card shows tier, reason, evidence
- [ ] Offline fallback works with zero live calls
- [ ] Demo under 2:45
- [ ] Closing line rehearsed, delivered unhurried
- [ ] No new features after 2:30
