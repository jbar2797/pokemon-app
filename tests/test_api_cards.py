# tests/test_api_cards.py
from __future__ import annotations

from starlette.testclient import TestClient

from poke_pricer.api.app import app

client = TestClient(app)


def test_card_search_smoke() -> None:
    # Should accept ?q=... and return 200 even if dataset is minimal
    resp = client.get("/v1/cards/search", params={"q": "pik"})
    assert resp.status_code == 200


def test_card_by_id_404() -> None:
    # Nonexistent ID should return 404
    resp = client.get("/v1/cards/9999999")
    assert resp.status_code == 404
