"""
AI Engine - LLaMA-3 integration via Groq / Ollama.
Handles all AI generation: chat, summaries, quizzes, flashcards, insights, translation.
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Cached active model to avoid redundant fallback checks
_ACTIVE_GROQ_MODEL = None


def generate_response(prompt, max_tokens=2048):
    """Generate a response using LLaMA-3 (via Groq or local Ollama) with resilient fallback."""
    global _ACTIVE_GROQ_MODEL
    provider = getattr(settings, 'AI_PROVIDER', 'groq').lower()

    if provider == 'groq':
        try:
            from groq import Groq
            api_key = getattr(settings, 'GROQ_API_KEY', '')
            if not api_key:
                raise ValueError("GROQ_API_KEY is not set in .env")
            client = Groq(api_key=api_key)

            configured_model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
            
            # Candidate models to try in order if one is deprecated / decommissioned
            candidates = [
                _ACTIVE_GROQ_MODEL,
                configured_model,
                'llama-3.3-70b-versatile',
                'openai/gpt-oss-20b',
                'openai/gpt-oss-120b',
            ]
            
            # Remove falsy values and duplicates while preserving order
            unique_candidates = []
            for m in candidates:
                if m and m not in unique_candidates:
                    unique_candidates.append(m)

            last_error = None
            for model_name in unique_candidates:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=0.7,
                    )
                    _ACTIVE_GROQ_MODEL = model_name
                    return response.choices[0].message.content
                except Exception as e:
                    err_msg = str(e)
                    # If model not found / decommissioned / unauthorized, try next candidate
                    if 'model_not_found' in err_msg or 'does not exist' in err_msg or '404' in err_msg:
                        logger.warning(f"Groq model '{model_name}' not available ({err_msg}). Trying fallback...")
                        last_error = e
                        continue
                    else:
                        logger.error(f"Groq API call failed with model '{model_name}': {e}")
                        raise

            # If all preset candidates failed with model_not_found, dynamically discover available models
            try:
                models_data = client.models.list()
                discovered_ids = [m.id for m in getattr(models_data, 'data', []) if hasattr(m, 'id')]
                # Filter out whisper / guard / non-chat models
                chat_candidates = [
                    m for m in discovered_ids
                    if not any(x in m for x in ['whisper', 'guard', 'embedding', 'distil'])
                ]
                for disc_model in (chat_candidates or discovered_ids):
                    if disc_model not in unique_candidates:
                        try:
                            logger.info(f"Trying dynamically discovered Groq model: {disc_model}")
                            response = client.chat.completions.create(
                                model=disc_model,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=max_tokens,
                                temperature=0.7,
                            )
                            _ACTIVE_GROQ_MODEL = disc_model
                            return response.choices[0].message.content
                        except Exception:
                            continue
            except Exception as disc_err:
                logger.error(f"Dynamic Groq model discovery failed: {disc_err}")

            if last_error:
                raise last_error

        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    elif provider == 'ollama':
        try:
            import requests
            url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434').rstrip('/')
            model = getattr(settings, 'OLLAMA_MODEL', 'llama3')
            response = requests.post(
                f"{url}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens,
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data['message']['content']
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}")


def chat_with_document(query, context_chunks, chat_history=None):
    """RAG-based chat: answer questions using document context."""
    context = "\n\n---\n\n".join([c['text'] for c in context_chunks])

    history_text = ""
    if chat_history:
        for msg in chat_history[-4:]:  # Last 4 messages for context
            role = "User" if msg['role'] == 'user' else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    prompt = f"""You are an AI document assistant. Answer the user's question ONLY based on the provided document context.
If the answer cannot be found in the context, say "I couldn't find this information in the document."

Always be helpful, accurate, and cite which part of the document your answer comes from.
Support markdown formatting in your response for better readability.

DOCUMENT CONTEXT:
{context}

{f'CONVERSATION HISTORY:{chr(10)}{history_text}' if history_text else ''}

USER QUESTION: {query}

Provide a comprehensive answer based on the document context. Include relevant details and cite sources."""

    response = generate_response(prompt)
    return response


def generate_summary(text, summary_type='medium'):
    """Generate document summary of specified type."""
    type_instructions = {
        'short': 'Write a concise summary in 2-3 sentences capturing the main points.',
        'medium': 'Write a comprehensive summary in 1-2 paragraphs covering all key points.',
        'detailed': 'Write a detailed and thorough summary covering all important aspects, arguments, and conclusions. Use multiple paragraphs.',
        'bullet': 'Summarize the document as a well-organized list of bullet points. Use markdown bullet points (-).',
        'executive': 'Write an executive summary suitable for business stakeholders. Include: Overview, Key Findings, Implications, and Recommendations.',
    }

    instruction = type_instructions.get(summary_type, type_instructions['medium'])

    prompt = f"""Analyze the following document and generate a summary.

INSTRUCTIONS: {instruction}

DOCUMENT TEXT:
{text[:3000]}

Generate the summary now:"""

    return generate_response(prompt)


def generate_quiz(text, quiz_type='mcq', difficulty='medium', num_questions=5):
    """Generate quiz questions from document text."""
    type_instructions = {
        'mcq': f'Generate {num_questions} multiple choice questions. Each question must have exactly 4 options labeled A), B), C), D). One must be correct.',
        'true_false': f'Generate {num_questions} True/False questions.',
        'fill_blank': f'Generate {num_questions} fill-in-the-blank questions. In the question text, replace the missing word or phrase with exactly "___" (three underscores). The correct_answer must be the missing word or phrase only.',
        'short': f'Generate {num_questions} short answer questions that can be answered in 1-2 sentences.',
    }

    instruction = type_instructions.get(quiz_type, type_instructions['mcq'])

    # Build type-specific JSON examples so the LLM returns the right shape
    if quiz_type == 'mcq':
        json_example = '[{"question": "What is X?", "options": ["A) Alpha", "B) Beta", "C) Gamma", "D) Delta"], "correct_answer": "A) Alpha", "explanation": "Because ..."}]'
        extra_rule = 'CRITICAL: The "correct_answer" value MUST be an EXACT copy of one of the strings in the "options" array, character-for-character including the letter prefix like "A) ...". Do NOT return just the letter.'
    elif quiz_type == 'true_false':
        json_example = '[{"question": "The sky is blue.", "options": ["True", "False"], "correct_answer": "True", "explanation": "Because ..."}]'
        extra_rule = 'CRITICAL: Every question MUST have "options": ["True", "False"]. The "correct_answer" MUST be exactly "True" or "False". Do NOT set options to null.'
    elif quiz_type == 'fill_blank':
        json_example = '[{"question": "The capital of France is ___.", "options": null, "correct_answer": "Paris", "explanation": "Because ..."}]'
        extra_rule = 'CRITICAL: The question text MUST contain "___" where the blank is. The "correct_answer" must be ONLY the missing word or short phrase, not a full sentence. Set "options" to null.'
    else:
        json_example = '[{"question": "Explain what X is.", "options": null, "correct_answer": "X is ...", "explanation": "Because ..."}]'
        extra_rule = 'Set "options" to null for short answer questions.'

    prompt = f"""Based on the following document, generate a quiz.

INSTRUCTIONS: {instruction}
DIFFICULTY: {difficulty}

{extra_rule}

DOCUMENT TEXT:
{text[:3000]}

Return the quiz as a valid JSON array. Each question object must have:
- "question": the question text
- "options": array of option strings, or null if not applicable
- "correct_answer": the correct answer (must EXACTLY match one option for MCQ/True-False)
- "explanation": brief explanation of the answer

Return ONLY the JSON array, no other text. Example format:
{json_example}"""

    response = generate_response(prompt)

    # Parse JSON from response
    try:
        # Try to extract JSON from response
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        json_str = json_str.strip()
        questions = json.loads(json_str)

        # Post-process to fix common LLM formatting issues
        for q in questions:
            # Ensure true_false always has options
            if quiz_type == 'true_false' and (not q.get('options') or len(q.get('options', [])) == 0):
                q['options'] = ['True', 'False']
            # Normalize true/false correct_answer
            if quiz_type == 'true_false' and q.get('correct_answer'):
                ca = q['correct_answer'].strip().lower()
                q['correct_answer'] = 'True' if ca == 'true' else 'False'

            # For MCQ, ensure correct_answer exactly matches one option
            if quiz_type == 'mcq' and q.get('options'):
                ca = q.get('correct_answer', '')
                # If correct_answer is not an exact match, try to find the matching option
                if ca not in q['options']:
                    ca_lower = ca.lower().strip()
                    matched = False
                    for opt in q['options']:
                        if opt.lower().strip() == ca_lower:
                            q['correct_answer'] = opt
                            matched = True
                            break
                    if not matched:
                        # Try matching by letter prefix (e.g. correct_answer="A" -> find option starting with "A)")
                        for opt in q['options']:
                            if ca_lower and opt.lower().startswith(ca_lower[0] + ')'):
                                q['correct_answer'] = opt
                                break

        return questions
    except json.JSONDecodeError:
        logger.error(f"Failed to parse quiz JSON: {response[:200]}")
        # Return a simple format
        return [{"question": "Quiz generation encountered a formatting issue. Please try again.", "options": None, "correct_answer": "", "explanation": ""}]


def generate_flashcards(text, num_cards=10):
    """Generate flashcards from document text."""
    prompt = f"""Based on the following document, generate {num_cards} study flashcards.

DOCUMENT TEXT:
{text[:3000]}

Return as a valid JSON array where each card has:
- "front": the question or concept (keep it concise)
- "back": the answer or explanation

Return ONLY the JSON array:
[{{"front": "...", "back": "..."}}]"""

    response = generate_response(prompt)

    try:
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        cards = json.loads(json_str.strip())
        return cards
    except json.JSONDecodeError:
        return [{"front": "Error generating flashcards", "back": "Please try again"}]


def generate_insights(text):
    """Generate comprehensive insights from document."""
    prompt = f"""Analyze the following document and extract structured insights.

DOCUMENT TEXT:
{text[:3000]}

Return as a valid JSON object with these keys:
- "main_objective": the main objective or purpose of the document (string)
- "important_facts": list of important facts (array of strings)
- "important_dates": list of important dates mentioned (array of strings)
- "important_numbers": list of important numbers/statistics (array of strings)
- "action_items": list of action items or recommendations (array of strings)
- "conclusion": the main conclusion (string)
- "recommendations": list of recommendations (array of strings)

Return ONLY the JSON object:"""

    response = generate_response(prompt)

    try:
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        insights = json.loads(json_str.strip())
        return insights
    except json.JSONDecodeError:
        return {
            "main_objective": "Could not parse insights. Please try again.",
            "important_facts": [],
            "important_dates": [],
            "important_numbers": [],
            "action_items": [],
            "conclusion": "",
            "recommendations": []
        }


def translate_text(text, target_language='hi'):
    """Translate text to target language."""
    lang_names = {
        'en': 'English',
        'hi': 'Hindi',
        'gu': 'Gujarati',
    }
    lang_name = lang_names.get(target_language, 'Hindi')

    prompt = f"""Translate the following text to {lang_name}. 
Maintain the original formatting and structure.

TEXT:
{text[:3000]}

TRANSLATION:"""

    return generate_response(prompt)


def generate_suggested_questions(text):
    """Generate suggested questions about the document."""
    prompt = f"""Based on the following document, suggest 5 interesting questions a reader might want to ask.

DOCUMENT TEXT:
{text[:2000]}

Return as a JSON array of strings:
["question 1", "question 2", ...]"""

    response = generate_response(prompt, max_tokens=1024)

    try:
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        questions = json.loads(json_str.strip())
        return questions[:5]
    except json.JSONDecodeError:
        return [
            "What is the main topic of this document?",
            "What are the key findings?",
            "What conclusions are drawn?",
            "What recommendations are made?",
            "Who is the target audience?"
        ]
