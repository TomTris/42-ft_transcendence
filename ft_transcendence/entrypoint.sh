#!/bin/sh
# Wait for the Postgres container to be ready
# Optionally, you can add a wait-for-it or similar script to handle waiting for Postgres to be available.

# Run migrations
sleep 2
i=0
while [ ! -e /vault/file/created ] && [ $i -lt 60 ]; do
  sleep 2
  echo "Script is running"
  i=$(($i + 1))
done

echo "Script is going to finish"
sleep 3
python manage.py makemigrations users
python manage.py makemigrations pages
python manage.py makemigrations chat
python manage.py makemigrations game
python manage.py makemigrations 
python manage.py migrate

# Start the Django development server
python manage.py runserver 0.0.0.0:8000