# ProcureWatch

Government procurement anomaly detection system for India.

## Quickstart (3 commands)

```bash
cp .env.example .env
docker-compose up --build -d
# Visit http://localhost:3000
```

The `api-seed` service auto-seeds 600+ synthetic tenders on first boot.

## Services

| Service      | Port | Description                    |
|--------------|------|--------------------------------|
| frontend     | 3000 | Next.js dashboard              |
| api          | 8000 | FastAPI backend                |
| postgres     | 5432 | PostgreSQL 16 + pgvector       |
| redis        | 6379 | Redis 7 (Celery broker)        |
| celery       | —    | Async task worker              |
| celery-beat  | —    | Scheduled task runner          |

## API Endpoints

- `GET /tenders` — list/filter tenders
- `GET /dashboard/stats` — dashboard statistics
- `POST /tenders/ingest` — ingest raw scraped data
- `POST /tenders/seed` — seed database with synthetic data
- `GET /health` — health check

## Detection Rules

| Rule              | Threshold                         | Severity      | Risk +  |
|-------------------|-----------------------------------|---------------|---------|
| `single_bid`      | bid_count=1 AND value>₹5L        | high/medium   | +35     |
| `rushed_timeline` | close_date - tender_date < 3 days | critical/high | +30     |
| `bid_splitting`   | 3+ wins same vendor+ministry/30d  | high          | +40     |
