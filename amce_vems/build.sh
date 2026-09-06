#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python manage.py migrate --noinput

# Collect static files into staticfiles/
python manage.py collectstatic --noinput

# Automatically seed Master Data (Vendors, 50 Criteria, Calendar, and Super Admin 'admin')
python manage.py seed_evaluation_data

