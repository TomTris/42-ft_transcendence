#!/bin/sh
# Wait for the Postgres container to be ready
# Optionally, you can add a wait-for-it or similar script to handle waiting for Postgres to be available.

# Run migrations
sleep 15
i=0
while [ ! -e /vault/token-volume/created ] && [ $i -lt 60 ]; do
  sleep 3
  echo "Script is running"
  i=$(($i + 1))
done
echo "Script is running"
sleep 3
echo "Script is going to finish"
python manage.py makemigrations users
python manage.py makemigrations pages
python manage.py makemigrations chat
python manage.py makemigrations game
python manage.py makemigrations 
python manage.py migrate

# Start the Django development server
echo "Server On\nNow we are back and more powerful!!" > /app/users/send_to_subscribers.txt
python manage.py collectstatic && python manage.py send_email && python manage.py runserver 0.0.0.0:8000