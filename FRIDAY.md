# Friday — before 11:00

## Submission (deadline 4:00 PM HARD — start at 3:30 regardless of state)

The event page specifies the 4:00 PM deadline and 1–2 builders per team but
**no submission format** — confirm the mechanism (form? Luma? on-site?) at
morning check-in or in Discord, first thing.

Pre-staged tonight:
- [ ] **Repo**: add the remote and push (`git remote add origin <url> && git push -u origin main --tags`). README is the judge-facing front page.
- [ ] **Write-up**: README.md doubles as it (pitch, measured frontier table, how to run, requirement compliance). If a separate form field wants prose, paste README's first two sections.
- [ ] **Video**: not known to be required — stretch only, never before rehearsal.
- **3:30 trigger**: whatever state the build is in, start submitting. The
  workbook's hard-stop philosophy, applied to the deadline.

**Rollback point**: tag `pre-hackathon-stable` = tonight's tested state
(offline demo verified in a fresh venv). If the morning re-run or any edit
breaks something: `git reset --hard pre-hackathon-stable` and demo the
offline path.

---

Everything below is verification, not building. If any check fails, the fix is
the first build-block task.

0. **Re-run the full pipeline during build hours** — refreshes every timestamp
   in Snowflake and EverOS, so "we ran this today, here's the query history" is
   the answer instead of explaining Thursday timestamps. Doubles as the live-path
   smoke test on venue WiFi. **Cost ~$0.30 of trial credit, ~10-12 minutes** —
   no-hesitation decision:
   ```bash
   ./rebuild.sh
   ```
   One command: wipes the five tables + result CSVs (backing them up to
   `data/results.pre-rebuild.bak/` first; git also has them), re-runs the 61
   calls with full narration, rescores, reloads Snowflake, re-logs EverOS, and
   diffs the new numbers against the committed run — flagging any drift the
   demo script would need to absorb. Add `--quiet` for a terse rerun.
   **Known behaviors, not failures:** EverOS flush may report `no_extraction`
   once before succeeding on a retry — expected async extraction, the script
   retries automatically. OPP-008's cheap-tier blocker is bistable across runs
   (COMPETITION vs SECURITY_LEGAL), so the 0.90 changed-count prints 8 or 9 —
   if the final RESULT block flags drift, sync the two spoken numbers before
   rehearsing: Beat 4's frontier recital in the demo script, and the waste-card
   question ("...when N decisions changed") in the judge doc. 0.98/0.95 have
   been stable across all runs. **If a stage fails partway:** stages are
   independently runnable — fix, then resume without re-burning model calls,
   e.g. `cd scripts && python3 rebuild.py --stage load --stage everos --stage compare`
   (calls are cached; even `--stage calls` re-spends nothing that succeeded).
   If venue WiFi fights: `git checkout -- data/results/` restores the offline
   fallback, and the demo needs nothing live.
1. **Rehearse 3× under 2:45** ([05_Demo_Script.md](05_Demo_Script.md)) — the only
   open workbook exit item. Full script is 2:43 at 135 wpm (zero slack); rehearse
   the compressed version (2:23) at least once. Time every run.
2. **EverOS on venue WiFi:** run
   ```bash
   python3 scripts/everos_log.py --search "OPP-008"
   ```
   — confirm retrieval works from the venue. This exact command is also the
   Q&A response to "do you actually use EverOS?" (showing retrieval beats
   describing it — see the script's Q&A appendix). It fails gracefully with a
   one-line message if offline; if the venue blocks it, say so plainly and
   fall back to describing the logged sessions.
3. **Demo machine setup — launch BOTH, present from live:** run
   `./demo-offline.sh` (port 8501, tab "DBE · OFFLINE") and `./demo-live.sh`
   (port 8502, tab "DBE · LIVE") in two terminals at setup. Click through the
   live tab once — all three slider stops, heroes, expanders. **Present from
   the live tab;** if WiFi or Snowflake hiccups mid-demo, Cmd+Tab to the
   offline tab — same screen, same numbers, no restart. The Source badge and
   the tab title both say which one you're on.
4. **Reconciliation Q&A armor (optional, 2 min):** Thursday's calls will have
   landed in `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY` by morning —
   run the workbook §6 reconciliation query; if totals line up, that's one
   sentence of armor ("our ledger reconciles against Snowflake's").
5. **Discord (nice-to-have):** Function Studio availability; whether EverOS
   judging expects visible Skills behavior beyond the retrievable decision log.

Hard marks: **2:30 PM feature stop** (workbook) · **4:00 PM hard submission
deadline** (event page). Re-read [03_Judge_Questions.md](03_Judge_Questions.md)
in the morning — answers work only in your own voice.
