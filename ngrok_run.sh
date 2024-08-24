#!/bin/bash

if [ ! -e .domain_name.txt ]; then
echo ".domain_name doesn't exists"
exit 1
fi

if [ ! -e .ngrok_token.txt ]; then
echo ".ngrok_token.txt doesn't exists"
exit 1
fi

if [ ! -e ngrok_running ]; then
docker run --net=host -it -e NGROK_AUTHTOKEN=$(cat .ngrok_token.txt) ngrok/ngrok:latest http --domain=$(cat .domain_name.txt) 443 2>/dev/null | echo ""
fi
touch ngrok_running