from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'file_type', 'file_size_display', 'page_count', 'word_count', 'is_processed', 'uploaded_at')
    list_filter = ('file_type', 'is_processed', 'uploaded_at')
    search_fields = ('title', 'user__username', 'text_content')
    readonly_fields = ('uploaded_at', 'updated_at')
    date_hierarchy = 'uploaded_at'


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'page_number')
    list_filter = ('document',)
