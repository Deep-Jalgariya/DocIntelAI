from django.urls import path
from . import views

app_name = 'ai_core'

urlpatterns = [
    # Chat
    path('chat/<int:doc_id>/', views.chat_view, name='chat'),
    path('chat/<int:doc_id>/send/', views.chat_send, name='chat_send'),
    path('chat/<int:doc_id>/clear/', views.chat_clear, name='chat_clear'),

    # Summary
    path('summary/<int:doc_id>/', views.summary_view, name='summary'),
    path('summary/<int:doc_id>/generate/', views.summary_generate, name='summary_generate'),

    # Quiz
    path('quiz/<int:doc_id>/', views.quiz_view, name='quiz'),
    path('quiz/<int:doc_id>/generate/', views.quiz_generate, name='quiz_generate'),

    # Flashcards
    path('flashcards/<int:doc_id>/', views.flashcard_view, name='flashcards'),
    path('flashcards/<int:doc_id>/generate/', views.flashcard_generate, name='flashcard_generate'),

    # Keywords
    path('keywords/<int:doc_id>/', views.keyword_view, name='keywords'),

    # NER
    path('ner/<int:doc_id>/', views.ner_view, name='ner'),

    # Topics
    path('topics/<int:doc_id>/', views.topic_view, name='topics'),

    # Insights
    path('insights/<int:doc_id>/', views.insight_view, name='insights'),
    path('insights/<int:doc_id>/generate/', views.insight_generate, name='insight_generate'),

    # Translation
    path('translate/<int:doc_id>/', views.translate_view, name='translate'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
