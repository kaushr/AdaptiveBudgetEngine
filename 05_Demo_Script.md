# Demo Script — T14 (two presenters · target: under 2:45)

**PAYAL** opens with the elevator pitch; **KAUSHIK** runs the demo walkthrough;
both field Q&A. Every number below is from the measured run (`RUN_SUMMARY`,
Aug 7). Projections are labeled projected. Say "changed," never "improved."
The dead-deal line is Q&A armor — NOT in the flow.

Screen state at start: slider at **0.98 · Conservative**, hero selector on
**settled**.

**Q&A split:** Payal takes business/value questions (elevator variants, "who
buys this," "why now"); Kaushik takes measurement/technical (dead deals, call
counts, EverOS, the prompt contract).

---

## Beat 0 — PAYAL · The elevator pitch *(~0:00–0:41)*

> A sales manager with thirty deals hires an expensive consultant to review every one, every week. On most deals, he looks for two minutes and says what the junior analyst would have said for free. On a few messy ones, he genuinely earns the fee. The waste isn't hiring the consultant — it's hiring him for deals where a glance was enough. Decision Budget Engine is the rule that decides, per deal, who reviews it — from information the manager already has, and never the deal's size.
>
> Kaushik will show you what that looks like, measured.

*(Do NOT fold in the Snowflake-differentiation two-liner here — it's Q&A armor,
in the judge doc's elevator section.)*

## Beat 1 — KAUSHIK · The bill *(~0:41–0:55)*

> Here's that consultant bill, measured: twenty-one cents for this run — projected, about seventy-two dollars a week at ten thousand records. The amber card: premium spend on decisions that were already made.

## Beat 2 — KAUSHIK · The slider *(~0:55–1:40)* — move 0.98 → 0.95 → 0.90, back to 0.98

> How settled must a deal be before we stop paying? A dial, not a doctrine.
>
> At Conservative, cost drops to **53 percent** of reference and **only 4 of 30 decisions changed**. Verdict agreement is **90 percent** — measured, and we show it.
>
> *(point at pinned record)* This **$2.4M** record — 93 percent probability, complexity four — goes premium, premium, **cheap** as the threshold loosens. Deal size never enters the rule.
>
> What you're watching is the calibration run — the thing you do once to choose your policy. Every day after this, only the adaptive arm runs, and this measured table is why you can trust it.

## Beat 3 — KAUSHIK · Where reasoning still pays *(~1:40–2:00)* — select **contestable**

> So where does reasoning still pay? This contested **$750K** claims pilot. The cheap tier sees the departed champion — the loudest flag. Premium reads the same record and finds the real blocker: nobody owns the budget decision. Same workload, different business context, different reasoning budget.

## Beat 4 — KAUSHIK · Frontier, method, close *(~2:00–2:36)*

> Thirteen, twenty, thirty percent routed cheap; four, six, nine changed; cost fifty-three down to forty-five percent. Pick your point. Every decision — signals, tier, result — logs to EverOS: the memory a learned policy trains on.
>
> For this prototype, the premium model is our reference implementation, not truth. In production we'd evaluate against expert labels and actual business outcomes.
>
> *(pause)* Enterprise AI shouldn't spend the same intelligence on every decision. It should spend where additional reasoning can still change the outcome.

---

## Q&A armor (ready, not in the flow)

**Dead deals** (KAUSHIK) — *"Two of your changed records are dead deals."* Two moves: concede the composition, then pivot to the design property. (~20s)
> Correct — two of the four are dead deals, marked not-consequential in the drill-down. But note the direction: they were routed cheap precisely because nothing can change what happens to them — an error there has no blast radius. The veto routes cheap exactly where being wrong is safest, and the column proves it with data.

**Same question, non-technical judge** (PAYAL, ~15s):
> The junior analyst and the consultant disagreeing about a dead deal changes nobody's Monday. Disagreeing about a live deal changes who the rep calls tomorrow. Consequential marks the second kind — and only two of our four disagreements are that kind.

*If anyone touches the 4-of-30, this is the best sixty seconds of the day: an unplanned finding that became evidence the veto works. Have it in your mouth, not just on this page.*

**"Do you actually use EverOS?"** (KAUSHIK) — show, don't describe. Run in a terminal:
```bash
python3 scripts/everos_log.py --search "OPP-008"
```
Live retrieval of that record's routing story with relevance scores. While it
runs, the one-liner: *"Snowflake is where the decisions are made and audited;
EverOS is where the system remembers them — and that memory is what turns
today's hand-set thresholds into tomorrow's learned policy."* Full answer in
the judge doc ("How do you actually use EverOS?").

**"Doesn't Snowflake already do this?" / differentiation** (PAYAL) — the
two-liner lives in the judge doc's elevator section; don't spend it in the
pitch.

Everything else: `03_Judge_Questions.md`. Re-read it the morning of.

## Timing — calibrated to 135 wpm (presentation pace under pressure)

| Beat | Speaker | Words | Time | Cumulative |
|---|---|---|---|---|
| 0 · Elevator | PAYAL | 96 | 0:43 | 0:43 |
| 1 · Bill | KAUSHIK | 32 | 0:14 | 0:57 |
| 2 · Slider | KAUSHIK | 106 | 0:47 (incl. slider moves) | 1:44 |
| 3 · Contestable | KAUSHIK | 45 | 0:20 | 2:04 |
| 4 · Frontier + close | KAUSHIK | 81 | 0:36 | 2:40 |

**Total 360 words ≈ 2:40 at 135 wpm** (a few of those are silent stage
directions, so spoken is ~2:36) — inside 2:45 with the reserve compressions
untouched. C1 (amber-card compression) and C3
(the "different Monday" sentence) are already taken — they're baked into the
text above.

**Compression points still in reserve** if a rehearsal runs over:

| # | Where | Cut | Saves |
|---|---|---|---|
| R1 | Beat 2, pin | Drop to a pointing gesture + "premium, premium, cheap — size never enters the rule." | ~12 words / 5s |
| R2 | Beat 4 | "Pick your point. Every decision … trains on." → "Pick your point — every decision logs to EverOS." | ~15 words / 7s |

**Never cut:** the calibration sentence, the methodology statement, the
closing line, the plainly-spoken 90 percent — and Payal's handoff line.

## Rehearsal notes

- **The handoff is the highest-risk seam** in a two-presenter demo. Rehearse
  the transition specifically, at least twice: Payal's "…what that looks like,
  measured" must interlock with Kaushik's "Here's that consultant bill,
  measured" with no gap — the repeated word is the latch.
- **Payal should say her 40 seconds out loud a few times solo** — she's
  picking up a script she didn't write, an hour before delivery.
- Three clean full runs under 2:45 before submitting (workbook T15).
