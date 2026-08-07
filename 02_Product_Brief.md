# Decision Budget Engine

**A runtime business policy that allocates the right reasoning tier to each individual decision within a workload.**

---

## In one sentence

Workload-level optimization picks the best model for a task. Decision Budget Engine decides how much intelligence each individual business record within that task deserves.

---

## The problem

Enterprises are converging on a single answer to AI cost: evaluate a workload once, pick the cheapest model that clears a quality bar, apply it to everything. It's a real advance over sending everything to the frontier model, and the tooling for it is arriving fast.

It also has a blind spot. Within one workload, the records aren't equally worth reasoning about.

A sales manager reviewing 30 opportunities asks the same question of every one: *can I trust this forecast, what's the biggest risk, and what should I do next?* That's one workload. But a $5M renewal at 99% with legal complete and no competitor is a decision that's already made — no amount of additional reasoning changes what the rep does Monday. A $400K expansion at 52% with a stalled security review, an absent economic buyer, and a competitor circling is a decision that better reasoning genuinely moves.

Workload optimization gives both the same model. That's either overspending on the first or underserving the second, and usually both.

---

## Why now

Cost governance for AI has matured quickly — and Snowflake itself just shipped the strongest version of it. Cortex AI Functions cost management is now GA: account-level spend aggregation with threshold alerts, per-user monthly spending limits with automatic access revocation, and runaway-query detection and cancellation. Add the older layer — spend visibility, chargeback, budgets — and every level of the hierarchy is governed: the account, the user, the query.

Every level except one. Nothing in that stack decides whether a given **record inside a query** deserved the tokens it consumed. Account, user, and query controls answer *who spent what, and should they be allowed to.* That's consumption control, and it's necessary.

None of it answers *was this particular inference worth buying.* As agent execution volume grows from thousands to millions of calls, a per-workload default can become a major source of overspend wherever the records inside that workload vary widely in how much they're worth reasoning about. The blind spot isn't an abstract claim — it's visible in the current GA feature set: the governance hierarchy stops one level above where the money is actually spent.

---

## How this is different

**Traditional workload optimization**

```
Opportunity Analysis workload
            |
            v
      One selected model
            |
            v
      All 30 opportunities
```

**Decision Budget Engine**

```
Opportunity Analysis workload
            |
            v
   Adaptive Business Policy
            |
            +--> Opportunity A  -->  cheap
            +--> Opportunity B  -->  premium
            +--> Opportunity C  -->  balanced
            +--> Opportunity D  -->  cheap
```

Same workload. Different business context. Different reasoning budget.

This is a layer, not a replacement:

```
Workload-level model evaluation
   "What's the best model for Opportunity Analysis?"
                    +
Decision Budget Engine
   "Which opportunities actually deserve that model?"
```

---

## How it works

**Input:** business context from CRM — amount, close probability, stage, activity recency, stakeholder coverage, competitor presence, blockers, champion status, notes, timeline.

**Decision Complexity Score:** a deterministic count of active risk signals. Explicitly distinct from close probability — probability is how confident the business is, complexity is how much unresolved evidence must be reasoned over. A deal can be uncertain and simple, or probable and messy.

**Policy:** rules-based and explainable. Certainty checks run first and can veto spend. Strategic importance sets a floor but never bypasses certainty — a settled strategic deal still routes cheap. There is no direct multiplier on deal size anywhere in the logic.

**Explainability:** every routing decision returns the selected tier, the reason, the business evidence used, and the thresholds applied. Nothing is a black box.

The prototype policy is deliberately simple so it can be read aloud and audited. A production policy would be learned from expert labels and observed outcomes.

---

## How we measure

Two arms run over the same 30 opportunities in one script:

- **Reference Policy** — every record to the premium model
- **Adaptive Business Policy** — tier selected per record

The headline is not cost savings. It's:

> **Only X of 30 decisions changed when we bought more reasoning.**

That number is measured, not asserted. A decision *changed* when the verdict or the primary blocker differs between arms — both scored by exact match against fixed enums, automatically.

Supporting: verdict agreement, blocker agreement, total cost per arm, and premium spend on records where nothing changed.

**On methodology:** the premium model is a reference implementation, not ground truth. In production we'd evaluate against expert labels and closed-won outcomes. We say **changed**, never **improved** — changed is measurable, improved is not.

**Three operating points** — conservative, balanced, savings-oriented — produced by varying one threshold with the policy logic held constant. The output isn't a single correct answer; it's a frontier an enterprise tunes to its own risk tolerance.

---

## Why Snowflake

The business context already lives in the warehouse. Routing on business signals means reading the same tables that feed the BI, which puts the policy next to the data instead of in a separate service with its own copy of the truth.

Every routing decision, model output, token count, cost, and explanation writes back to Snowflake — so the audit trail for *why this record got this much intelligence* sits in the same governed place as the spend it produced.

And because the spend surface is also Snowflake's, our numbers reconcile against theirs by construction: token counts in `MODEL_RUNS` roll up to the same totals Snowflake reports in `CORTEX_FUNCTIONS_USAGE_HISTORY`, per model. Cost governance sees the query; this system explains the records inside it — same ledger, one level deeper. It sits on top, not beside.

---

## Demo

**Setup.** A manager reviews 30 opportunities, all in one workload. Reference Policy sends every one to the premium model. Here's the bill.

**The proof.** Move the probability slider from uncertain to settled. Deal size never changes. The reasoning tier drops. *This isn't routing by deal size — the workload hasn't changed, only the business context of this one decision.*

**The story.** The $5M renewal at 99%. Reference: premium. Adaptive: cheap. Same verdict, same action. *Same workload, different business context, different reasoning budget.* Then the contestable mid-market deal, where the two tiers visibly diverge and the premium answer synthesizes the conflicting signals better.

**The evidence.** Decisions changed. Agreement. Cost. Frontier. Methodology statement.

**Close:** *Enterprise AI shouldn't spend the same intelligence on every decision. It should spend where additional reasoning can still change the outcome.*

---

## Expected questions

**Isn't this just an if statement?**
Today, deliberately — every routing decision has to be explainable and auditable. The interesting part isn't the branching, it's what the branches key on. In production the policy would be learned from expert labels and observed outcomes rather than hand-set: the system tries a tier, records whether the decision actually changed, and updates its own allocation rule over time. That's a contextual bandit — an algorithm that balances exploiting the tier it currently believes is right against occasionally testing a different one to keep learning.

**Doesn't Snowflake already do cost optimization?**
Yes, at the workload and user level — quotas, attribution, model selection per function. Those answer who spent what and which model fits a task. This answers a different question: within one task, which records deserve the reasoning. It sits on top rather than beside.

**How do you know the cheap answers are good?**
We don't claim they're good — we measure whether they're different. Verdict and blocker are scored by exact match against the premium arm. Where they differ, we show it. The premium model is a reference implementation, not truth, and we're explicit about that.

**What if agreement is low?**
Then you move along the frontier. Three operating points, one threshold, same logic. The product isn't one correct policy — it's a tunable one.

**Why route on probability rather than deal value?**
Because deal value doesn't predict whether reasoning changes anything. A large settled deal is the clearest case of overspend in the whole dataset, and a size-based policy gets it exactly backwards.

**What's the path to production?**
Outcome labels — but not closed-won alone, since a deal can close in spite of bad advice. You'd want expert review of the recommendations plus signals on whether the suggested action was taken and what followed. With that, "changed" becomes "improved," the policy becomes learnable, and the frontier becomes an optimization rather than a setting.

---

## What we are not claiming

- Not that the premium model is correct
- Not that the changed decisions were better decisions
- Not a computed ROI on reasoning — that requires outcome data we don't have yet
- Not a replacement for workload-level model evaluation or spend governance

The prototype proves one thing: business context within a workload predicts whether additional reasoning changes the answer. That's enough to build on.
