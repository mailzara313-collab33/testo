from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from flask import Flask, request, jsonify, render_template_string
import os
import time

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
    log("🌐 Chromium başlatılıyor...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        log("✅ Chromium başlatıldı!")
        return True
    except Exception as e:
        log(f"❌ Hata: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template_string("""
    <h2>🚀 Enpara Bot</h2>
    <input id="tc" placeholder="TC"><br><br>
    <input id="sifre" placeholder="Şifre" type="password"><br><br>
    <button onclick="baslat()">Başlat</button>

    <pre id="out"></pre>

    <script>
    async function baslat(){
        const res = await fetch('/giris', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                tc: document.getElementById('tc').value,
                sifre: document.getElementById('sifre').value
            })
        });
        const data = await res.json();
        document.getElementById('out').innerText = JSON.stringify(data,null,2);
    }
    </script>
    """)

@app.route('/giris', methods=['POST'])
def giris():
    global durum, mesaj, driver
    
    data = request.get_json()
    tc = data.get('tc', '')
    sifre = data.get('sifre', '')
    
    log("🚀 Giriş başlatılıyor...")
    
    if driver is None:
        if not create_driver():
            return jsonify({"durum": "HATA", "mesaj": "Chromium başlatılamadı"})
    
    try:
        driver.get("https://internetsubesi.enpara.com/Login/LoginPage.aspx")
        time.sleep(3)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtuserid"))
        ).send_keys(tc)
        
        driver.find_element(By.ID, "txtpass").send_keys(sifre)
        driver.find_element(By.ID, "ctl00_MainContent_lbtnNext").click()
        
        durum = "MOBIL_ONAY_BEKLIYOR"
        mesaj = "Telefonundan onay ver"
        
        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})
        
    except Exception as e:
        log(str(e))
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})

@app.route('/kontrol')
def kontrol():
    global durum, mesaj
    
    try:
        if "AccountSummary" in driver.current_url:
            durum = "GIRIS_BASARILI"
            mesaj = "Giriş başarılı"
        return jsonify({"durum": durum, "mesaj": mesaj})
    except Exception as e:
        return jsonify({"durum": "HATA", "mesaj": str(e)})

@app.route('/transfer', methods=['POST'])
def transfer():
    global durum
    
    if durum != "GIRIS_BASARILI":
        return jsonify({"durum": "HATA", "mesaj": "Önce giriş yap"})
    
    data = request.json
    iban = data.get("iban")
    tutar = data.get("tutar")

    try:
        driver.get("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx")
        time.sleep(3)

        driver.find_element(By.ID, "txtIban").send_keys(iban)
        driver.find_element(By.ID, "txtAmount").send_keys(str(tutar))

        driver.find_element(By.ID, "btnNext").click()
        driver.find_element(By.ID, "btnConfirm").click()

        return jsonify({"durum": "BASARILI"})
    
    except Exception as e:
        return jsonify({"durum": "HATA", "mesaj": str(e)})

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
