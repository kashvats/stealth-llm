import json
import os
import logging
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple

from rag_retriever import RAGRetriever, RAGDocument

logger = logging.getLogger(__name__)
class KnowledgeBase:
    def __init__(self, file_path: str = "dsa.json"):
        self.file_path = file_path
        self.algo_path = "algorithms.json"
        self.data: List[Dict] = []
        self.patterns: List[Dict] = []
        self._title_index: Dict[str, Dict] = {}  # normalized title -> item
        self._rag = RAGRetriever()
        self.load()
        self.load_patterns()
        self._build_index()

    def load_patterns(self):
        if os.path.exists(self.algo_path):
            try:
                with open(self.algo_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.patterns = data.get("patterns", [])
                logger.info(f"Loaded {len(self.patterns)} golden algorithms.")
            except json.JSONDecodeError as e:
                logger.error(f"Corrupt algorithms JSON at {self.algo_path}: {e}")
                self.patterns = []
            except IOError as e:
                logger.error(f"Cannot read algorithms file {self.algo_path}: {e}")
                self.patterns = []
            except Exception as e:
                logger.error(f"Unexpected error loading algorithms: {type(e).__name__}: {e}")
                self.patterns = []
        else:
            logger.debug(f"Algorithms file not found at {self.algo_path}")

    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Retrieves a golden solution by its ID."""
        for p in self.patterns:
            if p["id"] == pattern_id:
                return p
        return None

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(f"Loaded {len(self.data)} local knowledge items.")
            except json.JSONDecodeError as e:
                logger.error(f"Corrupt knowledge base JSON at {self.file_path}: {e}")
                self.data = []
            except IOError as e:
                logger.error(f"Cannot read knowledge base file {self.file_path}: {e}")
                self.data = []
            except Exception as e:
                logger.error(f"Unexpected error loading knowledge base: {type(e).__name__}: {e}")
                self.data = []

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            logger.info(f"Knowledge base saved to {self.file_path}")
        except IOError as e:
            logger.error(f"Cannot write to knowledge base file {self.file_path}: {e}")
        except TypeError as e:
            logger.error(f"Knowledge base contains non-serializable data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving knowledge base: {type(e).__name__}: {e}")

    def _build_index(self) -> None:
        """Build O(1) title index and RAG TF-IDF index after data loads."""
        self._title_index = {}
        for item in self.data:
            q = item.get("question", "").lower().strip()
            # Index the short title before the first colon (e.g. "two sum")
            title = q.split(":")[0].strip() if ":" in q else q[:50]
            self._title_index[title] = item
        self._rag.index(self.data, self.patterns)
        logger.info(f"Title index: {len(self._title_index)} entries. RAG index ready.")

    def search(self, query: str, top_k: int = 3) -> Optional[str]:
        """
        RAG retrieval: returns a formatted context string for LLM injection,
        or None if nothing relevant found.
        """
        return self._rag.build_context(query, top_k=top_k)

    def lookup(self, query: str, threshold: float = 0.6) -> Optional[Dict]:
        """Finds the best match for a query using title-aware structural matching."""
        if not query or len(query) < 5:
            return None

        query_clean = query.lower().strip()

        # 0. O(1) title index lookup (fastest path)
        for title, item in self._title_index.items():
            if title and len(title) >= 4 and title in query_clean:
                logger.info(f"Local Match Found! (Index hit: {title})")
                return item

        # 1. Title/Keyword Priority Matching (fallback scan)
        for item in self.data:
            q_text = item.get("question", "").lower()

            if ":" in q_text:
                title = q_text.split(":")[0].strip()
                if title in query_clean:
                    logger.info(f"Local Match Found! (Problem Recognized: {title})")
                    return item

            elif len(q_text) < 50 and q_text in query_clean:
                logger.info(f"Local Match Found! (Standalone Title: {q_text})")
                return item

        # 2. Substring fallback (Fast)
        for item in self.data:
            q_text = item.get("question", "").lower()
            if q_text in query_clean or query_clean in q_text:
                logger.info("Local Match Found! (Substring Match)")
                return item

        # 3. Fuzzy match (Robust fallback for variations)
        best_match = None
        highest_ratio = 0.0
        for item in self.data:
            q_text = item.get("question", "").lower()
            ratio = SequenceMatcher(None, query_clean, q_text).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = item

        if highest_ratio >= threshold:
            logger.info(f"Local Match Found! (Fuzzy Ratio: {highest_ratio:.2f})")
            return best_match
        
        return None

    def add_entry(self, question: str, answer: str, category: str = "DSA"):
        """Adds a new entry and persists to disk. Cleans title if possible."""
        # Avoid duplicate entries if possible
        if self.lookup(question, threshold=0.95):
            logger.info("Entry already exists in KnowledgeBase. Skipping add.")
            return

        # Attempt to create a cleaner title/question for the registry
        # If it's a long text with Input/Output, we try to keep just the first few lines
        lines = question.splitlines()
        clean_q = lines[0]
        if len(lines) > 1 and ("input" in lines[1].lower() or "output" in lines[1].lower()):
             # It's a structured problem, keep the first line as the 'Question/Title'
             pass
        elif len(question) > 150:
             clean_q = question[:150] + "..."

        new_id = max([item.get("id", 0) for item in self.data] or [0]) + 1
        new_entry = {
            "id": new_id,
            "question": clean_q,
            "answer": answer,
            "category": category,
            "tags": ["auto-cached"]
        }
        self.data.append(new_entry)
        self.save()
        self._build_index()  # keep RAG + title index in sync
