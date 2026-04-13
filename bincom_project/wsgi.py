"""
WSGI config for bincom_project.

Exposes the WSGI callable as a module-level variable named ``application``.
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bincom_project.settings')

application = get_wsgi_application()

# Vercel's Python runtime looks for `app`
app = application
