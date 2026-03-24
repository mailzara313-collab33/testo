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
    
    # Stealth ayarları (2026 için önemli)
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
        
        # Extra stealth scriptleri
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr']});
            """
        })
        
        log("✅ Chromium stealth modda başlatıldı!")
        return True
    except Exception as e:
        log(f"❌ Driver başlatılamadı: {e}")
        return False

# ====================== HTML ARAYÜZ ======================
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Enpara Otomatik Transfer</title>
    <style>body{font-family:Arial; text-align:center; padding:20px;}</style>
</head>
<body>
    <h2>Enpara Kendi Hesap Botu</h2>
    <input id="tc" placeholder="TC / Müşteri No" style="width:300px"><br><br>
    <input id="sifre" type="password" placeholder="Şifre" style="width:300px"><br><br>
    <input id="iban" placeholder="Hedef IBAN" style="width:300px"><br><br>
    <input id="tutar" placeholder="Tutar (ör: 100.50)" style="width:300px"><br><br>
    
    <button onclick="baslat()" style="padding:10px 20px; font-size:16px;">BAŞLAT</button>
    
    <h3 id="status">Durum: BEKLIYOR</h3>
    <pre id="logs" style="text-align:left; background:#f4f4f4; padding:10px; max-height:400px; overflow:auto;"></pre>

    <script>
    async function baslat(){
        const tc = document.getElementById('tc').value;
        const sifre = document.getElementById('sifre').value;
        
        const res = await fetch('/giris', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({tc, sifre})
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
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({iban, tutar})
        });
        const data = await res.json();
        guncelle(data);
    }

    function guncelle(data){
        document.getElementById("status").innerText = "Durum: " + data.durum + " - " + data.mesaj;
        if(data.logs){
            document.getElementById("logs").innerText = data.logs.join("\\n");
        }
    }
    </script>
</body>
</html>
""")

# ====================== GİRİŞ ======================
@app.route('/giris', methods=['POST'])
def giris():
    global durum, mesaj, driver
    data = request.json
    tc = data.get("tc")
    sifre = data.get("sifre")

    log("🚀 Giriş işlemi başlıyor...")

    if driver is None:
        if not create_driver():
            return jsonify({"durum":"HATA", "mesaj":"Driver başlatılamadı", "logs":logs})

    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://internetsubesi.enpara.com/Login/LoginPage.aspx")
        time.sleep(3)

        userid = wait.until(EC.presence_of_element_located((By.ID, "txtuserid")))
        userid.clear()
        userid.send_keys(tc)

        password = driver.find_element(By.ID, "txtpass")
        password.clear()
        password.send_keys(sifre)

        next_btn = driver.find_element(By.ID, "ctl00_MainContent_lbtnNext")
        next_btn.click()

        log("✅ Giriş butonuna basıldı. Mobil onay bekleniyor...")
        durum = "MOBIL_ONAY_BEKLIYOR"
        mesaj = "Telefonuna SMS veya Enpara Mobil onayı gelmesini bekle. Onay verildikten sonra /kontrol sayfası otomatik devam eder."

        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})

    except Exception as e:
        log(f"❌ Giriş hatası: {str(e)}")
        return jsonify({"durum":"HATA", "mesaj": str(e), "logs": logs})

# ====================== KONTROL ======================
@app.route('/kontrol')
def kontrol():
    global durum, mesaj
    try:
        current_url = driver.current_url.lower()
        if any(x in current_url for x in ["accountsummary", "hesapozeti", "dashboard"]):
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
        time.sleep(3)

        # IBAN alanı (farklı ID’ler olabilir)
        iban_field = wait.until(EC.any_of(
            EC.presence_of_element_located((By.ID, "txtIban")),
            EC.presence_of_element_located((By.NAME, "iban")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='IBAN']"))
        ))
        iban_field.clear()
        iban_field.send_keys(iban)

        # Tutar alanı
        amount_field = driver.find_element(By.ID, "txtAmount") if driver.find_elements(By.ID, "txtAmount") else \
                       driver.find_element(By.NAME, "amount")
        amount_field.clear()
        amount_field.send_keys(tutar)

        # Butonlar
        next_btn = driver.find_element(By.ID, "btnNext") if driver.find_elements(By.ID, "btnNext") else \
                   driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[value='İleri']")
        next_btn.click()
        time.sleep(2)

        confirm_btn = driver.find_element(By.ID, "btnConfirm") if driver.find_elements(By.ID, "btnConfirm") else \
                      driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[value='Onayla']")
        confirm_btn.click()

        log("✅ Transfer komutu gönderildi.")
        durum = "TRANSFER_BASARILI"
        return jsonify({"durum":"BASARILI", "mesaj":"Transfer işlemi başlatıldı (onay sayfası gelebilir)", "logs":logs})

    except Exception as e:
        log(f"❌ Transfer hatası: {str(e)}")
        return jsonify({"durum":"HATA", "mesaj": str(e), "logs":logs})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
