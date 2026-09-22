from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('document/<int:doc_id>/', views.document_analytics, name='document_analytics'),
    path('usage/', views.usage_analytics, name='usage'),
]
