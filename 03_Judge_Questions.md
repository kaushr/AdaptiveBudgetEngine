# Judge Questions — Prep Sheet

Read the morning of. Answer in two or three sentences and stop talking. Over-explaining a good answer reads as defensiveness.

**Three things to never say:** that the premium model is correct, that the changed decisions were better, or a number you didn't measure.

---

## Tier 1 — you will get these

### "Isn't this just an if statement?"

Today, deliberately — every routing decision has to be explainable and auditable. The interesting part isn't the branching, it's what the branches key on. In production the policy would be learned from expert labels and observed outcomes rather than hand-set.

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

---

## Tier 3 — the hard ones

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
