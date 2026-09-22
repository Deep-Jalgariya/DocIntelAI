from django.contrib import admin
from .models import Summary, ChatMessage, Quiz, Flashcard, Keyword, Topic, Entity, Insight


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('document', 'summary_type', 'language', 'created_at')
    list_filter = ('summary_type', 'language', 'created_at')
    search_fields = ('document__title', 'content')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'document__title', 'user__username')

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Content'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('document', 'quiz_type', 'difficulty', 'question_count', 'created_at')
    list_filter = ('quiz_type', 'difficulty', 'created_at')

    def question_count(self, obj):
        return len(obj.questions) if obj.questions else 0
    question_count.short_description = 'Questions'


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('document', 'card_count', 'created_at')
    list_filter = ('created_at',)

    def card_count(self, obj):
        return len(obj.cards) if obj.cards else 0
    card_count.short_description = 'Cards'


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ('document', 'word', 'frequency', 'importance')
    list_filter = ('document',)
    search_fields = ('word',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('document', 'name', 'confidence')
    list_filter = ('document',)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('document', 'entity_type', 'text', 'count')
    list_filter = ('entity_type', 'document')
    search_fields = ('text',)


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('document', 'created_at')
    list_filter = ('created_at',)
