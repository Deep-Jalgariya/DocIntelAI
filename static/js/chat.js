/* ════════════════════════════════════════════════════════════════
   Chat Interface JavaScript
   ChatGPT-like experience: typing, markdown, sources, copy
   ════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('chat-send-btn');

    if (!chatForm) return;

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    // Send on Enter (not Shift+Enter)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // Suggested question buttons
    document.querySelectorAll('.suggested-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            chatInput.value = this.textContent;
            sendMessage();
        });
    });

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage('user', message);
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Hide suggested questions
        const suggestedContainer = document.querySelector('.suggested-questions');
        if (suggestedContainer) suggestedContainer.style.display = 'none';

        // Show typing indicator
        const typingEl = addTypingIndicator();

        // Send to server
        const docId = chatForm.dataset.docId;
        fetch(`/ai/chat/${docId}/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({ message: message })
        })
        .then(res => res.json())
        .then(data => {
            typingEl.remove();
            addMessage('assistant', data.response, data.sources);
        })
        .catch(err => {
            typingEl.remove();
            addMessage('assistant', 'Sorry, something went wrong. Please try again.');
        });
    }

    function addMessage(role, content, sources = null) {
        const div = document.createElement('div');
        div.className = `chat-message ${role}`;

        const avatarIcon = role === 'user' ? 'fa-user' : 'fa-robot';

        // Parse markdown for assistant messages
        let displayContent = content;
        if (role === 'assistant' && typeof marked !== 'undefined') {
            displayContent = marked.parse(content);
        } else {
            displayContent = content.replace(/\n/g, '<br>');
        }

        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources-toggle" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                    <i class="fas fa-book-open"></i> View Sources (${sources.length})
                </div>
                <div class="sources-list" style="display:none;">
                    ${sources.map((s, i) => `<div class="mb-2"><strong>Source ${i+1}:</strong> ${s.text}</div>`).join('')}
                </div>
            `;
        }

        div.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div>
                <div class="message-content">${displayContent}</div>
                ${role === 'assistant' ? sourcesHtml : ''}
                <div class="message-actions">
                    <button class="btn btn-sm btn-outline-premium copy-btn">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;

        const copyBtn = div.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', function() {
                copyToClipboard(content);
            });
        }

        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function addTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'chat-message assistant';
        div.id = 'typing-indicator';
        div.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return div;
    }

    // Scroll to bottom on load
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});

/* ─── Clear Chat ──────────────────────────────────────────────── */
function clearChat(docId) {
    if (!confirm('Clear all chat history for this document?')) return;

    fetch(`/ai/chat/${docId}/clear/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(res => res.json())
    .then(() => {
        document.getElementById('chat-messages').innerHTML = '';
        showToast('Chat history cleared', 'success');
    });
}
