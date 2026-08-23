#!/bin/bash
export COMPOSE_BAKE=true
echo "[🔄 Building fresh and starting all scrapers...]"

docker-compose build --no-cache
docker-compose up

