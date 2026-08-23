#!/bin/bash

sudo docker compose down
sudo docker compose up --build --scale telegram=1 telegram
