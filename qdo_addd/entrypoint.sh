#!/bin/sh
# Wait for the Postgres container to be ready
# Optionally, you can add a wait-for-it or similar script to handle waiting for Postgres to be available.

# Run migrations
cd /app
clear
echo "12310"
ls
echo "1231a"
python3 manage.py makemigrations users
echo "1232a"
python3 manage.py migrate
echo "1233a"

# Start the Django development server
python3 manage.py runserver 0.0.0.0:8000
echo "1234a"