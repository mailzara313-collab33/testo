from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from flask import Flask, request, jsonify, render_template_string
import os
import time

app = Flask(__name__)

# Global değişkenler
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
    options.binary_location = "/usr/bin/chromium-browser"
    
    # Render.com için optimize
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new")
    
    # Render'da chromedriver yolu farklı olabilir
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        log("✅ Chromium başlatıldı!")
        return True
    except Exception as e:
        log(f"❌ Hata: {str(e)[:200]}")
        # Alternatif yol dene
        try:
            service = Service("/usr/lib/chromium-browser/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            log("✅ Chromium başlatıldı (alternatif yol)!")
            return True
        except Exception as e2:
            log(f"❌ Alternatif de başarısız: {str(e2)[:200]}")
            return False

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enpara Bot - Render</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { color: #333; text-align: center; }
        input, button {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { opacity: 0.9; }
        #status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #f0f0f0;
        }
        .waiting { background: #fff3cd !important; color: #856404; }
        .success { background: #d4edda !important; color: #155724; }
        .error { background: #f8d7da !important; color: #721c24; }
        #logs {
            margin-top: 20px;
            padding: 15px;
            background: #1e1e1e;
            color: #00ff00;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏦 Enpara Bot</h1>
        
        <div id="formSection">
            <h3>🔐 Giriş Bilgileri</h3>
            <input type="text" id="tc" placeholder="TC Kimlik No" maxlength="11">
            <input type="password" id="sifre" placeholder="İnternet Şifresi">
            
            <h3>💸 Transfer Bilgisi</h3>
            <input type="text" id="iban" placeholder="IBAN">
            <input type="number" id="tutar" placeholder="Tutar (TL)">
            <input type="text" id="aciklama" placeholder="Açıklama">
            
            <button onclick="baslat()">🚀 Başlat</button>
        </div>
        
        <div id="mobileSection" style="display:none;">
            <div class="waiting" style="padding: 30px; text-align: center; border-radius: 10px;">
                <h2>📱 Mobil Onay Bekleniyor</h2>
                <p>Telefonundaki Enpara uygulamasından girişi onayla</p>
                <p style="margin-top: 15px;">Kontrol ediliyor... <span id="sure">0</span> sn</p>
            </div>
        </div>
        
        <div id="status"></div>
        <div id="logs"></div>
    </div>
    
    <script>
    async function baslat() {
        const tc = document.getElementById('tc').value;
        const sifre = document.getElementById('sifre').value;
        
        if(!tc || !sifre) {
            alert('TC ve şifre girin!');
            return;
        }
        
        document.getElementById('formSection').style.display = 'none';
        document.getElementById('mobileSection').style.display = 'block';
        
        // Giriş yap
        const res = await fetch('/giris', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tc, sifre})
        });
        
        const data = await res.json();
        updateStatus(data);
        
        if(data.durum === 'MOBIL_ONAY_BEKLIYOR') {
            startChecking();
        }
    }
    
    function startChecking() {
        let sure = 0;
        setInterval(async () => {
            sure++;
            document.getElementById('sure').innerText = sure;
            
            if(sure % 3 === 0) {
                const res = await fetch('/kontrol');
                const data = await res.json();
                updateStatus(data);
                updateLogs(data.logs);
                
                if(data.durum === 'GIRIS_BASARILI') {
                    // Transfer yap
                    await transfer();
                } else if(data.durum === 'HATA') {
                    alert('Hata: ' + data.mesaj);
                    location.reload();
                }
            }
        }, 1000);
    }
    
    async function transfer() {
        const iban = document.getElementById('iban').value;
        const tutar = document.getElementById('tutar').value;
        const aciklama = document.getElementById('aciklama').value;
        
        if(!iban || !tutar) {
            alert('IBAN ve tutar girin!');
            return;
        }
        
        const res = await fetch('/transfer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({iban, tutar, aciklama})
        });
        
        const data = await res.json();
        updateStatus(data);
        
        if(data.durum === 'BASARILI') {
            document.getElementById('mobileSection').innerHTML = 
                '<div class="success" style="padding: 30px; text-align: center;">' +
                '<h2>✅ Transfer Tamamlandı!</h2>' +
                '<p>Referans: ' + data.referans + '</p>' +
                '</div>';
        }
    }
    
    function updateStatus(data) {
        const s = document.getElementById('status');
        s.innerText = data.durum + ': ' + data.mesaj;
        s.className = data.durum === 'HATA' ? 'error' : 
                     data.durum === 'BASARILI' ? 'success' : 'waiting';
    }
    
    function updateLogs(logs) {
        if(logs) {
            document.getElementById('logs').innerHTML = logs.join('<br>');
        }
    }
    </script>
</body>
</html>
    ''')

@app.route('/giris', methods=['POST'])
def giris():
    global durum, mesaj, driver
    
    data = request.get_json()
    tc = data.get('tc', '')
    sifre = data.get('sifre', '')
    
    log(f"🚀 Giriş başlatılıyor... TC: {tc[:4]}****{tc[-2:]}")
    
    if driver is None:
        if not create_driver():
            return jsonify({"durum": "HATA", "mesaj": "Chromium başlatılamadı"})
    
    try:
        log("📍 Enpara açılıyor...")
        driver.get("https://internetsubesi.enpara.com/Login/LoginPage.aspx")
        time.sleep(3)
        
        log("📝 TC giriliyor...")
        tc_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtuserid"))
        )
        tc_input.clear()
        tc_input.send_keys(tc)
        
        log("🔑 Şifre giriliyor...")
        driver.find_element(By.ID, "txtpass").send_keys(sifre)
        
        log("🚀 Giriş yapılıyor...")
        driver.find_element(By.ID, "ctl00_MainContent_lbtnNext").click()
        
        durum = "MOBIL_ONAY_BEKLIYOR"
        mesaj = "Telefonundan onay ver"
        log("📱 MOBİL ONAY BEKLENİYOR!")
        
        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})
        
    except Exception as e:
        durum = "HATA"
        mesaj = str(e)[:200]
        log(f"❌ HATA: {mesaj}")
        return jsonify({"durum": "HATA", "mesaj": mesaj, "logs": logs})

@app.route('/kontrol', methods=['GET'])
def kontrol():
    global durum, mesaj
    
    if driver is None:
        return jsonify({"durum": "BEKLIYOR", "mesaj": "Başlatılmadı", "logs": logs})
    
    try:
        current_url = driver.current_url
        
        if "Account/AccountSummary" in current_url:
            if durum != "GIRIS_BASARILI":
                durum = "GIRIS_BASARILI"
                mesaj = "Giriş başarılı!"
                log("✅ GİRİŞ BAŞARILI!")
            return jsonify({"durum": "GIRIS_BASARILI", "mesaj": mesaj, "logs": logs})
        
        errors = driver.find_elements(By.ID, "divErrorMsg")
        if errors and errors[0].text.strip():
            durum = "HATA"
            mesaj = errors[0].text.strip()
            return jsonify({"durum": "HATA", "mesaj": mesaj, "logs": logs})
        
        return jsonify({"durum": durum, "mesaj": mesaj, "logs": logs})
        
    except Exception as e:
        return jsonify({"durum": durum, "mesaj": str(e)[:100], "logs": logs})

@app.route('/transfer', methods=['POST'])
def transfer():
    global durum, mesaj
    
    if durum != "GIRIS_BASARILI":
        return jsonify({"durum": "HATA", "mesaj": "Önce giriş yap!", "logs": logs})
    
    data = request.get_json()
    iban = data.get('iban', '')
    tutar = data.get('tutar', '')
    aciklama = data.get('aciklama', 'Transfer')
    
    log(f"💸 Transfer: {tutar} TL")
    
    try:
        driver.get("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx")
        time.sleep(3)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtIban"))
        ).send_keys(iban)
        
        driver.find_element(By.ID, "btnQuery").click()
        time.sleep(2)
        
        driver.find_element(By.ID, "txtAmount").send_keys(str(tutar))
        driver.find_element(By.ID, "txtDescription").send_keys(aciklama)
        
        driver.find_element(By.ID, "btnNext").click()
        time.sleep(2)
        driver.find_element(By.ID, "btnConfirm").click()
        time.sleep(3)
        
        refs = driver.find_elements(By.CLASS_NAME, "reference-no")
        ref = refs[0].text if refs else "Yok"
        
        log(f"✅ Transfer tamamlandı! Ref: {ref}")
        return jsonify({"durum": "BASARILI", "mesaj": "Tamamlandı", "referans": ref, "logs": logs})
        
    except Exception as e:
        log(f"❌ Transfer hatası: {e}")
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
  
