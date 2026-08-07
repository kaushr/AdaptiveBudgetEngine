#!/usr/bin/env bash
# Decision Budget Engine — Intellinomics
# Built at the Snowflake x Beta Fund AI Token Economics Hackathon, Aug 2026
# MIT License — see LICENSE
# Demo, live mode: same UI reading the five result tables from
# DECISION_BUDGET.DEMO. Still zero model calls — AI_COMPLETE exists only in
# scripts/run_arms.py. Needs snowflake-connector-python in .venv and
# .streamlit/secrets.toml (see README). Mode is a launch decision on purpose:
# the Source line is a provenance claim, not a view preference.
# Pinned to 8502 so live and offline (8501) can run side by side.
cd "$(dirname "$0")"
exec env DBE_SOURCE=snowflake .venv/bin/streamlit run app/streamlit_app.py --server.port 8502
