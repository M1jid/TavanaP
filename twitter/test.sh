#!/bin/bash

sudo docker stop twitter-test
sudo docker rm twitter-test
sudo docker build -t twitter-test .

sudo docker run -it --rm --name twitter-test \
  -e MODE=DEVELOPMENT \
  --network services_app-network \
  --add-host=host.docker.internal:host-gateway \
  twitter
