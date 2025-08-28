# Portfolio API

This document describes the **Portfolio** endpoints exposed by the Pokemon Pricer HTTP API.
It complements the core endpoints (`/health`, `/v1/catalog/summary`, `/v1/reports/top-movers`) and the **Cards** endpoints documented in `docs/API_CARDS.md`.

> **Base URL (local dev):** `http://127.0.0.1:8001`

---

## Endpoints (Summary)

| Method | Path                               | Purpose                                      |
|-------:|------------------------------------|----------------------------------------------|
|  POST  | `/v1/portfolio/value`              | Compute current portfolio value from holdings |

---

## Schemas

### Request — `POST /v1/portfolio/value`

**Body (JSON):**

```json
{
  "holdings": [
    { "card_id": 2, "quantity": 3.0 },
    { "card_id": 1, "quantity": 1.0 }
  ]
}
```

- `holdings`: **required**. A list of items you own.
  - `card_id`: integer, **required**. Must match an existing card id in the catalog.
  - `quantity`: number, **required**, must be `> 0`.

### Response — `POST /v1/portfolio/value`

```json
{
  "total_value": 40.3,
  "positions": [
    {
      "card_id": 2,
      "name": "Pikachu",
      "set_code": "BASE",
      "number": "58/102",
      "quantity": 3.0,
      "price": 10.1,
      "value": 30.3,
      "date": "2025-02-02 00:00:00",
      "source": "csv"
    },
    {
      "card_id": 1,
      "name": "Charizard",
      "set_code": "BASE",
      "number": "4/102",
      "quantity": 1.0,
      "price": 10.0,
      "value": 10.0,
      "date": "2025-01-01 00:00:00",
      "source": "csv"
    }
  ],
  "missing_card_ids": []
}
```

- `total_value`: Sum of `value` across all returned positions.
- `positions`: One entry per input `card_id` that had a known latest price.
  - `value = quantity * price` (price is the latest known per card).
- `missing_card_ids`: Any `card_id`s from the request that were **not** found in the catalog (these are ignored in `positions` and `total_value`).

---

## Examples

### cURL

> Before running: seed demo data and start the API:
>
> ```bash
> uv run poke-pricer db init
> uv run poke-pricer demo seed
> uv run poke-pricer api serve --host 127.0.0.1 --port 8001 --log-level warning
> ```

Now compute value for 3× Pikachu (id=2) and 1× Charizard (id=1):

```bash
curl -sS -X POST "http://127.0.0.1:8001/v1/portfolio/value" \
  -H "Content-Type: application/json" \
  -d '{
        "holdings": [
          {"card_id": 2, "quantity": 3.0},
          {"card_id": 1, "quantity": 1.0}
        ]
      }' | jq .
```

### JavaScript (fetch)

```js
const body = {
  holdings: [
    { card_id: 2, quantity: 3.0 },
    { card_id: 1, quantity: 1.0 },
  ],
};

const res = await fetch("http://127.0.0.1:8001/v1/portfolio/value", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

if (!res.ok) {
  throw new Error(`HTTP ${res.status}`);
}
const data = await res.json();
console.log(data.total_value, data.positions);
```

---

## Status Codes

- **200 OK** — result returned.
- **422 Unprocessable Entity** — invalid JSON or missing/invalid fields.
- **500 Internal Server Error** — unexpected error on the server.

---

## Notes & Limitations (MVP)

- Prices are taken from the **latest** known price per card in the local catalog.
- If a card id is unknown, it is listed under `missing_card_ids` and ignored in the total.
- No persistence of portfolios — this is a **stateless** computation endpoint for MVP.

---

## Changelog

- **Sprint 17 (chg-0017)** — Initial Portfolio API (`POST /v1/portfolio/value`).
