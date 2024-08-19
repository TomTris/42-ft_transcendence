#!/bin/sh
# Wait for the Postgres container to be ready
# Optionally, you can add a wait-for-it or similar script to handle waiting for Postgres to be available.

# Run migrations
sleep 5
python manage.py makemigrations users
python manage.py migrate

# Start the Django development server
python manage.py runserver 0.0.0.0:8000