# Dataset Schema (Workbook T1)

## `OPPORTUNITIES` — one row per sales opportunity

| Column | Type | Notes |
|---|---|---|
| `opp_id` | TEXT | `OPP-001` … `OPP-030` |
| `name` | TEXT | Account + deal shorthand |
| `amount` | NUMBER | Deal size, USD. **Never a policy input** — its absence from the policy is the point. |
| `probability` | FLOAT | CRM close probability, 0–1. Policy input (certainty veto). |
| `stage` | TEXT | `DISCOVERY` · `QUALIFICATION` · `PROPOSAL` · `NEGOTIATION` · `CONTRACT` |
| `strategic_account` | BOOLEAN | Policy input (floor, never a bypass) |
| `no_economic_buyer` | BOOLEAN | Risk signal 1 |
| `competitor_present` | BOOLEAN | Risk signal 2 |
| `security_legal_blocked` | BOOLEAN | Risk signal 3 |
| `procurement_not_started` | BOOLEAN | Risk signal 4 |
| `champion_risk` | BOOLEAN | Risk signal 5 — champion departed or weakened |
| `inactive_21d` | BOOLEAN | Risk signal 6 — must agree with `days_since_activity > 21` |
| `conflicting_signals` | BOOLEAN | Risk signal 7 — notes/stage contradict each other or the probability |
| `days_since_activity` | NUMBER | Kept consistent with `inactive_21d` by a generator assertion |
| `close_date` | DATE | Timeline texture |
| `notes` | TEXT | CRM-style free text. Records with `conflicting_signals=TRUE` contain a visible contradiction. |

**Decision Complexity Score** = count of TRUE risk signals (0–7). 0–1 low · 2–3 medium · 4+ high. Deterministic, no model involved.

## AI task output schema (per model call)

| Field | Values |
|---|---|
| `verdict` | `ON_TRACK` · `AT_RISK` · `NO_ACTION_NEEDED` |
| `primary_blocker` | `ECONOMIC_BUYER` · `SECURITY_LEGAL` · `PROCUREMENT` · `COMPETITION` · `PRICING` · `CHAMPION_LOSS` · `INACTIVITY` · `NONE` |
| `next_best_action` | Free text, exactly one action |
| `reasoning` | Free text, grounded in record evidence |

The model never outputs a confidence score — CRM probability is a policy input only.

## Language rule (load-bearing)

In data notes, code comments, UI copy, and docs: decisions **changed** between arms — never "improved," "better," or "won." Changed is measured; improved is not.
