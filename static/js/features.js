/* ════════════════════════════════════════════════════════════════
   Text-to-Speech Controls
   ════════════════════════════════════════════════════════════════ */

let ttsUtterance = null;
let ttsState = 'stopped'; // stopped, playing, paused
let ttsSpeed = 1.0; // global speed variable
let ttsCurrentText = ''; // store current text for restart

function initTTS(text) {
    if (!('speechSynthesis' in window)) {
        showToast('Text-to-Speech is not supported in this browser.', 'warning');
        return;
    }

    // Detach old handlers before cancelling so they don't reset state
    if (ttsUtterance) {
        ttsUtterance.onend = null;
        ttsUtterance.onerror = null;
    }

    // Stop any existing speech
    speechSynthesis.cancel();

    // Read speed from dropdown (freshest value)
    const speedEl = document.getElementById('tts-speed');
    if (speedEl) {
        ttsSpeed = parseFloat(speedEl.value) || 1.0;
    }

    ttsCurrentText = text;
    ttsUtterance = new SpeechSynthesisUtterance(text);
    ttsUtterance.rate = ttsSpeed;
    ttsUtterance.lang = 'en-US';

    ttsUtterance.onend = () => {
        ttsState = 'stopped';
        updateTTSButtons();
    };

    ttsUtterance.onerror = () => {
        ttsState = 'stopped';
        updateTTSButtons();
    };

    speechSynthesis.speak(ttsUtterance);
    ttsState = 'playing';
    updateTTSButtons();
}

function pauseTTS() {
    if (ttsState === 'playing') {
        speechSynthesis.pause();
        ttsState = 'paused';
        updateTTSButtons();
    }
}

function resumeTTS() {
    if (ttsState === 'paused') {
        speechSynthesis.resume();
        ttsState = 'playing';
        updateTTSButtons();
    }
}

function stopTTS() {
    speechSynthesis.cancel();
    ttsState = 'stopped';
    updateTTSButtons();
}

function setTTSSpeed(speed) {
    ttsSpeed = parseFloat(speed) || 1.0;
    showToast('Speed set to ' + ttsSpeed + 'x', 'info', 1500);

    // If currently playing or paused, restart with new speed
    if (ttsCurrentText && (ttsState === 'playing' || ttsState === 'paused')) {
        initTTS(ttsCurrentText);
    }
}

function updateTTSButtons() {
    const playBtn = document.getElementById('tts-play');
    const pauseBtn = document.getElementById('tts-pause');
    const resumeBtn = document.getElementById('tts-resume');
    const stopBtn = document.getElementById('tts-stop');

    if (playBtn) playBtn.style.display = ttsState === 'stopped' ? 'inline-flex' : 'none';
    if (pauseBtn) pauseBtn.style.display = ttsState === 'playing' ? 'inline-flex' : 'none';
    if (resumeBtn) resumeBtn.style.display = ttsState === 'paused' ? 'inline-flex' : 'none';
    if (stopBtn) stopBtn.style.display = ttsState !== 'stopped' ? 'inline-flex' : 'none';
}

/* ────────────────────────────────────────────────────────────────
   Summary Generation
   ──────────────────────────────────────────────────────────────── */

function generateSummary(docId, type) {
    const container = document.getElementById('summary-content');
    const buttons = document.querySelectorAll('.summary-type-btn');

    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) btn.classList.add('active');
    });

    if (container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-premium mx-auto mb-3"></div>
                <p class="text-muted">Generating ${type} summary...</p>
            </div>`;
    }

    fetch(`/ai/summary/${docId}/generate/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ type: type })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else {
            let htmlContent = data.content;
            if (typeof marked !== 'undefined') {
                htmlContent = marked.parse(data.content);
            }
            container.innerHTML = `
                <div class="summary-text">${htmlContent}</div>
                <div class="d-flex gap-2 mt-4">
                    <button class="btn-outline-premium" onclick="copyToClipboard(document.querySelector('.summary-text').innerText)">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                    <button class="btn-outline-premium" onclick="generateSummary(${docId}, '${type}')">
                        <i class="fas fa-redo"></i> Regenerate
                    </button>
                    <button class="btn-outline-premium" onclick="translateSummary(${docId})">
                        <i class="fas fa-language"></i> Translate
                    </button>
                    <button class="btn-outline-premium" id="tts-play" onclick="initTTS(document.querySelector('.summary-text').innerText)">
                        <i class="fas fa-volume-up"></i> Read Aloud
                    </button>
                    <button class="btn-outline-premium" id="tts-pause" style="display:none" onclick="pauseTTS()">
                        <i class="fas fa-pause"></i> Pause
                    </button>
                    <button class="btn-outline-premium" id="tts-resume" style="display:none" onclick="resumeTTS()">
                        <i class="fas fa-play"></i> Resume
                    </button>
                    <button class="btn-outline-premium" id="tts-stop" style="display:none" onclick="stopTTS()">
                        <i class="fas fa-stop"></i> Stop
                    </button>
                </div>`;
            showToast('Summary generated!', 'success');
        }
    })
    .catch(err => {
        container.innerHTML = `<div class="alert alert-danger">Failed to generate summary. Please try again.</div>`;
    });
}

function translateSummary(docId) {
    const text = document.querySelector('.summary-text')?.innerText;
    if (!text) return;

    const lang = prompt('Translate to:\n1. Hindi (hi)\n2. Gujarati (gu)\n\nEnter language code:');
    if (!lang || !['hi', 'gu', 'en'].includes(lang)) {
        showToast('Invalid language. Use: hi, gu, or en', 'warning');
        return;
    }

    showLoading();

    fetch(`/ai/translate/${docId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ text: text, language: lang })
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.translated) {
            const container = document.getElementById('summary-content');
            if (container) {
                let translatedDiv = container.querySelector('.translation-card');
                if (!translatedDiv) {
                    translatedDiv = document.createElement('div');
                    translatedDiv.className = 'premium-card mt-4 translation-card';
                    container.appendChild(translatedDiv);
                }
                translatedDiv.innerHTML = `
                    <h6><i class="fas fa-language me-2"></i>Translation (${lang})</h6>
                    <p class="mb-0">${data.translated}</p>`;
            }
        }
    })
    .catch(() => {
        hideLoading();
        showToast('Translation failed', 'error');
    });
}

/* ────────────────────────────────────────────────────────────────
   Insights Generation
   ──────────────────────────────────────────────────────────────── */

function generateInsights(docId) {
    const container = document.getElementById('insights-container');
    const btn = document.getElementById('generate-insights-btn');

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<div class="spinner-premium" style="width:20px;height:20px;border-width:2px;"></div> Analyzing...';
    }

    fetch(`/ai/insights/${docId}/generate/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
        } else {
            renderInsights(data.insights, container);
            showToast('Insights generated!', 'success');
        }
    })
    .catch(err => showToast('Failed to generate insights', 'error'))
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic"></i> Generate Insights';
        }
    });
}

function renderInsights(insights, container) {
    if (!container) return;

    const sections = [
        { key: 'main_objective', icon: 'fa-bullseye', title: 'Main Objective', color: '#2563eb' },
        { key: 'important_facts', icon: 'fa-check-circle', title: 'Important Facts', color: '#14b8a6' },
        { key: 'important_dates', icon: 'fa-calendar', title: 'Important Dates', color: '#f59e0b' },
        { key: 'important_numbers', icon: 'fa-hashtag', title: 'Key Numbers', color: '#8b5cf6' },
        { key: 'action_items', icon: 'fa-tasks', title: 'Action Items', color: '#ec4899' },
        { key: 'conclusion', icon: 'fa-flag-checkered', title: 'Conclusion', color: '#06b6d4' },
        { key: 'recommendations', icon: 'fa-lightbulb', title: 'Recommendations', color: '#f97316' },
    ];

    let html = '<div class="row g-4">';
    sections.forEach(section => {
        const value = insights[section.key];
        if (!value || (Array.isArray(value) && value.length === 0)) return;

        let content = '';
        if (Array.isArray(value)) {
            content = '<ul class="mb-0 ps-3">' + value.map(v => `<li>${v}</li>`).join('') + '</ul>';
        } else {
            content = `<p class="mb-0">${value}</p>`;
        }

        html += `
            <div class="col-md-6">
                <div class="premium-card h-100" style="border-left: 4px solid ${section.color}">
                    <h6 class="d-flex align-items-center gap-2 mb-3">
                        <i class="fas ${section.icon}" style="color:${section.color}"></i>
                        ${section.title}
                    </h6>
                    ${content}
                </div>
            </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}
