# Scripture Sync - Usage Examples

## Basic Examples

### 1. Starting the System

```bash
# Quick start with Docker
./scripts/setup.sh

# Or manually
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Testing the API

```bash
# Use the test script
./scripts/test-api.sh

# Or manually test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/verses/
curl "http://localhost:8000/search?q=shepherd"
```

### 3. Using the Dashboard

1. Open http://localhost:3000
2. Click "Test Transcription" to see John 3:16 appear
3. Try searching for "Lord is my shepherd"
4. Click any verse in the Quick Select list
5. Open projection view: http://localhost:3000/projection

### 4. Manual Verse Selection

```bash
# Select a specific verse
curl -X POST http://localhost:8000/verses/manual \
  -H "Content-Type: application/json" \
  -d '{"verse_id": 1}'
```

### 5. Lock/Unlock Display

```bash
# Lock current verse
curl -X POST http://localhost:8000/lock \
  -H "Content-Type: application/json" \
  -d '{"locked": true, "verse_id": 1}'

# Unlock
curl -X POST http://localhost:8000/lock \
  -H "Content-Type: application/json" \
  -d '{"locked": false}'
```

## Advanced Examples

### Importing Full Bible Data

```bash
# Download or prepare your Bible JSON files
# Format: {"books": [{"name": "Genesis", "chapters": [...]}]}

# Run import script
cd /home/runner/work/scripture-sync/scripture-sync
./scripts/import-bible.py data/kjv.json data/niv.json
```

### Custom Whisper Model

```yaml
# Edit docker-compose.yml
environment:
  - WHISPER_MODEL=small  # Options: tiny, base, small, medium, large
```

### Adjusting Match Threshold

```bash
# Edit backend/.env
MIN_MATCH_SCORE=0.5  # Lower = more matches (default: 0.6)

# Restart backend
docker-compose restart backend
```

### Viewing Database

```bash
# Access SQLite database
docker-compose exec backend sqlite3 /app/data/scripture.db

# List all verses
SELECT * FROM verses LIMIT 10;

# View transcription logs
SELECT * FROM transcription_logs ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

## Python API Examples

### Using the Verse Matcher Programmatically

```python
from app.verse_matcher import VerseMatcher
from app.database import get_session

matcher = VerseMatcher()

# Initialize with database session
async with get_session() as session:
    await matcher.initialize(session)
    
    # Find best match
    result = await matcher.find_best_match(
        "God so loved the world",
        session,
        min_score=0.6
    )
    
    if result:
        verse, score, latency_ms = result
        print(f"Matched: {verse.book} {verse.chapter}:{verse.verse}")
        print(f"Score: {score:.2f}")
        print(f"Latency: {latency_ms:.1f}ms")
```

### Adding Custom Verses

```python
from app.database import get_session, Verse
from app.bible_data import normalize_text

async with get_session() as session:
    verse = Verse(
        version="KJV",
        book="Psalm",
        chapter=23,
        verse=1,
        text="The LORD is my shepherd; I shall not want.",
        search_text=normalize_text("The LORD is my shepherd; I shall not want."),
        embedding_index=0
    )
    session.add(verse)
    await session.commit()
```

## JavaScript/React Examples

### Connecting to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Scripture Sync');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'verse_match') {
    console.log('New verse:', data.verse.reference);
    console.log('Text:', data.verse.text);
    console.log('Score:', data.score);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Fetching Verses in React

```javascript
import { useState, useEffect } from 'react';

function VerseList() {
  const [verses, setVerses] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/verses/?limit=20')
      .then(res => res.json())
      .then(data => setVerses(data.verses))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      {verses.map(verse => (
        <div key={verse.id}>
          <h3>{verse.reference}</h3>
          <p>{verse.text}</p>
        </div>
      ))}
    </div>
  );
}
```

## Integration Examples

### Using with OBS (Open Broadcaster Software)

1. Start Scripture Sync projection view
2. In OBS, add Browser Source
3. URL: `http://localhost:3000/projection`
4. Width: 1920, Height: 1080
5. Enable "Shutdown source when not visible"
6. Refresh browser when no activity

### Integration with PowerPoint/Keynote

1. Open projection view in browser
2. Use screen capture/window capture
3. Or: Embed browser iframe in presentation software

### Mobile Control App

```javascript
// Simple mobile controller
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scripture Sync Remote</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    button { width: 100%; padding: 15px; margin: 10px 0; font-size: 18px; }
    input { width: 100%; padding: 10px; margin: 10px 0; }
  </style>
</head>
<body>
  <h1>Scripture Sync Remote</h1>
  <input id="search" type="text" placeholder="Search verses...">
  <button onclick="search()">Search</button>
  <button onclick="lock()">Toggle Lock</button>
  <div id="results"></div>
  
  <script>
    const API_URL = 'http://192.168.1.100:8000'; // Your server IP
    
    async function search() {
      const query = document.getElementById('search').value;
      const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data.matches.length > 0) {
        const verse = data.matches[0];
        await fetch(`${API_URL}/verses/manual`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({verse_id: verse.id})
        });
        alert('Verse displayed: ' + verse.reference);
      }
    }
    
    async function lock() {
      await fetch(`${API_URL}/lock`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({locked: true})
      });
      alert('Display locked');
    }
  </script>
</body>
</html>
```

## Performance Examples

### Measuring Latency

```bash
# Using curl to measure response time
time curl -s http://localhost:8000/search?q=shepherd > /dev/null

# Check transcription logs
docker-compose exec backend sqlite3 /app/data/scripture.db \
  "SELECT AVG(latency_ms), MIN(latency_ms), MAX(latency_ms) FROM transcription_logs;"
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test verse endpoint
ab -n 1000 -c 10 http://localhost:8000/verses/1

# Test search endpoint
ab -n 100 -c 5 "http://localhost:8000/search?q=love"
```

## Troubleshooting Examples

### Check Service Status

```bash
# Check if containers are running
docker-compose ps

# Check container health
docker-compose exec backend curl http://localhost:8000/health

# Check logs
docker-compose logs backend | tail -50
docker-compose logs frontend | tail -50
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove database
rm -f data/scripture.db

# Restart (database will be recreated)
docker-compose up -d
```

### Debug WebSocket Issues

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
ws.onmessage = (e) => console.log('Message:', e.data);
```

## Production Deployment Examples

### Using Systemd Service

```ini
# /etc/systemd/system/scripture-sync.service
[Unit]
Description=Scripture Sync
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/scripture-sync
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable scripture-sync
sudo systemctl start scripture-sync
```

### Using HTTPS with Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/scripture-sync
server {
    listen 443 ssl http2;
    server_name scripture.church.org;

    ssl_certificate /etc/letsencrypt/live/scripture.church.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scripture.church.org/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Backup and Restore

```bash
# Backup database
docker-compose exec backend \
  sqlite3 /app/data/scripture.db ".backup /app/data/backup.db"
cp data/scripture.db backups/scripture-$(date +%Y%m%d).db

# Restore database
docker-compose down
cp backups/scripture-20250108.db data/scripture.db
docker-compose up -d
```

## Tips and Best Practices

1. **Always test before live use** - Run a full test with actual audio
2. **Have backup verses ready** - Keep a printed list of common verses
3. **Monitor performance** - Check logs regularly for latency issues
4. **Use lock feature wisely** - Lock verses during important moments
5. **Keep backups** - Regular database backups are essential
6. **Network stability** - Ensure stable WiFi for WebSocket connections
7. **Screen management** - Use separate displays for dashboard and projection
8. **Practice navigation** - Familiarize operators with all controls
9. **Audio levels** - Test audio input levels before service
10. **Fallback plan** - Have manual slides ready as backup

## Community Examples

Share your own examples and use cases! Submit a pull request to add your examples here.
