#!/bin/bash

sudo docker stop telegram-test
sudo docker rm telegram-test
sudo docker build -t telegram-test .

sudo docker run -it --rm --name telegram-test \
  -v "$(pwd)/../metadata:/code/metadata" \
  -v "$(pwd)/../utils:/code/utils" \
  -v "$(pwd)/../.env:/code/.env" \
  -v "$(pwd)/../models:/code/models" \
  -v "$(pwd)/../certs:/code/certs" \
  -e MODE=DEVELOPMENT \
  --network services_app-network \
  --add-host=host.docker.internal:host-gateway \
  telegram-test
