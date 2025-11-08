# Scripture Sync - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites Check

Before starting, ensure you have:
- ✅ Docker Desktop installed and running
- ✅ At least 4GB RAM available
- ✅ 5GB free disk space

### Step 1: Clone Repository

```bash
git clone https://github.com/tiwa-codes/scripture-sync.git
cd scripture-sync
```

### Step 2: Start Services

**Option A: Automated Setup (Linux/Mac)**
```bash
./scripts/setup.sh
```

**Option B: Manual Docker Compose**
```bash
# Create data directory
mkdir -p data

# Build and start
docker-compose up -d

# Wait ~30 seconds for services to initialize
```

### Step 3: Access Application

Open your web browser:

- **Dashboard**: http://localhost:3000
- **Projection View**: http://localhost:3000/projection
- **API Docs**: http://localhost:8000/docs

### Step 4: Test the System

1. Click "Test Transcription" button in dashboard
2. Watch as the verse appears (John 3:16)
3. Try searching: "Lord is my shepherd"
4. Click any verse in the "Quick Select" list
5. Open projection view in a new window
6. Test the lock feature

## 🎯 Common Use Cases

### Church Service Setup

1. **Before Service:**
   - Start Docker containers
   - Open dashboard on operator laptop
   - Open projection view on projector/TV
   - Test audio input

2. **During Service:**
   - Audio automatically transcribes spoken words
   - Matching verses appear on projection
   - Use manual search if needed
   - Lock verses during display

3. **After Service:**
   - Review logs in database
   - Stop containers: `docker-compose down`

### Development Testing

```bash
# View logs
docker-compose logs -f

# Restart backend only
docker-compose restart backend

# Access backend shell
docker-compose exec backend bash

# Run database queries
docker-compose exec backend sqlite3 /app/data/scripture.db
```

## 🔧 Configuration

### Change Whisper Model

Edit `docker-compose.yml`:
```yaml
environment:
  - WHISPER_MODEL=small  # tiny, base, small, medium, large
```

Restart: `docker-compose up -d --build`

### Adjust Match Threshold

Edit `backend/.env`:
```
MIN_MATCH_SCORE=0.5  # Lower = more matches (default: 0.6)
```

### Custom Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:80"  # Change 8080 to your preferred port
```

## 📊 Verify Installation

### Check Service Health

```bash
# Check if services are running
docker-compose ps

# Test backend API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","locked":false,"active_connections":0}

# Test verse listing
curl http://localhost:8000/verses/

# Test search
curl "http://localhost:8000/search?q=God+so+loved"
```

### View Logs

```bash
# All logs
docker-compose logs

# Backend only
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check for port conflicts
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Remove old containers
docker-compose down -v
docker-compose up -d --build
```

### Can't Connect to WebSocket

1. Check backend is running: `docker-compose ps`
2. Verify no firewall blocking port 8000
3. Try accessing API directly: http://localhost:8000
4. Check browser console for errors (F12)

### Poor Match Results

1. Lower the threshold in `backend/.env`:
   ```
   MIN_MATCH_SCORE=0.4
   ```
2. Use more specific search terms
3. Try a larger Whisper model
4. Check transcription quality in dashboard

### High Latency

1. Use smaller Whisper model: `WHISPER_MODEL=tiny`
2. Check CPU usage: `docker stats`
3. Ensure no other heavy processes running
4. Consider increasing Docker memory limit

## 📱 Mobile Access

The dashboard and projection view work on mobile devices:

1. Find your computer's local IP: `ifconfig` or `ipconfig`
2. Access from mobile: `http://192.168.1.XXX:3000`
3. Note: Both devices must be on same network

## 🔐 Production Checklist

Before deploying in production:

- [ ] Change CORS origins in `backend/app/main.py`
- [ ] Add authentication (JWT or OAuth)
- [ ] Use HTTPS with SSL certificates
- [ ] Set up proper logging and monitoring
- [ ] Configure regular database backups
- [ ] Test with actual audio hardware
- [ ] Create systemd service for auto-start
- [ ] Document your specific setup

## 📚 Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [README.md](README.md) for detailed documentation
- Explore API at http://localhost:8000/docs
- Customize projection themes in `frontend/src/components/Projection.css`
- Add full Bible data (see README)

## 💡 Pro Tips

1. **Dual Monitors**: Run dashboard on one screen, projection on another
2. **Keyboard Shortcuts**: Use browser shortcuts for quick projection control
3. **Pre-load Verses**: Use Quick Select list before service starts
4. **Test Thoroughly**: Always test setup before live use
5. **Keep Backup**: Have printed verses as backup

## 🆘 Getting Help

- Check logs: `docker-compose logs`
- Review documentation: `README.md` and `ARCHITECTURE.md`
- Search issues: GitHub Issues
- Open new issue: Include logs and system info

## 🎉 Success!

If you can see verses appearing in both dashboard and projection view, you're all set! The system is ready for use.

Remember to test with actual audio input before your first live service.

---

**Happy Scripture Syncing! 📖✨**
