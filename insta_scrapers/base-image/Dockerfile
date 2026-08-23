xFROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# نصب پکیج‌های مورد نیاز سیستمی
RUN apt-get update && apt-get install -y \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نصب Playwright و مرورگرها
RUN playwright install --with-deps
