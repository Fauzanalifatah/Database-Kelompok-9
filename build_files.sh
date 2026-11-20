#!/bin/bash
echo "=== BUILD START ==="

# Install dependencies using python3
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Run database migrations to Supabase
python3 manage.py migrate --noinput || true

# Collect static files
python3 manage.py collectstatic --noinput --clear

echo "=== BUILD END ==="
