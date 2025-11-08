#!/usr/bin/env python3
"""
Import Bible data from JSON files into Scripture Sync database
Usage: python import-bible.py <kjv.json> <niv.json>
"""
import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import engine, Base, Verse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def import_bible(kjv_path: str, niv_path: str):
    """Import Bible data from JSON files"""
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        # Check if data already exists
        result = await session.execute(select(Verse).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Database already contains verses.")
            response = input("Delete existing data and re-import? (y/N): ")
            if response.lower() != 'y':
                print("Import cancelled.")
                return
            
            # Clear existing data
            await session.execute("DELETE FROM verses")
            await session.commit()
            print("✅ Existing data cleared")
        
        embedding_index = 0
        total_verses = 0
        
        for version, path in [("KJV", kjv_path), ("NIV", niv_path)]:
            if not Path(path).exists():
                print(f"⚠️  File not found: {path}")
                continue
            
            print(f"\n📖 Importing {version}...")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            version_verses = 0
            for book in data.get('books', []):
                book_name = book['name']
                print(f"  Loading {book_name}...", end='\r')
                
                for chapter in book.get('chapters', []):
                    chapter_num = chapter['chapter']
                    
                    for verse_data in chapter.get('verses', []):
                        verse_num = verse_data['verse']
                        text = verse_data['text']
                        
                        # Normalize text for searching
                        search_text = text.lower()
                        search_text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in search_text)
                        search_text = ' '.join(search_text.split())
                        
                        verse = Verse(
                            version=version,
                            book=book_name,
                            chapter=chapter_num,
                            verse=verse_num,
                            text=text,
                            search_text=search_text,
                            embedding_index=embedding_index
                        )
                        session.add(verse)
                        
                        embedding_index += 1
                        version_verses += 1
                        
                        # Commit in batches
                        if version_verses % 100 == 0:
                            await session.commit()
            
            await session.commit()
            total_verses += version_verses
            print(f"  ✅ {version}: {version_verses} verses imported")
        
        print(f"\n🎉 Import complete! Total verses: {total_verses}")
        print("\n📊 Summary:")
        result = await session.execute(select(Verse))
        verses = result.scalars().all()
        
        versions = {}
        for v in verses:
            versions[v.version] = versions.get(v.version, 0) + 1
        
        for version, count in versions.items():
            print(f"  {version}: {count} verses")

def main():
    if len(sys.argv) != 3:
        print("Usage: python import-bible.py <kjv.json> <niv.json>")
        print("\nExpected JSON format:")
        print("""{
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {
          "chapter": 1,
          "verses": [
            {"verse": 1, "text": "In the beginning..."}
          ]
        }
      ]
    }
  ]
}""")
        sys.exit(1)
    
    kjv_path = sys.argv[1]
    niv_path = sys.argv[2]
    
    asyncio.run(import_bible(kjv_path, niv_path))

if __name__ == "__main__":
    main()
