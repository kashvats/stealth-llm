"""
RAG Retriever — lightweight TF-IDF retrieval over dsa.json + algorithms.json.

No external deps (pure stdlib math). Scores are cosine similarity over
term-frequency vectors built at load time. Returns top-k chunks with scores
so even a 1B model can produce expert-quality answers using the retrieved context.
"""
import math
import re
import logging
from collections import Counter
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a","an","the","is","in","it","of","to","and","or","for","with",
    "this","that","you","we","be","as","at","by","on","do","so","if",
    "can","how","what","which","where","why","when","are","was","were",
    "from","have","has","had","will","would","could","should","not","but",
    "given","find","return","returns","write","function","problem","solve",
}

def _tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


class RAGDocument:
    __slots__ = ("source", "chunk_id", "text", "tf")

    def __init__(self, source: str, chunk_id: str, text: str):
        self.source = source
        self.chunk_id = chunk_id
        self.text = text
        tokens = _tokenize(text)
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        self.tf: Dict[str, float] = {t: c / total for t, c in counts.items()}


class RAGRetriever:
    """
    Build an in-memory TF-IDF index over KB entries and algorithm patterns.
    Call search(query, top_k) to retrieve the most relevant chunks.
    """

    def __init__(self):
        self._docs: List[RAGDocument] = []
        self._idf: Dict[str, float] = {}

    def index(self, kb_data: List[Dict], patterns: List[Dict]) -> None:
        """Build index from KnowledgeBase data and algorithm patterns."""
        docs: List[RAGDocument] = []

        for item in kb_data:
            q = item.get("question", "")
            a = item.get("answer", "")
            cq = item.get("counterQuestion", "")
            cqa = item.get("counterQuestionAnswer", "")
            text = f"{q}\n{a}\n{cq}\n{cqa}".strip()
            if text:
                docs.append(RAGDocument("kb", str(item.get("id", "")), text))

        for p in patterns:
            text = f"{p.get('name', '')}\n{p.get('description', '')}\n{p.get('code', '')}\n{p.get('complexity', '')}".strip()
            if text:
                docs.append(RAGDocument("algo", p.get("id", ""), text))

        self._docs = docs
        self._build_idf()
        logger.info(f"RAG index built: {len(docs)} documents")

    def _build_idf(self) -> None:
        N = len(self._docs)
        if N == 0:
            return
        df: Dict[str, int] = {}
        for doc in self._docs:
            for term in doc.tf:
                df[term] = df.get(term, 0) + 1
        self._idf = {t: math.log((N + 1) / (n + 1)) + 1.0 for t, n in df.items()}

    def _tfidf_vec(self, tf: Dict[str, float]) -> Dict[str, float]:
        return {t: v * self._idf.get(t, 1.0) for t, v in tf.items()}

    def _cosine(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        dot = sum(vec_a.get(t, 0.0) * v for t, v in vec_b.items())
        mag_a = math.sqrt(sum(v * v for v in vec_a.values())) or 1.0
        mag_b = math.sqrt(sum(v * v for v in vec_b.values())) or 1.0
        return dot / (mag_a * mag_b)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[RAGDocument, float]]:
        """Return top_k (doc, score) pairs sorted by relevance descending."""
        if not self._docs or not query:
            return []

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        q_tf = {t: c / len(q_tokens) for t, c in Counter(q_tokens).items()}
        q_vec = self._tfidf_vec(q_tf)

        scored = []
        for doc in self._docs:
            d_vec = self._tfidf_vec(doc.tf)
            score = self._cosine(q_vec, d_vec)
            if score > 0.0:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def build_context(self, query: str, top_k: int = 3, min_score: float = 0.05) -> Optional[str]:
        """
        Return a formatted context string to inject into the LLM system prompt.
        Returns None if no relevant chunks found above min_score.
        """
        results = self.search(query, top_k=top_k)
        relevant = [(doc, score) for doc, score in results if score >= min_score]
        if not relevant:
            return None

        parts = ["## Relevant Reference Material\n"]
        for i, (doc, score) in enumerate(relevant, 1):
            # Truncate to ~400 chars to stay small for 1B models
            snippet = doc.text[:400].strip()
            if len(doc.text) > 400:
                snippet += "..."
            parts.append(f"### Reference {i} (relevance: {score:.2f})\n{snippet}\n")

        return "\n".join(parts)
