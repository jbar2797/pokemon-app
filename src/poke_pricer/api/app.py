from __future__ import annotations

from fastapi import FastAPI, Query
from pydantic import BaseModel

from ..analytics.data_access import load_prices_df
from ..analytics.movers import compute_top_movers
from ..catalog.stats import catalog_summary_df

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="Pokemon Pricer API", version="0.1.0")


# -----------------------------------------------------------------------------
# Pydantic response models
# -----------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str


class CatalogSummary(BaseModel):
    total_cards: int = 0
    total_prices: int = 0
    min_date: str = ""
    max_date: str = ""
    sources: str = ""


class MoverItem(BaseModel):
    card_id: int
    name: str
    set_code: str
    number: str
    source: str
    price: float
    return_1d: float
    date: str
    bucket: str  # "winner" or "loser"


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)  # type: ignore[misc]
def health() -> HealthResponse:
    """
    Lightweight liveness probe.
    """
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/v1/catalog/summary", response_model=CatalogSummary)  # type: ignore[misc]
def catalog_summary() -> CatalogSummary:
    """
    Return counts, date range, and source list from the catalog.
    """
    df = catalog_summary_df()
    if df.empty:
        return CatalogSummary()

    row = df.iloc[0].to_dict()
    return CatalogSummary(
        total_cards=int(row.get("total_cards", 0)),
        total_prices=int(row.get("total_prices", 0)),
        min_date=str(row.get("min_date", "")),
        max_date=str(row.get("max_date", "")),
        sources=str(row.get("sources", "")),
    )


@app.get("/v1/reports/top-movers", response_model=list[MoverItem])  # type: ignore[misc]
def top_movers(
    k: int = Query(5, ge=1, description="Top-K winners and losers"),
    on_date: str | None = Query(None, description="YYYY-MM-DD (optional)"),
) -> list[MoverItem]:
    """
    Return top-K winners and losers for a given day.
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
