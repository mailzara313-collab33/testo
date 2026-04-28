"""
Google Ads servis katmanı.
DEMO_MODE=true iken gerçekçi mock veri döner.
DEMO_MODE=false iken google-ads-python SDK kullanır.
"""
import random
from datetime import date, timedelta
from typing import Any

from app.config import settings


# ─── Mock data helpers ────────────────────────────────────────────────────────

CAMPAIGN_TYPES = ["SEARCH", "DISPLAY", "SHOPPING", "PERFORMANCE_MAX", "VIDEO", "DEMAND_GEN"]
CAMPAIGN_STATUSES = ["ENABLED", "PAUSED", "REMOVED"]

_CAMPAIGN_NAMES = [
    "Brand - Genel", "Marka Koruma", "Rakip Kampanyası", "Kategori - Ayakkabı",
    "Kategori - Çanta", "Ürün - Yeni Sezon", "Remarketing - Site Ziyaretçileri",
    "PMAX - Tüm Ürünler", "Display - Farkındalık", "Video - YouTube Pre-roll",
]


def _rand_cost() -> float:
    return round(random.uniform(50, 8000), 2)


def _rand_metrics(cost: float) -> dict[str, Any]:
    impressions = int(cost * random.uniform(100, 800))
    clicks = int(impressions * random.uniform(0.01, 0.08))
    ctr = clicks / impressions if impressions else 0
    cpc = cost / clicks if clicks else 0
    conversions = clicks * random.uniform(0.02, 0.12)
    conv_value = conversions * random.uniform(100, 800)
    roas = conv_value / cost if cost else 0
    cpa = cost / conversions if conversions else 0
    return {
        "impressions": impressions,
        "clicks": clicks,
        "ctr": round(ctr * 100, 2),
        "cpc": round(cpc, 2),
        "conversions": round(conversions, 1),
        "conversion_value": round(conv_value, 2),
        "roas": round(roas, 2),
        "cpa": round(cpa, 2),
    }


def _generate_mock_accounts() -> list[dict]:
    return [
        {
            "customer_id": "1234567890",
            "name": "Marka A - Ana Hesap",
            "is_manager": False,
            "currency_code": "TRY",
            "time_zone": "Europe/Istanbul",
        },
        {
            "customer_id": "9876543210",
            "name": "Marka B - E-ticaret",
            "is_manager": False,
            "currency_code": "TRY",
            "time_zone": "Europe/Istanbul",
        },
        {
            "customer_id": "1111111111",
            "name": "MCC - Ajans Hesabı",
            "is_manager": True,
            "currency_code": "TRY",
            "time_zone": "Europe/Istanbul",
        },
    ]


def _generate_mock_campaigns(account_id: str, days: int = 1) -> list[dict]:
    random.seed(hash(account_id) % 9999)
    campaigns = []
    for i, name in enumerate(_CAMPAIGN_NAMES):
        cost = _rand_cost()
        metrics = _rand_metrics(cost)
        campaigns.append({
            "campaign_id": f"{account_id}_{1000 + i}",
            "campaign_name": name,
            "campaign_type": random.choice(CAMPAIGN_TYPES),
            "status": "PAUSED" if i % 4 == 3 else "ENABLED",
            "cost": cost * days,
            "daily_budget": round(cost * random.uniform(1.0, 1.4), 0),
            "avg_quality_score": round(random.uniform(4, 9), 1),
            "search_impression_share": round(random.uniform(0.20, 0.95), 2),
            **{k: v * days if k in ("impressions", "clicks", "conversions", "conversion_value") else v
               for k, v in metrics.items()},
        })
    return campaigns


def _generate_timeseries(account_id: str, date_from: date, date_to: date) -> list[dict]:
    points = []
    current = date_from
    random.seed(hash(account_id + str(date_from)) % 9999)
    while current <= date_to:
        base_cost = random.uniform(800, 4500)
        weekend_factor = 0.7 if current.weekday() >= 5 else 1.0
        cost = round(base_cost * weekend_factor, 2)
        metrics = _rand_metrics(cost)
        points.append({
            "date": current,
            "cost": cost,
            "clicks": metrics["clicks"],
            "impressions": metrics["impressions"],
            "conversions": metrics["conversions"],
            "roas": metrics["roas"],
        })
        current += timedelta(days=1)
    return points


def _generate_heatmap(account_id: str) -> list[dict]:
    cells = []
    random.seed(hash(account_id) % 1234)
    for day in range(7):
        for hour in range(24):
            # Lower performance late night, higher during business hours
            base = 1.0
            if 9 <= hour <= 18:
                base = random.uniform(1.5, 3.0)
            elif 0 <= hour <= 6:
                base = random.uniform(0.1, 0.5)
            cells.append({"day": day, "hour": hour, "value": round(base * random.uniform(0.6, 1.4), 2)})
    return cells


# ─── Service class ────────────────────────────────────────────────────────────

class GoogleAdsService:
    """
    Google Ads API ile etkileşim kurar.
    DEMO_MODE=true iken tüm metodlar mock veri döner.
    """

    def __init__(self) -> None:
        self._client = None
        if not settings.demo_mode:
            self._init_real_client()

    def _init_real_client(self) -> None:
        try:
            from google.ads.googleads.client import GoogleAdsClient  # type: ignore

            self._client = GoogleAdsClient.load_from_dict({
                "developer_token": settings.google_ads_developer_token,
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": settings.google_ads_refresh_token,
                "login_customer_id": settings.google_ads_login_customer_id,
                "use_proto_plus": True,
            })
        except Exception as exc:
            raise RuntimeError(f"Google Ads istemcisi başlatılamadı: {exc}") from exc

    # ── Accounts ──────────────────────────────────────────────────────────────

    async def list_accounts(self) -> list[dict]:
        if settings.demo_mode:
            return _generate_mock_accounts()

        ga_service = self._client.get_service("GoogleAdsService")
        query = """
            SELECT
              customer_client.client_customer,
              customer_client.level,
              customer_client.manager,
              customer_client.descriptive_name,
              customer_client.currency_code,
              customer_client.time_zone
            FROM customer_client
            WHERE customer_client.level <= 1
        """
        response = ga_service.search_stream(
            customer_id=settings.google_ads_login_customer_id,
            query=query,
        )
        accounts = []
        for batch in response:
            for row in batch.results:
                c = row.customer_client
                accounts.append({
                    "customer_id": str(c.client_customer).replace("customers/", ""),
                    "name": c.descriptive_name,
                    "is_manager": c.manager,
                    "currency_code": c.currency_code,
                    "time_zone": c.time_zone,
                })
        return accounts

    # ── Campaigns ─────────────────────────────────────────────────────────────

    async def list_campaigns(
        self,
        account_id: str,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        if settings.demo_mode:
            days = (date_to - date_from).days + 1
            return _generate_mock_campaigns(account_id, days)

        ga_service = self._client.get_service("GoogleAdsService")
        query = f"""
            SELECT
              campaign.id,
              campaign.name,
              campaign.advertising_channel_type,
              campaign.status,
              campaign_budget.amount_micros,
              metrics.cost_micros,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions,
              metrics.conversions_value,
              metrics.ctr,
              metrics.average_cpc,
              metrics.cost_per_conversion,
              metrics.search_impression_share,
              metrics.search_budget_lost_impression_share,
              metrics.search_rank_lost_impression_share
            FROM campaign
            WHERE segments.date BETWEEN '{date_from.isoformat()}' AND '{date_to.isoformat()}'
              AND campaign.status != 'REMOVED'
        """
        response = ga_service.search_stream(customer_id=account_id, query=query)
        campaigns = []
        for batch in response:
            for row in batch.results:
                c = row.campaign
                m = row.metrics
                b = row.campaign_budget
                cost = m.cost_micros / 1_000_000
                conversions = m.conversions
                campaigns.append({
                    "campaign_id": str(c.id),
                    "campaign_name": c.name,
                    "campaign_type": c.advertising_channel_type.name,
                    "status": c.status.name,
                    "cost": round(cost, 2),
                    "daily_budget": round(b.amount_micros / 1_000_000, 2),
                    "impressions": m.impressions,
                    "clicks": m.clicks,
                    "conversions": round(conversions, 1),
                    "conversion_value": round(m.conversions_value, 2),
                    "ctr": round(m.ctr * 100, 2),
                    "cpc": round(m.average_cpc / 1_000_000, 2),
                    "roas": round(m.conversions_value / cost, 2) if cost else 0,
                    "cpa": round(cost / conversions, 2) if conversions else 0,
                    "search_impression_share": round(m.search_impression_share, 2),
                    "search_lost_is_budget": round(m.search_budget_lost_impression_share, 2),
                    "search_lost_is_rank": round(m.search_rank_lost_impression_share, 2),
                })
        return campaigns

    # ── Time Series ───────────────────────────────────────────────────────────

    async def get_time_series(
        self, account_id: str, date_from: date, date_to: date
    ) -> list[dict]:
        if settings.demo_mode:
            return _generate_timeseries(account_id, date_from, date_to)

        ga_service = self._client.get_service("GoogleAdsService")
        query = f"""
            SELECT
              segments.date,
              metrics.cost_micros,
              metrics.clicks,
              metrics.impressions,
              metrics.conversions,
              metrics.conversions_value
            FROM customer
            WHERE segments.date BETWEEN '{date_from.isoformat()}' AND '{date_to.isoformat()}'
        """
        response = ga_service.search_stream(customer_id=account_id, query=query)
        points = []
        for batch in response:
            for row in batch.results:
                m = row.metrics
                cost = m.cost_micros / 1_000_000
                points.append({
                    "date": date.fromisoformat(row.segments.date),
                    "cost": round(cost, 2),
                    "clicks": m.clicks,
                    "impressions": m.impressions,
                    "conversions": round(m.conversions, 1),
                    "roas": round(m.conversions_value / cost, 2) if cost else 0,
                })
        return sorted(points, key=lambda p: p["date"])

    # ── Heatmap ───────────────────────────────────────────────────────────────

    async def get_hourly_heatmap(self, account_id: str) -> list[dict]:
        if settings.demo_mode:
            return _generate_heatmap(account_id)

        ga_service = self._client.get_service("GoogleAdsService")
        query = """
            SELECT
              segments.hour,
              segments.day_of_week,
              metrics.cost_micros,
              metrics.conversions
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
        """
        response = ga_service.search_stream(customer_id=account_id, query=query)
        cells: dict[tuple, list] = {}
        for batch in response:
            for row in batch.results:
                key = (row.segments.day_of_week.value % 7, row.segments.hour)
                cells.setdefault(key, []).append(row.metrics.conversions)
        return [
            {"day": d, "hour": h, "value": round(sum(vals) / len(vals), 2)}
            for (d, h), vals in cells.items()
        ]

    # ── Mutations ─────────────────────────────────────────────────────────────

    async def pause_campaign(self, account_id: str, campaign_id: str) -> bool:
        if settings.demo_mode:
            return True

        campaign_service = self._client.get_service("CampaignService")
        campaign_operation = self._client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(account_id, campaign_id)
        campaign.status = self._client.enums.CampaignStatusEnum.PAUSED
        field_mask = self._client.get_type("FieldMask")
        field_mask.paths.append("status")
        campaign_operation.update_mask.CopyFrom(field_mask)
        campaign_service.mutate_campaigns(
            customer_id=account_id,
            operations=[campaign_operation],
        )
        return True

    async def enable_campaign(self, account_id: str, campaign_id: str) -> bool:
        if settings.demo_mode:
            return True

        campaign_service = self._client.get_service("CampaignService")
        campaign_operation = self._client.get_type("CampaignOperation")
        campaign = campaign_operation.update
        campaign.resource_name = campaign_service.campaign_path(account_id, campaign_id)
        campaign.status = self._client.enums.CampaignStatusEnum.ENABLED
        field_mask = self._client.get_type("FieldMask")
        field_mask.paths.append("status")
        campaign_operation.update_mask.CopyFrom(field_mask)
        campaign_service.mutate_campaigns(
            customer_id=account_id,
            operations=[campaign_operation],
        )
        return True

    async def update_campaign_budget(
        self, account_id: str, campaign_id: str, daily_budget: float
    ) -> bool:
        if settings.demo_mode:
            return True

        budget_service = self._client.get_service("CampaignBudgetService")
        budget_operation = self._client.get_type("CampaignBudgetOperation")
        budget = budget_operation.update
        # First get the budget resource name for this campaign
        ga_service = self._client.get_service("GoogleAdsService")
        query = f"""
            SELECT campaign_budget.resource_name
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        response = ga_service.search(customer_id=account_id, query=query)
        for row in response:
            budget.resource_name = row.campaign_budget.resource_name
            break
        budget.amount_micros = int(daily_budget * 1_000_000)
        field_mask = self._client.get_type("FieldMask")
        field_mask.paths.append("amount_micros")
        budget_operation.update_mask.CopyFrom(field_mask)
        budget_service.mutate_campaign_budgets(
            customer_id=account_id,
            operations=[budget_operation],
        )
        return True

    # ── Keywords ──────────────────────────────────────────────────────────────

    async def get_search_terms(self, account_id: str, date_from: date, date_to: date) -> list[dict]:
        if settings.demo_mode:
            terms = [
                "koşu ayakkabısı", "spor ayakkabı erkek", "nike air max", "adidas ultraboost",
                "ucuz spor ayakkabı", "çanta bayan deri", "sırt çantası laptop",
                "iphone kılıf", "samsung kılıf", "kulaklık kablosuz", "akıllı saat",
                "yoga matı", "protein tozu", "vitamin c", "omega 3",
            ]
            return [
                {
                    "search_term": t,
                    "match_type": random.choice(["BROAD", "PHRASE", "EXACT"]),
                    "campaign_name": random.choice(_CAMPAIGN_NAMES[:5]),
                    "impressions": random.randint(100, 10000),
                    "clicks": random.randint(5, 500),
                    "cost": round(random.uniform(10, 500), 2),
                    "conversions": round(random.uniform(0, 20), 1),
                    "ctr": round(random.uniform(1, 10), 2),
                }
                for t in terms
            ]

        ga_service = self._client.get_service("GoogleAdsService")
        query = f"""
            SELECT
              search_term_view.search_term,
              search_term_view.status,
              segments.keyword.match_type,
              campaign.name,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.ctr
            FROM search_term_view
            WHERE segments.date BETWEEN '{date_from.isoformat()}' AND '{date_to.isoformat()}'
            ORDER BY metrics.cost_micros DESC
            LIMIT 500
        """
        response = ga_service.search_stream(customer_id=account_id, query=query)
        terms = []
        for batch in response:
            for row in batch.results:
                m = row.metrics
                terms.append({
                    "search_term": row.search_term_view.search_term,
                    "match_type": row.segments.keyword.match_type.name,
                    "campaign_name": row.campaign.name,
                    "impressions": m.impressions,
                    "clicks": m.clicks,
                    "cost": round(m.cost_micros / 1_000_000, 2),
                    "conversions": round(m.conversions, 1),
                    "ctr": round(m.ctr * 100, 2),
                })
        return terms


google_ads_service = GoogleAdsService()
