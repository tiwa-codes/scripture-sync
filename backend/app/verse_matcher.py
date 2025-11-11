"""
Hybrid verse matching system using:
1. Exact phrase matching
2. Fuzzy matching with RapidFuzz
3. Semantic similarity with embeddings + FAISS
"""
import time
import re
import numpy as np
from typing import List, Tuple, Optional
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Verse
from .bible_data import normalize_text

class VerseMatcher:
    REFERENCE_REGEX = re.compile(
        r"^\s*(?P<book>[1-3]?\s*[A-Za-z][\w\s]*?)\s+(?P<chapter>\d+)\s*[:.]\s*(?P<verse>\d+)"
        r"(?:\s*(?:\(|\[)?(?P<version>[A-Za-z0-9]+)(?:\)|\])?)?\s*$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.embedder = None
        self.faiss_index = None
        self.verses_cache = []
        self.book_lookup = {}
        self.reference_lookup = {}
        
    async def initialize(self, session: AsyncSession):
        """Initialize embeddings and FAISS index"""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            
            # Load embedding model
            self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Load all verses
            result = await session.execute(select(Verse).order_by(Verse.embedding_index))
            self.verses_cache = list(result.scalars().all())
            self._build_reference_cache()
            
            if not self.verses_cache:
                return
            
            # Generate embeddings
            texts = [v.text for v in self.verses_cache]
            embeddings = self.embedder.encode(texts, show_progress_bar=False)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dimension)
            self.faiss_index.add(embeddings.astype('float32'))
            
        except Exception as e:
            print(f"Warning: Could not initialize embeddings: {e}")
            # Continue without embeddings - will use exact/fuzzy matching only
    
    def exact_match(self, query: str, verse_text: str) -> float:
        """Check for exact phrase matches"""
        query_norm = normalize_text(query)
        verse_norm = normalize_text(verse_text)
        
        if not query_norm or not verse_norm:
            return 0.0
        
        # Check if query is a substring of verse
        if query_norm in verse_norm:
            # Score based on coverage
            return len(query_norm) / len(verse_norm)
        
        # Check if verse is a substring of query
        if verse_norm in query_norm:
            return len(verse_norm) / len(query_norm) * 0.9  # Slightly lower score
        
        return 0.0
    
    def fuzzy_match(self, query: str, verse_text: str) -> float:
        """Fuzzy matching with RapidFuzz"""
        query_norm = normalize_text(query)
        verse_norm = normalize_text(verse_text)
        
        if not query_norm or not verse_norm:
            return 0.0
        
        # Use partial ratio for best substring match
        score = fuzz.partial_ratio(query_norm, verse_norm) / 100.0
        return score
    
    def semantic_match(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Semantic similarity search using embeddings"""
        if not self.embedder or not self.faiss_index:
            return []
        
        try:
            # Encode query
            query_embedding = self.embedder.encode([query])
            
            # Search FAISS index
            distances, indices = self.faiss_index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.verses_cache))
            )
            
            # Convert distances to similarity scores (lower distance = higher similarity)
            # Use exponential decay for distance to similarity conversion
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.verses_cache):
                    similarity = np.exp(-dist / 10.0)  # Normalize distance
                    results.append((idx, float(similarity)))
            
            return results
        except Exception as e:
            print(f"Error in semantic matching: {e}")
            return []
    
    async def find_best_match(
        self, 
        query: str, 
        session: AsyncSession,
        min_score: float = 0.6,
        version: str | None = None,
    ) -> Optional[Tuple[Verse, float, float]]:
        """
        Find best matching verse using hybrid approach
        Returns: (verse, score, latency_ms)
        """
        start_time = time.time()
        
        if not query or len(query.strip()) < 5:
            return None

        # Direct reference lookup (e.g., "Genesis 2:19")
        reference_match = self.find_reference(query, version)
        if reference_match:
            latency_ms = (time.time() - start_time) * 1000
            return (reference_match, 1.0, latency_ms)
        
        # Get candidate verses from semantic search
        semantic_results = self.semantic_match(query, top_k=20)
        
        # If no semantic results, search all verses (fallback)
        if not semantic_results:
            if not self.verses_cache:
                result = await session.execute(select(Verse))
                self.verses_cache = list(result.scalars().all())
                self._build_reference_cache()

            candidates = [(i, 0.0) for i in range(len(self.verses_cache))]
        else:
            candidates = semantic_results
        
        # Combine scores from all methods
        best_verse = None
        best_score = 0.0
        using_embeddings = self.embedder is not None and self.faiss_index is not None
        
        for verse_idx, semantic_score in candidates:
            if verse_idx >= len(self.verses_cache):
                continue
                
            verse = self.verses_cache[verse_idx]
            
            # Calculate individual scores
            exact_score = self.exact_match(query, verse.text)
            fuzzy_score = self.fuzzy_match(query, verse.text)
            
            # Weighted combination
            # If embeddings are available, blend semantic scores; otherwise lean on fuzzy matches
            if using_embeddings:
                if exact_score > 0.5:
                    combined_score = 0.5 * exact_score + 0.3 * fuzzy_score + 0.2 * semantic_score
                else:
                    combined_score = 0.2 * exact_score + 0.5 * fuzzy_score + 0.3 * semantic_score
            else:
                combined_score = 0.3 * exact_score + 0.7 * fuzzy_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_verse = verse
        
        latency_ms = (time.time() - start_time) * 1000

        effective_min_score = min_score if using_embeddings else min(min_score, 0.5)

        if best_verse and best_score >= effective_min_score:
            return (best_verse, best_score, latency_ms)
        
        return None

    def _normalize_book(self, name: str) -> str:
        cleaned = re.sub(r"[^a-z0-9\s]", " ", name.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    def _build_reference_cache(self):
        self.book_lookup = {}
        self.reference_lookup = {}
        for verse in self.verses_cache:
            book_key = self._normalize_book(verse.book)
            if not book_key:
                continue
            self.book_lookup.setdefault(book_key, verse.book)
            ref_key = (book_key, verse.chapter, verse.verse)
            version_map = self.reference_lookup.setdefault(ref_key, {})
            version_map.setdefault('default', verse)
            version_map[verse.version.lower()] = verse

    def find_reference(self, query: str, version: str | None = None) -> Optional[Verse]:
        if not self.reference_lookup:
            return None

        match = self.REFERENCE_REGEX.match(query.strip())
        if not match:
            return None

        book_raw = match.group('book') or ''
        chapter_raw = match.group('chapter')
        verse_raw = match.group('verse')
        version_hint = version or match.group('version')

        if not (book_raw and chapter_raw and verse_raw):
            return None

        book_key = self._normalize_book(book_raw)
        if book_key not in self.book_lookup:
            return None

        try:
            chapter_num = int(chapter_raw)
            verse_num = int(verse_raw)
        except ValueError:
            return None

        ref_key = (book_key, chapter_num, verse_num)
        version_map = self.reference_lookup.get(ref_key)
        if not version_map:
            return None

        if version_hint:
            verse_obj = version_map.get(version_hint.lower())
            if verse_obj:
                return verse_obj

        return version_map.get('default')

# Global matcher instance
verse_matcher = VerseMatcher()
