from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from documents.models import Document
from documents.utils import count_text_stats
from .models import ActivityLog
from collections import Counter
import re


@login_required
def document_analytics(request, doc_id):
    """Display detailed analytics for a document."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)

    stats = {}
    most_common_words = []
    longest_paragraph = ""

    if doc.text_content:
        stats = count_text_stats(doc.text_content)
        stats['page_count'] = doc.page_count

        # Most common words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', doc.text_content.lower())
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were', 'been',
                      'have', 'has', 'had', 'not', 'but', 'what', 'all', 'can', 'from', 'they',
                      'will', 'would', 'there', 'their', 'which', 'about', 'also', 'more', 'other'}
        filtered = [w for w in words if w not in stop_words]
        most_common_words = Counter(filtered).most_common(15)

        # Longest paragraph
        paragraphs = [p for p in doc.text_content.split('\n\n') if p.strip()]
        if paragraphs:
            longest_paragraph = max(paragraphs, key=len)
            if len(longest_paragraph) > 500:
                longest_paragraph = longest_paragraph[:500] + '...'

    return render(request, 'analytics/document_analytics.html', {
        'document': doc,
        'stats': stats,
        'most_common_words': most_common_words,
        'longest_paragraph': longest_paragraph,
    })


@login_required
def usage_analytics(request):
    """Overall usage analytics."""
    activities = ActivityLog.objects.filter(user=request.user)

    context = {
        'total_activities': activities.count(),
        'recent_activities': activities[:20],
    }
    return render(request, 'analytics/usage.html', context)
