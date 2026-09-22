from django.db import models
from django.contrib.auth.models import User
from documents.models import Document


class ActivityLog(models.Model):
    """Log of user activities for analytics."""
    ACTION_TYPES = [
        ('upload', 'Document Upload'),
        ('delete', 'Document Delete'),
        ('rename', 'Document Rename'),
        ('chat', 'Chat Question'),
        ('summary', 'Summary Generated'),
        ('quiz', 'Quiz Generated'),
        ('flashcard', 'Flashcards Generated'),
        ('insight', 'Insights Generated'),
        ('export', 'Document Export'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"

    @property
    def icon(self):
        icons = {
            'upload': 'fa-cloud-upload-alt',
            'delete': 'fa-trash-alt',
            'rename': 'fa-edit',
            'chat': 'fa-comments',
            'summary': 'fa-align-left',
            'quiz': 'fa-question-circle',
            'flashcard': 'fa-clone',
            'insight': 'fa-lightbulb',
            'export': 'fa-download',
        }
        return icons.get(self.action_type, 'fa-circle')

    @property
    def color(self):
        colors = {
            'upload': '#2563eb',
            'delete': '#ef4444',
            'rename': '#f59e0b',
            'chat': '#8b5cf6',
            'summary': '#14b8a6',
            'quiz': '#ec4899',
            'flashcard': '#06b6d4',
            'insight': '#f97316',
            'export': '#10b981',
        }
        return colors.get(self.action_type, '#6b7280')
