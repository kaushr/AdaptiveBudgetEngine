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
   smoke test on venue WiFi. Tonight's results stay committed as the tested
   offline fallback; Friday's run becomes the live data. **Cost ~$0.30 of trial
   credit, ~10 minutes total** — no-hesitation decision:
   ```bash
   cd scripts
   rm ../data/results/call_cache.json   # force fresh calls (cache would no-op)
   python3 run_arms.py --heroes         # sanity: heroes land as authored (~1 min)
   python3 run_arms.py                  # remaining calls (~6 min)
   python3 summarize.py && python3 load_snowflake.py && python3 everos_log.py
   ```
   If venue WiFi fights: stop, keep the offline fallback, move on — it's the
   tested path and the demo needs nothing live.
1. **Rehearse 3× under 2:45** ([05_Demo_Script.md](05_Demo_Script.md)) — the only
   open workbook exit item. Full script is 2:43 at 135 wpm (zero slack); rehearse
   the compressed version (2:23) at least once. Time every run.
2. **EverOS on venue WiFi:** run
   `cd scripts && python3 everos_log.py --search "OPP-013 routing decision"` —
   confirm retrieval works from the venue. If it doesn't: the Aug 6 retrieval
   output is committed in the session history — screenshot fallback, and say so
   plainly if asked.
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
