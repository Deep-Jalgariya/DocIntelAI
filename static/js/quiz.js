/* ════════════════════════════════════════════════════════════════
   Quiz & Flashcard JavaScript
   ════════════════════════════════════════════════════════════════ */

/* ─── Quiz ────────────────────────────────────────────────────── */
function generateQuiz(docId) {
    const quizType = document.getElementById('quiz-type')?.value || 'mcq';
    const difficulty = document.getElementById('quiz-difficulty')?.value || 'medium';
    const numQuestions = document.getElementById('quiz-count')?.value || 5;
    const container = document.getElementById('quiz-container');
    const generateBtn = document.getElementById('generate-quiz-btn');

    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<div class="spinner-premium" style="width:20px;height:20px;border-width:2px;"></div> Generating...';
    }

    fetch(`/ai/quiz/${docId}/generate/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ type: quizType, difficulty: difficulty, num_questions: numQuestions })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
        } else {
            renderQuiz(data.questions, data.type, container);
            showToast('Quiz generated!', 'success');
        }
    })
    .catch(err => showToast('Failed to generate quiz', 'error'))
    .finally(() => {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Quiz';
        }
    });
}

function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderQuiz(questions, type, container) {
    if (!container) return;

    let html = `<div class="quiz-questions">`;
    questions.forEach((q, i) => {
        html += `
            <div class="premium-card mb-3 quiz-question" data-correct="${escapeAttr(q.correct_answer)}" id="question-${i}">
                <div class="d-flex align-items-start gap-3 mb-3">
                    <span class="badge bg-primary rounded-pill">${i + 1}</span>
                    <h6 class="mb-0">${q.question}</h6>
                </div>`;

        if (q.options && q.options.length > 0) {
            q.options.forEach((opt, j) => {
                html += `
                    <div class="form-check quiz-option mb-2" onclick="selectOption(this, ${i})">
                        <input class="form-check-input" type="radio" name="q${i}" value="${escapeAttr(opt)}" id="q${i}_${j}">
                        <label class="form-check-label" for="q${i}_${j}" style="cursor:pointer;">${opt}</label>
                    </div>`;
            });
        } else {
            html += `
                <input type="text" class="form-control form-control-premium mt-2" 
                    placeholder="Type your answer..." id="answer-${i}">`;
        }

        html += `
                <div class="quiz-explanation mt-3" style="display:none;">
                    <div class="alert alert-info py-2 px-3 mb-0">
                        <i class="fas fa-lightbulb me-1"></i> ${q.explanation || ''}
                    </div>
                </div>
            </div>`;
    });

    html += `</div>
        <div class="text-center mt-4">
            <button class="btn-gradient-primary" onclick="submitQuiz(${questions.length})">
                <i class="fas fa-check-circle"></i> Submit Quiz
            </button>
        </div>
        <div id="quiz-result" class="mt-4" style="display:none;"></div>`;

    container.innerHTML = html;
}

function selectOption(el, questionIndex) {
    const parent = document.getElementById(`question-${questionIndex}`);
    parent.querySelectorAll('.quiz-option').forEach(opt => opt.classList.remove('selected'));
    el.classList.add('selected');
    el.querySelector('input').checked = true;
}

function submitQuiz(totalQuestions) {
    let correct = 0;
    for (let i = 0; i < totalQuestions; i++) {
        const questionEl = document.getElementById(`question-${i}`);
        if (!questionEl) continue;

        const correctAnswer = (questionEl.dataset.correct || '').trim();
        const selected = questionEl.querySelector('input[type="radio"]:checked');
        const textInput = document.getElementById(`answer-${i}`);

        let userAnswer = '';
        if (selected) userAnswer = selected.value.trim();
        else if (textInput) userAnswer = textInput.value.trim();

        const explanation = questionEl.querySelector('.quiz-explanation');
        if (explanation) explanation.style.display = 'block';

        // Robust answer comparison
        let isCorrect = false;
        if (userAnswer && correctAnswer) {
            const userNorm = userAnswer.toLowerCase().replace(/\s+/g, ' ').trim();
            const correctNorm = correctAnswer.toLowerCase().replace(/\s+/g, ' ').trim();

            // 1. Exact match (case-insensitive)
            if (userNorm === correctNorm) {
                isCorrect = true;
            }
            // 2. MCQ: user selected option whose full text matches the correct_answer
            else if (selected && userNorm === correctNorm) {
                isCorrect = true;
            }
            // 3. Check if either contains the other (handles "A) answer" vs "A) answer" with minor whitespace diffs)
            else if (userNorm.includes(correctNorm) || correctNorm.includes(userNorm)) {
                isCorrect = true;
            }
            // 4. Extract just the letter prefix for MCQ comparison (e.g. "A" from "A) ...")
            else if (selected) {
                const userLetter = userNorm.match(/^([a-d])\)/);
                const correctLetter = correctNorm.match(/^([a-d])\)/);
                if (userLetter && correctLetter && userLetter[1] === correctLetter[1]) {
                    isCorrect = true;
                }
            }
            // 5. Fill-in-blank: flexible substring match for short answers
            else if (textInput) {
                if (correctNorm.includes(userNorm) || userNorm.includes(correctNorm)) {
                    isCorrect = true;
                }
            }
        }

        if (isCorrect) {
            correct++;
            questionEl.style.borderLeftColor = 'var(--success)';
            questionEl.style.borderLeftWidth = '4px';
        } else {
            questionEl.style.borderLeftColor = 'var(--danger)';
            questionEl.style.borderLeftWidth = '4px';
            // Show the correct answer when wrong
            const correctBadge = document.createElement('div');
            correctBadge.className = 'mt-2 small';
            correctBadge.innerHTML = `<span style="color:var(--success);"><i class="fas fa-check-circle me-1"></i><strong>Correct Answer:</strong> ${correctAnswer}</span>`;
            const explanationEl = questionEl.querySelector('.quiz-explanation');
            if (explanationEl) {
                explanationEl.parentNode.insertBefore(correctBadge, explanationEl);
            } else {
                questionEl.appendChild(correctBadge);
            }
        }
    }

    const percentage = Math.round((correct / totalQuestions) * 100);
    const resultEl = document.getElementById('quiz-result');
    if (resultEl) {
        resultEl.style.display = 'block';
        resultEl.innerHTML = `
            <div class="premium-card text-center">
                <h3 class="mb-2">${percentage >= 70 ? '🎉' : '📝'} Your Score</h3>
                <div class="stat-value" style="font-size:48px; color: var(--${percentage >= 70 ? 'success' : percentage >= 40 ? 'warning' : 'danger'})">
                    ${correct}/${totalQuestions}
                </div>
                <p class="text-muted">${percentage}% correct</p>
                <div class="progress-premium mt-3" style="max-width:300px; margin:0 auto;">
                    <div class="progress-bar-premium" style="width:${percentage}%; background: ${percentage >= 70 ? 'var(--success)' : percentage >= 40 ? 'var(--warning)' : 'var(--danger)'}"></div>
                </div>
            </div>`;
    }
}

/* ─── Flashcards ──────────────────────────────────────────────── */
let currentCardIndex = 0;
let flashcardData = [];

function generateFlashcards(docId) {
    const numCards = document.getElementById('flashcard-count')?.value || 10;
    const container = document.getElementById('flashcard-container');
    const generateBtn = document.getElementById('generate-flashcard-btn');

    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<div class="spinner-premium" style="width:20px;height:20px;border-width:2px;"></div> Generating...';
    }

    fetch(`/ai/flashcards/${docId}/generate/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ num_cards: numCards })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
        } else {
            flashcardData = data.cards;
            currentCardIndex = 0;
            renderFlashcard(container);
            showToast('Flashcards generated!', 'success');
        }
    })
    .catch(err => showToast('Failed to generate flashcards', 'error'))
    .finally(() => {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Flashcards';
        }
    });
}

function renderFlashcard(container) {
    if (!container || flashcardData.length === 0) return;

    const card = flashcardData[currentCardIndex];
    container.innerHTML = `
        <div class="text-center mb-3">
            <span class="badge bg-primary rounded-pill px-3 py-2">
                Card ${currentCardIndex + 1} of ${flashcardData.length}
            </span>
        </div>
        <div class="flashcard" onclick="this.classList.toggle('flipped')" id="current-flashcard">
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div>
                        <i class="fas fa-question-circle mb-3" style="font-size:28px; opacity:0.5"></i>
                        <p class="mb-0">${card.front}</p>
                    </div>
                </div>
                <div class="flashcard-back">
                    <div>
                        <i class="fas fa-lightbulb mb-3" style="font-size:28px; color:var(--accent);"></i>
                        <p class="mb-0">${card.back}</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="d-flex justify-content-center gap-3 mt-4">
            <button class="btn-outline-premium" onclick="prevCard()" ${currentCardIndex === 0 ? 'disabled' : ''}>
                <i class="fas fa-arrow-left"></i> Previous
            </button>
            <button class="btn-outline-premium" onclick="shuffleCards()">
                <i class="fas fa-random"></i> Shuffle
            </button>
            <button class="btn-gradient-primary" onclick="nextCard()" ${currentCardIndex === flashcardData.length - 1 ? 'disabled' : ''}>
                Next <i class="fas fa-arrow-right"></i>
            </button>
        </div>
        <div class="progress-premium mt-3" style="max-width:400px; margin:0 auto;">
            <div class="progress-bar-premium" style="width:${((currentCardIndex + 1) / flashcardData.length) * 100}%"></div>
        </div>`;
}

function nextCard() {
    if (currentCardIndex < flashcardData.length - 1) {
        currentCardIndex++;
        renderFlashcard(document.getElementById('flashcard-container'));
    }
}

function prevCard() {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        renderFlashcard(document.getElementById('flashcard-container'));
    }
}

function shuffleCards() {
    for (let i = flashcardData.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [flashcardData[i], flashcardData[j]] = [flashcardData[j], flashcardData[i]];
    }
    currentCardIndex = 0;
    renderFlashcard(document.getElementById('flashcard-container'));
    showToast('Cards shuffled!', 'info');
}
