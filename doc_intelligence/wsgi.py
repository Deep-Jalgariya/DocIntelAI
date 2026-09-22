"""WSGI config for doc_intelligence project."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doc_intelligence.settings')
application = get_wsgi_application()
