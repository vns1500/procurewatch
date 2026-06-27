# ProcureWatch

> **Government procurement anomaly detection for India — built to surface corruption signals before they disappear into the gazette.**

ProcureWatch is an open-source civic-tech platform that ingests government tender data, runs a deterministic risk-scoring engine against it, and surfaces anomalies — single-bid awards, rushed timelines, vendor bid-splitting — through a real-time dashboard. It is purpose-built for India's public procurement ecosystem and designed to be deployed in minutes with a single Docker command.

---

## Table of Contents

- [Why ProcureWatch](#why-procurewatch)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Detection Rules](#detection-rules)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Services](#services)
- [Production Deployment](#production-deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Why ProcureWatch

India's public procurement market exceeds ₹45 lakh crore annually. A significant portion of irregularities — single-bid tenders, artificially split contracts, unnaturally short bidding windows — are detectable through structured signals in tender metadata alone. ProcureWatch automates this detection layer so journalists, civil society organizations, and watchdog agencies don't have to do it by hand.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser / Client                   │
└───────────────────────┬─────────────────────────────────┘
                        │  HTTP
┌───────────────────────▼─────────────────────────────────┐
│              Next.js Frontend  :3000                    │
└───────────────────────┬─────────────────────────────────┘
                        │  REST
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI Backend   :8000                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Rule Engine │  │  AI Analysis │  │  Ingestion   │  │
│  │  (scoring)   │  │  (Claude)    │  │  (scraper)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────┬──────────────────────────────────┬─────────────┘
         │                                  │
┌────────▼────────┐               ┌─────────▼────────────┐
│  PostgreSQL 16  │               │       Redis 7        │
│  + pgvector     │               │   (Celery broker)    │
└─────────────────┘               └──────────────────────┘
                                           │
                              ┌────────────▼─────────────┐
                              │  Celery Worker + Beat    │
                              │  (async tasks, cron)     │
                              └──────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (TypeScript) |
| Backend | FastAPI (Python, async) |
| Database | PostgreSQL 16 + pgvector |
| Cache / Broker | Redis 7 |
| Task Queue | Celery + Celery Beat |
| AI Analysis | Anthropic Claude API |
| Payments | Stripe |
| Email Alerts | Resend |
| Storage / Exports | Cloudflare R2 (optional) |
| Error Monitoring | Sentry (optional) |
| Containerization | Docker Compose (dev + prod) |

---

## Detection Rules

ProcureWatch ships with three high-signal anomaly rules out of the box. Each rule fires independently and contributes additively to a tender's overall risk score.

| Rule | Trigger Condition | Severity | Risk Score |
|---|---|---|---|
| `single_bid` | `bid_count = 1` AND `tender_value > ₹5,00,000` | `high` / `medium` | +35 |
| `rushed_timeline` | `close_date − tender_date < 3 days` | `critical` / `high` | +30 |
| `bid_splitting` | Same vendor wins 3+ tenders from the same ministry within 30 days | `high` | +40 |

A tender with all three flags active carries a cumulative risk score of **105**, placing it in the critical review queue. The rule engine is deterministic and auditable — no black-box ML, every flag can be explained in plain language.

---

## Quickstart

**Prerequisites:** Docker and Docker Compose installed on your machine.

```bash
# 1. Clone the repository
git clone https://github.com/vns1500/procurewatch.git
cd procurewatch

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (other fields have working defaults)

# 3. Start all services
docker-compose up --build -d

# 4. Open the dashboard
# http://localhost:3000
```

The `api-seed` service runs automatically on first boot and populates the database with **600+ synthetic tenders** across ministries, vendors, and states — so the dashboard is immediately usable without any external data source.

To watch the seed logs:

```bash
docker-compose logs -f api-seed
```

To stop all services:

```bash
docker-compose down
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the values below. Fields marked **required** must be set before the application will start correctly.

```bash
# ── Database ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://procure:procure@postgres:5432/procurewatch
POSTGRES_USER=procure
POSTGRES_PASSWORD=procure          # Change in production

# ── Redis ─────────────────────────────────────────────────
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=                    # Set in production

# ── AI  [REQUIRED] ────────────────────────────────────────
ANTHROPIC_API_KEY=                 # Your Anthropic API key

# ── Payments (Stripe) ─────────────────────────────────────
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# ── Email (Resend) ────────────────────────────────────────
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=alerts@procurewatch.in

# ── Application ───────────────────────────────────────────
ENVIRONMENT=development
SECRET_KEY=                        # Generate with: openssl rand -hex 32
ADMIN_API_KEY=procurewatch-admin-secret
ALLOWED_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# ── Optional integrations ─────────────────────────────────
SENTRY_DSN=                        # Error tracking
R2_ACCOUNT_ID=                     # Cloudflare R2 for exports
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_BUCKET=procurewatch-exports

# ── Scraping ──────────────────────────────────────────────
SCRAPE_PROXY_URL=
LOG_LEVEL=INFO
```

---

## API Reference

The FastAPI backend auto-generates interactive documentation at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns service status |
| `GET` | `/tenders` | List and filter tenders (pagination, search, risk score) |
| `GET` | `/dashboard/stats` | Aggregate statistics for the dashboard |
| `POST` | `/tenders/ingest` | Ingest raw scraped tender data |
| `POST` | `/tenders/seed` | Seed the database with synthetic tender data |

### Example: List tenders with filters

```bash
curl "http://localhost:8000/tenders?min_risk=70&severity=critical&page=1&limit=20"
```

### Example: Dashboard statistics

```bash
curl "http://localhost:8000/dashboard/stats"
```

### Example: Ingest raw data

```bash
curl -X POST "http://localhost:8000/tenders/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: procurewatch-admin-secret" \
  -d '{"tenders": [...]}'
```

---

## Services

| Service | Port | Description |
|---|---|---|
| `frontend` | 3000 | Next.js dashboard — main user interface |
| `api` | 8000 | FastAPI backend — rule engine, REST API |
| `postgres` | 5432 | PostgreSQL 16 with pgvector extension |
| `redis` | 6379 | Redis 7 — Celery message broker |
| `celery` | — | Async task worker (concurrency: 2) |
| `celery-beat` | — | Scheduled task runner (cron jobs) |
| `api-seed` | — | One-shot seed job (exits after first boot) |

All services are health-checked. The API will not start until PostgreSQL and Redis pass their readiness probes.

---

## Production Deployment

A production-hardened Compose configuration is included at `docker-compose.prod.yml`. It uses separate production Dockerfiles, disables hot-reload volumes, enforces `restart: always` on all services, and expects secrets from `.env.prod` rather than `.env`.

```bash
# 1. Create your production environment file
cp .env.example .env.prod
# Fill in all values with production credentials

# 2. Deploy
docker-compose -f docker-compose.prod.yml up --build -d
```

**Production checklist before going live:**

- Set a strong, unique `SECRET_KEY` (minimum 32 random bytes)
- Set a strong `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
- Replace `ADMIN_API_KEY` with a secret value
- Set `ENVIRONMENT=production`
- Configure `ALLOWED_ORIGINS` to your actual domain
- Point `NEXT_PUBLIC_API_URL` to your public API URL
- Add `SENTRY_DSN` for error tracking
- Set up a reverse proxy (Nginx / Caddy) in front of ports 3000 and 8000
- Enable TLS

---

## Project Structure

```
procurewatch/
├── backend/                  # Python / FastAPI
│   ├── api/
│   │   └── main.py           # FastAPI application entry point
│   ├── tasks/
│   │   └── celery_app.py     # Celery configuration
│   ├── Dockerfile            # Development image
│   └── Dockerfile.prod       # Production image
├── frontend/                 # TypeScript / Next.js
│   ├── Dockerfile            # Development image
│   └── Dockerfile.prod       # Production image
├── .env.example              # Environment variable template
├── .env.prod                 # Production environment (git-ignored)
├── docker-compose.yml        # Development stack
├── docker-compose.prod.yml   # Production stack
└── README.md
```

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for non-trivial changes.

```bash
# Fork and clone
git clone https://github.com/<your-username>/procurewatch.git
cd procurewatch

# Create a feature branch
git checkout -b feature/your-feature-name

# Start the dev stack
cp .env.example .env
docker-compose up --build -d

# Make your changes, then open a PR against main
```

Areas where contributions are especially valuable: additional detection rules, support for new data sources (GEM portal, CPPP, state-level portals), improved risk-score explainability, and export/report generation.

---

## License

This project is open source. See [LICENSE](LICENSE) for details.

---

> Built for transparency in public spending. If this tool is useful to you — as a journalist, researcher, or civic technologist — consider starring the repository and sharing it with your network.
