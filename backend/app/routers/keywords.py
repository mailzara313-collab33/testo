from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser
from app.services.google_ads import google_ads_service

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.get("/search-terms")
async def get_search_terms(
    current_user: CurrentUser,
    account_id: str = Query(...),
    date_from: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    date_to: date = Query(default_factory=date.today),
) -> list[dict]:
    return await google_ads_service.get_search_terms(account_id, date_from, date_to)


@router.get("/ngrams")
async def get_ngrams(
    current_user: CurrentUser,
    account_id: str = Query(...),
    date_from: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    date_to: date = Query(default_factory=date.today),
    n: int = Query(2, ge=1, le=4),
) -> list[dict]:
    terms = await google_ads_service.get_search_terms(account_id, date_from, date_to)
    ngram_data: dict[str, dict] = {}

    for t in terms:
        words = t["search_term"].lower().split()
        for i in range(len(words) - n + 1):
            gram = " ".join(words[i : i + n])
            if gram not in ngram_data:
                ngram_data[gram] = {"ngram": gram, "impressions": 0, "clicks": 0, "cost": 0.0, "conversions": 0.0}
            ngram_data[gram]["impressions"] += t["impressions"]
            ngram_data[gram]["clicks"] += t["clicks"]
            ngram_data[gram]["cost"] += t["cost"]
            ngram_data[gram]["conversions"] += t["conversions"]

    result = list(ngram_data.values())
    for r in result:
        r["ctr"] = round(r["clicks"] / r["impressions"] * 100, 2) if r["impressions"] else 0
        r["cpa"] = round(r["cost"] / r["conversions"], 2) if r["conversions"] else 0

    return sorted(result, key=lambda x: x["cost"], reverse=True)[:100]


@router.get("/negative-suggestions")
async def get_negative_suggestions(
    current_user: CurrentUser,
    account_id: str = Query(...),
    date_from: date = Query(default_factory=lambda: date.today() - timedelta(days=29)),
    date_to: date = Query(default_factory=date.today),
    min_clicks: int = Query(20),
    max_conversions: float = Query(0.5),
) -> list[dict]:
    terms = await google_ads_service.get_search_terms(account_id, date_from, date_to)
    return [
        t for t in terms
        if t["clicks"] >= min_clicks and t["conversions"] <= max_conversions
    ]
