#!/bin/bash
# Vercel build step — collect static files into staticfiles_build/static
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
mkdir -p staticfiles_build
cp -r staticfiles staticfiles_build/static
