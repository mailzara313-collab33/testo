# ============================================
# ENPARA TRANSFER API - DOCKERFILE
# Python 3.11 + Chrome + ChromeDriver + Selenium
# ============================================

FROM python:3.11-slim-bookworm

# ============================================
# SİSTEM GÜNCELLEME VE BAĞIMLILIKLAR
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome için gerekli kütüphaneler
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    # Temel araçlar
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# CHROME KURULUMU (Stable)
# ============================================
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Chrome versionunu kontrol et (log için)
RUN google-chrome --version

# ============================================
# CHROMEDRIVER KURULUMU
# ============================================
# Chrome versiyonuna uygun ChromeDriver'ı indir
RUN CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //' | sed 's/ //g') \
    && CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \
    && DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION") \
    && wget -q "https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && chromedriver --version

# ============================================
# PYTHON ORTAMI
# ============================================
WORKDIR /app

# requirements.txt'i kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================
# UYGULAMA KODU
# ============================================
COPY . .

# Veritabanı dizini (SQLite için)
RUN mkdir -p /app/data && chmod 777 /app/data

# ============================================
# ÇEVRE DEĞİŞKENLERİ
# ============================================
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Flask varsayılanları
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# ============================================
# SAĞLIK KONTROLÜ
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5001}/healthz || exit 1

# ============================================
# PORT VE BAŞLATMA
# ============================================
EXPOSE 5001

# Render.com $PORT env kullanır, yoksa 5001
CMD exec gunicorn app:app --bind 0.0.0.0:${PORT:-5001} --workers 1 --threads 2 --timeout 120 --keep-alive 5 --log-level info
