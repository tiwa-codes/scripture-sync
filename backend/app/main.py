"""
FastAPI main application with WebSocket support
Real-time Scripture matching and projection
"""
import time
import asyncio
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db, get_session, TranscriptionLog, Verse
from .bible_data import load_bible_data
from .verse_matcher import verse_matcher
from .audio_processor import MockAudioProcessor

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.locked = False
        self.locked_verse_id: int = None
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Pydantic models
class TranscriptionResponse(BaseModel):
    text: str
    verse_id: int = None
    verse_reference: str = None
    verse_text: str = None
    match_score: float = None
    latency_ms: float = None

class ManualVerseRequest(BaseModel):
    verse_id: int

class LockRequest(BaseModel):
    locked: bool
    verse_id: int = None

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Load Bible data
    async for session in get_session():
        await load_bible_data(session)
        await verse_matcher.initialize(session)
        break
    
    print("Scripture Sync started successfully!")
    
    yield
    
    # Shutdown
    print("Shutting down...")

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio transcription callback
async def on_transcription(text: str):
    """Handle new transcription from audio processor"""
    if manager.locked:
        return  # Don't process new transcriptions when locked
    
    async for session in get_session():
        result = await verse_matcher.find_best_match(
            text, 
            session, 
            min_score=settings.min_match_score
        )
        
        if result:
            verse, score, latency_ms = result
            
            # Log transcription
            log = TranscriptionLog(
                timestamp=time.time(),
                transcribed_text=text,
                matched_verse_id=verse.id,
                match_score=score,
                latency_ms=latency_ms
            )
            session.add(log)
            await session.commit()
            
            # Broadcast to all clients
            await manager.broadcast({
                "type": "verse_match",
                "text": text,
                "verse": {
                    "id": verse.id,
                    "version": verse.version,
                    "book": verse.book,
                    "chapter": verse.chapter,
                    "verse": verse.verse,
                    "text": verse.text,
                    "reference": f"{verse.book} {verse.chapter}:{verse.verse} ({verse.version})"
                },
                "score": score,
                "latency_ms": latency_ms
            })
        
        break

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive client messages
            data = await websocket.receive_json()
            # Handle client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API endpoints
@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "locked": manager.locked
    }

@app.get("/verses/")
async def list_verses(
    version: str = None,
    book: str = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """List verses with optional filtering"""
    from sqlalchemy import select
    
    query = select(Verse)
    
    if version:
        query = query.filter(Verse.version == version)
    if book:
        query = query.filter(Verse.book == book)
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    verses = result.scalars().all()
    
    return {
        "verses": [
            {
                "id": v.id,
                "version": v.version,
                "book": v.book,
                "chapter": v.chapter,
                "verse": v.verse,
                "text": v.text,
                "reference": f"{v.book} {v.chapter}:{v.verse} ({v.version})"
            }
            for v in verses
        ]
    }

@app.get("/verses/{verse_id}")
async def get_verse(verse_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific verse by ID"""
    result = await session.get(Verse, verse_id)
    if not result:
        raise HTTPException(status_code=404, detail="Verse not found")
    
    return {
        "id": result.id,
        "version": result.version,
        "book": result.book,
        "chapter": result.chapter,
        "verse": result.verse,
        "text": result.text,
        "reference": f"{result.book} {result.chapter}:{result.verse} ({result.version})"
    }

@app.post("/verses/manual")
async def set_manual_verse(
    request: ManualVerseRequest,
    session: AsyncSession = Depends(get_session)
):
    """Manually set a verse to display"""
    verse = await session.get(Verse, request.verse_id)
    if not verse:
        raise HTTPException(status_code=404, detail="Verse not found")
    
    # Broadcast to all clients
    await manager.broadcast({
        "type": "manual_verse",
        "verse": {
            "id": verse.id,
            "version": verse.version,
            "book": verse.book,
            "chapter": verse.chapter,
            "verse": verse.verse,
            "text": verse.text,
            "reference": f"{verse.book} {verse.chapter}:{verse.verse} ({verse.version})"
        }
    })
    
    return {"status": "success", "verse_id": verse.id}

@app.post("/lock")
async def set_lock(request: LockRequest):
    """Lock/unlock the projection"""
    manager.locked = request.locked
    manager.locked_verse_id = request.verse_id if request.locked else None
    
    await manager.broadcast({
        "type": "lock_status",
        "locked": manager.locked,
        "verse_id": manager.locked_verse_id
    })
    
    return {
        "status": "success",
        "locked": manager.locked,
        "verse_id": manager.locked_verse_id
    }

@app.post("/transcribe")
async def manual_transcription(text: str):
    """Manually submit text for transcription (testing)"""
    await on_transcription(text)
    return {"status": "success", "text": text}

@app.get("/search")
async def search_verses(
    q: str,
    version: str = None,
    session: AsyncSession = Depends(get_session)
):
    """Search for verses matching a query"""
    result = await verse_matcher.find_best_match(q, session, min_score=0.3)
    
    if not result:
        return {"matches": []}
    
    verse, score, latency_ms = result
    
    return {
        "matches": [
            {
                "id": verse.id,
                "version": verse.version,
                "book": verse.book,
                "chapter": verse.chapter,
                "verse": verse.verse,
                "text": verse.text,
                "reference": f"{verse.book} {verse.chapter}:{verse.verse} ({verse.version})",
                "score": score
            }
        ],
        "latency_ms": latency_ms
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "locked": manager.locked,
        "active_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
