# src/poke_pricer/api/app.py
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..analytics.data_access import load_prices_df
from ..analytics.movers import compute_top_movers
from ..catalog.stats import catalog_summary_df

# ---- OpenAPI tags metadata ---------------------------------------------------
TAGS_METADATA = [
    {"name": "health", "description": "Service health and version."},
    {"name": "catalog", "description": "Catalog and dataset summaries."},
    {"name": "reports", "description": "Computed reports such as top movers."},
]

app = FastAPI(
    title="Pokemon Pricer API",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
)

# ---- CORS (MVP: permissive; tighten to your UI domain after MVP) ------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Response models ---------------------------------------------------------
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


# ---- Endpoints ---------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["health"])  # type: ignore[misc]
def health() -> HealthResponse:
    """Lightweight health endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/v1/catalog/summary", response_model=CatalogSummary, tags=["catalog"])  # type: ignore[misc]
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


@app.get("/v1/reports/top-movers", response_model=list[MoverItem], tags=["reports"])  # type: ignore[misc]
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
    return [
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
