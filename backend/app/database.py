from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, Float
from .config import settings

Base = declarative_base()

class Verse(Base):
    __tablename__ = "verses"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, index=True)  # KJV or NIV
    book = Column(String, index=True)
    chapter = Column(Integer, index=True)
    verse = Column(Integer, index=True)
    text = Column(Text)
    search_text = Column(Text, index=True)  # normalized for searching
    embedding_index = Column(Integer, index=True)  # index in FAISS

class TranscriptionLog(Base):
    __tablename__ = "transcription_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Float)
    transcribed_text = Column(Text)
    matched_verse_id = Column(Integer)
    match_score = Column(Float)
    latency_ms = Column(Float)

# Database engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
