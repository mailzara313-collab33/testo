FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Playwright + Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m playwright install chromium

CMD ["gunicorn", "app:app", "--workers", "1", "--threads", "2", "--timeout", "120", "--bind", "0.0.0.0:10000"]
