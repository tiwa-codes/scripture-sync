"""
Hybrid verse matching system using:
1. Exact phrase matching
2. Fuzzy matching with RapidFuzz
3. Semantic similarity with embeddings + FAISS
"""
import time
import numpy as np
from typing import List, Tuple, Optional
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Verse
from .bible_data import normalize_text

class VerseMatcher:
    def __init__(self):
        self.embedder = None
        self.faiss_index = None
        self.verses_cache = []
        
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
        min_score: float = 0.6
    ) -> Optional[Tuple[Verse, float, float]]:
        """
        Find best matching verse using hybrid approach
        Returns: (verse, score, latency_ms)
        """
        start_time = time.time()
        
        if not query or len(query.strip()) < 5:
            return None
        
        # Get candidate verses from semantic search
        semantic_results = self.semantic_match(query, top_k=20)
        
        # If no semantic results, search all verses (fallback)
        if not semantic_results:
            if not self.verses_cache:
                result = await session.execute(select(Verse))
                self.verses_cache = list(result.scalars().all())
            
            candidates = [(i, 0.0) for i in range(len(self.verses_cache))]
        else:
            candidates = semantic_results
        
        # Combine scores from all methods
        best_verse = None
        best_score = 0.0
        
        for verse_idx, semantic_score in candidates:
            if verse_idx >= len(self.verses_cache):
                continue
                
            verse = self.verses_cache[verse_idx]
            
            # Calculate individual scores
            exact_score = self.exact_match(query, verse.text)
            fuzzy_score = self.fuzzy_match(query, verse.text)
            
            # Weighted combination
            # Exact matches get highest priority
            if exact_score > 0.5:
                combined_score = 0.6 * exact_score + 0.3 * fuzzy_score + 0.1 * semantic_score
            else:
                combined_score = 0.2 * exact_score + 0.5 * fuzzy_score + 0.3 * semantic_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_verse = verse
        
        latency_ms = (time.time() - start_time) * 1000
        
        if best_verse and best_score >= min_score:
            return (best_verse, best_score, latency_ms)
        
        return None

# Global matcher instance
verse_matcher = VerseMatcher()
