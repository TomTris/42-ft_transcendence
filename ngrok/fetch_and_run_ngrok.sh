#!/bin/bash

sleep 4
while [ ! -e /vault/token-volume/created ] && [ $i -lt 60 ]; do
  sleep 3
done
echo "Ngrok script is running"
sleep 3

# Variables
VAULT_ADDR='http://vault:8200'
VAULT_SECRET_PATH='secret/ngork/ngrok_token'
VAULT_TOKEN=$(cat /vault/token-volume/rootToken)

# Retrieve ngrok authtoken from Vault
echo "Retrieving ngrok authtoken from Vault..."
ngrok_authtoken=$(python3 -c "
import hvac
client = hvac.Client(url='$VAULT_ADDR', token='$VAULT_TOKEN')
secret = client.secrets.kv.v2.read_secret_version(path='$VAULT_SECRET_PATH')['data']['data']
print(secret['ngrok_authtoken'])
")

domain_name=$(python3 -c "
import hvac
client = hvac.Client(url='$VAULT_ADDR', token='$VAULT_TOKEN')
secret = client.secrets.kv.v2.read_secret_version(path='$VAULT_SECRET_PATH')['data']['data']
print(secret['domain_name'])
")

if [ -z "$ngrok_authtoken" ]; then
  echo "Failed to retrieve ngrok authtoken from Vault."
  exit 1
fi

# Start ngrok with the retrieved authtoken
echo "Starting ngrok..."
ngrok http -authtoken="$ngrok_authtoken" --domain="$domain_name" 443
