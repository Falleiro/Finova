# FINOVA — Personal Finance Agent
> Financial Intelligence & Oversight Virtual Assistant

## 🧠 Project Overview

FINOVA is a personal AI finance agent that monitors the user's bank accounts, credit cards, and investment portfolio in real time through the **Open Finance API**. It communicates exclusively via **Telegram** and operates autonomously: sending daily summaries, monthly reports, transaction alerts, and investment swing notifications — and responding to on-demand queries.

This is a **single-user system**. All data is private and belongs only to the owner.

---

## 🏗️ Architecture

```
Telegram Bot (webhook)
        │
        ▼
  FINOVA Agent Core
  ├── Intent Classifier     → routes user messages to the right handler
  ├── Scheduler Engine      → cron jobs for daily (8AM) and monthly (1st) reports
  └── Event Trigger Engine  → polls Open Finance API every 5 min for new events
        │
        ▼
  Subagents Layer
  ├── data-fetcher          → pulls data from Open Finance API
  ├── report-builder        → generates text summaries + charts
  ├── alert-engine          → detects transactions and investment swings
  └── telegram-sender       → formats and sends messages via Telegram Bot API
        │
        ▼
  Data Layer
  ├── Open Finance API      → real-time bank + investment data (read-only)
  └── Local SQLite DB       → transaction history, categories, user preferences
```

---

## 🛠️ Tech Stack

- **Language:** Python 3.11+
- **Telegram:** `python-telegram-bot` (v21+)
- **Scheduler:** `APScheduler`
- **Open Finance API:** REST client via `httpx` (async)
- **Charts:** `matplotlib` + `plotly`
- **Database:** `SQLite` via `SQLAlchemy` (local cache + history)
- **Environment:** `python-dotenv` for secrets
- **Tests:** `pytest`

---

## 📁 Project Structure

```
finova/
├── .venv/                       ← virtual environment (never commit — add to .gitignore)
├── Dockerfile                   ← multi-stage build for production
├── docker-compose.yml           ← local development environment
├── .dockerignore
├── .gitignore
├── .env                         ← secrets (never commit)
├── .env.example                 ← template for secrets (safe to commit)
├── requirements.txt
├── CLAUDE.md
├── .env                         ← secrets (never commit)
├── .env.example
├── requirements.txt
├── main.py                      ← entrypoint
├── .claude/
│   ├── agents/
│   │   ├── data-fetcher.md
│   │   ├── report-builder.md
│   │   ├── alert-engine.md
│   │   └── telegram-sender.md
│   └── commands/
│       ├── daily-summary.md
│       ├── monthly-report.md
│       └── investment-alert.md
├── src/
│   ├── __init__.py
│   ├── config.py                ← loads env vars
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── crud.py
│   ├── open_finance/
│   │   ├── __init__.py
│   │   ├── client.py            ← Open Finance API wrapper
│   │   ├── accounts.py
│   │   ├── transactions.py
│   │   └── investments.py
│   ├── telegram/
│   │   ├── __init__.py
│   │   ├── bot.py               ← bot setup and webhook
│   │   ├── handlers.py          ← message intent routing
│   │   └── formatter.py         ← message formatting helpers
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── jobs.py              ← daily + monthly cron definitions
│   │   └── runner.py
│   ├── triggers/
│   │   ├── __init__.py
│   │   ├── transaction_watcher.py
│   │   └── investment_watcher.py
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── daily.py
│   │   ├── monthly.py
│   │   └── charts.py
│   └── agents/
│       ├── __init__.py
│       ├── orchestrator.py      ← main agent coordinator
│       └── intent_classifier.py
└── tests/
    ├── test_open_finance.py
    ├── test_reports.py
    └── test_triggers.py
```

---

## 🔐 Environment Variables

All secrets live in `.env`. Never hardcode credentials. Required variables:

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Open Finance API
OPEN_FINANCE_CLIENT_ID=
OPEN_FINANCE_CLIENT_SECRET=
OPEN_FINANCE_BASE_URL=
OPEN_FINANCE_CONSENT_TOKEN=

# App Config
TIMEZONE=America/Sao_Paulo
DAILY_REPORT_TIME=08:00
LARGE_TRANSACTION_THRESHOLD=200
INVESTMENT_ALERT_THRESHOLD=3.0
POLL_INTERVAL_SECONDS=300

# Database
DATABASE_URL=sqlite:///./finova.db
```

---

## 🔑 Core Rules for Claude

1. **Docker-first environment.** All development runs inside Docker via `docker-compose up`. Never install packages globally. If running without Docker for a quick test, use `python3 -m venv .venv`. The production environment is Railway — a container built from the `Dockerfile` in this repo.
2. **Read-only access to financial data.** Never write, transfer, or modify financial records. Only read from the Open Finance API.
2. **Single user system.** There is only one TELEGRAM_CHAT_ID. Never expose data to other recipients.
3. **Async-first.** All I/O operations (API calls, DB queries, Telegram sends) must be `async/await`.
4. **Error resilience.** Every external call must have try/except with graceful fallback and user notification.
5. **No duplicate alerts.** Use the local DB to track which events have already been sent (deduplication by event_id).
6. **Chart images** go to a `/tmp/finova_charts/` directory and are deleted after sending.
7. **All monetary values** are stored as integers in cents (avoid float precision issues).
8. **Categories** are auto-assigned to transactions using keyword matching from `src/config.py`.
9. **Tests must pass** before any feature is considered complete. Run `pytest` to verify.
10. **Logs** use Python's `logging` module with level INFO. No print() statements in production code.

---

## 📋 Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Async functions: always prefixed understanding they're async (no special prefix needed, just use `async def`)

---

## 🚀 How to Run

### Environment Strategy

| Context | Method |
|---|---|
| Local development | `docker-compose up` |
| Local testing (no Docker) | `python3 -m venv .venv` |
| Production 24/7 | Deploy to **Railway** via GitHub |

---

### Local Development with Docker (recommended)

```bash
# 1. Copy and fill in your secrets
cp .env.example .env

# 2. Build and start the container
docker-compose up --build

# 3. Watch logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

---

### Local Development without Docker (quick testing only)

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

### Production Deploy — Railway

1. Push the project to a **private** GitHub repository
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. In Railway dashboard → **Variables** tab → add all keys from `.env.example`
5. In Railway dashboard → **Volumes** tab → add a volume mounted at `/app/data`
6. Railway detects the `Dockerfile` automatically and builds + deploys
7. Every `git push` to `main` triggers a new deploy automatically

> ⚠️ Never commit `.env` to GitHub. Use Railway's Variables panel for all secrets in production.

---

## 📌 Current Status

- [x] Project scaffold
- [x] Open Finance API client (`src/open_finance/` — auth, accounts, transactions, investments)
- [x] Telegram bot layer (`src/telegram/` + `src/agents/`)
- [x] Database — `src/database/models.py` + `crud.py` (Account, Transaction, Investment + AsyncSessionLocal + init_db)
- [x] Daily summary — `src/reports/daily.py` → `build_daily_summary()` retorna Markdown
- [x] Monthly report + charts — `src/reports/monthly.py` + `charts.py` → `build_monthly_report()` retorna `(str, path)`
- [x] Scheduler — `src/scheduler/runner.py` + `jobs.py` (APScheduler: 8h diário, dia 1 mensal)
- [x] Transaction trigger — `src/triggers/transaction_watcher.py` (polling 5min, alerta se > threshold)
- [x] Investment trigger — `src/triggers/investment_watcher.py` (polling 5min, alerta se ±3%)
- [x] Tests (pytest) — 21/21 passando
- [ ] Teste end-to-end no Telegram: /start, /saldo, /extrato, /carteira