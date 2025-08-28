# tests/test_api_portfolio.py
from __future__ import annotations

from fastapi.testclient import TestClient

from poke_pricer.api.app import app

client = TestClient(app)


def test_portfolio_value_smoke() -> None:
    body = {"holdings": [{"card_id": 2, "quantity": 3.0}]}
    r = client.post("/v1/portfolio/value", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "total_value" in data
    assert data["total_value"] > 0
    assert isinstance(data.get("positions", []), list)
    assert any(p["card_id"] == 2 for p in data["positions"])
