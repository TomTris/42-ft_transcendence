#!/bin/bash

if [ ! -e ngrok_running ]; then
docker run --net=host -it -e NGROK_AUTHTOKEN=$(cat ./.env | grep "NGROK_AUTHTOKEN=" | cut -c17- | sed "s/^['\"]//;s/['\"]$//") \
        ngrok/ngrok:latest http --domain=$(cat ./.env | grep "DOMAIN_NAME=" | cut -c14- | sed "s/^['\"]//;s/['\"]$//") 443 2>/dev/null | echo ""
touch ngrok_running
fi