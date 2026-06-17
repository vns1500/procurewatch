"""Smoke tests — verify the API boots and core endpoints respond."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    from backend.api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health_ok(client):
    with patch("backend.api.main.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(return_value=AsyncMock(scalar_one=lambda: 0))
        mock_session_cls.return_value = mock_session

        with patch("redis.asyncio.from_url") as mock_redis:
            mock_r = AsyncMock()
            mock_r.ping = AsyncMock()
            mock_r.aclose = AsyncMock()
            mock_redis.return_value = mock_r

            resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


@pytest.mark.anyio
async def test_dashboard_stats(client):
    resp = await client.get("/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "flagged_this_month" in data
    assert "total_tenders_scanned" in data
    assert "suspicious_value" in data


@pytest.mark.anyio
async def test_tenders_list(client):
    resp = await client.get("/tenders")
    assert resp.status_code == 200
    data = resp.json()
    assert "tenders" in data
    assert "total" in data


@pytest.mark.anyio
async def test_vendors_list(client):
    resp = await client.get("/vendors")
    assert resp.status_code == 200
    data = resp.json()
    assert "vendors" in data


@pytest.mark.anyio
async def test_anomalies_list(client):
    resp = await client.get("/anomalies")
    assert resp.status_code == 200
    data = resp.json()
    assert "anomalies" in data


@pytest.mark.anyio
async def test_reports_list(client):
    resp = await client.get("/reports")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_alerts_list(client):
    resp = await client.get("/alerts")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_billing_plans(client):
    resp = await client.get("/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert "plans" in data
    assert "free" in data["plans"]
    assert "pro" in data["plans"]


@pytest.mark.anyio
async def test_security_headers(client):
    resp = await client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"


@pytest.mark.anyio
async def test_report_generate_requires_tenders(client):
    resp = await client.post("/reports/generate", json={"tender_ids": [], "report_type": "full"})
    assert resp.status_code == 422
