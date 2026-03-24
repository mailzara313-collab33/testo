# (sadece önemli yerleri kısaltmadan full veriyorum)

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

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        log("✅ Chromium başlatıldı!")
        return True
    except Exception as e:
        log(f"❌ Driver hata: {e}")
        return False


@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Bot</title>
</head>
<body>

<h2>ENPARA BOT</h2>

<input id="tc" placeholder="TC"><br><br>
<input id="sifre" placeholder="Şifre"><br><br>

<input id="iban" placeholder="IBAN"><br><br>
<input id="tutar" placeholder="Tutar"><br><br>

<button onclick="baslat()">BAŞLAT</button>

<h3 id="status"></h3>
<pre id="logs"></pre>

<script>
async function baslat(){
    const tc = document.getElementById('tc').value;
    const sifre = document.getElementById('sifre').value;

    const res = await fetch('/giris',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({tc,sifre})
    });

    const data = await res.json();
    guncelle(data);

    kontrol();
}

async function kontrol(){
    setInterval(async ()=>{
        const res = await fetch('/kontrol');
        const data = await res.json();

        guncelle(data);

        if(data.durum === "GIRIS_BASARILI"){
            transfer();
        }
    },3000);
}

async function transfer(){
    const iban = document.getElementById('iban').value;
    const tutar = document.getElementById('tutar').value;

    const res = await fetch('/transfer',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({iban,tutar})
    });

    const data = await res.json();
    guncelle(data);
}

function guncelle(data){
    document.getElementById("status").innerText = data.durum + " - " + data.mesaj;
    if(data.logs){
        document.getElementById("logs").innerText = data.logs.join("\\n");
    }
}
</script>

</body>
</html>
""")

@app.route('/giris', methods=['POST'])
def giris():
    global durum, mesaj, driver
    
    data = request.json
    tc = data.get("tc")
    sifre = data.get("sifre")

    log("🚀 giriş başladı")

    if driver is None:
        if not create_driver():
            return jsonify({"durum":"HATA","mesaj":"driver yok","logs":logs})

    try:
        driver.get("https://internetsubesi.enpara.com/Login/LoginPage.aspx")
        time.sleep(2)

        driver.find_element(By.ID,"txtuserid").send_keys(tc)
        driver.find_element(By.ID,"txtpass").send_keys(sifre)
        driver.find_element(By.ID,"ctl00_MainContent_lbtnNext").click()

        durum="MOBIL_ONAY_BEKLIYOR"
        mesaj="onay ver"

        return jsonify({"durum":durum,"mesaj":mesaj,"logs":logs})

    except Exception as e:
        log(str(e))
        return jsonify({"durum":"HATA","mesaj":str(e),"logs":logs})


@app.route('/kontrol')
def kontrol():
    global durum, mesaj

    try:
        if "AccountSummary" in driver.current_url:
            durum="GIRIS_BASARILI"
            mesaj="giriş başarılı"

        return jsonify({"durum":durum,"mesaj":mesaj,"logs":logs})

    except Exception as e:
        return jsonify({"durum":"HATA","mesaj":str(e)})


@app.route('/transfer', methods=['POST'])
def transfer():
    global durum

    data=request.json
    iban=data.get("iban")
    tutar=data.get("tutar")

    try:
        driver.get("https://internetsubesi.enpara.com/Transfer/TransferToAccount.aspx")
        time.sleep(2)

        driver.find_element(By.ID,"txtIban").send_keys(iban)
        driver.find_element(By.ID,"txtAmount").send_keys(tutar)

        driver.find_element(By.ID,"btnNext").click()
        driver.find_element(By.ID,"btnConfirm").click()

        return jsonify({"durum":"BASARILI","mesaj":"ok","logs":logs})

    except Exception as e:
        return jsonify({"durum":"HATA","mesaj":str(e),"logs":logs})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
