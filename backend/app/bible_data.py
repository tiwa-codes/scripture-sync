"""
Bible data loader and initializer
Loads KJV and NIV Bible text into the database
"""
import json
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Verse

# Simplified Bible data structure for initial implementation
# In production, this would load from JSON files
SAMPLE_BIBLE_DATA = {
    "KJV": {
        "John": {
            3: {
                16: "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
            }
        },
        "Psalm": {
            23: {
                1: "The LORD is my shepherd; I shall not want.",
                2: "He maketh me to lie down in green pastures: he leadeth me beside the still waters.",
                3: "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake.",
                4: "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me.",
            }
        },
        "Genesis": {
            1: {
                1: "In the beginning God created the heaven and the earth."
            }
        }
    },
    "NIV": {
        "John": {
            3: {
                16: "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."
            }
        },
        "Psalm": {
            23: {
                1: "The Lord is my shepherd, I lack nothing.",
                2: "He makes me lie down in green pastures, he leads me beside quiet waters,",
                3: "he refreshes my soul. He guides me along the right paths for his name's sake.",
                4: "Even though I walk through the darkest valley, I will fear no evil, for you are with me; your rod and your staff, they comfort me.",
            }
        },
        "Genesis": {
            1: {
                1: "In the beginning God created the heavens and the earth."
            }
        }
    }
}

def normalize_text(text: str) -> str:
    """Normalize text for searching"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def load_bible_data(session: AsyncSession):
    """Load Bible data into database"""
    # Check if data already loaded
    result = await session.execute(select(Verse).limit(1))
    if result.scalar_one_or_none():
        return  # Data already loaded
    
    embedding_index = 0
    for version, books in SAMPLE_BIBLE_DATA.items():
        for book, chapters in books.items():
            for chapter_num, verses in chapters.items():
                for verse_num, text in verses.items():
                    verse = Verse(
                        version=version,
                        book=book,
                        chapter=chapter_num,
                        verse=verse_num,
                        text=text,
                        search_text=normalize_text(text),
                        embedding_index=embedding_index
                    )
                    session.add(verse)
                    embedding_index += 1
    
    await session.commit()

async def load_full_bible_from_json(session: AsyncSession, kjv_path: str, niv_path: str):
    """
    Load full Bible data from JSON files
    Expected format:
    {
        "books": [
            {
                "name": "Genesis",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "..."}
                        ]
                    }
                ]
            }
        ]
    }
    """
    import os
    
    embedding_index = 0
    
    for version, path in [("KJV", kjv_path), ("NIV", niv_path)]:
        if not os.path.exists(path):
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for book in data.get('books', []):
            book_name = book['name']
            for chapter in book.get('chapters', []):
                chapter_num = chapter['chapter']
                for verse_data in chapter.get('verses', []):
                    verse_num = verse_data['verse']
                    text = verse_data['text']
                    
                    verse = Verse(
                        version=version,
                        book=book_name,
                        chapter=chapter_num,
                        verse=verse_num,
                        text=text,
                        search_text=normalize_text(text),
                        embedding_index=embedding_index
                    )
                    session.add(verse)
                    embedding_index += 1
        
        await session.commit()
