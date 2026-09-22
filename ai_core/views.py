import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from documents.models import Document
from .models import Summary, ChatMessage, Quiz, Flashcard, Keyword, Topic, Entity, Insight
from .ai_engine import (
    chat_with_document, generate_summary, generate_quiz,
    generate_flashcards, generate_insights, translate_text,
    generate_suggested_questions
)
from .embeddings import search_similar_chunks
from .nlp_utils import extract_entities_spacy, extract_keywords, detect_topics
from analytics.models import ActivityLog


# ─── Chat with Document ────────────────────────────────────────────────

@login_required
def chat_view(request, doc_id):
    """Render the chat interface."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    messages = ChatMessage.objects.filter(document=doc, user=request.user).order_by('created_at')

    # Generate suggested questions if no messages yet
    suggested = []
    if not messages.exists() and doc.text_content:
        try:
            suggested = generate_suggested_questions(doc.text_content)
        except Exception:
            suggested = [
                "What is this document about?",
                "What are the key points?",
                "Summarize the main findings.",
                "What conclusions are drawn?",
                "Who is the target audience?"
            ]

    return render(request, 'ai_core/chat.html', {
        'document': doc,
        'messages': messages,
        'suggested_questions': suggested,
    })


@login_required
def chat_send(request, doc_id):
    """Handle chat message and return AI response."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        data = json.loads(request.body)
        query = data.get('message', '').strip()
    except json.JSONDecodeError:
        query = request.POST.get('message', '').strip()

    if not query:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    # Save user message
    ChatMessage.objects.create(
        document=doc, user=request.user, role='user', content=query
    )

    try:
        # Search for relevant chunks
        context_chunks = search_similar_chunks(doc.id, query, top_k=5)

        if not context_chunks:
            # Fallback: use first part of document
            context_chunks = [{'text': doc.text_content[:3000], 'score': 1.0, 'chunk_index': 0}]

        # Get chat history
        history = list(
            ChatMessage.objects.filter(document=doc, user=request.user)
            .order_by('-created_at')[:10]
            .values('role', 'content')
        )
        history.reverse()

        # Generate AI response
        response_text = chat_with_document(query, context_chunks, history)

        # Build sources
        sources = [
            {'text': c['text'][:200] + '...', 'chunk_index': c.get('chunk_index', 0)}
            for c in context_chunks[:3]
        ]

        # Save assistant message
        ChatMessage.objects.create(
            document=doc, user=request.user, role='assistant',
            content=response_text, sources=sources
        )

        # Log activity
        ActivityLog.objects.create(
            user=request.user, action_type='chat', document=doc,
            details=f'Asked: "{query[:80]}"'
        )

        return JsonResponse({
            'response': response_text,
            'sources': sources,
        })

    except Exception as e:
        return JsonResponse({
            'response': f'Sorry, I encountered an error: {str(e)}. Please check your API key and try again.',
            'sources': [],
        })


@login_required
def chat_clear(request, doc_id):
    """Clear chat history for a document."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    ChatMessage.objects.filter(document=doc, user=request.user).delete()
    return JsonResponse({'status': 'success'})


# ─── Summary ──────────────────────────────────────────────────────────

@login_required
def summary_view(request, doc_id):
    """Render summary page with existing summaries."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    summaries = Summary.objects.filter(document=doc)
    return render(request, 'ai_core/summary.html', {
        'document': doc,
        'summaries': {s.summary_type: s for s in summaries},
    })


@login_required
def summary_generate(request, doc_id):
    """Generate a summary of specified type."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        data = json.loads(request.body)
        summary_type = data.get('type', 'medium')
    except json.JSONDecodeError:
        summary_type = request.POST.get('type', 'medium')

    if not doc.text_content:
        return JsonResponse({'error': 'Document has no text content'}, status=400)

    try:
        content = generate_summary(doc.text_content, summary_type)

        # Save or update summary
        summary, created = Summary.objects.update_or_create(
            document=doc, summary_type=summary_type,
            defaults={'content': content}
        )

        ActivityLog.objects.create(
            user=request.user, action_type='summary', document=doc,
            details=f'Generated {summary_type} summary'
        )

        return JsonResponse({
            'content': content,
            'type': summary_type,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── Quiz ─────────────────────────────────────────────────────────────

@login_required
def quiz_view(request, doc_id):
    """Render quiz page."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    quizzes = Quiz.objects.filter(document=doc)
    return render(request, 'ai_core/quiz.html', {
        'document': doc,
        'quizzes': quizzes,
    })


@login_required
def quiz_generate(request, doc_id):
    """Generate a quiz."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        data = json.loads(request.body)
        quiz_type = data.get('type', 'mcq')
        difficulty = data.get('difficulty', 'medium')
        num_questions = int(data.get('num_questions', 5))
    except (json.JSONDecodeError, ValueError):
        quiz_type = 'mcq'
        difficulty = 'medium'
        num_questions = 5

    try:
        questions = generate_quiz(doc.text_content, quiz_type, difficulty, num_questions)

        quiz = Quiz.objects.create(
            document=doc, quiz_type=quiz_type,
            difficulty=difficulty, questions=questions
        )

        ActivityLog.objects.create(
            user=request.user, action_type='quiz', document=doc,
            details=f'Generated {quiz_type} quiz ({difficulty})'
        )

        return JsonResponse({
            'quiz_id': quiz.id,
            'questions': questions,
            'type': quiz_type,
            'difficulty': difficulty,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── Flashcards ───────────────────────────────────────────────────────

@login_required
def flashcard_view(request, doc_id):
    """Render flashcard page."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    flashcard_sets = Flashcard.objects.filter(document=doc)
    return render(request, 'ai_core/flashcards.html', {
        'document': doc,
        'flashcard_sets': flashcard_sets,
    })


@login_required
def flashcard_generate(request, doc_id):
    """Generate flashcards."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        data = json.loads(request.body)
        num_cards = int(data.get('num_cards', 10))
    except (json.JSONDecodeError, ValueError):
        num_cards = 10

    try:
        cards = generate_flashcards(doc.text_content, num_cards)

        flashcard = Flashcard.objects.create(
            document=doc, cards=cards
        )

        ActivityLog.objects.create(
            user=request.user, action_type='flashcard', document=doc,
            details=f'Generated {len(cards)} flashcards'
        )

        return JsonResponse({
            'flashcard_id': flashcard.id,
            'cards': cards,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── Keywords ─────────────────────────────────────────────────────────

@login_required
def keyword_view(request, doc_id):
    """Extract and display keywords."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    # Check if keywords already extracted
    keywords = list(Keyword.objects.filter(document=doc).values('word', 'frequency', 'importance'))

    if not keywords and doc.text_content:
        # Extract keywords
        extracted = extract_keywords(doc.text_content)
        for kw in extracted:
            Keyword.objects.create(
                document=doc,
                word=kw['word'],
                frequency=kw['frequency'],
                importance=kw['importance']
            )
        keywords = extracted

    return render(request, 'ai_core/keywords.html', {
        'document': doc,
        'keywords': keywords,
    })


# ─── NER ──────────────────────────────────────────────────────────────

@login_required
def ner_view(request, doc_id):
    """Extract and display named entities with strict validation."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    from .nlp_utils import is_valid_entity

    # Purge existing invalid/misclassified entities from database
    existing_entities = Entity.objects.filter(document=doc)
    for ent in list(existing_entities):
        if not is_valid_entity(ent.entity_type, ent.text):
            ent.delete()

    entities = Entity.objects.filter(document=doc)

    if not entities.exists() and doc.text_content:
        # Re-extract clean entities using AI & spaCy
        extracted = extract_entities_spacy(doc.text_content)
        for entity_type, items in extracted.items():
            for item in items:
                if is_valid_entity(entity_type, item['text']):
                    Entity.objects.create(
                        document=doc,
                        entity_type=entity_type,
                        text=item['text'],
                        count=item['count']
                    )
        entities = Entity.objects.filter(document=doc)

    # Group by type
    entity_groups = {}
    for entity in entities:
        if entity.entity_type not in entity_groups:
            entity_groups[entity.entity_type] = []
        entity_groups[entity.entity_type].append(entity)

    return render(request, 'ai_core/ner.html', {
        'document': doc,
        'entity_groups': entity_groups,
    })


# ─── Topics ───────────────────────────────────────────────────────────

@login_required
def topic_view(request, doc_id):
    """Detect and display topics."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    topics = list(Topic.objects.filter(document=doc).values('name', 'confidence'))

    if not topics and doc.text_content:
        detected = detect_topics(doc.text_content)
        for t in detected:
            Topic.objects.create(
                document=doc,
                name=t['name'],
                confidence=t.get('confidence', 0.5)
            )
        topics = detected

    return render(request, 'ai_core/topics.html', {
        'document': doc,
        'topics': topics,
    })


# ─── Insights ─────────────────────────────────────────────────────────

@login_required
def insight_view(request, doc_id):
    """Generate and display AI insights."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        insight = Insight.objects.get(document=doc)
        insights_data = insight.content
    except Insight.DoesNotExist:
        insights_data = None

    return render(request, 'ai_core/insights.html', {
        'document': doc,
        'insights': insights_data,
    })


@login_required
def insight_generate(request, doc_id):
    """Generate insights via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        insights_data = generate_insights(doc.text_content)

        insight, created = Insight.objects.update_or_create(
            document=doc,
            defaults={'content': insights_data}
        )

        ActivityLog.objects.create(
            user=request.user, action_type='insight', document=doc,
            details='Generated AI insights'
        )

        return JsonResponse({'insights': insights_data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── Translation ──────────────────────────────────────────────────────

@login_required
def translate_view(request, doc_id):
    """Translate summary."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'hi')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        translated = translate_text(text, language)
        return JsonResponse({'translated': translated, 'language': language})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─── Settings Page ────────────────────────────────────────────────────

@login_required
def settings_view(request):
    """Render settings page."""
    return render(request, 'ai_core/settings.html')
