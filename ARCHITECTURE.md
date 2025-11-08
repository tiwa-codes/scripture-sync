# Scripture Sync Architecture

## System Overview

Scripture Sync is a real-time Bible verse matching system designed for church services and presentations. It listens to spoken words, transcribes them, and automatically displays matching Bible verses.

## Components

### 1. Audio Input Layer
- **PyAudio**: Captures audio from microphone or PA system
- **Audio Buffer**: Collects 3-second audio chunks for processing
- Supports multiple input devices
- Handles both live microphone and system audio routing

### 2. Transcription Engine
- **Whisper (OpenAI)**: State-of-the-art speech recognition
- Models: tiny, base (default), small, medium, large
- Processes audio chunks asynchronously
- Returns text with confidence scores
- Target: 500-800ms processing time

### 3. Verse Matching System

#### 3.1 Exact Match
- Normalizes text (lowercase, remove punctuation)
- Substring matching
- Highest priority for direct quotes
- Score: 0-1 based on coverage

#### 3.2 Fuzzy Match (RapidFuzz)
- Levenshtein distance-based similarity
- Handles typos and minor variations
- Partial ratio for best substring match
- Score: 0-1 normalized

#### 3.3 Semantic Search (FAISS + Embeddings)
- Sentence-BERT embeddings (all-MiniLM-L6-v2)
- 384-dimensional dense vectors
- FAISS IndexFlatL2 for L2 distance search
- Finds conceptually similar verses
- Returns top-k candidates

#### 3.4 Hybrid Scoring
```
if exact_score > 0.5:
    final_score = 0.6 * exact + 0.3 * fuzzy + 0.1 * semantic
else:
    final_score = 0.2 * exact + 0.5 * fuzzy + 0.3 * semantic
```

### 4. Backend (FastAPI)

#### 4.1 API Endpoints
- `GET /verses/` - List verses with filters
- `GET /verses/{id}` - Get specific verse
- `POST /verses/manual` - Manual verse selection
- `POST /lock` - Lock/unlock display
- `GET /search` - Search verses
- `POST /transcribe` - Test transcription
- `GET /health` - Health check

#### 4.2 WebSocket Server
- Path: `/ws`
- Bidirectional communication
- Events:
  - `verse_match` - Auto-matched verse
  - `manual_verse` - Manually selected
  - `lock_status` - Lock state change
- Broadcasts to all connected clients

#### 4.3 Database (SQLite + SQLAlchemy)

**Verses Table:**
```sql
CREATE TABLE verses (
    id INTEGER PRIMARY KEY,
    version VARCHAR,
    book VARCHAR,
    chapter INTEGER,
    verse INTEGER,
    text TEXT,
    search_text TEXT,
    embedding_index INTEGER
);
```

**Transcription Logs:**
```sql
CREATE TABLE transcription_logs (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    transcribed_text TEXT,
    matched_verse_id INTEGER,
    match_score REAL,
    latency_ms REAL
);
```

### 5. Frontend (React)

#### 5.1 Dashboard Component
- Real-time verse display
- Transcription monitoring
- Search interface
- Quick select verse list
- Lock/unlock controls
- Connection status indicator
- Test transcription button

#### 5.2 Projection Component
- Full-screen verse display
- Clean, readable typography
- Lock indicator
- Auto-updates via WebSocket
- Optimized for projector/TV output

#### 5.3 WebSocket Client
- Auto-reconnect on disconnect
- Event-driven updates
- Shared state management
- 3-second reconnect delay

### 6. Infrastructure

#### 6.1 Docker Containers
- **Backend**: Python 3.11 with all dependencies
- **Frontend**: Node build + Nginx production server
- Shared data volume for database
- Health checks for reliability

#### 6.2 Nginx Configuration
- Static file serving (React build)
- API reverse proxy to backend
- WebSocket upgrade headers
- Compression (gzip)
- Port 80 → Frontend, Port 8000 → Backend API

## Data Flow

```
Audio Input
    ↓
[3s buffer]
    ↓
Whisper Transcription (500-800ms)
    ↓
Text Output
    ↓
Verse Matcher
    ├─ Exact Match (10ms)
    ├─ Fuzzy Match (20ms)
    └─ Semantic Search (50ms)
    ↓
Hybrid Score Calculation
    ↓
Best Match (score > 0.6)
    ↓
Database Log (5ms)
    ↓
WebSocket Broadcast (10ms)
    ↓
All Clients Updated
    ├─ Dashboard
    └─ Projection
```

**Total Latency: ~700-1200ms** (well under 2s target)

## Scalability Considerations

### Current Limitations
- Single audio input stream
- SQLite (not ideal for high concurrency)
- In-memory FAISS index
- Single backend instance

### Future Improvements
- PostgreSQL for multi-client support
- Redis for pub/sub messaging
- Distributed FAISS with Milvus
- Load balancer for multiple backends
- Audio stream multiplexing
- GPU acceleration for Whisper

## Security Considerations

### Current State
- Local network deployment
- No authentication (trusted network)
- CORS open (for development)

### Production Recommendations
- JWT authentication
- HTTPS/WSS encryption
- CORS restricted to specific origins
- Rate limiting on API
- Input validation and sanitization
- Audit logging

## Performance Optimization

### Backend
1. **Async I/O**: All database and network operations are async
2. **Connection Pooling**: SQLAlchemy async session maker
3. **Caching**: Verses cached in memory after first load
4. **Batch Processing**: Audio processed in chunks
5. **Index Optimization**: FAISS flat index for speed

### Frontend
1. **Code Splitting**: React lazy loading (can be added)
2. **WebSocket**: Single persistent connection
3. **Debouncing**: Search input debounced (can be added)
4. **CSS Optimization**: Minimal, efficient styles
5. **Production Build**: Minified, tree-shaken

### Database
1. **Indexes**: On version, book, chapter, verse, search_text
2. **Prepared Statements**: SQLAlchemy ORM
3. **WAL Mode**: SQLite Write-Ahead Logging (can be enabled)
4. **Vacuum**: Periodic optimization (can be scheduled)

## Testing Strategy

### Unit Tests
- Verse matching accuracy
- Database operations
- API endpoint responses
- WebSocket message handling

### Integration Tests
- End-to-end transcription flow
- Multi-client WebSocket sync
- Lock functionality
- Search accuracy

### Performance Tests
- Latency benchmarks
- Concurrent client handling
- Database query performance
- Memory usage profiling

## Deployment Environments

### Development
- Local Python venv
- npm dev server
- Hot reload enabled
- Debug logging

### Production (Docker)
- Containerized services
- Nginx production server
- Health checks
- Restart policies
- Volume persistence

### Cloud (Future)
- Kubernetes orchestration
- Cloud SQL database
- CDN for frontend
- Auto-scaling
- Monitoring and alerting

## Monitoring and Observability

### Current Logging
- Console logs in backend
- Browser console in frontend
- Transcription logs in database

### Recommended Additions
- Structured logging (JSON)
- Log aggregation (ELK stack)
- Metrics (Prometheus)
- Distributed tracing (Jaeger)
- Uptime monitoring
- Performance dashboards

## Bible Data Management

### Current Implementation
- Hardcoded sample verses
- KJV and NIV translations
- ~10 verses for testing

### Production Setup
1. Obtain licensed Bible text
2. Convert to JSON format
3. Import with `load_full_bible_from_json()`
4. Generate embeddings (one-time)
5. Build FAISS index
6. Save index to disk

### Data Sources
- API.Bible (free tier available)
- Bible Gateway (requires permission)
- Public domain translations (KJV)
- Custom JSON files

## Extensibility

### Adding New Translations
1. Add JSON file to `data/`
2. Update loader to include new version
3. Regenerate embeddings
4. Update UI to show version filter

### Adding Features
- **History**: Track verse display history
- **Favorites**: Save frequently used verses
- **Themes**: Customizable projection themes
- **Remote Control**: Mobile app for control
- **Analytics**: Usage statistics and insights
- **Playlists**: Pre-planned verse sequences

### API Extensions
- RESTful API for external integrations
- Webhooks for verse display events
- GraphQL endpoint for flexible queries
- Export/import of settings and data

## Troubleshooting

### Common Issues

**Audio Not Working**
- Check PortAudio installation
- Verify device permissions
- Test with different device index
- Check audio levels

**Slow Transcription**
- Use smaller Whisper model (tiny/base)
- Reduce audio chunk size
- Check CPU usage
- Consider GPU acceleration

**Poor Match Accuracy**
- Adjust min_match_score threshold
- Tune hybrid scoring weights
- Add more training data
- Improve text normalization

**WebSocket Disconnects**
- Check network stability
- Increase timeout values
- Verify firewall settings
- Use WSS for encrypted connections

## Development Guidelines

### Code Style
- Python: PEP 8, Black formatter
- JavaScript: ESLint, Prettier
- Type hints in Python
- PropTypes in React (can be added)

### Git Workflow
- Feature branches
- Pull requests for review
- Semantic commit messages
- Version tags for releases

### Documentation
- Docstrings for all functions
- README for setup
- API documentation (OpenAPI/Swagger)
- Architecture diagrams

## License and Attribution

### Software License
- MIT License (permissive)
- Free for commercial use
- Attribution required

### Bible Text Licensing
- KJV: Public domain
- NIV: Requires license from Biblica
- Other translations: Check individual licenses
- Always respect copyright

## Conclusion

Scripture Sync is designed as a modular, scalable system with clear separation of concerns. The architecture prioritizes low latency, accuracy, and ease of deployment while remaining extensible for future enhancements.
