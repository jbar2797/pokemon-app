# Pokémon Card API — Cards Endpoints

**Status:** Draft for MVP
**Last updated:** 2025-08-27 22:42:38Z
**Scope:** Search cards, get card details, and fetch price history.
**Audience:** Frontend & tools that call the public HTTP API.

---

## Base URL (local/dev)

```
http://127.0.0.1:8001
```

> The API is served locally via `uv run poke-pricer api serve`. See **Local Smoke** at the end of this file.

---

## Authentication

- **None** for MVP (local/dev).
- CORS is permissive for MVP (allows any origin).

---

## Common Conventions

- **Dates** are strings in the form `YYYY-MM-DD HH:MM:SS` (naive, local project time).
- **IDs** are integer `card_id` values.
- Unless specified, responses are JSON and arrays are returned in a stable, intuitive order (e.g., price history is chronological).
- Errors follow FastAPI / Pydantic defaults with status codes like `404` (not found) or `422` (validation).

---

## Endpoints

### 1) Search Cards

**GET** `/v1/cards/search`

Search by fuzzy name prefix or fragment (e.g., "pik" matches **Pikachu**).

#### Query Parameters

| Name | Type | Required | Default | Notes |
|---|---|---|---|---|
| `q` | string | **Yes** | — | Text to search for. Short fragments are allowed. |

#### Response (200 OK)

Array of minimal card records:

```json
[
  { "card_id": 2, "name": "Pikachu", "set_code": "BASE", "number": "58/102" }
]
```

#### Errors

- `422 Unprocessable Entity` — missing or invalid `q` parameter.

#### Example

```bash
curl -fsS "http://127.0.0.1:8001/v1/cards/search?q=pik" | jq .
```

---

### 2) Card Details by ID

**GET** `/v1/cards/{id}`

Returns minimal card metadata plus **last observed price** and its source/date.

#### Path Parameters

| Name | Type | Required | Notes |
|---|---|---|---|
| `id` | integer | **Yes** | `card_id` of the card. |

#### Response (200 OK)

```json
{
  "card_id": 2,
  "name": "Pikachu",
  "set_code": "BASE",
  "number": "58/102",
  "last_price": 10.1,
  "last_date": "2025-02-02 00:00:00",
  "source": "csv"
}
```

#### Errors

- `404 Not Found` — no card with that `id` was found.

#### Example

```bash
curl -fsS "http://127.0.0.1:8001/v1/cards/2" | jq .
```

---

### 3) Card Price History

**GET** `/v1/cards/{id}/prices`

Returns historical prices for the given card. Chronological (oldest → newest).

#### Path / Query Parameters

| Name | In | Type | Required | Default | Notes |
|---|---|---|---|---|---|
| `id` | path | integer | **Yes** | — | `card_id` of the card. |
| `limit` | query | integer | No | _all available_ | Maximum number of rows to return. |

#### Response (200 OK)

```json
[
  { "date": "2025-02-01 00:00:00", "price": 9.9, "source": "csv" },
  { "date": "2025-02-02 00:00:00", "price": 10.1, "source": "csv" }
]
```

#### Errors

- `404 Not Found` — no card with that `id` was found.
- `422 Unprocessable Entity` — invalid `limit` (e.g., negative or too large).

#### Example

```bash
curl -fsS "http://127.0.0.1:8001/v1/cards/2/prices?limit=10" | jq .
```

---

## OpenAPI / Tags

These endpoints are tagged under **Cards** in the generated OpenAPI docs. If you run the server locally, you can visit:

- Swagger UI: `http://127.0.0.1:8001/docs`
- OpenAPI JSON: `http://127.0.0.1:8001/openapi.json`

---

## Local Smoke (Quick Start)

1. **Seed demo data and run the API**

   ```bash
   uv run poke-pricer db init
   uv run poke-pricer demo seed
   uv run poke-pricer api serve --host 127.0.0.1 --port 8001 --log-level warning
   ```

2. **Probe the endpoints** (new terminal):

   ```bash
   # Health
   curl -fsS http://127.0.0.1:8001/health | jq .

   # Search
   curl -fsS "http://127.0.0.1:8001/v1/cards/search?q=pik" | jq .

   # Details
   curl -fsS "http://127.0.0.1:8001/v1/cards/2" | jq .

   # Prices
   curl -fsS "http://127.0.0.1:8001/v1/cards/2/prices?limit=10" | jq .
   ```

> Tip: you also have `scripts/morning_check.sh` which seeds demo data, runs the API, and probes core endpoints automatically.

---

## Changelog

- **Sprint 16 (chg-0016):** Added `/v1/cards/search`, `/v1/cards/{id}`, and `/v1/cards/{id}/prices` with typed responses and tests.

---

## Notes & Future Work

- Sort & pagination for search results (MVP may omit or hard-limit).
- Add richer metadata (rarity, condition, grading, images) when available.
- Expand sources beyond CSV and unify timestamps / timezones.
