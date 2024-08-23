#!/bin/sh

# Start Vault server in the background
# export VAULT_ADDR='http://127.0.0.1:8200'
sleep 5
until nc -z -v -w30 postgres 5432
do
  echo "Waiting for PostgreSQL database connection..."
  sleep 5
done

echo "Running Vault configuration"
vault server -config=/vault/config/vault-config.hcl &
sleep 3

# Wait for Vault to start

# Initialize Vault and save keys to file
# echo "Initializing Vault"
echo "----------1--------"
vault operator init  -key-shares=5 -key-threshold=3 > /vault/file/keys.txt
echo "----------2--------"
# cat /vault/file/keys.txt

cat /vault/file/keys.txt | grep "Unseal Key 1: " | cut -c15- > /vault/file/key1 && chmod 777 /vault/file/key1
cat /vault/file/keys.txt | grep "Unseal Key 2: " | cut -c15- > /vault/file/key2 && chmod 777 /vault/file/key2
cat /vault/file/keys.txt | grep "Unseal Key 3: " | cut -c15- > /vault/file/key3 && chmod 777 /vault/file/key3
cat /vault/file/keys.txt | grep "Unseal Key 4: " | cut -c15- > /vault/file/key4 && chmod 777 /vault/file/key4
cat /vault/file/keys.txt | grep "Unseal Key 5: " | cut -c15- > /vault/file/key5 && chmod 777 /vault/file/key5

cat /vault/file/keys.txt | grep "Initial Root Token: " | cut -c21- > /vault/file/rootToken && chmod 777 /vault/file/rootToken

# echo 5
vault operator unseal $(cat /vault/file/key1)
vault operator unseal $(cat /vault/file/key2)
vault operator unseal $(cat /vault/file/key3)
export VAULT_TOKEN=$(cat /vault/file/rootToken)
# echo 6
# Configure Vault to use PostgreSQL as the storage backend
vault secrets enable -path=secret kv-v2
# echo 7
echo "Storing initial secrets"
# Store initial secrets
vault kv put secret/postgresql/db_credentials \
  db_name=mydatabase \
  db_user=myuser \
  db_password=mypassword \
  db_host=postgres \
  db_port=5432
# echo 8
# # Keep the container run
wait