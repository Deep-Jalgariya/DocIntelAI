"""
Document text extraction and processing utilities.
Supports PDF (PyMuPDF + pdfplumber), DOCX (python-docx), and TXT files.
"""
import re
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF with pdfplumber fallback."""
    text = ""
    page_count = 0
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        page_count = len(doc)
        for page in doc:
            text += page.get_text() + "\n\n"
        doc.close()
    except Exception as e:
        logger.warning(f"PyMuPDF failed, trying pdfplumber: {e}")
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        except Exception as e2:
            logger.error(f"Both PDF extractors failed: {e2}")
            raise Exception(f"Could not extract text from PDF: {e2}")
    return text.strip(), page_count


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        text = "\n\n".join(paragraphs)
        return text.strip(), len(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise Exception(f"Could not extract text from DOCX: {e}")


def extract_text_from_txt(file_path):
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        return text.strip(), len(paragraphs)
    except Exception as e:
        logger.error(f"TXT extraction failed: {e}")
        raise Exception(f"Could not extract text from TXT: {e}")


def extract_text(file_path, file_type):
    """Extract text from document based on file type."""
    extractors = {
        'pdf': extract_text_from_pdf,
        'docx': extract_text_from_docx,
        'txt': extract_text_from_txt,
    }
    extractor = extractors.get(file_type)
    if not extractor:
        raise ValueError(f"Unsupported file type: {file_type}")
    return extractor(file_path)


def clean_text(text):
    """Clean and normalize extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)
    # Remove null bytes
    text = text.replace('\x00', '')
    # Normalize unicode
    text = text.strip()
    return text


def count_text_stats(text):
    """Calculate text statistics."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    paragraphs = [p for p in text.split('\n\n') if p.strip()]

    word_count = len(words)
    char_count = len(text)
    paragraph_count = len(paragraphs)
    sentence_count = len(sentences)
    avg_sentence_length = round(word_count / max(sentence_count, 1), 1)
    reading_time = round(word_count / 200)  # avg 200 wordperminute

    # Reading difficulty (simple Flesch-like score)
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
    if avg_word_length < 4.5:
        difficulty = 'Easy'
    elif avg_word_length < 5.5:
        difficulty = 'Medium'
    else:
        difficulty = 'Hard'

    return {
        'word_count': word_count,
        'char_count': char_count,
        'paragraph_count': paragraph_count,
        'sentence_count': sentence_count,
        'avg_sentence_length': avg_sentence_length,
        'reading_time': max(reading_time, 1),
        'difficulty': difficulty,
    }


def split_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    """Split text into overlapping chunks for RAG."""
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        return chunks
    except ImportError:
        # Fallback: simple splitting
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap
        return chunks
