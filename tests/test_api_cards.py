# tests/test_api_cards.py
from __future__ import annotations

from fastapi.testclient import TestClient

from poke_pricer.api.app import app

client = TestClient(app)


def test_card_search_smoke() -> None:
    r = client.get("/v1/cards/search", params={"q": "pik"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any("pik" in item["name"].lower() for item in data)


def test_card_by_id_404() -> None:
    r = client.get("/v1/cards/999999")
    assert r.status_code == 404


def test_card_prices_smoke() -> None:
    r = client.get("/v1/cards/2/prices", params={"limit": 10})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "price" in data[0]
