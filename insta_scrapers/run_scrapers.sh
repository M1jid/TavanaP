#!/bin/bash
export COMPOSE_BAKE=true
echo "[🧹 Removing old images...]"

docker compose down --rmi all --volumes --remove-orphans

echo "[🔄 Building fresh and starting all scrapers...]"
docker compose build --no-cache
docker compose up


