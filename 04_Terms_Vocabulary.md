# Terms & Vocabulary — Decision Budget Engine

For Kaushik and Payal. The point of this doc: on stage and in Q&A, using the *right word consistently* matters more than fancy words. Judges hear sloppy vocabulary as sloppy thinking. When in doubt, use the exact term from this sheet.

Words in one group are NOT interchangeable with words in another group, even when they feel similar. The "don't confuse with" column is the whole value of this doc.

---

## 1. The core objects

| Term | Means | Don't confuse with |
|---|---|---|
| **Workload** | The whole task: "analyze 30 opportunities." One workload, many records. | Not a single record. Snowflake's tooling optimizes at this level; we go one level deeper. |
| **Record / Opportunity** | One row — one deal. The unit our policy routes. | "Opportunity" (sales word) and "record" (data word) are the same thing here. Use "record" when speaking generally, "opportunity" when speaking about sales. |
| **Hero (record)** | One of the 3 hand-authored records built to demonstrate a specific behavior: the settled one ($5M renewal), the contestable one ($400K expansion), the complex one. | Not "the best" records — the *demonstration* records. |

---

## 2. Tiers vs. policies vs. arms (the most common mix-up)

| Term | Means | Don't confuse with |
|---|---|---|
| **Tier** | A level of reasoning spend: **cheap / balanced / premium**. Each tier maps to one model. | Tiers are NOT policies. "Cheap" is a tier, not a run and not a policy. |
| **Model** | The actual LLM behind a tier: llama3.1-8b (cheap), mistral-large2 (balanced), claude-sonnet-4-5 (premium). | Say "tier" when talking about the policy's choice; say "model" only when the specific LLM matters. |
| **Policy** | The rule that assigns a tier to each record. Ours: certainty first, then complexity, then strategic floor. | Not a model, not a threshold. The policy *contains* thresholds. |
| **Adaptive (Business) Policy** | Our policy — picks a tier per record from business context. | — |
| **Reference Policy** | The comparison policy: every record gets premium. What customers do today. | NOT "ground truth," NOT "the correct answers." It is a *reference implementation* — the thing we compare against, not the thing that's right. |
| **Arm** | One side of the comparison when both policies run over the same records. "The reference arm" / "the adaptive arm." | An arm is a policy *being executed in the evaluation*. Casual synonym for policy in the context of the run. |
| **Operating point** | One position on the frontier: Conservative (0.98) / Balanced (0.95) / Savings-oriented (0.90). | These are NOT tiers. "Balanced" is unfortunately both a tier name and an operating-point name — when ambiguity is possible, say "the balanced tier" vs "the balanced threshold." |

**The sentence that uses them all correctly:** "At the conservative operating point, the adaptive policy routes 4 records to the cheap tier, and we compare that arm's conclusions against the reference arm."

---

## 3. Measurement words (precision matters most here)

| Term | Means | Don't confuse with |
|---|---|---|
| **Conclusion** | What a model returned for a record: its verdict + primary blocker. | NOT "outcome." Conclusions come from models. Outcomes happen in the real world. |
| **Outcome** | What happened in reality: the deal closed, stalled, died. We do NOT have outcome data in the demo. | Never say "the model's outcome." Models produce conclusions. |
| **Changed** | The verdict OR the blocker differs between the two arms for a record. Determined by exact string match on enums — a `!=`, no judgment involved. | NOT "improved." Changed = the answers differ. We never claim the premium answer is better. |
| **Improved** | Forbidden word in the demo, with one exception: describing the *future* — "with expert labels, changed becomes improved." | Never use it about our current results. |
| **Agreement** | % of records where both arms reached the same conclusion. Measures *consistency between arms*, not correctness. | High agreement does NOT mean the answers are right. It means the cheap tier reproduces the premium tier's answers. |
| **Exact match** | How we score: string equality on enum fields. Reproducible by anyone. | There is no LLM judging the results. Deliberately. |
| **Enum** | A fixed list of allowed values (ON_TRACK / AT_RISK / NO_ACTION_NEEDED). Both models must pick from the list — that's what makes comparison a `!=`. | Not free text. Free-text fields (next action, reasoning) are shown to humans, never auto-scored. |
| **Headline (metric)** | "Only X of 30 decisions changed when we bought more reasoning." The one number the demo is built around. | This is the buyer's framing (what did extra spend change?), which is fine for the headline. In methodology discussion, use the symmetric phrasing: "the two tiers reach different conclusions on X of 30 records." |

---

## 4. The policy's inputs

| Term | Means | Don't confuse with |
|---|---|---|
| **(Close) probability** | The CRM's confidence the deal closes (0–1). A business input we read, not something a model produces. | NOT model confidence. Our models never output a confidence number — deliberately. If asked, the only confidence number on screen is the CRM's. |
| **Settled** | A record whose action is already determined — probability very high (or very low). Reasoning can't change what happens Monday. | Settled ≠ simple. Settled is about certainty of the outcome path. |
| **(Decision) Complexity (Score)** | Count of active risk signals (no economic buyer, competitor present, legal blocked, …). Measures how much unresolved evidence must be reasoned over. | NOT probability. A deal can be uncertain and simple, or probable and messy. These are the two independent axes of the whole product. |
| **Threshold** | A cut-off inside the policy, e.g. "probability ≥ 0.95 → settled → cheap." The frontier is made by moving ONE threshold. | The threshold is a *parameter of* the policy, not the policy itself. |
| **Certainty veto** | The design rule that being settled overrides everything — even a strategic, complex deal routes cheap if it's settled. Runs first in the policy. | — |
| **Strategic floor** | Strategic accounts get at least the balanced tier — but the floor never overrides the certainty veto. | A floor, not a bypass. |

---

## 5. Evaluation lifecycle

| Term | Means | Don't confuse with |
|---|---|---|
| **Calibration (run)** | The dual-arm comparison — run occasionally on a sample to measure the frontier and pick an operating point. **This is what the demo shows.** | Not the daily operation. If a judge says "you're doubling cost," this is the answer: only during calibration. |
| **Runtime** | Daily operation: ONE arm only (adaptive). Each record gets one call at its assigned tier. Strictly cheaper than premium-everything. | — |
| **Recalibration** | Re-running calibration periodically because data drifts. Sample-sized, occasional. | — |
| **Frontier** | The measured trade-off table: for each operating point — cost, % cheap, decisions changed, agreement. The deliverable is this table, not one "correct" setting. | Not a predicted curve — three *measured* points. We don't draw a line through them. |
| **Dry run** | Running the policy arithmetic over the dataset with NO model calls — just checking the routing distributions. Free, instant. | Not the same as the offline fallback (below). |
| **Fallback (table)** | Real results pre-loaded into a table so the demo runs with zero live calls if WiFi/auth fails on stage. Same UI, canned data. | The data in it is real (from the calibration run) — "fallback" refers to connectivity, not fake numbers. |

---

## 6. The three layers (for the "what if all 30 are wrong?" question)

| Term | Means |
|---|---|
| **Layer 1 — Consistency** | What the demo measures: do the arms agree? Says nothing about correctness. |
| **Layer 2 — Expert labels** | Managers rate outputs blind (not knowing which arm produced which). Adjudicates: is the consensus right (on agreeing records)? Who won each disagreement? Only after this can "5 changed" become "N better, M worse" — the one place "improved" is earned. |
| **Layer 3 — Outcomes** | Reality as the rater: was the action taken, did the blocker materialize, did the deal close. Slow, noisy, free. NOT closed-won alone — deals close despite bad advice. |
| **Double duty** | The same expert labels both score the arms AND train the router (records with a signature that reliably favors premium teach the policy to send that signature premium). |

---

## 7. Platform words

| Term | Means | Don't confuse with |
|---|---|---|
| **Cortex** | Snowflake's AI feature family. Our model calls go through it. | — |
| **AI_COMPLETE / AISQL** | The current SQL functions for calling models in Snowflake (successor to `CORTEX.COMPLETE()`). We use these. | — |
| **Warehouse** | Snowflake's compute engine (ours: `COMPUTE_WH`). Costs money while running. | NOT a workspace (Snowsight UI folder) and NOT a database (where tables live). Three different things. |
| **CoCo / Cortex Code** | Snowflake's coding agent (CLI: `cortex`). We use it for building, it is not part of the product. | — |
| **EverOS** | The event-mandated memory layer. In our design: policy decisions logged as **Cases**; repeated patterns become **Skills**. It's the substrate for Layer 3 learning. | Integration is additive (we log to it), not load-bearing (routing doesn't depend on it). |
| **Snowflake's cost stack** | Their new GA controls: account spend aggregation, per-user limits, runaway-query cancellation. Governs accounts/users/queries. | It never looks *inside* a query at individual records. That gap is our product. Say "we sit on top, not beside." |

---

## 8. Forbidden words / phrases (quick check before speaking)

- **"Improved," "better," "wins"** about our results → say **"changed"** / "the conclusions differ"
- **"Ground truth"** about the premium arm → say **"reference implementation"**
- **"The model's outcome"** → say **"the model's conclusion"**
- **"Confidence"** about model output → models don't output confidence; only the CRM probability exists
- **"Savings dial"** framing for the slider → say **"how settled must a deal be before we stop paying for reasoning"**
- **A number you didn't measure** → "I don't know — I'd test it by X"

---

*Practice: each of you pick a hero record and explain its routing out loud using only terms from this sheet. If you reach for a word not on the sheet, either it belongs here (add it) or there's a more precise word already listed.*
