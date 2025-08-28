# src/poke_pricer/api/app.py
from __future__ import annotations

import pandas as pd
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..analytics.data_access import load_prices_df
from ..analytics.movers import compute_top_movers
from ..catalog.stats import catalog_summary_df

# -------------------------------
# Pydantic models (request/response)
# -------------------------------


class HealthResponse(BaseModel):
    status: str
    version: str


class CatalogSummary(BaseModel):
    total_cards: int
    total_prices: int
    min_date: str
    max_date: str
    sources: str


class MoverItem(BaseModel):
    card_id: int
    name: str
    set_code: str
    number: str
    source: str
    price: float
    return_1d: float
    date: str
    bucket: str


class CardSearchItem(BaseModel):
    card_id: int
    name: str
    set_code: str
    number: str


class CardDetail(BaseModel):
    card_id: int
    name: str
    set_code: str
    number: str
    last_price: float
    last_date: str
    source: str


class CardPricePoint(BaseModel):
    date: str
    price: float
    source: str


class HoldingIn(BaseModel):
    card_id: int
    quantity: float


class PortfolioValueRequest(BaseModel):
    holdings: list[HoldingIn]


class PositionValue(BaseModel):
    card_id: int
    name: str
    set_code: str
    number: str
    quantity: float
    price: float
    value: float
    date: str
    source: str


class PortfolioValueResponse(BaseModel):
    total_value: float
    positions: list[PositionValue]
    missing_card_ids: list[int]


# -------------------------------
# FastAPI app + CORS
# -------------------------------

app = FastAPI(title="Pokemon Pricer API", version="0.1.0")

# Permissive CORS for MVP (adjust later when UI origin is known)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock down before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Helpers
# -------------------------------


def _normalize_prices_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure expected columns, dtypes, and sort order."""
    if df.empty:
        return df.copy()

    cols = [
        "card_id",
        "name",
        "set_code",
        "number",
        "source",
        "price",
        "date",
    ]
    # Keep only known columns that exist
    exists = [c for c in cols if c in df.columns]
    out = df[exists].copy()

    # Types
    if "card_id" in out.columns:
        out["card_id"] = pd.to_numeric(out["card_id"], errors="coerce").astype("Int64")
    if "price" in out.columns:
        out["price"] = pd.to_numeric(out["price"], errors="coerce")
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")

    # Sort by date
    sort_cols = [c for c in ["card_id", "date"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)

    # Drop rows missing essential fields
    essential = [c for c in ["card_id", "date", "price"] if c in out.columns]
    if essential:
        out = out.dropna(subset=essential)

    return out


def _latest_per_card(df: pd.DataFrame) -> pd.DataFrame:
    """Return latest row per card_id based on 'date'."""
    if df.empty:
        return df.copy()
    if "card_id" not in df.columns or "date" not in df.columns:
        return df.iloc[0:0].copy()

    srt = df.sort_values(["card_id", "date"])
    latest = srt.groupby("card_id", as_index=False).tail(1).reset_index(drop=True)
    return latest


# -------------------------------
# Endpoints
# -------------------------------


@app.get("/health", response_model=HealthResponse, tags=["Meta"])  # type: ignore[misc]
def health() -> HealthResponse:
    """Lightweight health endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get(
    "/v1/catalog/summary",
    response_model=CatalogSummary,
    tags=["Catalog"],
)  # type: ignore[misc]
def catalog_summary() -> CatalogSummary:
    """
    Return counts, date range, and sources from the catalog.
    If no data is present, returns zeros/empty strings.
    """
    df = catalog_summary_df()
    if df.empty:
        return CatalogSummary(
            total_cards=0,
            total_prices=0,
            min_date="",
            max_date="",
            sources="",
        )
    row = df.iloc[0].to_dict()
    return CatalogSummary(
        total_cards=int(row.get("total_cards", 0)),
        total_prices=int(row.get("total_prices", 0)),
        min_date=str(row.get("min_date", "")),
        max_date=str(row.get("max_date", "")),
        sources=str(row.get("sources", "")),
    )


@app.get(
    "/v1/reports/top-movers",
    response_model=list[MoverItem],
    tags=["Reports"],
)  # type: ignore[misc]
def top_movers(
    k: int = Query(5, ge=1, description="Top-K winners and losers"),
    on_date: str | None = Query(None, description="YYYY-MM-DD (optional)"),
) -> list[MoverItem]:
    """
    Return top-K winners and losers for a day.
    When there is no data, returns an empty list.
    """
    df = load_prices_df()
    if df.empty:
        return []

    tm = compute_top_movers(df, k=k, on_date=on_date)
    items: list[MoverItem] = [
        MoverItem(
            card_id=int(r["card_id"]),
            name=str(r["name"]),
            set_code=str(r["set_code"]),
            number=str(r["number"]),
            source=str(r["source"]),
            price=float(r["price"]),
            return_1d=float(r["return_1d"]),
            date=str(r["date"]),
            bucket=str(r["bucket"]),
        )
        for r in tm.to_dict(orient="records")
    ]
    return items


@app.get(
    "/v1/cards/search",
    response_model=list[CardSearchItem],
    tags=["Cards"],
)  # type: ignore[misc]
def card_search(
    q: str = Query(
        ...,
        min_length=1,
        description="Name substring (case-insensitive)",
    ),
) -> list[CardSearchItem]:
    """Search by name across the latest snapshot of each card."""
    df_raw = load_prices_df()
    if df_raw.empty:
        return []

    df = _normalize_prices_df(df_raw)
    latest = _latest_per_card(df)

    mask = latest["name"].str.contains(q, case=False, na=False)
    hits = latest.loc[mask, ["card_id", "name", "set_code", "number"]]
    out = [
        CardSearchItem(
            card_id=int(r["card_id"]),
            name=str(r["name"]),
            set_code=str(r["set_code"]),
            number=str(r["number"]),
        )
        for r in hits.to_dict(orient="records")
    ]
    return out


@app.get(
    "/v1/cards/{card_id}",
    response_model=CardDetail,
    tags=["Cards"],
)  # type: ignore[misc]
def card_by_id(card_id: int) -> CardDetail:
    """Return card details using the latest price snapshot for that card."""
    df_raw = load_prices_df()
    if df_raw.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    df = _normalize_prices_df(df_raw)
    one = df.loc[df["card_id"] == card_id]
    if one.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    last = one.sort_values("date").tail(1).iloc[0]
    return CardDetail(
        card_id=int(last["card_id"]),
        name=str(last["name"]),
        set_code=str(last["set_code"]),
        number=str(last["number"]),
        last_price=float(last["price"]),
        last_date=str(last["date"]),
        source=str(last["source"]),
    )


@app.get(
    "/v1/cards/{card_id}/prices",
    response_model=list[CardPricePoint],
    tags=["Cards"],
)  # type: ignore[misc]
def card_prices(
    card_id: int,
    limit: int = Query(
        50,
        ge=1,
        le=500,
        description="Max number of price points (most recent first)",
    ),
) -> list[CardPricePoint]:
    """Return price history for a card (most recent first)."""
    df_raw = load_prices_df()
    if df_raw.empty:
        return []

    df = _normalize_prices_df(df_raw)
    one = df.loc[df["card_id"] == card_id]
    if one.empty:
        return []

    # Most recent first, then trim to limit
    one = one.sort_values("date", ascending=False).head(limit)
    points = [
        CardPricePoint(
            date=str(r["date"]),
            price=float(r["price"]),
            source=str(r["source"]),
        )
        for r in one[["date", "price", "source"]].to_dict(orient="records")
    ]
    return points


@app.post(
    "/v1/portfolio/value",
    response_model=PortfolioValueResponse,
    tags=["Portfolio"],
)  # type: ignore[misc]
def portfolio_value(
    # Ruff rule B008: suppress Body(...) call in default param
    req: PortfolioValueRequest = Body(  # noqa: B008
        ...,
        description="List of holdings (card_id, quantity)",
    ),
) -> PortfolioValueResponse:
    """Compute current portfolio value based on latest prices."""
    df_raw = load_prices_df()
    if df_raw.empty:
        return PortfolioValueResponse(
            total_value=0.0,
            positions=[],
            missing_card_ids=[h.card_id for h in req.holdings],
        )

    df = _normalize_prices_df(df_raw)
    latest = _latest_per_card(df)

    idx = latest.set_index("card_id")
    positions: list[PositionValue] = []
    missing: list[int] = []
    total_value = 0.0

    for h in req.holdings:
        if h.card_id not in idx.index:
            missing.append(h.card_id)
            continue

        row = idx.loc[h.card_id]
        price = float(row["price"])
        value = price * h.quantity
        total_value += value

        positions.append(
            PositionValue(
                card_id=int(h.card_id),
                name=str(row.get("name", "")),
                set_code=str(row.get("set_code", "")),
                number=str(row.get("number", "")),
                quantity=float(h.quantity),
                price=price,
                value=value,
                date=str(row.get("date", "")),
                source=str(row.get("source", "")),
            )
        )

    return PortfolioValueResponse(
        total_value=float(total_value),
        positions=positions,
        missing_card_ids=missing,
    )
