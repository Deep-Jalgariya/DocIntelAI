"""ASGI config for doc_intelligence project."""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doc_intelligence.settings')
application = get_asgi_application()
