# Friday — before 11:00

Everything below is verification, not building. If any check fails, the fix is
the first build-block task.

1. **Rehearse 3× under 2:45** ([05_Demo_Script.md](05_Demo_Script.md)) — the only
   open workbook exit item. Full script is 2:43 at 135 wpm (zero slack); rehearse
   the compressed version (2:23) at least once. Time every run.
2. **EverOS on venue WiFi:** run
   `cd scripts && python3 everos_log.py --search "OPP-013 routing decision"` —
   confirm retrieval works from the venue. If it doesn't: the Aug 6 retrieval
   output is committed in the session history — screenshot fallback, and say so
   plainly if asked.
3. **Demo machine click-through:** `.venv/bin/streamlit run app/streamlit_app.py`
   (offline path, zero dependencies) — all three slider stops, all three heroes,
   all three expanders, once.
4. **Reconciliation Q&A armor (optional, 2 min):** Thursday's calls will have
   landed in `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY` by morning —
   run the workbook §6 reconciliation query; if totals line up, that's one
   sentence of armor ("our ledger reconciles against Snowflake's").
5. **Discord (nice-to-have):** Function Studio availability; whether EverOS
   judging expects visible Skills behavior beyond the retrievable decision log.

Hard marks: **2:30 PM feature stop** (workbook) · **4:00 PM hard submission
deadline** (event page). Re-read [03_Judge_Questions.md](03_Judge_Questions.md)
in the morning — answers work only in your own voice.
