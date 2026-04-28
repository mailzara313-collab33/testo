# AdOps Command Center

Google Ads hesaplarını ajans seviyesinde yöneten, çoklu hesap destekli,
gerçek zamanlı performans dashboard'u ve otomatik optimizasyon motoru.

## Özellikler

- **Çok Hesaplı Yönetim** — MCC hesabı altındaki tüm hesapları listele ve yönet
- **Performans Dashboard** — KPI kartları, zaman serisi grafik, heatmap
- **Kampanya Yönetimi** — Filtreleme, sıralama, duraklat/başlat, bütçe güncelle
- **Anahtar Kelime Lab** — Arama terimleri, N-gram analizi, negatif öneriler
- **Otomasyon Motoru** — IF/THEN kuralları, dry-run modu, audit log
- **Bütçe Takibi** — Pacing göstergesi, kampanya bazlı harcama
- **Raporlama** — PDF, Excel, otomatik e-posta (Sprint 7)

## Hızlı Başlangıç

```bash
# 1. Ortam değişkenlerini hazırla
cp .env.example .env
# .env dosyasını düzenle

# 2. Docker ile başlat (tek komut)
docker compose up --build

# 3. Tarayıcıda aç
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Demo Giriş

```
E-posta: admin@adops.local
Şifre:   Admin1234!
```

> `DEMO_MODE=true` ile Google Ads API bağlantısı olmadan çalışır.

## Manuel Başlangıç

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir -p data
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## Google Ads API Bağlantısı

`.env` içine şunları girin:

```env
DEMO_MODE=false
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...
```

Detaylı OAuth2 kurulum rehberi: [Google Ads API Quickstart](https://developers.google.com/google-ads/api/docs/first-call/overview)

## Mimari

```
adops/
├── backend/          # FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── models/   # SQLAlchemy modelleri
│   │   ├── schemas/  # Pydantic şemalar
│   │   ├── routers/  # API endpoint'leri
│   │   ├── services/ # Google Ads + iş mantığı
│   │   └── core/     # JWT auth, bağımlılıklar
│   └── alembic/      # DB migrasyonları
└── frontend/         # Next.js 14 + TypeScript
    ├── app/          # App Router sayfaları
    ├── components/   # UI bileşenleri
    ├── lib/          # API client, auth store
    └── types/        # TypeScript tipleri
```

## Sprint Planı

| Sprint | Konu | Durum |
|--------|------|-------|
| 0 | Proje iskeleti | ✅ Tamamlandı |
| 1 | Google Ads API erişimi | ✅ Tamamlandı (demo mode) |
| 2 | Backend foundation | ✅ Tamamlandı |
| 3 | Frontend foundation | ✅ Tamamlandı |
| 4 | Performance Dashboard | ✅ Tamamlandı |
| 5 | Campaign Management | ✅ Tamamlandı |
| 6 | Automation Engine | ✅ Tamamlandı |
| 7 | Reporting (PDF/Excel/Email) | 🔜 Sonraki |
| 8 | Production Readiness | 🔜 Sonraki |
