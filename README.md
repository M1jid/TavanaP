# TavanaP

**Multi-platform social intelligence pipeline** — collect, stream, store, and analyze public content from Telegram, Twitter/X, Instagram, and RSS at scale.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
[![Kafka](https://img.shields.io/badge/Apache-Kafka-231F20.svg)](https://kafka.apache.org/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-Search-005571.svg)](https://www.elastic.co/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<p dir="rtl">
<strong>توانا‌پی</strong> یک پلتفرم جامع جمع‌آوری و تحلیل داده از شبکه‌های اجتماعی است: تلگرام، توییتر/X، اینستاگرام و RSS — با معماری رویدادمحور، مقیاس‌پذیر و آمادهٔ پروداکشن.
</p>

---

## Why TavanaP?

| | English | فارسی |
|---|---|---|
| **Ingest** | Multi-account Telegram, Twitter (Nitter), Instagram scrapers, RSS feeds | جمع‌آوری چنداکانتی تلگرام، توییتر، اینستاگرام و فیدهای RSS |
| **Stream** | Kafka + KSQL for real-time routing and enrichment | استریم بلادرنگ با Kafka و KSQL |
| **Store** | Elasticsearch for search, MinIO for media, PostgreSQL for metadata, Redis for cache | ذخیره در Elasticsearch، MinIO، PostgreSQL و Redis |
| **Serve** | FastAPI reporting & admin APIs, delivery bots, channel bridges | API گزارش‌گیری، ربات‌ها و بریج کانال‌ها |
| **Ops** | Dockerized services, proxy rotation, GitLab CI samples | سرویس‌های داکری، چرخش پروکسی، نمونه CI |

---

## Architecture

```text
  Telegram / Twitter / Instagram / RSS
                 │
                 ▼
        ┌─────────────────┐
        │  Collectors     │  telegram · twitter · nitter · insta_scrapers · rss
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  Kafka / KSQL   │  topics · streams · connectors
        └────────┬────────┘
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 Elasticsearch  MinIO    PostgreSQL
     │
     ▼
  report API  ·  delivery  ·  bots
```

### Repository map

| Path | Role |
|------|------|
| `telegram/` | Multi-account Telegram collector (FastAPI + Telethon-style clients) |
| `twitter/` | Twitter/X collection service |
| `nitter/` | Nitter-based Twitter frontend/helper stack |
| `instagram/` · `insta_scrapers/` | Instagram scrapers (multi-worker) |
| `rss/` | Async RSS fetch & Kafka publish |
| `db/` | Metadata / CRUD FastAPI service (channels, users, accounts, …) |
| `report/` | Analytics & reporting API (trends, posts, wordclouds, …) |
| `delivery/` | Downstream delivery pipeline |
| `bots/` | Telegram admin / routing bots |
| `telegram_account_manager/` | Account lifecycle helper service |
| `utils/` | Shared Kafka, ES, Redis, MinIO, proxy helpers |
| `docker-compose.yml` | Local Postgres, Redis, Nginx, PgAdmin |

---

## Quick start

### 1. Prerequisites

- Docker & Docker Compose  
- Python 3.9+ (for local service runs)  
- Access to Kafka, Elasticsearch, MinIO (or your own cluster)

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — never commit real secrets
```

### 3. Core infra (local)

```bash
docker compose up -d
```

### 4. Run a service (example: Telegram)

```bash
cd telegram
pip install -r requirements.txt
# Ensure .env is loaded / mounted
./run.sh   # or: python main.py
```

Each service has its own `Dockerfile`, `docker-compose.yml`, and `run.sh` / `stop.sh`.

> **فارسی:** ابتدا `.env.example` را کپی کنید، مقادیر را پر کنید، با `docker compose up -d` زیرساخت محلی را بالا بیاورید، سپس هر سرویس را جدا اجرا کنید.

---

## Security checklist (important)

Before publishing or sharing this repo:

- [x] `.env` is gitignored — use `.env.example` only  
- [x] `certs/`, `proxy/`, `metadata/`, session files ignored  
- [x] Hardcoded bot tokens removed from source (use env / placeholders)  
- [ ] **Revoke any previously leaked Telegram bot tokens** (BotFather → revoke)  
- [ ] Rotate DB, MinIO, Elasticsearch, and JWT secrets if they ever left your machine  
- [ ] Keep Instagram/Twitter session files out of git  

```bash
# Local-only secrets stay local
cp .env.example .env
```

---

## Stack

- **API:** FastAPI, Uvicorn, Pydantic  
- **Messaging:** Apache Kafka, KSQLDB  
- **Search & storage:** Elasticsearch, MinIO (S3), PostgreSQL, Redis  
- **Collectors:** Telegram multi-account, Nitter, Instagram workers, RSS  
- **Proxy:** Xray config rotation  
- **CI:** `.gitlab-ci.yml` sample for image build/deploy  

---

## Contributing

1. Fork & create a feature branch  
2. Keep secrets out of commits (run a quick `git diff` check)  
3. Prefer small, focused PRs per service  

Issues and PRs for collectors, connectors, and docs are welcome.

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.

---

## Persian overview / معرفی فارسی

**توانا‌پی** پلتفرم جمع‌آوری و هوش اجتماعی چندمنبعی است که برای مقیاس سازمانی طراحی شده:

- **جمع‌آوری:** مانیتورینگ کانال/گروه تلگرام با چند اکانت، توییتر، اینستاگرام، RSS  
- **پردازش:** صف و استریم با Kafka/KSQL، کش Redis، رسانه روی MinIO  
- **تحلیل و API:** سرویس `report` برای ترند، پست، وردکلاد و مدیریت کوئری/کانال کاربر  
- **عملیات:** داکر، پروکسی چرخشی، جداسازی سرویس‌ها برای دیپلوی مستقل  

اگر این پروژه برایتان مفید بود، ⭐ استار بدهید تا بیشتر دیده شود.

---

<p align="center">
  Built for real-time social data · آماده برای دادهٔ اجتماعی بلادرنگ
</p>
