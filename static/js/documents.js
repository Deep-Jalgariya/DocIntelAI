/* ════════════════════════════════════════════════════════════════
   Document Upload & Management JavaScript
   Drag & drop, progress bar, AJAX operations
   ════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function() {
    initDragDrop();
    const searchInput = document.getElementById('document-search-input');
    if (searchInput && searchInput.value) {
        filterDocumentsLive(searchInput.value);
    }
});

/* ─── Realtime Document Live Filter ───────────────────────────── */
function filterDocumentsLive(query) {
    const term = (query || '').toLowerCase().trim();
    const docCards = document.querySelectorAll('.animate-fade-in[id^="doc-"]');
    let visibleCount = 0;

    docCards.forEach(card => {
        const titleEl = card.querySelector('.doc-title');
        const titleText = titleEl ? titleEl.textContent.toLowerCase() : '';
        if (!term || titleText.includes(term)) {
            card.style.display = '';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    const noMatchesEl = document.getElementById('no-search-results');
    if (noMatchesEl) {
        if (visibleCount === 0 && docCards.length > 0) {
            noMatchesEl.classList.remove('d-none');
        } else {
            noMatchesEl.classList.add('d-none');
        }
    }
}

function initDragDrop() {
    const dropZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    if (!dropZone || !fileInput) return;

    // Click to open file picker
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    ['dragenter', 'dragover'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropZone.addEventListener(event, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleUpload(this.files[0]);
        }
    });
}

function handleUpload(file) {
    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const validExtensions = ['.pdf', '.docx', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
        showToast('Unsupported file type. Please upload PDF, DOCX, or TXT files.', 'error');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 52428800) {
        showToast('File too large. Maximum size is 50MB.', 'error');
        return;
    }

    uploadFile(file);
}

function uploadFile(file) {
    const progressContainer = document.getElementById('upload-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const uploadZone = document.getElementById('upload-zone');

    if (progressContainer) progressContainer.style.display = 'block';
    if (uploadZone) uploadZone.style.display = 'none';

    const formData = new FormData();
    formData.append('document', file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            if (progressBar) progressBar.style.width = percent + '%';
            if (progressText) progressText.textContent = `Uploading... ${percent}%`;
        }
    });

    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            if (progressText) progressText.textContent = 'Processing document...';

            setTimeout(() => {
                showToast(data.message, 'success');
                window.location.href = `/documents/${data.document_id}/`;
            }, 500);
        } else {
            const data = JSON.parse(xhr.responseText);
            showToast(data.error || 'Upload failed', 'error');
            resetUploadUI();
        }
    });

    xhr.addEventListener('error', () => {
        showToast('Upload failed. Please try again.', 'error');
        resetUploadUI();
    });

    xhr.open('POST', '/documents/upload/');
    xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
    xhr.send(formData);
}

function resetUploadUI() {
    const progressContainer = document.getElementById('upload-progress');
    const uploadZone = document.getElementById('upload-zone');
    if (progressContainer) progressContainer.style.display = 'none';
    if (uploadZone) uploadZone.style.display = 'block';
}

/* ─── Document Operations ─────────────────────────────────────── */
function deleteDocument(docId, title) {
    if (!confirm(`Delete "${title}"? This action cannot be undone.`)) return;

    fetch(`/documents/${docId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Document deleted', 'success');
            const card = document.getElementById(`doc-${docId}`);
            if (card) {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => card.remove(), 300);
            }
        }
    })
    .catch(() => showToast('Failed to delete', 'error'));
}

/* ─── Document Selection & Bulk Delete Operations ───────────────── */
function toggleSelectAll(selectAllEl) {
    const checkboxes = document.querySelectorAll('.doc-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = selectAllEl.checked;
    });
    updateSelectionState();
}

function updateSelectionState() {
    const checkboxes = document.querySelectorAll('.doc-checkbox');
    const checkedCount = document.querySelectorAll('.doc-checkbox:checked').length;
    const selectAllEl = document.getElementById('select-all-docs');
    const btnBulkDelete = document.getElementById('btn-bulk-delete');
    const countSpan = document.getElementById('selected-count');

    if (countSpan) countSpan.textContent = checkedCount;

    if (btnBulkDelete) {
        if (checkedCount > 0) {
            btnBulkDelete.classList.remove('d-none');
            btnBulkDelete.classList.add('d-flex');
        } else {
            btnBulkDelete.classList.add('d-none');
            btnBulkDelete.classList.remove('d-flex');
        }
    }

    if (selectAllEl && checkboxes.length > 0) {
        selectAllEl.checked = checkedCount === checkboxes.length;
        selectAllEl.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

function deleteSelectedDocuments() {
    const checkedBoxes = document.querySelectorAll('.doc-checkbox:checked');
    const docIds = Array.from(checkedBoxes).map(cb => cb.value);

    if (docIds.length === 0) return;

    if (!confirm(`Are you sure you want to delete ${docIds.length} selected document(s)? This action cannot be undone.`)) return;

    fetch('/documents/bulk-delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ doc_ids: docIds })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`${data.count} document(s) deleted successfully`, 'success');
            docIds.forEach(id => {
                const card = document.getElementById(`doc-${id}`);
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.9)';
                    setTimeout(() => card.remove(), 300);
                }
            });
            setTimeout(() => {
                updateSelectionState();
                const remaining = document.querySelectorAll('.doc-card');
                if (remaining.length === 0) {
                    window.location.reload();
                }
            }, 350);
        } else {
            showToast(data.error || 'Failed to delete selected documents', 'error');
        }
    })
    .catch(() => showToast('Failed to delete selected documents', 'error'));
}

function renameDocument(docId) {
    const newTitle = prompt('Enter new document name:');
    if (!newTitle || !newTitle.trim()) return;

    fetch(`/documents/${docId}/rename/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCsrfToken()
        },
        body: `title=${encodeURIComponent(newTitle.trim())}`
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('Document renamed', 'success');
            const titleEl = document.querySelector(`#doc-${docId} .doc-title`);
            if (titleEl) titleEl.textContent = data.title;
        }
    })
    .catch(() => showToast('Failed to rename', 'error'));
}
