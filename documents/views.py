import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.contrib import messages
from django.db.models import Q
from .models import Document, DocumentChunk
from .utils import extract_text, clean_text, count_text_stats, split_into_chunks
from analytics.models import ActivityLog


@login_required
def document_list(request):
    """List all user documents with search, filter, sort."""
    documents = Document.objects.filter(user=request.user)

    # Search
    search = request.GET.get('search', '')
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | Q(text_content__icontains=search)
        )

    # Filter by type
    file_type = request.GET.get('type', '')
    if file_type:
        documents = documents.filter(file_type=file_type)

    # Sort
    sort = request.GET.get('sort', '-uploaded_at')
    if sort in ['title', '-title', 'uploaded_at', '-uploaded_at', 'file_size', '-file_size']:
        documents = documents.order_by(sort)

    context = {
        'documents': documents,
        'search': search,
        'file_type': file_type,
        'sort': sort,
    }
    return render(request, 'documents/document_list.html', context)


@login_required
def document_upload(request):
    """Handle document upload with processing."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Validate file type
        ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
        if ext not in ['pdf', 'docx', 'txt']:
            return JsonResponse({'error': 'Unsupported file type. Please upload PDF, DOCX, or TXT.'}, status=400)

        # Validate file size (50MB max)
        if uploaded_file.size > 52428800:
            return JsonResponse({'error': 'File too large. Maximum size is 50MB.'}, status=400)

        # Create document
        doc = Document.objects.create(
            user=request.user,
            title=os.path.splitext(uploaded_file.name)[0],
            file=uploaded_file,
            file_type=ext,
            file_size=uploaded_file.size,
        )

        # Process document
        try:
            text, page_count = extract_text(doc.file.path, ext)
            text = clean_text(text)
            stats = count_text_stats(text)

            doc.text_content = text
            doc.page_count = page_count if ext == 'pdf' else 1
            doc.word_count = stats['word_count']
            doc.char_count = stats['char_count']
            doc.paragraph_count = stats['paragraph_count']
            doc.save()

            # Split into chunks
            chunks = split_into_chunks(text)
            
            # Efficiently bulk insert all chunks in a single query
            chunk_objects = [
                DocumentChunk(
                    document=doc,
                    chunk_text=chunk,
                    chunk_index=i,
                    page_number=1
                )
                for i, chunk in enumerate(chunks)
            ]
            DocumentChunk.objects.bulk_create(chunk_objects)

            # Generate embeddings in the background to prevent request timing out
            import threading
            from django import db

            def run_indexing_background(doc_id, chunks_list):
                try:
                    from ai_core.embeddings import create_faiss_index
                    create_faiss_index(doc_id, chunks_list)
                    
                    # Mark document as fully processed
                    d = Document.objects.get(id=doc_id)
                    d.is_processed = True
                    d.save()
                except Exception as ex:
                    print(f"Background embedding generation failed: {ex}")
                finally:
                    db.connections.close_all()

            threading.Thread(
                target=run_indexing_background,
                args=(doc.id, chunks),
                daemon=True
            ).start()

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action_type='upload',
                document=doc,
                details=f'Uploaded "{doc.title}"'
            )

            return JsonResponse({
                'status': 'success',
                'document_id': doc.id,
                'title': doc.title,
                'message': 'Document uploaded and processing started in the background!'
            })
        except Exception as e:
            doc.save()
            return JsonResponse({
                'status': 'success',
                'document_id': doc.id,
                'title': doc.title,
                'message': f'Document uploaded. Text extraction had issues: {str(e)}'
            })

    return render(request, 'documents/upload.html')


@login_required
def document_detail(request, doc_id):
    """Document detail/viewer page."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    context = {
        'document': doc,
        'stats': count_text_stats(doc.text_content) if doc.text_content else {},
    }
    return render(request, 'documents/document_detail.html', context)


@login_required
def document_delete(request, doc_id):
    """Delete a document."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    title = doc.title
    doc.delete()

    ActivityLog.objects.create(
        user=request.user,
        action_type='delete',
        details=f'Deleted "{title}"'
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    messages.success(request, f'Document "{title}" deleted.')
    return redirect('documents:list')


@login_required
def document_bulk_delete(request):
    """Bulk delete selected documents."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            doc_ids = data.get('doc_ids', [])
        except Exception:
            doc_ids = request.POST.getlist('doc_ids[]')

        if not doc_ids:
            return JsonResponse({'error': 'No documents selected'}, status=400)

        docs = Document.objects.filter(user=request.user, id__in=doc_ids)
        count = docs.count()
        for doc in docs:
            ActivityLog.objects.create(
                user=request.user,
                action_type='delete',
                details=f'Deleted "{doc.title}"'
            )
        docs.delete()
        return JsonResponse({'status': 'success', 'count': count})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def document_rename(request, doc_id):
    """Rename a document."""
    if request.method == 'POST':
        doc = get_object_or_404(Document, id=doc_id, user=request.user)
        new_title = request.POST.get('title', '').strip()
        if new_title:
            old_title = doc.title
            doc.title = new_title
            doc.save()
            ActivityLog.objects.create(
                user=request.user,
                action_type='rename',
                document=doc,
                details=f'Renamed "{old_title}" to "{new_title}"'
            )
            return JsonResponse({'status': 'success', 'title': new_title})
        return JsonResponse({'error': 'Title cannot be empty'}, status=400)
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def document_download(request, doc_id):
    """Download original document file."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    if doc.file and os.path.exists(doc.file.path):
        return FileResponse(
            open(doc.file.path, 'rb'),
            as_attachment=True,
            filename=f"{doc.title}.{doc.file_type}"
        )
    raise Http404("File not found")


@login_required
def document_viewer(request, doc_id):
    """Full PDF/document viewer page."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    context = {
        'document': doc,
    }
    return render(request, 'documents/viewer.html', context)


@login_required
def search_in_document(request, doc_id):
    """Search text within a document."""
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    query = request.GET.get('q', '').strip()

    if not query or not doc.text_content:
        return JsonResponse({'results': [], 'count': 0})

    text = doc.text_content
    paragraphs = text.split('\n\n')
    results = []
    total_count = 0

    for i, para in enumerate(paragraphs):
        if query.lower() in para.lower():
            count = para.lower().count(query.lower())
            total_count += count
            # Highlight matches
            import re
            highlighted = re.sub(
                f'({re.escape(query)})',
                r'<mark>\1</mark>',
                para,
                flags=re.IGNORECASE
            )
            results.append({
                'paragraph': i + 1,
                'text': highlighted,
                'occurrences': count,
            })

    return JsonResponse({
        'results': results,
        'count': total_count,
        'query': query,
    })
