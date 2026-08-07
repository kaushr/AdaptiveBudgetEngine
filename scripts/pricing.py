"""Pricing constants — Snowflake Service Consumption Table, effective July 31, 2026.

Rates are the AI_COMPLETE rows (AISQL), in AI Credits per one million tokens.
Source: snowflake.com/legal-files/CreditConsumptionTable.pdf (verified Aug 6, 2026).
Note: the REST "Cortex Inference" table lists lower rates (e.g. llama3.1-8b at
0.11) — we call via AI_COMPLETE in SQL, so the AI_COMPLETE rows apply.
"""

# model -> (input_credits_per_1m, output_credits_per_1m)
CREDIT_RATES = {
    "llama3.1-8b": (0.132, 0.132),
    "mistral-large2": (1.20, 3.60),
    "claude-sonnet-4-5": (1.80, 9.00),
}

# Stated assumption for $ display: on-demand Enterprise, AWS us-west-2.
DOLLARS_PER_CREDIT = 3.00

TIER_MODEL = {
    "cheap": "llama3.1-8b",
    "balanced": "mistral-large2",
    "premium": "claude-sonnet-4-5",
}


def call_credits(model, input_tokens, output_tokens):
    ci, co = CREDIT_RATES[model]
    return (input_tokens * ci + output_tokens * co) / 1_000_000
