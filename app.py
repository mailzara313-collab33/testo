# app.py - Playwright + Render (Free Plan)

import os
import time
import asyncio
from playwright.async_api import async_playwright
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Global değişkenler
browser = None
page = None
durum = "BEKLIYOR"
mesaj = "Hazır"
logs = []

def log(m):
    global logs
    m = f"[{time.strftime('%H:%M:%S')}] {m}"
    logs.append(m)
    print(m, flush=True)

async def create_browser():
    """Playwright ile Chromium başlat"""
    global browser, page
    
    log("🌐 Playwright başlatılıyor...")
    
    try:
        playwright = await async_playwright().start()
        
        # Chromium'u indir ve başlat (kendi içinde)
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080"
            ]
        )
        
        page = await browser.new_page()
        log("✅ Chromium başlatıldı!")
        return True
        
    except Exception as e:
        log(f"❌ Hata: {str(e)[:200]}")
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
        
        const res = await fetch('/giris', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({tc, sifre})
        });
        
        const data = await res.json();
        updateStatus(data);
        updateLogs(data.logs);
        
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
        updateLogs(data.logs);
        
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
    global durum, mesaj, browser, page
    
    data = request.get_json()
    tc = data.get('tc', '')
    sifre = data.get('sifre', '')
    
    log(f"🚀 Giriş başlatılıyor... TC: {tc[:4]}****{tc[-2:]}")
    
    # Async fonksiyonu sync çağır
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    if browser is None:
        success = loop.run_until_complete(create_browser())
        if not success:
            return jsonify({"durum": "HATA", "mesaj": "Chromium başlatılamadı", "logs": logs})
    
    try:
        loop.run_until_complete(page.goto("https://internetsubesi.enpara.com/Login/LoginPage.aspx"))
        loop.run_until_complete(page.wait_for_timeout(3000))
        
        log("📝 TC giriliyor...")
        loop.run_until_complete(page.fill("#txtuserid", tc))
        
        log("🔑 Şifre giriliyor...")
        loop.run_until_complete(page.fill("#txtpass", sifre))
        
        log("🚀 Giriş yapılıyor...")
        loop.run_until_complete(page.click("#ctl00_MainContent_lbtnNext"))
        
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
    
    if browser is None:
        return jsonify({"durum": "BEKLIYOR", "mesaj": "Başlatılmadı", "logs": logs})
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        current_url = loop.run_until_complete(page.url())
        
        if "Account/AccountSummary" in current_url:
            if durum != "GIRIS_BASARILI":
                durum = "GIRIS_BASARILI"
                mesaj = "Giriş başarılı!"
                log("✅ GİRİŞ BAŞARILI!")
            return jsonify({"durum": "GIRIS_BASARILI", "mesaj": mesaj, "logs": logs})
        
        # Hata kontrolü
        error_elem = loop.run_until_complete(page.query_selector("#divErrorMsg"))
        if error_elem:
            error_text = loop.run_until_complete(error_elem.inner_text())
            if error_text.strip():
                durum = "HATA"
                mesaj = error_text.strip()
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(page.goto("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx"))
        loop.run_until_complete(page.wait_for_timeout(3000))
        
        loop.run_until_complete(page.fill("#txtIban", iban))
        loop.run_until_complete(page.click("#btnQuery"))
        loop.run_until_complete(page.wait_for_timeout(2000))
        
        loop.run_until_complete(page.fill("#txtAmount", str(tutar)))
        loop.run_until_complete(page.fill("#txtDescription", aciklama))
        
        loop.run_until_complete(page.click("#btnNext"))
        loop.run_until_complete(page.wait_for_timeout(2000))
        loop.run_until_complete(page.click("#btnConfirm"))
        loop.run_until_complete(page.wait_for_timeout(3000))
        
        refs = loop.run_until_complete(page.query_selector_all(".reference-no"))
        ref = refs[0].inner_text() if refs else "Yok"
        
        log(f"✅ Transfer tamamlandı! Ref: {ref}")
        return jsonify({"durum": "BASARILI", "mesaj": "Tamamlandı", "referans": ref, "logs": logs})
        
    except Exception as e:
        log(f"❌ Transfer hatası: {e}")
        return jsonify({"durum": "HATA", "mesaj": str(e), "logs": logs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
            
