# src/poke_pricer/client.py
from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Any, Literal, TypedDict, cast

import requests

__all__ = ["PokemonAPIError", "Holding", "PokemonClient"]


class PokemonAPIError(RuntimeError):
    """Raised when the API returns an error HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class Holding(TypedDict):
    """Holding item used by the portfolio endpoint."""

    card_id: int
    quantity: float


class PokemonClient:
    """
    Minimal typed Python SDK client for the Pokemon Pricer API.

    Usage:
        from poke_pricer.client import PokemonClient, Holding

        with PokemonClient() as client:
            print(client.health())
            positions = [{"card_id": 2, "quantity": 3.0}]
            print(client.portfolio_value(positions))
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()
        self._own_session = session is None
        self._session.headers.setdefault("User-Agent", "pokemon-sdk/0.1")

    # Context manager -----------------------------------------------------

    def __enter__(self) -> PokemonClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        # Always close the session we created ourselves; do not swallow exceptions.
        if self._own_session:
            self._session.close()
        return False

    # Low-level request helpers ------------------------------------------

    def _request_json(
        self,
        method: Literal["GET", "POST"],
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        resp = self._session.request(
            method,
            url,
            params=params,
            json=json_payload,
            timeout=self._timeout,
        )
        if resp.status_code >= 400:
            # surface text as-is; API returns JSON bodies but string is fine for users
            raise PokemonAPIError(resp.status_code, resp.text)
        return resp.json()

    def _get_json_obj(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        val = self._request_json("GET", path, params=params)
        if not isinstance(val, dict):
            typ = type(val).__name__
            raise PokemonAPIError(
                -1,
                f"Expected JSON object from GET {path}, got {typ}",
            )
        return cast(dict[str, Any], val)

    def _get_json_list(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        val = self._request_json("GET", path, params=params)
        if not isinstance(val, list):
            typ = type(val).__name__
            raise PokemonAPIError(
                -1,
                f"Expected JSON array from GET {path}, got {typ}",
            )
        # Ensure list items are objects (not strings/numbers)
        out: list[dict[str, Any]] = []
        for i, item in enumerate(val):
            if not isinstance(item, dict):
                t = type(item).__name__
                raise PokemonAPIError(
                    -1,
                    f"Expected list of objects from GET {path}; item {i} is {t}",
                )
            out.append(cast(dict[str, Any], item))
        return out

    def _post_json_obj(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        val = self._request_json("POST", path, params=params, json_payload=json_payload)
        if not isinstance(val, dict):
            typ = type(val).__name__
            raise PokemonAPIError(
                -1,
                f"Expected JSON object from POST {path}, got {typ}",
            )
        return cast(dict[str, Any], val)

    # High-level API methods ---------------------------------------------

    def health(self) -> dict[str, Any]:
        return self._get_json_obj("/health")

    def catalog_summary(self) -> dict[str, Any]:
        return self._get_json_obj("/v1/catalog/summary")

    # Cards
    def cards_search(self, q: str) -> list[dict[str, Any]]:
        return self._get_json_list("/v1/cards/search", params={"q": q})

    def card_detail(self, card_id: int) -> dict[str, Any]:
        return self._get_json_obj(f"/v1/cards/{card_id}")

    def card_prices(self, card_id: int, *, limit: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return self._get_json_list(f"/v1/cards/{card_id}/prices", params=params)

    # Portfolio
    def portfolio_value(self, holdings: Sequence[Holding]) -> dict[str, Any]:
        payload = {"holdings": list(holdings)}
        return self._post_json_obj("/v1/portfolio/value", json_payload=payload)
