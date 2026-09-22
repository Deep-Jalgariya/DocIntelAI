import os
from django.db import models
from django.contrib.auth.models import User


def document_upload_path(instance, filename):
    """Generate upload path: media/documents/user_id/filename"""
    return f'documents/user_{instance.user.id}/{filename}'


class Document(models.Model):
    """Uploaded document with extracted text and metadata."""
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.BigIntegerField(default=0)  # in bytes
    page_count = models.IntegerField(default=0)
    word_count = models.IntegerField(default=0)
    char_count = models.IntegerField(default=0)
    paragraph_count = models.IntegerField(default=0)
    text_content = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        # Delete FAISS index if exists
        from django.conf import settings
        index_path = os.path.join(settings.FAISS_INDEX_DIR, f'doc_{self.id}')
        if os.path.exists(index_path):
            import shutil
            shutil.rmtree(index_path)
        super().delete(*args, **kwargs)


class DocumentChunk(models.Model):
    """Text chunk from a document for RAG retrieval."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(default=1)

    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
