/* ════════════════════════════════════════════════════════════════
   Global App JavaScript
   Theme toggle, toasts, sidebar, utilities
   ════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSidebar();
    initScrollAnimations();
    initTooltips();
});

/* ─── Theme Management ────────────────────────────────────────── */
function initTheme() {
    // Force light theme always (dark mode removed)
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
}

function applyTheme(theme) {
    // Dark mode removed — always use light
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
}

function toggleTheme() {
    // Dark mode removed — no-op
}

/* ─── Sidebar ─────────────────────────────────────────────────── */
function initSidebar() {
    if (window._sidebarInitialized) return;
    window._sidebarInitialized = true;

    const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay') || document.querySelector('.sidebar-overlay');
    const toggles = document.querySelectorAll('#sidebar-toggle, .sidebar-toggle');

    function toggleSidebar() {
        if (!sidebar) return;
        const isOpen = sidebar.classList.contains('open') || sidebar.classList.contains('show');
        if (isOpen) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('open', 'show');
        if (overlay) overlay.classList.add('active', 'show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('open', 'show');
        if (overlay) overlay.classList.remove('active', 'show');
        document.body.style.overflow = '';
    }

    toggles.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar();
        });
    });

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSidebar();
    });

    // Reset on desktop resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 992) {
            closeSidebar();
        }
    });

    // Touch Edge Swipe Gestures (Swipe right from left screen edge to open on phone)
    let touchStartX = 0;
    let touchStartY = 0;

    document.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
        if (window.innerWidth > 992 || e.changedTouches.length !== 1) return;
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const diffX = touchEndX - touchStartX;
        const diffY = Math.abs(touchEndY - touchStartY);

        // Swipe right from left edge (x < 45px) -> Open sidebar
        if (touchStartX < 45 && diffX > 50 && diffY < 80) {
            openSidebar();
        }
        // Swipe left when sidebar is open -> Close sidebar
        else if (sidebar && (sidebar.classList.contains('open') || sidebar.classList.contains('show')) && diffX < -50 && diffY < 80) {
            closeSidebar();
        }
    }, { passive: true });
}

/* ─── Scroll Animations ───────────────────────────────────────── */
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar-landing');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 50);
        });
    }
}

/* ─── Bootstrap Tooltips ──────────────────────────────────────── */
function initTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
    }
}

/* ─── Toast Notifications ─────────────────────────────────────── */
function showToast(message, type = 'success', duration = 4000) {
    let container = document.querySelector('.toast-container-custom');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast-custom ${type}`;
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}" style="color: var(--${type === 'error' ? 'danger' : type})"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/* ─── Loading Overlay ─────────────────────────────────────────── */
function showLoading() {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-premium mx-auto mb-3"></div>
                <p class="text-muted">Processing...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    setTimeout(() => overlay.classList.add('active'), 10);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

/* ─── CSRF Token ──────────────────────────────────────────────── */
function getCsrfToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

/* ─── Copy to Clipboard ──────────────────────────────────────── */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success', 2000);
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        textarea.remove();
        showToast('Copied!', 'success', 2000);
    });
}

/* ─── Format File Size ────────────────────────────────────────── */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/* ─── Relative Time ───────────────────────────────────────────── */
function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    const intervals = {
        year: 31536000, month: 2592000, week: 604800,
        day: 86400, hour: 3600, minute: 60
    };
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
    }
    return 'Just now';
}
