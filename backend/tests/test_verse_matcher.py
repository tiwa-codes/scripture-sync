"""
Tests for verse matching functionality
"""
import pytest
from app.verse_matcher import VerseMatcher
from app.bible_data import normalize_text


def test_normalize_text():
    """Test text normalization"""
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("God's love") == "god s love"
    assert normalize_text("  Multiple   spaces  ") == "multiple spaces"


def test_exact_match():
    """Test exact matching"""
    matcher = VerseMatcher()
    
    # Exact substring match
    score = matcher.exact_match(
        "God so loved the world",
        "For God so loved the world, that he gave his only begotten Son"
    )
    assert score > 0.3
    
    # No match
    score = matcher.exact_match(
        "something completely different",
        "For God so loved the world"
    )
    assert score < 0.1


def test_fuzzy_match():
    """Test fuzzy matching"""
    matcher = VerseMatcher()
    
    # Similar text
    score = matcher.fuzzy_match(
        "God so loved the world",
        "For God so loved the world that"
    )
    assert score > 0.7
    
    # Partial match with typo
    score = matcher.fuzzy_match(
        "God so lovd the wrld",
        "For God so loved the world"
    )
    assert score > 0.6
    
    # No match
    score = matcher.fuzzy_match(
        "completely different",
        "nothing similar here"
    )
    assert score < 0.5


@pytest.mark.asyncio
async def test_verse_matcher_initialization():
    """Test verse matcher can be initialized"""
    matcher = VerseMatcher()
    assert matcher.embedder is None
    assert matcher.faiss_index is None
    assert len(matcher.verses_cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
