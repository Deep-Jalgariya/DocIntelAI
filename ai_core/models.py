from django.db import models
from django.contrib.auth.models import User
from documents.models import Document


class Summary(models.Model):
    """AI-generated document summary."""
    SUMMARY_TYPES = [
        ('short', 'Short Summary'),
        ('medium', 'Medium Summary'),
        ('detailed', 'Detailed Summary'),
        ('bullet', 'Bullet Points'),
        ('executive', 'Executive Summary'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='summaries')
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPES)
    content = models.TextField()
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Summaries'

    def __str__(self):
        return f"{self.get_summary_type_display()} - {self.document.title}"


class ChatMessage(models.Model):
    """Chat message between user and AI about a document."""
    ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField()
    sources = models.JSONField(blank=True, null=True)  # [{page, text}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class Quiz(models.Model):
    """AI-generated quiz from document."""
    QUIZ_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blanks'),
        ('short', 'Short Questions'),
    ]
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    questions = models.JSONField()  # List of question objects
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return f"{self.get_quiz_type_display()} ({self.difficulty}) - {self.document.title}"


class Flashcard(models.Model):
    """AI-generated flashcards from document."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='flashcards')
    cards = models.JSONField()  # [{front, back}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Flashcards - {self.document.title}"


class Keyword(models.Model):
    """Extracted keyword from document."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='keywords')
    word = models.CharField(max_length=100)
    frequency = models.IntegerField(default=0)
    importance = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-importance']

    def __str__(self):
        return f"{self.word} ({self.frequency})"


class Topic(models.Model):
    """Detected topic from document."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    confidence = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-confidence']

    def __str__(self):
        return f"{self.name} ({self.confidence:.0%})"


class Entity(models.Model):
    """Named entity extracted from document."""
    ENTITY_TYPES = [
        ('PERSON', 'Person'),
        ('ORG', 'Organization'),
        ('GPE', 'Location'),
        ('DATE', 'Date'),
        ('MONEY', 'Money'),
        ('PHONE', 'Phone Number'),
        ('EMAIL', 'Email'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='entities')
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    text = models.CharField(max_length=500)
    count = models.IntegerField(default=1)

    class Meta:
        ordering = ['entity_type', '-count']
        verbose_name_plural = 'Entities'

    def __str__(self):
        return f"{self.text} ({self.entity_type})"


class Insight(models.Model):
    """AI-generated insights from document."""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='insights')
    content = models.JSONField()  # {objective, facts, dates, numbers, action_items, conclusion, recommendations}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Insights - {self.document.title}"
