"""
Embeddings engine using Sentence Transformers and FAISS.
Handles embedding generation, FAISS index creation, and similarity search.
"""
import os
import json
import logging
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# Global model cache
_model = None


def get_embedding_model():
    """Load and cache the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not installed. Embeddings disabled.")
            return None
    return _model


def generate_embeddings(texts):
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    if model is None:
        return None
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embeddings, dtype='float32')


def create_faiss_index(doc_id, chunks):
    """Create and save a FAISS index for document chunks."""
    try:
        import faiss
    except ImportError:
        logger.warning("FAISS not installed. Index creation skipped.")
        return False

    embeddings = generate_embeddings(chunks)
    if embeddings is None:
        return False

    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity with normalized vectors)
    index.add(embeddings)

    # Save index
    index_dir = os.path.join(settings.FAISS_INDEX_DIR, f'doc_{doc_id}')
    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, 'index.faiss'))

    # Save chunks mapping
    with open(os.path.join(index_dir, 'chunks.json'), 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)

    logger.info(f"Created FAISS index for document {doc_id} with {len(chunks)} chunks")
    return True


def search_similar_chunks(doc_id, query, top_k=5):
    """Search for similar chunks in the FAISS index."""
    try:
        import faiss
    except ImportError:
        logger.warning("FAISS not installed. Falling back to text search.")
        return _fallback_search(doc_id, query, top_k)

    index_dir = os.path.join(settings.FAISS_INDEX_DIR, f'doc_{doc_id}')
    index_path = os.path.join(index_dir, 'index.faiss')
    chunks_path = os.path.join(index_dir, 'chunks.json')

    if not os.path.exists(index_path):
        return _fallback_search(doc_id, query, top_k)

    # Load index and chunks
    index = faiss.read_index(index_path)
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Generate query embedding
    query_embedding = generate_embeddings([query])
    if query_embedding is None:
        return _fallback_search(doc_id, query, top_k)

    # Search
    scores, indices = index.search(query_embedding, min(top_k, len(chunks)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(chunks):
            results.append({
                'text': chunks[idx],
                'score': float(score),
                'chunk_index': int(idx),
            })

    return results


def _fallback_search(doc_id, query, top_k=5):
    """Fallback text-based search when FAISS is not available."""
    from documents.models import DocumentChunk
    chunks = DocumentChunk.objects.filter(document_id=doc_id)
    query_lower = query.lower()

    scored_chunks = []
    for chunk in chunks:
        text_lower = chunk.chunk_text.lower()
        # Simple keyword matching score
        words = query_lower.split()
        score = sum(1 for w in words if w in text_lower) / max(len(words), 1)
        if score > 0:
            scored_chunks.append({
                'text': chunk.chunk_text,
                'score': score,
                'chunk_index': chunk.chunk_index,
            })

    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:top_k]
