#!/usr/bin/env bash
# Clean-slate rebuild: wipe all outputs, re-run the 61 model calls, rescore,
# reload Snowflake, re-log EverOS, verify, and diff against committed numbers.
# Narrates everything by default; --quiet for reruns, --full-prompts for
# untruncated prompts. ~10-12 minutes, ~$0.30 of trial credit.
cd "$(dirname "$0")/scripts"
exec python3 rebuild.py "$@"
