from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('upload/', views.document_upload, name='upload'),
    path('bulk-delete/', views.document_bulk_delete, name='bulk_delete'),
    path('<int:doc_id>/', views.document_detail, name='detail'),
    path('<int:doc_id>/delete/', views.document_delete, name='delete'),
    path('<int:doc_id>/rename/', views.document_rename, name='rename'),
    path('<int:doc_id>/download/', views.document_download, name='download'),
    path('<int:doc_id>/viewer/', views.document_viewer, name='viewer'),
    path('<int:doc_id>/search/', views.search_in_document, name='search'),
]
