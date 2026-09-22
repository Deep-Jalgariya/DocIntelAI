from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from documents.models import Document
from ai_core.models import ChatMessage, Summary
from analytics.models import ActivityLog


@login_required
def index(request):
    """Main dashboard view with stats and recent activity."""
    user = request.user
    documents = Document.objects.filter(user=user)

    # Stats
    total_documents = documents.count()
    total_questions = ChatMessage.objects.filter(user=user, role='user').count()
    total_summaries = Summary.objects.filter(document__user=user).count()
    storage_bytes = documents.aggregate(total=Sum('file_size'))['total'] or 0
    storage_mb = round(storage_bytes / (1024 * 1024), 2)

    # Recent activity
    recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:10]
    recent_documents = documents.order_by('-uploaded_at')[:5]

    context = {
        'total_documents': total_documents,
        'total_questions': total_questions,
        'total_summaries': total_summaries,
        'storage_used': storage_mb,
        'recent_activities': recent_activities,
        'recent_documents': recent_documents,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def chart_data(request):
    """Return chart data as JSON for dashboard charts:
    - uploads/questions: daily breakdown (past 14 days)
    - summaries: monthly breakdown (past 6 months)
    """
    user = request.user
    now = timezone.now()
    today = now.date()

    # 1. Daily breakdown (past 14 days) for Line Chart (Upload & Query Analytics)
    days_list = [today - timedelta(days=i) for i in range(13, -1, -1)]
    start_daily = timezone.make_aware(timezone.datetime.combine(days_list[0], timezone.datetime.min.time()))

    uploads_qs = Document.objects.filter(user=user, uploaded_at__gte=start_daily)
    questions_qs = ChatMessage.objects.filter(user=user, role='user', created_at__gte=start_daily)

    uploads_dict = {}
    for doc in uploads_qs:
        day_key = doc.uploaded_at.strftime('%d %b')
        uploads_dict[day_key] = uploads_dict.get(day_key, 0) + 1

    questions_dict = {}
    for q in questions_qs:
        day_key = q.created_at.strftime('%d %b')
        questions_dict[day_key] = questions_dict.get(day_key, 0) + 1

    uploads_data = [{'month': d.strftime('%d %b'), 'count': uploads_dict.get(d.strftime('%d %b'), 0)} for d in days_list]
    questions_data = [{'month': d.strftime('%d %b'), 'count': questions_dict.get(d.strftime('%d %b'), 0)} for d in days_list]

    # 2. Monthly breakdown (past 6 months) for Doughnut Chart (Uploads by Period)
    import datetime
    months_list = []
    for i in range(5, -1, -1):
        year = now.year
        month = now.month - i
        if month <= 0:
            month += 12
            year -= 1
        months_list.append((year, month))

    first_yr, first_mo = months_list[0]
    start_date_6_months = timezone.make_aware(datetime.datetime(first_yr, first_mo, 1))

    monthly_docs_qs = Document.objects.filter(user=user, uploaded_at__gte=start_date_6_months)
    monthly_docs_dict = {}
    for doc in monthly_docs_qs:
        m_key = doc.uploaded_at.strftime('%b %Y')
        monthly_docs_dict[m_key] = monthly_docs_dict.get(m_key, 0) + 1

    summaries_data = []
    for yr, mo in months_list:
        dt = datetime.date(yr, mo, 1)
        m_str = dt.strftime('%b %Y')
        c = monthly_docs_dict.get(m_str, 0)
        summaries_data.append({'month': m_str, 'count': c})

    data = {
        'uploads': uploads_data,
        'questions': questions_data,
        'summaries': summaries_data,
    }
    return JsonResponse(data)
