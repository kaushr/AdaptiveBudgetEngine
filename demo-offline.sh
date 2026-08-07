#!/usr/bin/env bash
# Demo, offline mode (the default demo path): reads data/results/*.csv,
# zero network, zero Snowflake, zero model calls.
# Pinned to 8501 so offline and live (8502) can run side by side.
cd "$(dirname "$0")"
exec .venv/bin/streamlit run app/streamlit_app.py --server.port 8501
