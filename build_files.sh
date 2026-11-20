#!/bin/bash
echo "Building project..."
python3.12 -m pip install -r requirements.txt

echo "Running database migrations..."
python3.12 manage.py migrate --noinput

echo "Collecting static files..."
python3.12 manage.py collectstatic --noinput --clear
