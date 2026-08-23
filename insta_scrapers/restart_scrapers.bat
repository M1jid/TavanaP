#!/bin/bash
echo "[♻️ Restarting all scrapers...]"

docker-compose down

echo "[🚀 Starting containers and streaming logs...]"
docker-compose up --build

