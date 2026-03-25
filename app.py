import json
import os
import sqlite3
import time
import uuid
import random
import unicodedata
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash
from flask_cors import CORS


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.environ.get("TOKEN_DB_PATH", os.path.join(DATA_DIR, "app.db"))

FLASK_SECRET = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

# ADMIN IBAN BİLGİLERİ (Coin değil, banka transferi)
ADMIN_IBAN = os.environ.get("ADMIN_IBAN", "TR000000000000000000000000")
ADMIN_AD_SOYAD = os.environ.get("ADMIN_AD_SOYAD", "ADMIN AD SOYAD")
ADMIN_BANKA = os.environ.get("ADMIN_BANKA", "Enpara")

# RENDER.COM PostgreSQL (varsa kullan, yoksa SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL", "")

TOKEN_LOGIN_URL = os.environ.get("TOKEN_LOGIN_URL", "https://internetsubesi.enpara.com/Login/LoginPage.aspx").strip()
TOKEN_FIELD_ISLEM_NO = os.environ.get("TOKEN_FIELD_ISLEM_NO_SELECTOR", "#txtuserid")
TOKEN_FIELD_KULLANICI_ADI = os.environ.get("TOKEN_FIELD_KULLANICI_ADI_SELECTOR", "#txtpass")
TOKEN_SUBMIT_SELECTOR = os.environ.get("TOKEN_SUBMIT_SELECTOR", "#ctl00_MainContent_lbtnNext")
TOKEN_SUCCESS_SELECTOR = os.environ.get("TOKEN_SUCCESS_SELECTOR", "").strip()
TOKEN_SUCCESS_URL_SUBSTRING = os.environ.get("TOKEN_SUCCESS_URL_SUBSTRING", "Default.aspx").strip()
SELENIUM_TIMEOUT_SEC = int(os.environ.get("SELENIUM_TIMEOUT_SEC", "20"))

# UI transfer settings (Enpara)
USE_UI_TRANSFER = os.environ.get("USE_UI_TRANSFER", "1") == "1"
TRANSFER_MENU_SELECTOR = os.environ.get("TRANSFER_MENU_SELECTOR", "a.Sub_menu_head")
TRANSFER_MENU_TEXT = os.environ.get("TRANSFER_MENU_TEXT", "TRANSFER")
TRANSFER_OTHER_SELECTOR = os.environ.get(
    "TRANSFER_OTHER_SELECTOR",
    "a[onclick*='MoneyTransferToOtherAccountVirtualMain']",
)
TRANSFER_IFRAME_SELECTOR = os.environ.get("TRANSFER_IFRAME_SELECTOR", "#MyPlaceHolder")
TRANSFER_TYPE_DROPDOWN_INPUT = os.environ.get("TRANSFER_TYPE_DROPDOWN_INPUT", "#ctl00_MainContent_TransferTypeDropDownList_Input")
TRANSFER_TYPE_DROPDOWN_ARROW = os.environ.get("TRANSFER_TYPE_DROPDOWN_ARROW", "#ctl00_MainContent_TransferTypeDropDownList_Arrow")
TRANSFER_TYPE_VALUE = os.environ.get("TRANSFER_TYPE_VALUE", "07")
TRANSFER_IBAN_SELECTOR = os.environ.get("TRANSFER_IBAN_SELECTOR", "#ctl00_MainContent_IBANTextBox")
TRANSFER_RECIPIENT_SELECTOR = os.environ.get("TRANSFER_RECIPIENT_SELECTOR", "#ctl00_MainContent_RecipientNameTextBox")
TRANSFER_AMOUNT_SELECTOR = os.environ.get("TRANSFER_AMOUNT_SELECTOR", "#ctl00_MainContent_TransferAmountTextBox")
TRANSFER_DESC_SELECTOR = os.environ.get("TRANSFER_DESC_SELECTOR", "").strip()
TRANSFER_SUBMIT_SELECTOR = os.environ.get("TRANSFER_SUBMIT_SELECTOR", "#ctl00_MainContent_NextButton")
TRANSFER_CONFIRM_SELECTOR = os.environ.get("TRANSFER_CONFIRM_SELECTOR", "#ctl00_MainContent_NavigationControl_ConfirmButton")
TRANSFER_SUCCESS_SELECTOR = os.environ.get("TRANSFER_SUCCESS_SELECTOR", ".DialogFieldImageSuccess")
TRANSFER_SUCCESS_URL_SUBSTRING = os.environ.get("TRANSFER_SUCCESS_URL_SUBSTRING", "Default.aspx")
TRANSFER_ERROR_SELECTOR = os.environ.get("TRANSFER_ERROR_SELECTOR", ".hata_msj, .error")
TRANSFER_OTP_URL_SUBSTRING = os.environ.get("TRANSFER_OTP_URL_SUBSTRING", "MobileApprovePage.aspx")
TRANSFER_OTP_INPUT_SELECTOR = os.environ.get("TRANSFER_OTP_INPUT_SELECTOR", "").strip()
TRANSFER_OTP_SUBMIT_SELECTOR = os.environ.get("TRANSFER_OTP_SUBMIT_SELECTOR", "").strip()
TRANSFER_DESCRIPTION = os.environ.get("TRANSFER_DESCRIPTION", "Ihale Teminat Odemesi")
UI_SESSION_TTL_SEC = int(os.environ.get("UI_SESSION_TTL_SEC", "300"))

PENDING_UI_SESSIONS = {}

app = Flask(__name__, template_folder=os.path.join(APP_DIR, "templates"))
app.secret_key = FLASK_SECRET
CORS(app, origins="*")  # PHP sitesinden erişim için CORS açık

# ====================== VERİTABANI (SQLite / PostgreSQL) ======================
def get_db_connection():
    """Render'da PostgreSQL, local'de SQLite"""
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Veritabanı tablolarını oluştur"""
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # PostgreSQL tabloları
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ihaleler (
                id SERIAL PRIMARY KEY,
                ad VARCHAR(255) NOT NULL,
                sure VARCHAR(50) NOT NULL,
                teminat_tutar DECIMAL(10,2) NOT NULL,
                aciklama TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS token_links (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL UNIQUE,
                islem_no VARCHAR(100) NOT NULL,
                kullanici_adi VARCHAR(100) NOT NULL,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                ihale_id INTEGER NOT NULL,
                tutar DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) NOT NULL,
                txn_id VARCHAR(100),
                banka_adi VARCHAR(100),
                gonderen_iban VARCHAR(50),
                alici_iban VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transfer_log (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                ihale_id INTEGER,
                tutar DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) NOT NULL,
                hata_mesaji TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    else:
        # SQLite
        os.makedirs(DATA_DIR, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ihaleler (
                    id INTEGER PRIMARY KEY,
                    ad TEXT NOT NULL,
                    sure TEXT NOT NULL,
                    teminat_tutar REAL NOT NULL,
                    aciklama TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS token_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    islem_no TEXT NOT NULL,
                    kullanici_adi TEXT NOT NULL,
                    linked_at TEXT NOT NULL
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    ihale_id INTEGER NOT NULL,
                    tutar REAL NOT NULL,
                    status TEXT NOT NULL,
                    txn_id TEXT,
                    banka_adi TEXT,
                    gonderen_iban TEXT,
                    alici_iban TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transfer_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    ihale_id INTEGER,
                    tutar REAL NOT NULL,
                    status TEXT NOT NULL,
                    hata_mesaji TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()

# ====================== HUMAN-LIKE HELPER FUNCTIONS ======================
def human_delay(min_sec=0.8, max_sec=2.8):
    time.sleep(random.uniform(min_sec, max_sec))

def human_type(element, text):
    from selenium.webdriver.common.keys import Keys
    element.click()
    element.clear()
    for char in str(text):
        element.send_keys(char)
        time.sleep(random.uniform(0.04, 0.22))
    human_delay(0.4, 1.0)

def human_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        human_delay(0.6, 1.5)
        element.click()
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            raise e

# ====================== SELENIUM DRIVER SETUP ======================
def get_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        
        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        raise Exception(f"Selenium driver başlatılamadı: {e}")

# ====================== ENPARA TRANSFER (İNSAN GİBİ) ======================
def perform_enpara_transfer(driver, amount, selectors, user_id, ihale_id):
    """
    Enpara'dan Admin IBAN'ına para transferi
    """
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(driver, 25)
        
        # Log kaydı
        log_transfer(user_id, ihale_id, amount, "started", "Transfer başlatıldı")

        human_delay(1.5, 3.0)

        # Transfer menüsü
        if selectors.get("TRANSFER_MENU_SELECTOR"):
            menu = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["TRANSFER_MENU_SELECTOR"])))
            human_click(driver, menu)
            human_delay(1.2, 2.5)

        # Diğer hesaba transfer
        if selectors.get("TRANSFER_OTHER_SELECTOR"):
            other = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["TRANSFER_OTHER_SELECTOR"])))
            human_click(driver, other)
            human_delay(1.8, 3.2)

        # Iframe
        if selectors.get("TRANSFER_IFRAME_SELECTOR"):
            wait.until(EC.frame_to_be_available_and_switch_to_it(selectors["TRANSFER_IFRAME_SELECTOR"]))

        # Transfer tipi seç (Başka Hesaba = 07)
        if selectors.get("TRANSFER_TYPE_DROPDOWN_INPUT"):
            type_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["TRANSFER_TYPE_DROPDOWN_INPUT"])))
            human_click(driver, type_input)
            human_delay(0.8, 1.6)
            if selectors.get("TRANSFER_TYPE_DROPDOWN_ARROW"):
                arrow = driver.find_element(By.CSS_SELECTOR, selectors["TRANSFER_TYPE_DROPDOWN_ARROW"])
                human_click(driver, arrow)
            human_delay(1.0, 2.0)
            # Değer seç
            transfer_type = selectors.get("TRANSFER_TYPE_VALUE", "07")
            driver.execute_script(f"arguments[0].value = '{transfer_type}';", type_input)

        # Admin IBAN gir
        iban_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["TRANSFER_IBAN_SELECTOR"])))
        human_type(iban_el, ADMIN_IBAN)

        # Admin Ad Soyad gir
        rec_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["TRANSFER_RECIPIENT_SELECTOR"])))
        human_type(rec_el, ADMIN_AD_SOYAD)

        # Tutar gir (Türkçe format: 1.234,56)
        amount_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["TRANSFER_AMOUNT_SELECTOR"])))
        human_type(amount_el, f"{amount:.2f}".replace(".", ","))

        # Açıklama gir (varsa)
        if selectors.get("TRANSFER_DESC_SELECTOR"):
            try:
                desc_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["TRANSFER_DESC_SELECTOR"])))
                aciklama = selectors.get("TRANSFER_DESCRIPTION", f"Ihale-{ihale_id} Teminat")
                human_type(desc_el, aciklama)
            except:
                pass

        human_delay(1.2, 2.5)

        # İleri butonu
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["TRANSFER_SUBMIT_SELECTOR"])))
        human_click(driver, submit)

        human_delay(1.5, 3.0)

        # Onay butonu
        if selectors.get("TRANSFER_CONFIRM_SELECTOR"):
            confirm = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selectors["TRANSFER_CONFIRM_SELECTOR"]))
            )
            human_click(driver, confirm)

        # Push onay sayfası kontrolü
        if selectors.get("PUSH_APPROVE_PAGE_URL_SUBSTRING") and selectors["PUSH_APPROVE_PAGE_URL_SUBSTRING"] in driver.current_url:
            session_id = uuid.uuid4().hex
            PENDING_UI_SESSIONS[session_id] = {
                "driver": driver, 
                "created_at": time.time(),
                "user_id": user_id,
                "ihale_id": ihale_id,
                "amount": amount
            }
            log_transfer(user_id, ihale_id, amount, "needs_push", "Push onay bekleniyor")
            return {
                "status": "needs_push",
                "txn_id": session_id,
                "message": "Telefonunuzdan Enpara push bildirimini onaylayın.",
                "alici_iban": ADMIN_IBAN,
                "alici_ad_soyad": ADMIN_AD_SOYAD
            }

        # Hata kontrolü
        if selectors.get("TRANSFER_ERROR_SELECTOR"):
            try:
                err_el = driver.find_element(By.CSS_SELECTOR, selectors["TRANSFER_ERROR_SELECTOR"])
                err_text = err_el.text.strip()
                if err_text:
                    log_transfer(user_id, ihale_id, amount, "error", err_text)
                    return {"status": "error", "error": err_text}
            except:
                pass

        # Başarı kontrolü
        if selectors.get("TRANSFER_SUCCESS_URL_SUBSTRING") and selectors["TRANSFER_SUCCESS_URL_SUBSTRING"] in driver.current_url:
            log_transfer(user_id, ihale_id, amount, "success", "Transfer tamamlandı")
            return {
                "status": "success",
                "message": f"{amount} TL {ADMIN_AD_SOYAD} ({ADMIN_IBAN}) hesabına gönderildi",
                "alici_iban": ADMIN_IBAN,
                "alici_ad_soyad": ADMIN_AD_SOYAD
            }

        if selectors.get("TRANSFER_SUCCESS_SELECTOR"):
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selectors["TRANSFER_SUCCESS_SELECTOR"])))
                log_transfer(user_id, ihale_id, amount, "success", "Transfer tamamlandı")
                return {
                    "status": "success",
                    "message": f"{amount} TL {ADMIN_AD_SOYAD} ({ADMIN_IBAN}) hesabına gönderildi",
                    "alici_iban": ADMIN_IBAN,
                    "alici_ad_soyad": ADMIN_AD_SOYAD
                }
            except:
                pass

        return {
            "status": "success",
            "message": "Transfer işlemi tamamlandı",
            "alici_iban": ADMIN_IBAN,
            "alici_ad_soyad": ADMIN_AD_SOYAD
        }

    except Exception as e:
        error_msg = str(e)
        log_transfer(user_id, ihale_id, amount, "error", error_msg)
        return {"status": "error", "error": error_msg}

# ====================== VERİTABANI FONKSİYONLARI ======================
def log_transfer(user_id, ihale_id, tutar, status, hata_mesaji=None):
    """Transfer log kaydı"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if DATABASE_URL and DATABASE_URL.startswith("postgres"):
            cur.execute("""
                INSERT INTO transfer_log (user_id, ihale_id, tutar, status, hata_mesaji)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, ihale_id, tutar, status, hata_mesaji))
        else:
            cur.execute("""
                INSERT INTO transfer_log (user_id, ihale_id, tutar, status, hata_mesaji, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, ihale_id, tutar, status, hata_mesaji, utc_now()))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Log hatası: {e}")

def utc_now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def db_fetch_one(query, params=()):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        cur.execute(query, params)
        row = cur.fetchone()
        result = dict(zip([desc[0] for desc in cur.description], row)) if row else None
    else:
        cur.execute(query, params)
        row = cur.fetchone()
        result = dict(row) if row else None
    
    cur.close()
    conn.close()
    return result

def db_fetch_all(query, params=()):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
    else:
        cur.execute(query, params)
        rows = cur.fetchall()
        result = [dict(row) for row in rows]
    
    cur.close()
    conn.close()
    return result

def db_execute(query, params=()):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        cur.execute(query, params)
    else:
        cur.execute(query, params)
    
    lastrowid = cur.lastrowid
    conn.commit()
    cur.close()
    conn.close()
    return lastrowid

def get_user_id():
    user_id = (
        request.args.get("user_id")
        or request.headers.get("X-User-Id")
        or session.get("user_id")
    )
    if not user_id:
        user_id = "demo_user"
    session["user_id"] = user_id
    return user_id

def parse_amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None
    if amount <= 0:
        return None
    return float(amount.quantize(Decimal("0.01")))

def is_token_linked(user_id):
    return db_fetch_one("SELECT * FROM token_links WHERE user_id = %s" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT * FROM token_links WHERE user_id = ?", (user_id,)) is not None

def upsert_token_link(user_id, islem_no, kullanici_adi):
    existing = db_fetch_one("SELECT * FROM token_links WHERE user_id = %s" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT * FROM token_links WHERE user_id = ?", (user_id,))
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        if existing:
            db_execute("""
                UPDATE token_links SET islem_no = %s, kullanici_adi = %s, linked_at = NOW() WHERE user_id = %s
            """, (islem_no, kullanici_adi, user_id))
        else:
            db_execute("""
                INSERT INTO token_links (user_id, islem_no, kullanici_adi) VALUES (%s, %s, %s)
            """, (user_id, islem_no, kullanici_adi))
    else:
        if existing:
            db_execute("""
                UPDATE token_links SET islem_no = ?, kullanici_adi = ?, linked_at = ? WHERE user_id = ?
            """, (islem_no, kullanici_adi, utc_now(), user_id))
        else:
            db_execute("""
                INSERT INTO token_links (user_id, islem_no, kullanici_adi, linked_at) VALUES (?, ?, ?, ?)
            """, (user_id, islem_no, kullanici_adi, utc_now()))

def record_payment(user_id, ihale_id, tutar, status, txn_id=None, banka_adi=None):
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        return db_execute("""
            INSERT INTO payments (user_id, ihale_id, tutar, status, txn_id, banka_adi, alici_iban, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (user_id, ihale_id, tutar, status, txn_id, banka_adi, ADMIN_IBAN))
    else:
        now = utc_now()
        return db_execute("""
            INSERT INTO payments (user_id, ihale_id, tutar, status, txn_id, banka_adi, alici_iban, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, ihale_id, tutar, status, txn_id, banka_adi, ADMIN_IBAN, now, now))

def update_payment_status(payment_id, status):
    if DATABASE_URL and DATABASE_URL.startswith("postgres"):
        db_execute("UPDATE payments SET status = %s, updated_at = NOW() WHERE id = %s", (status, payment_id))
    else:
        db_execute("UPDATE payments SET status = ?, updated_at = ? WHERE id = ?", (status, utc_now(), payment_id))

def get_pending_payment(user_id):
    query = "SELECT * FROM payments WHERE user_id = %s AND status = 'pending_otp' ORDER BY id DESC LIMIT 1" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT * FROM payments WHERE user_id = ? AND status = 'pending_otp' ORDER BY id DESC LIMIT 1"
    return db_fetch_one(query, (user_id,))

def get_token_credentials(user_id):
    query = "SELECT islem_no, kullanici_adi FROM token_links WHERE user_id = %s" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT islem_no, kullanici_adi FROM token_links WHERE user_id = ?"
    row = db_fetch_one(query, (user_id,))
    if not row:
        return None, None
    return row.get("islem_no"), row.get("kullanici_adi")

def cleanup_pending_ui_sessions():
    now = time.time()
    expired = []
    for key, entry in list(PENDING_UI_SESSIONS.items()):
        if now - entry.get("created_at", now) > UI_SESSION_TTL_SEC:
            expired.append(key)
    for key in expired:
        entry = PENDING_UI_SESSIONS.pop(key, None)
        driver = entry.get("driver") if entry else None
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def open_token_session(islem_no, kullanici_adi):
    if not TOKEN_LOGIN_URL:
        time.sleep(1.0)
        return False, "TOKEN_LOGIN_URL tanimli degil", None

    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:
        return False, f"Selenium import error: {exc}", None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(TOKEN_LOGIN_URL)
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT_SEC)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, TOKEN_FIELD_ISLEM_NO)))
        user_el = driver.find_element(By.CSS_SELECTOR, TOKEN_FIELD_ISLEM_NO)
        pass_el = driver.find_element(By.CSS_SELECTOR, TOKEN_FIELD_KULLANICI_ADI)

        user_el.click()
        user_el.send_keys(Keys.CONTROL + "a")
        user_el.send_keys(islem_no)

        pass_el.click()
        pass_el.send_keys(Keys.CONTROL + "a")
        pass_el.send_keys(kullanici_adi)

        driver.find_element(By.CSS_SELECTOR, TOKEN_SUBMIT_SELECTOR).click()

        if TOKEN_SUCCESS_SELECTOR:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, TOKEN_SUCCESS_SELECTOR)))
        elif TOKEN_SUCCESS_URL_SUBSTRING:
            wait.until(lambda drv: TOKEN_SUCCESS_URL_SUBSTRING in drv.current_url)
        else:
            time.sleep(1.5)

        return True, "ok", driver
    except Exception as exc:
        driver.quit()
        return False, f"Token login failed: {exc}", None

def link_token_account(islem_no, kullanici_adi):
    if not TOKEN_LOGIN_URL:
        time.sleep(1.0)
        return True, "Simulated token link"

    ok, message, driver = open_token_session(islem_no, kullanici_adi)
    if driver:
        driver.quit()
    return ok, "Token account linked" if ok else message

# ====================== API ROUTES ======================
@app.route("/api/banka-ekle", methods=["POST"])
def banka_ekle():
    """
    PHP'den banka bilgisi ekleme
    {
        "user_id": "123",
        "banka_id": 1,
        "banka_adi": "Enpara",
        "islem_no": "123456789",
        "kullanici_adi": "sifre123"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "error": "JSON data gerekli"}), 400
    
    user_id = data.get("user_id")
    banka_id = data.get("banka_id")
    banka_adi = data.get("banka_adi", "Enpara")
    islem_no = data.get("islem_no")
    kullanici_adi = data.get("kullanici_adi")
    
    if not all([user_id, islem_no, kullanici_adi]):
        return jsonify({"status": "error", "error": "user_id, islem_no ve kullanici_adi zorunlu"}), 400
    
    # Token doğrula
    success, message = link_token_account(islem_no, kullanici_adi)
    if not success:
        return jsonify({"status": "error", "error": message}), 400
    
    # Veritabanına kaydet
    upsert_token_link(user_id, islem_no, kullanici_adi)
    
    return jsonify({
        "status": "success",
        "message": f"{banka_adi} hesabı bağlandı",
        "user_id": user_id
    })

@app.route("/api/odeme-yap", methods=["POST"])
def api_odeme_yap():
    """
    PHP'den ödeme yapma
    {
        "user_id": "123",
        "ihale_id": 456,
        "tutar": 1250.75,
        "banka_id": 1,
        "selectors": { ... }  // Opsiyonel, varsayılan Enpara
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "error": "JSON data gerekli"}), 400
    
    user_id = data.get("user_id")
    ihale_id = data.get("ihale_id", 1)
    tutar = parse_amount(data.get("tutar"))
    selectors = data.get("selectors", {})
    
    if not user_id:
        return jsonify({"status": "error", "error": "user_id zorunlu"}), 400
    
    if not tutar:
        return jsonify({"status": "error", "error": "Geçerli tutar gerekli"}), 400
    
    # Varsayılan Enpara seçicileri
    if not selectors:
        selectors = {
            "TRANSFER_MENU_SELECTOR": TRANSFER_MENU_SELECTOR,
            "TRANSFER_MENU_TEXT": TRANSFER_MENU_TEXT,
            "TRANSFER_OTHER_SELECTOR": TRANSFER_OTHER_SELECTOR,
            "TRANSFER_IFRAME_SELECTOR": TRANSFER_IFRAME_SELECTOR,
            "TRANSFER_TYPE_DROPDOWN_INPUT": TRANSFER_TYPE_DROPDOWN_INPUT,
            "TRANSFER_TYPE_DROPDOWN_ARROW": TRANSFER_TYPE_DROPDOWN_ARROW,
            "TRANSFER_TYPE_VALUE": TRANSFER_TYPE_VALUE,
            "TRANSFER_IBAN_SELECTOR": TRANSFER_IBAN_SELECTOR,
            "TRANSFER_RECIPIENT_SELECTOR": TRANSFER_RECIPIENT_SELECTOR,
            "TRANSFER_AMOUNT_SELECTOR": TRANSFER_AMOUNT_SELECTOR,
            "TRANSFER_SUBMIT_SELECTOR": TRANSFER_SUBMIT_SELECTOR,
            "TRANSFER_CONFIRM_SELECTOR": TRANSFER_CONFIRM_SELECTOR,
            "TRANSFER_SUCCESS_URL_SUBSTRING": TRANSFER_SUCCESS_URL_SUBSTRING,
            "TRANSFER_SUCCESS_SELECTOR": TRANSFER_SUCCESS_SELECTOR,
            "TRANSFER_ERROR_SELECTOR": TRANSFER_ERROR_SELECTOR,
            "PUSH_APPROVE_PAGE_URL_SUBSTRING": TRANSFER_OTP_URL_SUBSTRING,
            "TRANSFER_DESC_SELECTOR": TRANSFER_DESC_SELECTOR,
            "TRANSFER_DESCRIPTION": TRANSFER_DESCRIPTION
        }
    
    # Token kontrol
    islem_no, kullanici_adi = get_token_credentials(user_id)
    if not islem_no or not kullanici_adi:
        return jsonify({"status": "error", "error": "Banka hesabı bağlı değil. Önce /api/banka-ekle kullanın"}), 400
    
    # Oturum aç
    ok, message, driver = open_token_session(islem_no, kullanici_adi)
    if not ok or not driver:
        return jsonify({"status": "error", "error": message}), 500
    
    # Transfer yap
    try:
        result = perform_enpara_transfer(driver, tutar, selectors, user_id, ihale_id)
    except Exception as exc:
        driver.quit()
        return jsonify({"status": "error", "error": f"Transfer hatası: {exc}"}), 500
    
    # Sonuç işle
    if result.get("status") == "needs_push":
        payment_id = record_payment(user_id, ihale_id, tutar, "pending_otp", result.get("txn_id"), "Enpara")
        return jsonify({
            "status": "needs_push",
            "payment_id": payment_id,
            "txn_id": result.get("txn_id"),
            "message": result.get("message"),
            "alici_iban": ADMIN_IBAN,
            "alici_ad_soyad": ADMIN_AD_SOYAD
        })
    
    if result.get("status") == "success":
        record_payment(user_id, ihale_id, tutar, "completed", None, "Enpara")
        # Driver kapat
        try:
            driver.quit()
        except:
            pass
        return jsonify({
            "status": "success",
            "message": result.get("message"),
            "tutar": tutar,
            "alici_iban": ADMIN_IBAN,
            "alici_ad_soyad": ADMIN_AD_SOYAD
        })
    
    # Hata durumunda driver kapat
    try:
        driver.quit()
    except:
        pass
    
    return jsonify({
        "status": "error",
        "error": result.get("error", "Transfer başarısız")
    }), 500

@app.route("/api/push-onayla", methods=["POST"])
def api_push_onayla():
    """
    PHP'den push bildirimini kontrol et (veya OTP kodu ile onayla)
    {
        "user_id": "123",
        "txn_id": "abc123..."
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "error": "JSON data gerekli"}), 400
    
    txn_id = data.get("txn_id")
    
    if not txn_id:
        return jsonify({"status": "error", "error": "txn_id zorunlu"}), 400
    
    cleanup_pending_ui_sessions()
    entry = PENDING_UI_SESSIONS.get(txn_id)
    
    if not entry:
        return jsonify({"status": "error", "error": "Oturum bulunamadı veya süre doldu"}), 400
    
    driver = entry.get("driver")
    user_id = entry.get("user_id")
    ihale_id = entry.get("ihale_id")
    amount = entry.get("amount")
    
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        
        wait = WebDriverWait(driver, 5)  # Kısa bekle, push zaten onaylanmış olmalı
        
        # Başarı kontrolü
        success = False
        
        # URL kontrolü
        if TRANSFER_SUCCESS_URL_SUBSTRING in driver.current_url:
            success = True
        
        # Selector kontrolü
        if not success and TRANSFER_SUCCESS_SELECTOR:
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, TRANSFER_SUCCESS_SELECTOR)))
                success = True
            except:
                pass
        
        # Hata kontrolü
        if not success and TRANSFER_ERROR_SELECTOR:
            try:
                err_el = driver.find_element(By.CSS_SELECTOR, TRANSFER_ERROR_SELECTOR)
                err_text = err_el.text.strip()
                if err_text:
                    return jsonify({"status": "error", "error": err_text}), 400
            except:
                pass
        
        if success:
            # Ödemeyi tamamla
            pending = get_pending_payment(user_id)
            if pending:
                update_payment_status(pending["id"], "completed")
            
            log_transfer(user_id, ihale_id, amount, "success", "Push onaylandı")
            
            return jsonify({
                "status": "success",
                "message": f"{amount} TL başarıyla gönderildi",
                "alici_iban": ADMIN_IBAN,
                "alici_ad_soyad": ADMIN_AD_SOYAD
            })
        else:
            return jsonify({
                "status": "pending",
                "message": "Henüz onaylanmamış veya sayfa yükleniyor"
            })
            
    finally:
        PENDING_UI_SESSIONS.pop(txn_id, None)
        if driver:
            try:
                driver.quit()
            except:
                pass

@app.route("/api/durum-kontrol/<user_id>", methods=["GET"])
def api_durum_kontrol(user_id):
    """Kullanıcının son ödeme durumunu kontrol et"""
    payments = db_fetch_all(
        "SELECT * FROM payments WHERE user_id = %s ORDER BY created_at DESC LIMIT 5" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (user_id,)
    )
    
    token = db_fetch_one(
        "SELECT * FROM token_links WHERE user_id = %s" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SELECT * FROM token_links WHERE user_id = ?",
        (user_id,)
    )
    
    return jsonify({
        "status": "success",
        "banka_bagli": token is not None,
        "banka_bilgisi": {
            "islem_no": token.get("islem_no")[:6] + "****" if token else None,
            "linked_at": token.get("linked_at") if token else None
        } if token else None,
        "son_odemeler": payments
    })

@app.route("/api/admin-bilgi", methods=["GET"])
def api_admin_bilgi():
    """Admin IBAN bilgilerini döndür (PHP'den çağrılacak)"""
    return jsonify({
        "status": "success",
        "admin_iban": ADMIN_IBAN,
        "admin_ad_soyad": ADMIN_AD_SOYAD,
        "admin_banka": ADMIN_BANKA
    })

@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({
        "status": "ok",
        "admin_banka": ADMIN_BANKA,
        "veritabani": "PostgreSQL" if DATABASE_URL and DATABASE_URL.startswith("postgres") else "SQLite"
    })

# ====================== BAŞLATMA ======================
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))  # Render PORT env kullanır
    app.run(host="0.0.0.0", port=port, debug=False)
