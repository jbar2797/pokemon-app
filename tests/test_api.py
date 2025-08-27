from __future__ import annotations

from fastapi.testclient import TestClient

from poke_pricer.api.app import app
from poke_pricer.db import init_db
from poke_pricer.services.seed import seed_demo


def _client() -> TestClient:
    # Use the default configured SQLite path; init and seed per test module
    init_db()
    seed_demo()
    return TestClient(app)


def test_health() -> None:
    client = _client()
    r = client.get("/health")
    assert r.status_code == 200
    js = r.json()
    assert js["status"] == "ok"
    assert "version" in js


def test_catalog_summary() -> None:
    client = _client()
    r = client.get("/v1/catalog/summary")
    assert r.status_code == 200
    js = r.json()
    want = {"total_cards", "total_prices", "min_date", "max_date", "sources"}
    assert want <= set(js.keys())


def test_top_movers() -> None:
    client = _client()
    r = client.get("/v1/reports/top-movers?k=2")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    if arr:
        keys = {
            "card_id",
            "name",
            "set_code",
            "number",
            "source",
            "price",
            "return_1d",
            "date",
            "bucket",
        }
        assert keys <= set(arr[0].keys())
