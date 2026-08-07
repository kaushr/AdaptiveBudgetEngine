# Demo Script — T14 (target: under 2:45)

Every number below is from the measured run (`RUN_SUMMARY`, Aug 6). Projections
are labeled projected. Say "changed," never "improved." The dead-deal line is
Q&A armor — NOT in the flow.

Screen state at start: slider at **0.98 · Conservative**, hero selector on
**settled**.

---

## Beat 1 — The bill *(~0:00–0:35)*

> A sales manager reviews thirty opportunities every week. One workload — and workload-level optimization would pick one model for all of it. Today's default sends every record to the premium model. Here's the bill: twenty-one cents for this run — projected at ten thousand records a week, about seventy-two dollars, every week, for this one workload.
>
> The amber card is the part that should bother you: premium spend on decisions that were **already made** — records so settled the cheap tier reaches identical conclusions.

## Beat 2 — The slider *(~0:35–1:25)* — move slider 0.98 → 0.95 → 0.90, then back to 0.98

> One control: how settled must a deal be before we stop paying for reasoning? Three measured operating points — this is a dial, not a doctrine.
>
> At Conservative, cost drops to **53 percent** of reference and **only 4 of 30 decisions changed**. Verdict agreement is **90 percent** — measured, and we show it.
>
> *(point at pinned record)* This record: **$2.4M**, 93 percent probability, complexity four. Deal size never changes — and across the three thresholds its tier goes premium, premium, **cheap**. We are not routing by deal size. Certainty vetoes spend.
>
> What you're watching is the calibration run — the thing you do once to choose your policy. Every day after this, only the adaptive arm runs, and this measured table is why you can trust it.

## Beat 3 — Where reasoning still pays *(~1:25–2:05)* — select **contestable** hero

> So where does reasoning still pay? This contested **$750K** claims pilot. The cheap tier sees the departed champion — the loudest flag in the record. The premium tier reads the same record and finds the real blocker: **nobody currently owns the budget decision**. Different conclusions, different Monday for that rep.
>
> Same workload, different business context, different reasoning budget.

## Beat 4 — The frontier, the method, the close *(~2:05–2:40)*

> The whole frontier: **13, 20, 30 percent** routed cheap; **4, 6, 9** decisions changed; cost **53 down to 45 percent** of reference. An enterprise picks its point on this curve — and every routing decision, with its signals, tier, and result, is logged to EverOS: the memory substrate a learned policy trains on.
>
> For this prototype, the premium model is our reference implementation, not truth. In production we'd evaluate against expert labels and actual business outcomes.
>
> *(pause)* Enterprise AI shouldn't spend the same intelligence on every decision. It should spend where additional reasoning can still change the outcome.

---

## Q&A armor (ready, not in the flow)

**Dead deals** — *"Two of your changed records are dead deals."* Two moves: concede the composition, then pivot to the design property. (~20s)
> Correct — two of the four are dead deals, marked not-consequential in the drill-down. But note the direction: they were routed cheap precisely because nothing can change what happens to them — an error there has no blast radius. The veto routes cheap exactly where being wrong is safest, and the column proves it with data.

**Same question, non-technical judge** (~15s):
> The junior analyst and the consultant disagreeing about a dead deal changes nobody's Monday. Disagreeing about a live deal changes who the rep calls tomorrow. Consequential marks the second kind — and only two of our four disagreements are that kind.

*If anyone touches the 4-of-30, this is the best sixty seconds of the day: an unplanned finding that became evidence the veto works. Have it in your mouth, not just on this page.*

**"Do you actually use EverOS?"** — show, don't describe. Run in a terminal:
```bash
python3 scripts/everos_log.py --search "OPP-008"
```
Live retrieval of that record's routing story with relevance scores. While it
runs, the one-liner: *"Snowflake is where the decisions are made and audited;
EverOS is where the system remembers them — and that memory is what turns
today's hand-set thresholds into tomorrow's learned policy."* Full answer in
the judge doc ("How do you actually use EverOS?").

Everything else: `03_Judge_Questions.md`. Re-read it the morning of.

## Timing notes — calibrated to 135 wpm (presentation pace under pressure)

Full script is 367 words ≈ **2:43 at 135 wpm — zero slack.** Rehearse the full
version once to hear it, then decide per beat. Three compression points, in the
order to take them; **rehearse the compressed version at least once** so it's
in your mouth if the timer's running hot:

| # | Where | Replace | With | Saves |
|---|---|---|---|---|
| C1 | Beat 1, ¶2 | the whole amber-card paragraph | "The amber card: premium spend on decisions that were already made." | ~20 words / 9s |
| C2 | Beat 2, pin | the whole pinned-record passage | "This $2.4M record — 93 percent probability, complexity four — goes premium, premium, cheap as the threshold loosens. Deal size never enters the rule." | ~18 words / 8s |
| C3 | Beat 3 | "Different conclusions, different Monday for that rep." | *(cut)* | ~8 words / 4s |

All three taken: **321 words ≈ 2:23 at 135 wpm** — comfortable slack for slider
moves and the pause.

**Never cut:** the calibration sentence, the methodology statement, the closing
line, or the plainly-spoken 90 percent.

Three clean rehearsal runs under 2:45 before submitting (workbook T15).
