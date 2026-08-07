# Decision Budget Engine — Setup Doc

**Living document — update as we go.** This gets a new dev machine from zero to "can run the build" with no interactive prompts required.

Last updated: Aug 6, 2026 (Kaushik's machine, verified working end to end — Snowflake and EverMind both tested)

---

## Event facts (from the Luma page)

**Snowflake × Beta Fund × Evermind Agent & Token Economy Hackathon** — Menlo Park, CA. Teams of 1–2.

- **Track we're entering: Track 1 — "Cost of Intelligence" (cheaper AI execution)** — direct fit for Decision Budget Engine. (Other tracks: Value of Intelligence, Wildcard.)
- **Requirement: every team must build with EverMind infrastructure** — *"using EverOS for memory, personalization, context, or learning layers, while leveraging Snowflake."* This was missed in initial planning and only caught when we read the event page directly. **Treat the event page as the source of truth — re-read it end to end before Friday; don't rely on secondhand summaries.** See §12 for our verified EverOS setup.
- **Schedule:** 9:00 check-in → 10:00–11:00 workshops → 11:00–4:00 build (lunch at 12) → 4:00–5:00 demos (**3-minute limit**) → 5:00 voting/awards. The workbook timeline (11:00 start, 2:30 hard stop, 2:45 demo target) maps onto this.
- **Prizes:** $600 / $500 / $400 + $200 standout (with UpScaleX 1:1).
- **Partner credits:** Snowflake (Cortex access + credits), EverMind (EverOS credits + engineering support).

---

## 0. What you're setting up

- A Snowflake trial account (AI Data Cloud, not the CoCo-only signup)
- Snowflake CLI (`snow`) authenticated via key pair — no passwords, no MFA prompts on every run
- Cortex Code CLI (`cortex`)
- The Snowflake Cortex Code plugin for Claude Code
- Cost guardrails so nobody's card gets charged

Do this in order. Steps depend on each other.

---

## 1. Create the Snowflake account

Go to the signup link from the event (has `regcode=ATTENDSUMMIT26` in the URL — use that exact link, not a generic Snowflake signup, so the event promo attaches).

When it asks you to choose an account type:

- **Choose "AI Data Cloud"**, not "CoCo." CoCo-only signup gives you a lightweight coding-agent account with a smaller credit allowance and no real platform underneath it. AI Data Cloud gives you the full account — warehouses, databases, Cortex `COMPLETE()`, Streamlit — plus $400 in trial credits, which is what we need.

When it asks for edition and region:

- **Edition: Enterprise** (same free trial, no feature gates we might hit later)
- **Cloud: AWS, Region: US West (Oregon)** — broadest Cortex model availability, lowest latency from the Bay Area

Activate via the email link.

---

## 2. Install the CLIs

You need two separate CLIs — don't confuse them:

- `cortex` — the Cortex Code agentic coding tool
- `snow` — the Snowflake CLI, used for running SQL, managing connections, creating warehouses/databases

### Cortex Code CLI
Install per Snowflake's official install script for your OS (see docs.snowflake.com → Cortex Code CLI). Verify:

```bash
cortex --version
```

### Snowflake CLI

**On Mac, use Homebrew** — pip is a common failure point (broken/orphaned Python environments, e.g. leftover Anaconda shims):

```bash
brew install snowflake-cli
snow --version
```

If `pip install snowflake-cli` is your only option and it fails with something like `bad interpreter: No such file or directory`, don't debug the old Python — just use Homebrew instead.

---

## 3. Install the Claude Code plugin

Inside a Claude Code session (or via `claude` CLI):

```bash
claude plugin install snowflake-cortex-code@claude-plugins-official
```

Or in-session: `/plugins` → find "Snowflake Cortex Code" → install.

This plugin auto-detects Snowflake-flavored prompts in Claude Code and routes them to the `cortex` CLI. It requires `cortex` to already be on PATH (step 2) and a working connection (step 4) to actually do anything.

---

## 4. Set up the Snowflake connection

### 4a. Get your account identifier

Snowsight (browser) → click your name, bottom-left → **Account** → copy account identifier. Format looks like `TBITDZY-OQ97319` (org-accountname).

### 4b. Initial connection (password, temporary)

```bash
snow connection add
```

Answer prompts:
- name: `default`
- account: your identifier from 4a
- user: your Snowflake username (**not necessarily your email** — check Snowsight profile page if unsure)
- password: your password
- role: `ACCOUNTADMIN`
- warehouse: `COMPUTE_WH`
- database / schema / host / port / protocol / region: leave blank
- **authenticator: leave blank** (do NOT enter `externalbrowser` — that's for SSO/SAML accounts and will fail with a SAML IdP error on a plain trial account)
- everything else: blank

Test:
```bash
snow connection test
```

If you get `Incorrect username or password`, double check the username in Snowsight (profile page), not your email.

### 4c. Switch to key-pair auth (recommended — do this before Friday)

Password auth breaks the moment MFA gets enforced on the account (see §5), and typing a password for every one of Friday's dozens of script runs is a bad time anyway. Set up a key pair once:

```bash
cd ~/.snowflake
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out sf_key.p8 -nocrypt
openssl rsa -in sf_key.p8 -pubout -out sf_key.pub
cat sf_key.pub
```

Copy everything between (not including) the `-----BEGIN PUBLIC KEY-----` / `-----END PUBLIC KEY-----` lines, joined into one continuous string (no line breaks).

In **Snowsight → Projects → Workspaces** (older UI: Worksheets), open a SQL file with role `ACCOUNTADMIN` and warehouse `COMPUTE_WH` selected, then run:

```sql
ALTER USER <your_username> SET RSA_PUBLIC_KEY='<paste the one-line public key here>';
```

Verify it registered:
```sql
DESC USER <your_username>;
```
Look for `RSA_PUBLIC_KEY_FP` with a value.

### 4d. Edit config.toml to use the key

```bash
nano ~/.snowflake/config.toml
```

Your `[connections.default]` block should look like this — **every value needs double quotes**, and delete the `password` line entirely:

```toml
[connections.default]
account = "TBITDZY-OQ97319"
user = "YOUR_USERNAME"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "DECISION_BUDGET"
schema = "DEMO"
authenticator = "SNOWFLAKE_JWT"
private_key_file = "/Users/YOUR_MAC_USERNAME/.snowflake/sf_key.p8"
```

Common mistakes that break this file:
- Missing quotes around any value → `Configuration file seems to be corrupted` error
- Accidentally duplicating a key (e.g. `private_key_file=private_key_file = "..."` from a bad paste) → same corruption error, check the exact line the error points to

Test:
```bash
snow connection test
```
Should return a clean status table with no password prompt, ever again.

---

## 5. Handle MFA (if it triggers)

Adding a credit card (§7) can flip the account into enforcing MFA on password logins. If `snow connection test` suddenly says `Multi-factor authentication is required`:

1. In Snowsight → your profile → **Authentication** → **Add authentication method** → set up a TOTP authenticator (Google Authenticator, 1Password, etc.)
2. This satisfies the *account's* MFA requirement for browser login.
3. Your CLI is unaffected once you're on key-pair auth (§4c/4d) — key-pair auth doesn't go through the password/MFA path at all. This is the main reason to set up key-pair auth early rather than fighting MFA prompts all week.

---

## 6. Create the project database

```bash
snow sql -q "CREATE DATABASE DECISION_BUDGET; CREATE SCHEMA DECISION_BUDGET.DEMO;"
```

If your `config.toml` already sets `database = "DECISION_BUDGET"` and `schema = "DEMO"` (§4d), scripts won't need to fully qualify table names.

---

## 7. Enable Cortex (AI functions) — the trial gate

Fresh trial accounts block `SNOWFLAKE.CORTEX.COMPLETE()` with:
```
AI function COMPLETE is not available for trial accounts.
```

This is a **billing gate, not a region gate.** Fix:

1. Snowsight → **Admin → Cost Management → Billing** (or profile → Billing) → add a payment method (card).
2. You will see a **temporary authorization hold** (not a real charge) on the card — this is normal, it verifies the card and should drop off in a few days.
3. Wait a few minutes for the restriction to lift, then retry.

You do NOT need to change cross-region settings for this specific error, but it's harmless to also run:
```bash
snow sql -q "ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION'"
```
(Broadens which regions can serve a model call — worth doing regardless.)

### Use `AI_COMPLETE`, not legacy `CORTEX.COMPLETE()` (verified Aug 6, 2026)

Snowflake's newer AISQL functions are the current interface — `AI_COMPLETE` verified working with all three locked models on this account. **Use `AI_COMPLETE` everywhere;** `SNOWFLAKE.CORTEX.COMPLETE()` also works but is the legacy path.

```bash
snow sql -q "SELECT AI_COMPLETE('llama3.1-8b', 'Say OK')"
snow sql -q "SELECT AI_COMPLETE('mistral-large2', 'Say OK')"
snow sql -q "SELECT AI_COMPLETE('claude-sonnet-4-5', 'Say OK')"
```

**Findings from testing (don't re-test):**

- **Model name must be a string literal.** `AI_COMPLETE(CASE tier WHEN ... END, prompt)` fails to compile (`needs to be a string literal`). Per-row routing in a single statement instead uses one branch per tier, unioned — the tier expression lives in the `WHERE`:
  ```sql
  SELECT opp_id, 'cheap' AS tier, AI_COMPLETE('llama3.1-8b', prompt) FROM opps WHERE tier='cheap'
  UNION ALL
  SELECT opp_id, 'balanced', AI_COMPLETE('mistral-large2', prompt) FROM opps WHERE tier='balanced'
  UNION ALL
  SELECT opp_id, 'premium', AI_COMPLETE('claude-sonnet-4-5', prompt) FROM opps WHERE tier='premium'
  ```
  Verified working. This is still the "per-row tier expression evaluated against columns already in the table" story from the judge prep — the routing predicate is SQL over business columns; only the model binding is per-branch.
- **Token usage comes back in-band:** `AI_COMPLETE(model => '...', prompt => '...', show_details => TRUE)` returns JSON with `usage.prompt_tokens` / `completion_tokens` / `total_tokens` plus the model name — workbook T8 (usage capture) needs no separate mechanism.

**Tier mapping locked in:**

| Tier | Model |
|---|---|
| cheap | `llama3.1-8b` |
| balanced | `mistral-large2` |
| premium | `claude-sonnet-4-5` |

Known bad names (don't waste time retrying): `claude-3-5-sonnet`, `claude-3-7-sonnet`, `claude-4-sonnet` — wrong format, all return `unknown model`.

If you need to check what's actually available on your account, `SHOW MODELS IN ACCOUNT` returns nothing useful (that command lists custom ML models you've registered, not the Cortex catalog) — just test candidate name strings directly.

---

## 8. Cost guardrails

Real risk here is *not* Cortex spend — a full 30-record, 2-arm run (60 short LLM calls) costs pennies of credit. The real risk is an idle warehouse left running. Do all of these:

### 8a. Auto-suspend every warehouse (the one that actually matters)

```bash
snow sql -q "SHOW WAREHOUSES"
```

Trial accounts typically provision three: `COMPUTE_WH`, `SNOWFLAKE_LEARNING_WH`, `SYSTEM$STREAMLIT_NOTEBOOK_WH`. Set all to suspend after 60s idle:

```bash
snow sql -q "ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 60"
snow sql -q "ALTER WAREHOUSE SNOWFLAKE_LEARNING_WH SET AUTO_SUSPEND = 60"
```
(`SYSTEM$STREAMLIT_NOTEBOOK_WH` is usually already at 60s.)

**All scripts and `snow sql` calls should run against `COMPUTE_WH` only** — it's the default in `config.toml`, so this is automatic as long as you don't create additional warehouses.

### 8b. Resource monitor — hard suspend on warehouse compute

```bash
snow sql -q "CREATE RESOURCE MONITOR HACKATHON_CAP WITH CREDIT_QUOTA=100 FREQUENCY=MONTHLY START_TIMESTAMP=IMMEDIATELY TRIGGERS ON 75 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND_IMMEDIATE"
snow sql -q "ALTER ACCOUNT SET RESOURCE_MONITOR = HACKATHON_CAP"
```

100 credits ≈ way more warehouse compute than this project will use, comfortably under the $400 trial limit. This governs *warehouse* spend only — does not cover serverless Cortex calls.

### 8c. Budget — covers Cortex/serverless spend

Snowsight → **Admin → Cost Management → Budgets** → create an account-level budget (e.g. $300) with email alerts. This is a notify-only guardrail, not a hard stop, but it's the only mechanism that watches serverless AI spend.

### 8d. Habit

Check **Admin → Cost Management** in Snowsight at the end of each work session. Expect near-zero credit consumption at our scale — if you see something unexpected, stop and investigate before continuing.

### 8e. After the hackathon

Remove the card or drop the account once submitted, so nothing can roll into paid usage after the 30-day trial window.

---

## 9. Verify everything end to end

```bash
snow connection test
snow sql -q "SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', 'Say OK')"
```

Then in Claude Code, ask in plain language:
> "Show me my Snowflake warehouses"

If it routes through the plugin → `cortex` CLI → your connection and returns real warehouse data, the entire chain (plugin, CLI, auth, account) is proven working.

---

## 10. Known gotchas (so we don't re-debug these)

| Symptom | Cause | Fix |
|---|---|---|
| `SAML Identity Provider account parameter` error | `authenticator = externalbrowser` set on a non-SSO account | Remove/leave blank |
| `Incorrect username or password` | Using email instead of actual Snowflake username | Check Snowsight profile page for real username |
| `Configuration file seems to be corrupted` | Missing quotes or duplicated key in `config.toml` | Quote every value; check the exact line number in the error |
| `AI function COMPLETE is not available for trial accounts` | No card on file | Add card in Billing, wait a few minutes |
| `Multi-factor authentication is required` (CLI) | Card added → account now enforces MFA on password logins | Enroll MFA in Snowsight (for browser login) + switch CLI to key-pair auth (bypasses this entirely) |
| `unknown model "..."` from `COMPLETE()` | Wrong Cortex model name string | Use confirmed names in §7; don't guess Anthropic's own model-naming convention |
| `pip install snowflake-cli` fails, `bad interpreter` | Broken/orphaned Python env (e.g. dead Anaconda symlink) | Use `brew install snowflake-cli` instead |

---

## 11. Still open / to fill in

- [x] ~~Pricing constants~~ — resolved from the official Service Consumption Table (effective July 31, 2026), AI_COMPLETE rows, credits per 1M tokens in/out: llama3.1-8b 0.132/0.132 · mistral-large2 1.20/3.60 · claude-sonnet-4-5 1.80/9.00. Encoded in `scripts/pricing.py` with $3.00/credit (Enterprise on-demand, AWS us-west-2) as the stated $ assumption.
- [ ] Function Studio availability — ask in event Discord
- [x] ~~Repo scaffold + fallback table mechanism~~ — done; `data/results/*.csv` is the offline fallback, `DBE_SOURCE` flag switches the UI to Snowflake.
- [x] ~~UI framework decision~~ — Streamlit confirmed and built (`app/streamlit_app.py`, venv at `.venv/` on Python 3.11 — do NOT use the pyenv 3.8 shim, it's too old for Streamlit).
- [ ] **EverOS integration depth** — confirm how "deep" the integration needs to be to satisfy the requirement (logging Cases may be enough — or judges may expect visible Skills/learning behavior in the demo). Ask in event Discord, alongside the Function Studio question; EverMind is offering engineering support, so there may be a sanctioned low-lift path.
- [ ] **Test the EverOS Claude Code plugin** as a fast integration path (see §12).

*(Resolved: Cloud vs local runtime — Cloud, tested end to end Aug 6. Integration point — `POLICY_DECISIONS` → Cases, additive not load-bearing. See §12.)*

---

## 12. EverMind / EverOS (event requirement — verified working Aug 6, 2026)

The event **requires** every team to build with EverMind's EverOS (memory / personalization / context / learning layer). Account created and cloud API tested end to end.

### What it is

EverOS is an agent memory layer: you feed it conversation messages (or documents), it asynchronously extracts structured "episodes" and atomic facts, and you retrieve them via semantic search. Two deployment options:

- **EverOS Cloud** (managed, zero ops) — API at `https://api.evermind.ai`. **This is what we use** — decided and verified working (see below); no local server to babysit on demo day, and EverMind is providing credits.
- **Open-source local runtime** ([github.com/EverMind-AI/EverOS](https://github.com/EverMind-AI/EverOS)) — local-first Python library; storage stack is Markdown (source of truth) + SQLite (state/queues) + LanceDB (vectors/BM25). Not our path, documented for completeness.

Core mechanism worth knowing for the demo story: agent activity is recorded as **Cases**; repeated patterns get distilled into reusable **Skills** — procedural memory that improves over time instead of starting from scratch. EverOS also ships a Claude Code plugin marketplace, worth checking as a fast integration path.

### Where it fits our architecture

The policy's decision log is the natural integration point. `POLICY_DECISIONS` writes (tier selected, reason, evidence, whether the arms' conclusions agreed) map onto EverOS Cases; if repeated patterns self-promote to Skills, that's a live, small-scale demonstration of the exact "production policy would be learned from expert labels and observed outcomes" answer already in `03_Judge_Questions.md` Tier 1.

**Integration should be additive, not load-bearing** — the core routing logic doesn't need to run *through* EverOS, it just needs to *feed* it. Scope this as a few added lines in workbook tasks T6/T9, not a redesign.

### Auth

- API key from the [everos.evermind.ai](https://everos.evermind.ai) dashboard.
- Stored in `local/evermind.env` (the `local/` folder is gitignored — key never enters the repo or the docs) as `EVERMIND_API_KEY=...`
- Sent as a Bearer token: `Authorization: Bearer $EVERMIND_API_KEY`

### Verified round trip (all three tested)

```bash
source local/evermind.env

# 1. Add — NOTE: returns {"status":"queued"} — extraction is ASYNC
curl -sS -X POST https://api.evermind.ai/api/v2/memory/add \
  -H "Authorization: Bearer $EVERMIND_API_KEY" -H "Content-Type: application/json" \
  -d "{\"session_id\": \"s1\", \"user_id\": \"kaushik\",
       \"messages\": [{\"role\": \"user\", \"sender_id\": \"kaushik\",
                       \"timestamp\": $(date +%s)000, \"content\": \"...\"}]}"

# 2. Flush — forces extraction so search can find it immediately
curl -sS -X POST https://api.evermind.ai/api/v2/memory/flush \
  -H "Authorization: Bearer $EVERMIND_API_KEY" -H "Content-Type: application/json" \
  -d '{"session_id": "s1", "user_id": "kaushik"}'

# 3. Search — returns episodes with summaries + atomic_facts + relevance scores
curl -sS -X POST https://api.evermind.ai/api/v2/memory/search \
  -H "Authorization: Bearer $EVERMIND_API_KEY" -H "Content-Type: application/json" \
  -d '{"query": "...", "user_id": "kaushik"}'
```

### API gotchas (all hit and solved during setup — don't re-debug)

| Symptom | Cause | Fix |
|---|---|---|
| 400 `sender_id is required` | Each message needs `sender_id`, not just `role` | Add `"sender_id"` to every message object |
| 400 `cannot unmarshal string ... timestamp of type int64` | ISO-8601 timestamp string | Timestamp must be numeric |
| 422 `must be a unix millisecond timestamp` | Seconds instead of milliseconds | Use epoch **ms**: `$(date +%s)000` |
| Search returns nothing right after add | `add` only queues; extraction is async | Call `/api/v2/memory/flush` first (returns `{"status":"extracted"}`) |

**Caution on extracted summaries:** the extraction model paraphrases and can embellish — our literal test message "setup test ... says OK" came back as the project "had been approved." Fine for memory/context retrieval; do not treat extracted summaries as verbatim records in anything user-facing.
