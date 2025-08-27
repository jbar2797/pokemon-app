# src/poke_pricer/api/app.py
from __future__ import annotations

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..analytics.data_access import load_prices_df
from ..analytics.movers import compute_top_movers
from ..catalog.stats import catalog_summary_df

# -------------------- Pydantic response models --------------------


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


class CardLite(BaseModel):
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


class PricePoint(BaseModel):
    date: str
    price: float
    source: str


# -------------------- FastAPI app + CORS --------------------

app = FastAPI(title="Pokemon Pricer API", version="0.1.0")

# CORS: permissive for MVP; tighten later when UI origin is known.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Helpers (typed) --------------------


def _latest_per_card(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the latest row per card_id from a prices dataframe.

    Expected columns: ['card_id', 'name', 'set_code', 'number', 'source', 'price', 'date'].
    """
    if df.empty:
        return df
    df_sorted = df.sort_values(["card_id", "date"])
    idx = df_sorted.groupby("card_id")["date"].idxmax()
    latest = df_sorted.loc[idx].sort_values("card_id")
    return latest


# -------------------- Endpoints --------------------


@app.get("/health", response_model=HealthResponse, tags=["System"])  # type: ignore[misc]
def health() -> HealthResponse:
    """Lightweight health endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/v1/catalog/summary", response_model=CatalogSummary, tags=["Catalog"])  # type: ignore[misc]
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


@app.get("/v1/reports/top-movers", response_model=list[MoverItem], tags=["Reports"])  # type: ignore[misc]
def top_movers(
    k: int = Query(5, ge=1, description="Top-K winners and losers"),
    on_date: str | None = Query(None, description="YYYY-MM-DD (optional)"),
) -> list[MoverItem]:
    """Return top-K winners and losers for a day."""
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


# -------------------- New: Cards endpoints --------------------


@app.get("/v1/cards/search", response_model=list[CardLite], tags=["Cards"])  # type: ignore[misc]
def card_search(
    q: str = Query(..., min_length=1, description="Substring search on name/set_code/number"),
) -> list[CardLite]:
    """
    Substring search across latest info for each card.
    Returns [] if no data.
    """
    df = load_prices_df()
    if df.empty:
        return []

    latest = _latest_per_card(df)
    mask = (
        latest["name"].str.contains(q, case=False, na=False)
        | latest["set_code"].str.contains(q, case=False, na=False)
        | latest["number"].str.contains(q, case=False, na=False)
    )
    rows = latest.loc[mask]

    return [
        CardLite(
            card_id=int(r["card_id"]),
            name=str(r["name"]),
            set_code=str(r["set_code"]),
            number=str(r["number"]),
        )
        for r in rows.to_dict(orient="records")
    ]


@app.get("/v1/cards/{card_id}", response_model=CardDetail, tags=["Cards"])  # type: ignore[misc]
def card_by_id(card_id: int) -> CardDetail:
    """
    Return latest details for a card by ID.
    404 if the card_id does not exist.
    """
    df = load_prices_df()
    if df.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    latest = _latest_per_card(df)
    row = latest.loc[latest["card_id"] == card_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    r = row.iloc[0].to_dict()
    return CardDetail(
        card_id=int(r["card_id"]),
        name=str(r["name"]),
        set_code=str(r["set_code"]),
        number=str(r["number"]),
        last_price=float(r["price"]),
        last_date=str(r["date"]),
        source=str(r["source"]),
    )


@app.get("/v1/cards/{card_id}/prices", response_model=list[PricePoint], tags=["Cards"])  # type: ignore[misc]
def card_price_history(
    card_id: int,
    limit: int = Query(90, ge=1, le=1000, description="Max number of points, oldest→newest"),
) -> list[PricePoint]:
    """
    Return historical price points for a card (up to `limit`).
    404 if the card_id has no records.
    """
    df = load_prices_df()
    if df.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    rows = df.loc[df["card_id"] == card_id].sort_values("date")
    if rows.empty:
        raise HTTPException(status_code=404, detail="Card not found")

    rows = rows.tail(limit)
    return [
        PricePoint(date=str(r["date"]), price=float(r["price"]), source=str(r["source"]))
        for r in rows.to_dict(orient="records")
    ]
