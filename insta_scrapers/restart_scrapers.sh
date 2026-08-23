#!/bin/bash
export COMPOSE_BAKE=true
echo "[🔁 Restarting all scrapers...]"

docker compose down

echo "[🚀 Starting with existing images and volumes...]"
docker compose up 
