storage "postgresql" {
  connection_url = "postgres://myuser:mypassword@postgres:5432/mydatabase?sslmode=disable"
}


listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://vault:8200"
