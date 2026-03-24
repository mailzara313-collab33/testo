from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask, request, jsonify, render_template_string
import time
import os

app = Flask(__name__)

driver = None
durum = "BEKLIYOR"
mesaj = "Hazır"
logs = []

def log(m):
    global logs
    m = f"[{time.strftime('%H:%M:%S')}] {m}"
    logs.append(m)
    print(m, flush=True)

def create_driver():
    global driver
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        # Stealth
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """
        })
        log("✅ Stealth Chromium başlatıldı!")
        return True
    except Exception as e:
        log(f"❌ Driver hatası: {e}")
        return False

# ====================== ARAYÜZ (senin orijinaline çok yakın) ======================
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Enpara Bot</title>
    <style>body{font-family:Arial; text-align:center; padding:30px;}</style>
</head>
<body>
    <h2>ENPARA KENDİ HESAP BOTU</h2>
    <input id="tc" placeholder="TC / Müşteri No" style="width:320px;padding:8px;"><br><br>
    <input id="sifre" type="password" placeholder="Şifre" style="width:320px;padding:8px;"><br><br>
    <input id="iban" placeholder="Hedef IBAN" style="width:320px;padding:8px;"><br><br>
    <input id="tutar" placeholder="Tutar (ör: 250.75)" style="width:320px;padding:8px;"><br><br>
    
    <button onclick="baslat()" style="padding:12px 30px; font-size:18px;">BAŞLAT</button>
    
    <h3 id="status">Durum: BEKLIYOR</h3>
    <pre id="logs" style="text-align:left; background:#f8f8f8; padding:15px; max-height:500px; overflow:auto; border:1px solid #ddd;"></pre>

    <script>
    async function baslat(){
        const tc = document.getElementById('tc').value;
        const sifre = document.getElementById('sifre').value;
        
        const res = await fetch('/giris', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tc, sifre})
        });
        const data = await res.json();
        guncelle(data);
        kontrolLoop();
    }

    async function kontrolLoop(){
        setInterval(async () => {
            const res = await fetch('/kontrol');
            const data = await res.json();
            guncelle(data);
            
            if(data.durum === "GIRIS_BASARILI"){
                transferYap();
            }
        }, 4000);
    }

    async function transferYap(){
        const iban = document.getElementById('iban').value;
        const tutar = document.getElementById('tutar').value;
        
        const res = await fetch('/transfer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({iban, tutar})
        });
        const data = await res.json();
        guncelle(data);
    }

    function guncelle(data){
        document.getElementById("status").innerText = "Durum: " + data.durum + " — " + data.mesaj;
        if(data.logs) document.getElementById("logs").innerText = data.logs.join("\\n");
    }
    </script>
</body>
</html>
""")

# ====================== GİRİŞ (EN ÖNEMLİ KISIM - DÜZENLENDİ) ======================
@app.route('/giris', methods=['POST'])
def giris():
    global durum, mesaj, driver
    data = request.json
    tc = data.get("tc")
    sifre = data.get("sifre")

    log("🚀 Giriş başlıyor...")

    if driver is None:
        if not create_driver():
            return jsonify({"durum":"HATA","mesaj":"Driver başlatılamadı","logs":logs})

    try:
        wait = WebDriverWait(driver, 30)
        
        driver.get("https://internetsubesi.enpara.com/Login/LoginPage.aspx")
        time.sleep(7)                    # Sayfa tam yüklenene kadar uzun bekleme
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)

        log(f"Şu anki URL: {driver.current_url}")

        # Senin orijinal HTML'indeki txtuserid
        userid = wait.until(EC.any_of(
            EC.presence_of_element_located((By.ID, "txtuserid")),
            EC.presence_of_element_located((By.NAME, "ctl00$MainContent$txtuserid"))
        ))
        userid.clear()
        userid.send_keys(tc)
        log("✅ TC/Müşteri No girildi")

        # Şifre
        password = wait.until(EC.presence_of_element_located((By.ID, "txtpass")))
        password.clear()
        password.send_keys(sifre)
        log("✅ Şifre girildi")

        # Buton (senin orijinal ID)
        login_btn = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_MainContent_lbtnNext")))
        login_btn.click()
        log("✅ Giriş butonuna basıldı - Mobil onay bekleniyor...")

        durum = "MOBIL_ONAY_BEKLIYOR"
        mesaj = "Telefonuna SMS / Enpara Mobil onayı gelmesini bekle ve onayla."

        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})

    except Exception as e:
        log(f"❌ Giriş hatası: {str(e)}")
        try:
            log("=== SAYFA KAYNAĞI ÖNİZLEME ===")
            log(driver.page_source[:1800])   # İlk 1800 karakter (sorunu görmemize yeter)
        except:
            pass
        return jsonify({"durum":"HATA","mesaj":str(e),"logs":logs})

# ====================== KONTROL ======================
@app.route('/kontrol')
def kontrol():
    global durum, mesaj
    try:
        current_url = driver.current_url.lower()
        if any(x in current_url for x in ["accountsummary", "hesapozeti", "dashboard", "main"]):
            durum = "GIRIS_BASARILI"
            mesaj = "Giriş başarılı! Transfer yapabilirsiniz."
        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})
    except Exception as e:
        return jsonify({"durum":"HATA", "mesaj": str(e), "logs": logs})

# ====================== TRANSFER ======================
@app.route('/transfer', methods=['POST'])
def transfer():
    global durum
    data = request.json
    iban = data.get("iban")
    tutar = data.get("tutar")

    try:
        wait = WebDriverWait(driver, 15)
        driver.get("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx")
        time.sleep(5)

        iban_field = wait.until(EC.any_of(
            EC.presence_of_element_located((By.ID, "txtIban")),
            EC.presence_of_element_located((By.NAME, "iban"))
        ))
        iban_field.clear()
        iban_field.send_keys(iban)

        amount_field = driver.find_element(By.ID, "txtAmount") if driver.find_elements(By.ID, "txtAmount") else driver.find_element(By.NAME, "amount")
        amount_field.clear()
        amount_field.send_keys(tutar)

        # Butonlar (değişmiş olabilir)
        driver.find_element(By.ID, "btnNext").click() if driver.find_elements(By.ID, "btnNext") else driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        driver.find_element(By.ID, "btnConfirm").click() if driver.find_elements(By.ID, "btnConfirm") else driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        log("✅ Transfer komutu gönderildi")
        return jsonify({"durum":"BASARILI","mesaj":"Transfer başlatıldı","logs":logs})

    except Exception as e:
        log(f"❌ Transfer hatası: {str(e)}")
        return jsonify({"durum":"HATA","mesaj":str(e),"logs":logs})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
