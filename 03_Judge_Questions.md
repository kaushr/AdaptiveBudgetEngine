# Judge Questions — Prep Sheet

Read the morning of. Answer in two or three sentences and stop talking. Over-explaining a good answer reads as defensiveness.

**Three things to never say:** that the premium model is correct, that the changed decisions were better, or a number you didn't measure.

**Vocabulary rule:** the arms reach **conclusions** (verdict, blocker); deals have **outcomes** (closed, stalled, died). Canonical phrasing for the metric: *"on 5 of 30 records, the cheap and premium tiers reach different conclusions."* Note the symmetry — neither arm changed the other's answer; both answered independently and the answers differ. Never use wording that implies the adaptive arm deviated from a baseline-of-truth.

---

## The elevator framing (for non-technical judges)

A manager with 30 deals hires an expensive consultant to review every one, every week. On most deals the consultant looks for two minutes and says what the junior analyst would have said for free. On a few messy ones, the consultant genuinely earns the fee. The waste isn't hiring the consultant — it's hiring the consultant for deals where a glance was enough. This product is the rule that decides, per deal, who reviews it — using information the manager already has (how settled is it? how many unresolved problems?), never the deal's size.

**The two-line differentiation:** Snowflake's new cost stack (spend aggregation, per-user limits, runaway-query cancellation, workload model selection) governs accounts, users, and queries — it never looks inside a query at row 7 vs row 8. Token/model efficiency makes every call cheaper or picks a better default; both still treat every record identically. We're the layer that varies treatment per record — stacks on top of both, competes with neither.

---

## Tier 1 — you will get these

### "Isn't this just an if statement?"

Today, deliberately — every routing decision has to be explainable and auditable. The interesting part isn't the branching, it's what the branches key on. In production the policy would be learned from expert labels and observed outcomes rather than hand-set. The labels do double duty: the same expert labels that score the arms are training signal for the router — if records with a given signature (say, high complexity + departed champion) reliably favor premium, the policy learns to send that signature premium.

*Don't get defensive. The simplicity is a feature and you should sound like you chose it.*

### "Doesn't Snowflake already do this?"

At the workload and user level — quotas, attribution, per-function model selection. Those answer who spent what and which model fits a task. This answers a different question: within one task, which records deserve the reasoning. It sits on top rather than beside.

### "How do you know the cheap answers are good?"

We don't claim they're good — we measure whether they're different. Verdict and blocker are scored by exact match against the premium arm. The premium model is a reference implementation, not truth, and we say so.

### "So you're just routing by deal size."

No — and this is the one place I'd demo rather than answer. Move the probability slider. Deal size stays fixed, tier drops. A large settled deal is the clearest case of overspend in the dataset; a size-based policy gets it exactly backwards.

### "What if agreement comes back low?"

Then you move along the frontier. Three operating points, one threshold, same logic. The product isn't one correct policy — it's a tunable one.

*If your measured number is unflattering, lead with this framing rather than waiting to be asked.*

### "Doesn't running two models on everything double the cost?"

Only during calibration, which is occasional and sample-sized. Daily runtime is single-arm — each record gets exactly one call at its assigned tier — strictly cheaper than the premium-everything status quo. This is standard eval practice: nobody runs an A/B test forever; you run it until you trust the winner, ship the winner, re-test on a cadence.

---

## Tier 2 — likely from a PM or someone who's built this

### "This is a sales use case. Snowflake is horizontal."

The policy needs two signals from any domain: how settled is this record's outcome, and how much unresolved evidence has to be synthesized. Sales hands you both for free — CRM probability and a count of risk flags. Support triage, claims, contract review, and credit decisions all have the same shape: obvious cases and borderline cases sharing one workload.

Credit is the cleanest analogue — applicants well above or below the cutoff are decided regardless of how hard you think; the ones near the boundary are where reasoning changes the answer.

### "What if there's no probability column?"

Then you need computable proxies — document length, party count, entity count, contradiction markers, reopen count, time since last state change — or a cheap screening pass that emits a complexity score.

**The constraint worth stating:** the signal has to cost meaningfully less than the decision it gates. If screening costs nearly as much as answering, this layer stops paying for itself and workload-level optimization is the right tool. That's a real boundary and I'd rather name it than have it found.

### "How would this work as a platform feature rather than an app?"

Ship the hook, not the policy. An AI function that takes a per-row tier expression evaluated against columns already in the table — plus the decision log, the explainability record, and an evaluation harness that reports decisions-changed at each threshold. The platform provides the mechanism; the customer supplies the policy, because only they know their error costs.

### "Your threshold is arbitrary."

Correct, and necessarily so — the right bar is a function of what a wrong answer costs. A wrong sales verdict costs a rep a bad Monday; a wrong claims verdict costs real money. No vendor can ship a correct default, which is exactly why the deliverable is a frontier rather than a number.

### "One dial doesn't scale — real deployments have many parameters."

Right, but the customer should still see one control. They can't reason about two thresholds jointly; they can state one thing they know — how much decision drift the business tolerates. The system solves for the parameter vector satisfying that constraint: minimize cost subject to agreement above a floor. With one parameter the frontier is a line you read off a table. With many it's a surface you search. Same objective.

### "How do the parameters get set in production?"

Three stages. Sweep the parameter grid offline against a labeled sample and let the customer pick a point. Recalibrate periodically, because the frontier moves as data drifts. Then learn online from outcomes. Most of the value is in stage one — plenty of systems never need stage three.

### "Do your call counts and costs reconcile?"

Exactly. 61 unique model calls across all operating points: 30 premium (the reference arm; adaptive premium routes reuse them), 9 cheap and 20 balanced (the unions across the three thresholds — assignments nest as the threshold loosens), plus 2 extra cheap calls for the hero side-by-side view. The Usage expander shows the calls behind the selected view, deduplicated so a call shared by both arms is counted once. `MODEL_RUNS` intentionally has one row per record per arm (120) for per-arm accounting — physical spend is always aggregated over unique (record, tier) calls, reconcilable against `CORTEX_FUNCTIONS_USAGE_HISTORY`.

### "How do you actually use EverOS?"

**The one-liner: "Snowflake is where the decisions are made and audited; EverOS is where the system remembers them — and that memory is what turns today's hand-set thresholds into tomorrow's learned policy."**

The honest current state, stated first: every routing decision is logged as an episode — signals seen → tier chosen → whether the arms agreed. EverOS extracts and indexes them; retrieval works (verified at 0.85+ relevance on per-record queries, re-verified on each rebuild). Nothing in the routing path reads from it today — the policy doesn't query EverOS to make decisions.

Why that's the right scope, not a gap: EverOS's Cases→Skills model is the substrate the three-stage lifecycle needs. Decisions accumulate now; outcome labels and expert judgments attach later; repeated patterns ("records with this signature keep favoring premium") distill into learned routing. The hand-set policy becomes a learned one by reading exactly the memory we're writing today. The missing ingredient is labels, not infrastructure.

**If pushed:** "Today, write plus retrieval — the loop that reads it back into routing is stage three, and it needs outcome data we don't have. What we verified is that the memory layer extracts and retrieves our decisions." (Then show it: `python3 scripts/everos_log.py --search "OPP-008"` — live retrieval beats description.)

**Paired: "What is Snowflake doing here?"** Business context lives in `OPPORTUNITIES` — the columns the policy routes on. Inference runs in-warehouse via `AI_COMPLETE`, next to that data. Every conclusion, token count, cost, and explanation writes back to `MODEL_RUNS` / `POLICY_DECISIONS` / `RUN_SUMMARY` — reconcilable against `CORTEX_FUNCTIONS_USAGE_HISTORY`, the same ledger Snowflake's own cost tooling reads.

### "Why is the waste card only 2 when 9 decisions changed?"

They're disjoint by definition. Waste = records routed cheap where cheap reached **identical** conclusions to premium — the premium spend bought nothing. Changed = records where the conclusions **differ** — premium bought a different answer. A record is one or the other, never both. Waste is where routing cheap is airtight; changed-while-routed-cheap is the residual risk the conservative end of the frontier exists for.

### "Why only three models / three tiers?"

A tier is a price-quality point on an ordered ladder, not a model family. Production ladders can mix different models, the same model at different reasoning-effort budgets (increasingly the natural knob — one model with adjustable reasoning gives a smooth ladder with consistent style), or different context strategies. The policy is agnostic to what populates the ladder — it only needs tiers ordered by cost. More tiers is more thresholds, same logic; three is a demo choice, not an architectural limit.

### "Why only two enum fields? Real decisions are richer."

Two enums are the deliberately minimal contract that makes agreement a `!=`. Production returns a richer per-record mix, each scored by type: more enums (action category, escalation level) by exact match; numerics (days-to-close, discount ceiling) by tolerance bands; extracted facts (named economic buyer) by lookup against the CRM; free text shown to humans, not auto-scored. The generalizing principle: structure the output so agreement is computable — the frontier machinery follows from that, regardless of field count.

**If asked why not LLM-as-judge:** deliberately absent from scoring. A judge model would make the headline number carry a second model's biases, and hands judges the "AI grading AI" attack. Exact match on contractually-forced enums is reproducible by anyone with the two output tables.

---

## Tier 3 — the hard ones

### "Agreement means nothing if all 30 conclusions are wrong."

Correct — concede immediately. Agreement measures consistency between arms, not correctness; if the premium arm is wrong, high agreement means faithfully reproducing wrongness at lower cost. Then the three-layer path:

- **Layer 1 (this demo): consistency.** Exact-match on enums. All we claim. The premium arm is a reference implementation, not truth.
- **Layer 2 (expert labels): accuracy.** Managers review outputs blind to which arm produced them, marked right/wrong. Blind rating does two distinct jobs: on the ~25 *agreeing* records, labels test whether the consensus is right — whether the premium arm deserves to be the reference at all; on the ~5 *disagreeing* records, labels adjudicate which arm won each disagreement. Only after adjudication does "5 differ" become "N better, M worse" — the one construction where "improved" is earned. Volunteer the honest possibility that the cheap arm wins some adjudications (small models can be less prone to overthinking clean signals) — a finding the unlabeled demo cannot see, and a good faith-marker. Available immediately, expensive per label.
- **Layer 3 (outcomes over time).** Track whether the recommended action was taken and whether the flagged blocker materialized — NOT closed-won alone, since deals close despite bad advice and die despite good advice; outcome labels need intermediate signals to be attributable. Slow, noisy, free, unlimited.

**The kicker:** with those labels, "changed" becomes "improved," and the same frontier becomes an optimization instead of a setting — the measurement scaffolding in this demo is the same scaffolding the real system trains on. Nothing is thrown away; the labels get better.

**EverMind tie-in (one line):** Layer 3 is the EverOS integration — Cases record decision + evidence + eventual outcome; Skills are the patterns learned from them. The event's required infrastructure is the memory substrate for exactly this loop.

### "Two of your changed records are dead deals — doesn't that inflate the number?"

Concede the composition openly: 4 changed at Conservative, of which 2 are disagreements without consequence and 2 are live — and the drill-down table shows which is which (`consequential` column). The two dead deals (p ≤ 0.10) changed because the cheap model keeps calling a dead deal AT_RISK where premium says NO_ACTION_NEEDED.

Then the pivot — note the **direction** of the logic: those records were routed cheap precisely because nothing can change what happens to them. A cheap-model error there is a disagreement with no blast radius. The certainty veto doesn't just save money on settled records; it routes cheap exactly where being wrong is safest — and the consequential column demonstrates that with data. Concession first, then this: it turns the composition of the 4 from a weakness admitted into a design property proven, found in the measured run rather than designed in.

### "Isn't the prompt just telling the model the answer?"

It pins vocabulary, not substance. The numbered procedure fixes what the verdict *words* mean — where "settled" ends and "at risk" begins — so the arms can't disagree by using the same word differently. The judgment the model still owns is the substance: does this record's evidence require intervention now, which of eight blockers is primary, and what's the next action — exactly the fields where the tiers diverge (the contestable hero splits CHAMPION_LOSS vs ECONOMIC_BUYER under this same prompt). The full prompt is on screen in "The question" expander; a contract that decided the answers would produce 100% agreement, and we measure 90.

### "What did you learn building this?"

Small models need contracts written as procedures, not descriptions — llama ignored adjective-based verdict rules until we restructured them as a numbered decision procedure, applied identically to both arms so the measurement stayed valid. The interesting engineering in per-record routing is the task contract, not the routing.

### "Couldn't the cheap model be wrong on the deals you routed cheap, and you'd never know?"

Yes. That's the honest limit of the design and it's why we route cheap on *settled* decisions specifically — where the action is already determined, an error has less room to change anything. The residual risk is real, and it's what the conservative end of the frontier is for.

*Do not try to argue this away. Conceding it cleanly is more credible than any answer you could construct.*

### "What's the path from 'changed' to 'improved'?"

Outcome labels — but not closed-won alone, since a deal can close in spite of bad advice. You'd want expert review of the recommendations plus signals on whether the suggested action was taken and what followed.

### "Thirty synthetic records isn't evidence."

Agreed — it's a demonstration that the mechanism works and the measurement is honest, not a claim about effect size. The number that generalizes is the method: run both arms, score exact-match on structured fields, report what changed. That runs on real data unchanged.

### "Why not just always use the cheap model?"

Because some decisions do change — that's what the headline metric measures. If the answer were zero, the right move would be to drop the premium tier entirely, and this system would have told you that. It's as useful for finding where you're *underspending* as overspending.

### "What breaks first at scale?"

The signal layer. Policy evaluation is arithmetic and free; the cost is producing settledness and complexity for workloads that don't hand them to you in columns. That's the piece that would need real engineering.

---

## If you don't know

Say so, then say what you'd do to find out. "I don't know — I'd test it by X" is a strong answer at a hackathon and a much better one than improvising.
