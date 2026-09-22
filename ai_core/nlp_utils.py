"""
NLP utilities using spaCy and NLTK.
Named Entity Recognition, keyword extraction, topic detection.
"""
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


import json

DISEASE_AND_INVALID_TERMS = {
    'covid-19', 'covid19', 'covid', 'covid-', 'sars-cov-2', 'sars-cov', 'coronavirus', 
    'ebola', 'hiv', 'aids', 'influenza', 'flu', 'cancer', 'diabetes', 
    'malaria', 'asthma', 'pneumonia', 'disease', 'virus', 'infection',
    '75th %', '75th', 'myselfd', 'myself', 'himself', 'herself', 'themselves',
    'prob', 'gpa', 'weekly', 'monthly', 'yearly', 'daily', 'age 35', 'age',
    'percent', 'percentage', '%', '1446'
}


def is_valid_entity(entity_type, text):
    """Strict validation rules to prevent misclassifications like COVID-19 under Location/Person."""
    if not text:
        return False
    t_clean = text.strip()
    t_lower = t_clean.lower()

    if len(t_clean) < 2:
        return False

    # Filter out disease names, truncated strings, pronouns, and invalid symbols
    if t_lower in DISEASE_AND_INVALID_TERMS:
        return False
    if any(t_lower.startswith(d) for d in ['covid', 'sars-cov', 'coronavirus']):
        return False
    if t_clean.endswith('-') or t_clean.startswith('%') or t_clean.endswith('%'):
        return False

    if entity_type == 'PERSON':
        # Person names cannot contain digits or disease words
        if any(char.isdigit() for char in t_clean):
            return False
        if not t_clean[0].isupper():
            return False

    elif entity_type == 'GPE':  # Locations
        # Locations cannot contain digits or disease words
        if any(char.isdigit() for char in t_clean):
            return False
        if not t_clean[0].isupper():
            return False

    elif entity_type == 'ORG':  # Organizations
        # Organizations cannot be diseases
        if t_lower in ['covid-19', 'covid', 'covid-']:
            return False

    elif entity_type == 'DATE':
        # Valid year range (1800-2099) if numeric string
        if t_clean.isdigit():
            val = int(t_clean)
            if not (1800 <= val <= 2099):
                return False
        if t_lower in ['weekly', 'monthly', 'yearly', 'daily'] or 'age' in t_lower:
            return False

    elif entity_type == 'MONEY':
        # Money MUST contain a currency symbol or currency word
        has_currency = any(symbol in t_clean for symbol in ['$', '€', '£', '₹', '¥', 'USD', 'INR', 'EUR']) or \
                       any(word in t_lower for word in ['dollar', 'dollars', 'euro', 'euros', 'pound', 'rupee', 'cent'])
        if not has_currency:
            return False

    return True


def extract_entities_spacy(text):
    """Extract named entities using AI / spaCy with strict validation."""
    # 1. Try AI LLM Extraction for high precision
    try:
        from ai_core.ai_engine import generate_response
        prompt = f"""Extract high-accuracy Named Entities from the text below.
Categories:
- PERSON: Real full names of individual human people (e.g. "Jacob F. French", "Maria Paola Ugalde"). DO NOT include diseases, viruses (COVID-19), locations, or organizations.
- ORG: Real organizations, companies, universities, institutes (e.g. "ASU", "World Health Organization"). DO NOT include disease names (COVID-19) or generic scores like "GPA" or "Prob".
- GPE: Real physical geographic locations, cities, states, countries (e.g. "New York", "United States"). DO NOT include disease names (COVID-19), percentages, or pronouns.
- DATE: Specific dates or years (e.g. "2020", "July 27, 2026"). DO NOT include random numbers like "1446" or words like "weekly".
- MONEY: Currency values with symbols or currency terms (e.g. "$80,000", "thousands of dollars"). DO NOT include plain numbers like "10" or "80,000".
- EMAIL: Email addresses found.
- PHONE: Phone numbers found.

TEXT:
{text[:4000]}

Return ONLY a JSON object:
{{
  "PERSON": ["Full Name 1"],
  "ORG": ["Org Name 1"],
  "GPE": ["Location Name 1"],
  "DATE": ["2020"],
  "MONEY": ["$80,000"],
  "EMAIL": ["user@domain.com"],
  "PHONE": ["123-456-7890"]
}}"""

        response_str = generate_response(prompt, max_tokens=1024)
        if '```json' in response_str:
            response_str = response_str.split('```json')[1].split('```')[0]
        elif '```' in response_str:
            response_str = response_str.split('```')[1].split('```')[0]

        parsed = json.loads(response_str.strip())
        result = {}
        for etype in ['PERSON', 'ORG', 'GPE', 'DATE', 'MONEY', 'EMAIL', 'PHONE']:
            items = parsed.get(etype, [])
            valid_items = [it.strip() for it in items if is_valid_entity(etype, str(it))]
            counted = Counter(valid_items)
            result[etype] = [{'text': k, 'count': v} for k, v in counted.most_common(20)]

        if any(len(v) > 0 for v in result.values()):
            return result

    except Exception as e:
        logger.warning(f"AI entity extraction failed, falling back to spaCy: {e}")

    # 2. Fallback: spaCy
    entities = {
        'PERSON': [],
        'ORG': [],
        'GPE': [],
        'DATE': [],
        'MONEY': [],
    }

    try:
        import spacy
        try:
            nlp = spacy.load('en_core_web_sm')
        except OSError:
            logger.warning("spaCy model not found. Using regex fallback.")
            return extract_entities_regex(text)

        max_len = 100000
        doc = nlp(text[:max_len])

        for ent in doc.ents:
            if ent.label_ in entities:
                val = ent.text.strip()
                if is_valid_entity(ent.label_, val):
                    entities[ent.label_].append(val)

    except ImportError:
        logger.warning("spaCy not installed. Using regex fallback.")
        return extract_entities_regex(text)

    result = {}
    for entity_type, items in entities.items():
        counted = Counter(items)
        result[entity_type] = [
            {'text': text_val, 'count': count}
            for text_val, count in counted.most_common(20)
        ]

    regex_entities = extract_entities_regex(text)
    result['PHONE'] = regex_entities.get('PHONE', [])
    result['EMAIL'] = regex_entities.get('EMAIL', [])

    return result


def extract_entities_regex(text):
    """Fallback regex-based entity extraction."""
    entities = {}

    # Email extraction
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email_counts = Counter(emails)
    entities['EMAIL'] = [{'text': e, 'count': c} for e, c in email_counts.most_common(10)]

    # Phone number extraction
    phones = re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', text)
    phones = [p.strip() for p in phones if len(p.strip()) >= 10]
    phone_counts = Counter(phones)
    entities['PHONE'] = [{'text': p, 'count': c} for p, c in phone_counts.most_common(10)]

    # Date extraction
    dates = re.findall(
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b|\b(?:19|20)\d{2}\b',
        text, re.IGNORECASE
    )
    valid_dates = [d.strip() for d in dates if is_valid_entity('DATE', d)]
    entities['DATE'] = [{'text': d, 'count': c} for d, c in Counter(valid_dates).most_common(10)]

    # Money extraction
    money = re.findall(r'[\$\€\£\₹]\s*[\d,]+\.?\d*|\d+\.?\d*\s*(?:dollars|euros|pounds|rupees)', text, re.IGNORECASE)
    valid_money = [m.strip() for m in money if is_valid_entity('MONEY', m)]
    entities['MONEY'] = [{'text': m, 'count': c} for m, c in Counter(valid_money).most_common(10)]

    return entities


def extract_keywords(text, top_n=20):
    """Extract keywords using TF-IDF or frequency analysis."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        # TF-IDF based extraction
        vectorizer = TfidfVectorizer(
            max_features=top_n * 2,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )

        # Split text into sentences as "documents"
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if len(sentences) < 2:
            sentences = [text]

        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()

        # Get average TF-IDF scores
        avg_scores = tfidf_matrix.mean(axis=0).A1
        keyword_scores = list(zip(feature_names, avg_scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)

        # Also get frequency
        word_freq = Counter(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were', 'been',
                      'have', 'has', 'had', 'not', 'but', 'what', 'all', 'can', 'her', 'his',
                      'from', 'they', 'will', 'would', 'there', 'their', 'which', 'when', 'how',
                      'each', 'she', 'him', 'into', 'than', 'its', 'also', 'more', 'other', 'about'}

        keywords = []
        for word, score in keyword_scores[:top_n]:
            freq = sum(word_freq.get(w, 0) for w in word.split())
            if word.lower() not in stop_words and freq > 0:
                keywords.append({
                    'word': word,
                    'frequency': freq,
                    'importance': round(float(score), 4),
                })

        return keywords[:top_n]

    except ImportError:
        # Fallback: simple frequency-based extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were', 'been',
                      'have', 'has', 'had', 'not', 'but', 'what', 'all', 'can', 'from', 'they',
                      'will', 'would', 'there', 'their', 'which', 'about', 'also', 'more', 'other'}
        filtered = [w for w in words if w not in stop_words]
        freq = Counter(filtered)
        max_freq = max(freq.values()) if freq else 1

        return [
            {'word': word, 'frequency': count, 'importance': round(count / max_freq, 4)}
            for word, count in freq.most_common(top_n)
        ]


def detect_topics(text):
    """Detect main topics from text using AI or keyword clustering."""
    try:
        from ai_core.ai_engine import generate_response
        prompt = f"""Analyze this text and identify the top 5-8 main topics or themes.

TEXT:
{text[:3000]}

Return as a JSON array where each item has "name" (topic name, 2-5 words) and "confidence" (0.0 to 1.0):
[{{"name": "...", "confidence": 0.95}}]

Return ONLY the JSON array:"""

        response = generate_response(prompt, max_tokens=1024)

        import json
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0]
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0]
        topics = json.loads(json_str.strip())
        return topics

    except Exception as e:
        logger.error(f"Topic detection failed: {e}")
        # Fallback: use top keywords as topics
        keywords = extract_keywords(text, top_n=8)
        return [
            {'name': kw['word'].title(), 'confidence': kw['importance']}
            for kw in keywords
        ]
