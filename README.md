# AI Document Intelligence Platform

A production-ready, AI-powered document intelligence and analytics web application built with **Django**, **Groq / Ollama (LLaMA-3)**, **LangChain**, and **FAISS**. This application features a premium SaaS-like user interface with full dark mode support, glassmorphism cards, interactive quiz generators, and study flashcards.

## Key Features

- 🔐 **Complete Authentication**: Register, login, profile pictures, details update, and password resets.
- 📂 **Document Management**: Drag-and-drop uploads for PDF, DOCX, and TXT with size validation and OCR-ready text extraction.
- 💬 **RAG AI Chat**: Talk to your document with exact source citation and markdown text formatting.
- 📝 **AI Summarizer**: Short, medium, detailed, bullets, and business-focused executive summaries.
- 🎙️ **TTS & Translation**: Read summaries aloud with adjustable speed, and translate them to Hindi or Gujarati.
- 🧠 **Interactive Quizzes**: Generate MCQ, True/False, fill-in-the-blanks, or short questions at customizable difficulty settings.
- 🃏 **Study Flashcards**: Study mode with premium 3D flipping card animations.
- 🏷️ **NLP Pipeline**: Detect Named Entities (NER) (People, Currencies, Locations, Dates, Emails, Phones), keywords, and document topics.
- 📊 **Analytics Dashboard**: Chart.js charts rendering document upload counts and question stats over time.
- 📄 **Export to PDF**: Client-side PDF export for quizzes, flashcards, summaries, and extracted insights.

---

## Quick Start

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Run:
```bash
pip install -r requirements.txt
```

### 2. Download spaCy NER Model
```bash
python -m spacy download en_core_web_sm
```

### 3. Add Groq API Key
Create a `.env` file in the root directory (or modify the existing one):
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
SECRET_KEY=django-insecure-key-for-development-change-in-production
DEBUG=True
AI_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Initialize Database
```bash
python manage.py makemigrations accounts documents ai_core analytics
python manage.py migrate
```

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to use the application!
