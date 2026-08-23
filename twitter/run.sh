#!/bin/bash

# Stop and remove existing containers
sudo docker compose -p collector down

# Start with scaling
sudo docker compose -p collector up --build --scale twitter=1
