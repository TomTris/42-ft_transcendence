#!/bin/sh

# Start Vault server in the background
rm -rf /vault/token-volume/created
sleep 5
until nc -z -v -w30 postgres 5432
do
  echo "Waiting for PostgreSQL database connection..."
  sleep 5
done

echo "Running Vault configuration"
cat << EOF > /vault/config/vault-config.hcl
storage "postgresql" {
	connection_url = "postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB?sslmode=disable"
}


listener "tcp" {
	address = "0.0.0.0:8200"
	tls_disable = 1
}

api_addr = "http://vault:8200"
EOF

vault server -config=/vault/config/vault-config.hcl &
sleep 3

# Wait for Vault to start

# Initialize Vault and save keys to file
echo "Initializing Vault"

# Check if the length is greater than 0
if [ $(cat "/vault/file/keys.txt" | wc -c) -gt 0 ]; then
echo "skip init part, already init"
else
echo "----------1--------"
vault operator init  -key-shares=5 -key-threshold=3 > /vault/file/keys.txt

cat /vault/file/keys.txt | grep "Unseal Key 1: " | cut -c15- > /vault/file/key1 && chmod 777 /vault/file/key1
cat /vault/file/keys.txt | grep "Unseal Key 2: " | cut -c15- > /vault/file/key2 && chmod 777 /vault/file/key2
cat /vault/file/keys.txt | grep "Unseal Key 3: " | cut -c15- > /vault/file/key3 && chmod 777 /vault/file/key3
cat /vault/file/keys.txt | grep "Unseal Key 4: " | cut -c15- > /vault/file/key4 && chmod 777 /vault/file/key4
cat /vault/file/keys.txt | grep "Unseal Key 5: " | cut -c15- > /vault/file/key5 && chmod 777 /vault/file/key5

cat /vault/file/keys.txt | grep "Initial Root Token: " | cut -c21- > /vault/token-volume/rootToken && chmod 777 /vault/token-volume/rootToken
echo "----------2--------"
fi
# echo 5
vault operator unseal $(cat /vault/file/key1)
vault operator unseal $(cat /vault/file/key2)
vault operator unseal $(cat /vault/file/key3)
export VAULT_TOKEN=$(cat /vault/token-volume/rootToken)
# echo 6
# Configure Vault to use PostgreSQL as the storage backend
vault secrets enable -path=secret kv-v2
# echo 7
echo "Storing initial secrets"
# Store initial secrets
vault kv put secret/postgresql/db_credentials \
  db_name=$POSTGRES_DB \
  db_user=$POSTGRES_USER \
  db_password=$POSTGRES_PASSWORD \
  db_host=postgres \
  db_port=5432\
  \
  SECRET_KEY=$SECRET_KEY\
  DEBUG=$DEBUG\
  \
  private_key=$private_key\
  infura_url=$infura_url\
  contract_address=$contract_address\
  deployer_account=$deployer_account\
  \
  EMAIL_BACKEND=$EMAIL_BACKEND\
  EMAIL_HOST=$EMAIL_HOST\
  EMAIL_HOST_USER=$EMAIL_HOST_USER\
  EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD\
  EMAIL_PORT=$EMAIL_PORT\
  EMAIL_USE_TLS=$EMAIL_USE_TLS\
  EMAIL_USE_SSL=$EMAIL_USE_SSL\

touch /vault/token-volume/created
echo Done1
sleep 10
echo Done1
rm -rf /vault/token-volume/created
echo Done2
# # Keep the container run
wait