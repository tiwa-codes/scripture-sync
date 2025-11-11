# Scripture Sync

**Offline Real-time Scripture Assistant** - Python FastAPI + React

A powerful system that listens to audio (microphone or PA system), transcribes spoken words using Whisper.cpp, and matches phrases to Bible verses from KJV and NIV translations using hybrid scoring (exact match, RapidFuzz, and embeddings with FAISS). Real-time verse projection via WebSocket with manual override and lock controls.

## ✨ Features

- 🎤 **Real-time Audio Transcription** - Whisper.cpp streaming for live audio processing
- 📖 **Dual Bible Translation Support** - KJV and NIV
- 🔍 **Hybrid Search System**:
  - Exact phrase matching
  - Fuzzy matching with RapidFuzz
  - Semantic similarity using sentence embeddings + FAISS
  - Scripture reference parsing (e.g., `Genesis 2:19`, `John 3:16 NIV`)
- ⚡ **Low Latency** - Target <2s from speech to verse display
- 📺 **Dual Display Mode**:
  - Dashboard for operators (search, manual selection, lock controls)
  - Projection view for congregation display
- 🔒 **Manual Override & Lock** - Control verse display with operator intervention
- 💾 **SQLite Storage** - Transcription logs and verse database
- 🐳 **Docker Ready** - Complete containerized deployment
- 🌐 **WebSocket Updates** - Real-time synchronization across all clients

## 🏗️ Architecture

```
┌─────────────────┐
│  Audio Input    │ (Microphone / PA System)
│  (PyAudio)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Whisper.cpp    │ (Speech-to-Text)
│  Transcription  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Verse Matcher  │
│  - Exact Match  │
│  - RapidFuzz    │
│  - FAISS Search │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     WebSocket      ┌─────────────────┐
│  FastAPI        │◄──────────────────►│  React Frontend │
│  Backend        │                    │  - Dashboard    │
│  (Port 8000)    │                    │  - Projection   │
└────────┬────────┘                    └─────────────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │
│  - Verses       │
│  - Logs         │
└─────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/tiwa-codes/scripture-sync.git
cd scripture-sync

# Run setup script
./scripts/setup.sh

# Access the application
# Dashboard: http://localhost:3000
# Projection: http://localhost:3000/projection
# API: http://localhost:8000
```

### Option 2: Development Setup

```bash
# Clone the repository
git clone https://github.com/tiwa-codes/scripture-sync.git
cd scripture-sync

# Run development setup
./scripts/dev-setup.sh

# Start backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (Terminal 2)
cd frontend
npm start

# Open http://localhost:3000
```

## 📋 Prerequisites

### For Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

### For Development
- Python 3.11+
- Node.js 18+
- npm 9+
- FFmpeg (for audio processing)
- PortAudio (for microphone input)

### System Dependencies (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    portaudio19-dev \
    ffmpeg \
    git \
    nodejs \
    npm
```

## 🎯 Usage

### Dashboard Controls

1. **View Current Verse** - See the matched verse with confidence score and latency
2. **Search Verses** - Manually search by text or reference (try `Genesis 2:19` or `John 3:16 NIV`)
3. **Quick Select** - Choose from a list of common verses
4. **Lock Control** - Lock the current verse to prevent auto-updates
5. **Test Transcription** - Simulate audio input for testing
6. **Open Projection** - Launch the congregation view in a new window

### API Endpoints

- `GET /` - Health check and status
- `GET /verses/` - List all verses (with filtering)
- `GET /verses/{verse_id}` - Get specific verse
- `POST /verses/manual` - Manually set a verse
- `POST /lock` - Lock/unlock projection
- `POST /transcribe` - Submit text for transcription (testing)
- `GET /search?q={query}` - Search for verses
- `GET /health` - Service health status
- `WS /ws` - WebSocket connection for real-time updates

### WebSocket Events

**Server → Client:**
- `verse_match` - New verse matched from transcription
- `manual_verse` - Verse manually selected
- `lock_status` - Lock state changed

## 🔧 Configuration

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/scripture.db
WHISPER_MODEL=base
MAX_LATENCY_SECONDS=2.0
MIN_MATCH_SCORE=0.6
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FAISS_INDEX_PATH=./data/faiss_index.bin
```

### Whisper Model Options
- `tiny` - Fastest, lower accuracy (~1GB RAM)
- `base` - Balanced (default) (~1GB RAM)
- `small` - Better accuracy (~2GB RAM)
- `medium` - High accuracy (~5GB RAM)
- `large` - Best accuracy (~10GB RAM)

## 📊 Performance

- **Target Latency**: <2 seconds (speech to display)
- **Typical Performance**:
  - Audio capture: 100-200ms
  - Transcription (base model): 500-800ms
  - Verse matching: 50-150ms
  - WebSocket delivery: 10-50ms
  - **Total**: ~700-1200ms ✅

## 🗄️ Database Schema

### Verses Table
- `id` - Primary key
- `version` - KJV or NIV
- `book` - Book name
- `chapter` - Chapter number
- `verse` - Verse number
- `text` - Verse text
- `search_text` - Normalized text for searching
- `embedding_index` - Index in FAISS

### Transcription Logs
- `id` - Primary key
- `timestamp` - Unix timestamp
- `transcribed_text` - Original transcription
- `matched_verse_id` - Matched verse ID
- `match_score` - Confidence score (0-1)
- `latency_ms` - Processing time

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Use the "Test Transcription" button in the dashboard
2. Try search queries: "God so loved the world", "Lord is my shepherd", `Genesis 2:19 NIV`
3. Test WebSocket by opening multiple browser tabs
4. Test lock functionality

## 🐳 Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec backend sqlite3 /app/data/scripture.db
```

## 📝 Adding Full Bible Data

The sample implementation includes a few verses for testing. To add the complete Bible:

1. Obtain KJV and NIV Bible data in JSON format
2. Place files in `data/kjv.json` and `data/niv.json`
3. Use the import function:

> The loader accepts either the original `{"books": [...]}` layout or nested dictionaries like `{"Genesis": {"1": {"1": "In the beginning..."}}}` – mixing formats is fine.

```python
from app.bible_data import load_full_bible_from_json

# In your initialization
await load_full_bible_from_json(
    session, 
    "data/kjv.json", 
    "data/niv.json"
)
```

Or rebuild the SQLite database directly:

```bash
cd backend
source venv/bin/activate
python ../scripts/import-bible.py data/kjv.json data/niv.json
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- OpenAI Whisper for speech recognition
- FastAPI for the backend framework
- React for the frontend
- FAISS for efficient similarity search
- RapidFuzz for fuzzy string matching

## 💡 Future Enhancements

- [ ] Support for additional Bible translations
- [ ] Multi-language support
- [ ] Audio device selection in UI
- [ ] Verse history and favorites
- [ ] Theme customization for projection
- [ ] Mobile app integration
- [ ] Cloud deployment guide
- [ ] Performance monitoring dashboard

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ for churches and ministries