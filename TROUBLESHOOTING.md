# Scripture Sync - Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Docker Not Found

**Symptoms:**
```
bash: docker: command not found
```

**Solution:**
1. Install Docker: https://docs.docker.com/get-docker/
2. Ensure Docker daemon is running: `sudo systemctl start docker`
3. Add user to docker group: `sudo usermod -aG docker $USER`
4. Log out and back in

#### Docker Compose Not Found

**Symptoms:**
```
bash: docker-compose: command not found
```

**Solution:**
1. Install Docker Compose: https://docs.docker.com/compose/install/
2. Or use `docker compose` (newer syntax): `docker compose up -d`

#### Permission Denied

**Symptoms:**
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Service Startup Issues

#### Containers Won't Start

**Symptoms:**
- Services exit immediately
- Status shows "Exited (1)"

**Diagnosis:**
```bash
docker-compose ps
docker-compose logs backend
docker-compose logs frontend
```

**Solutions:**

1. **Port already in use:**
```bash
# Find what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process or change ports in docker-compose.yml
```

2. **Build failed:**
```bash
# Rebuild with no cache
docker-compose build --no-cache
docker-compose up -d
```

3. **Missing dependencies:**
```bash
# Check backend logs
docker-compose logs backend | grep -i error

# Rebuild backend
docker-compose build backend
```

#### Database Initialization Failed

**Symptoms:**
- Backend crashes on startup
- "no such table" errors

**Solution:**
```bash
# Remove old database
rm -f data/scripture.db

# Restart services
docker-compose restart backend
```

#### Out of Memory

**Symptoms:**
- Container killed
- Exit code 137

**Solution:**
1. Increase Docker memory limit (Docker Desktop settings)
2. Use smaller Whisper model: `WHISPER_MODEL=tiny`
3. Close other applications

### WebSocket Issues

#### Cannot Connect to WebSocket

**Symptoms:**
- Dashboard shows "Disconnected"
- Browser console: "WebSocket connection failed"

**Diagnosis:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws  # Install: npm install -g wscat
```

**Solutions:**

1. **Backend not running:**
```bash
docker-compose restart backend
```

2. **Firewall blocking:**
```bash
# Check firewall
sudo ufw status

# Allow port if needed
sudo ufw allow 8000
```

3. **CORS or proxy issue:**
   - Check browser console for CORS errors
   - Verify nginx configuration
   - Check `docker-compose logs frontend`

#### Frequent Disconnections

**Symptoms:**
- WebSocket connects then disconnects repeatedly
- "WebSocket closed" messages

**Solutions:**

1. **Network instability:**
   - Use wired connection instead of WiFi
   - Check network quality
   - Reduce distance to router

2. **Timeout too short:**
   - Increase timeout in WebSocket configuration
   - Add keepalive messages

3. **Server overloaded:**
```bash
# Check CPU and memory
docker stats

# Reduce load or increase resources
```

### Audio Processing Issues

#### No Audio Input

**Symptoms:**
- Transcription never updates
- No audio being captured

**Diagnosis:**
```bash
# List audio devices
docker-compose exec backend python3 -c "import pyaudio; p = pyaudio.PyAudio(); print([p.get_device_info_by_index(i)['name'] for i in range(p.get_device_count())])"
```

**Solutions:**

1. **PortAudio not installed:**
```bash
# In container
docker-compose exec backend apt-get update
docker-compose exec backend apt-get install -y portaudio19-dev

# Or rebuild
docker-compose build backend --no-cache
```

2. **Wrong device selected:**
   - Modify audio_processor.py to specify device_index
   - Test with different device indices

3. **Permissions:**
   - Add user to audio group: `sudo usermod -aG audio $USER`
   - Give Docker access to audio devices

#### Poor Transcription Quality

**Symptoms:**
- Incorrect or nonsensical transcriptions
- No verse matches

**Solutions:**

1. **Background noise:**
   - Use directional microphone
   - Reduce ambient noise
   - Adjust audio input gain

2. **Whisper model too small:**
```yaml
# Edit docker-compose.yml
environment:
  - WHISPER_MODEL=small  # or medium
```

3. **Audio quality:**
   - Check sample rate (should be 16kHz)
   - Ensure mono audio
   - Verify no audio distortion

#### Slow Transcription

**Symptoms:**
- Latency > 2 seconds
- System feels sluggish

**Solutions:**

1. **Use smaller model:**
```yaml
WHISPER_MODEL=tiny  # Fastest option
```

2. **Check CPU usage:**
```bash
docker stats
top
```

3. **GPU acceleration:**
   - Install CUDA and nvidia-docker
   - Use GPU-enabled Whisper

4. **Reduce audio chunk size:**
   - Edit audio_processor.py
   - Decrease buffer_duration

### Verse Matching Issues

#### No Matches Found

**Symptoms:**
- Search returns empty results
- Transcriptions don't match verses

**Solutions:**

1. **Lower match threshold:**
```bash
# Edit backend/.env
MIN_MATCH_SCORE=0.4  # Default: 0.6
```

2. **Database empty:**
```bash
# Check verses count
docker-compose exec backend sqlite3 /app/data/scripture.db "SELECT COUNT(*) FROM verses;"

# If 0, database is empty - restart backend
docker-compose restart backend
```

3. **Embeddings not generated:**
```bash
# Check logs for embedding errors
docker-compose logs backend | grep -i embedding

# If error, clear database and restart
```

#### Incorrect Matches

**Symptoms:**
- Wrong verses being matched
- Low confidence scores

**Solutions:**

1. **Adjust scoring weights:**
   - Edit verse_matcher.py
   - Tune exact/fuzzy/semantic balance

2. **Improve search text:**
   - Use more specific phrases
   - Include book/chapter references

3. **Add more context:**
   - Increase audio buffer duration
   - Wait for complete sentences

### Performance Issues

#### High Memory Usage

**Symptoms:**
- System slow
- Out of memory errors

**Solutions:**

1. **Monitor memory:**
```bash
docker stats
```

2. **Reduce model sizes:**
   - Smaller Whisper model
   - Smaller embedding model

3. **Clear cache:**
```bash
docker-compose down
docker system prune -a
docker-compose up -d
```

#### High CPU Usage

**Symptoms:**
- CPU at 100%
- System lag

**Solutions:**

1. **Check what's consuming CPU:**
```bash
docker stats
```

2. **Optimize settings:**
   - Reduce transcription frequency
   - Use smaller models
   - Limit concurrent requests

3. **Add rate limiting:**
   - Implement request throttling
   - Add delays between processing

#### Slow Database Queries

**Symptoms:**
- API responses slow
- High latency

**Solutions:**

1. **Check database size:**
```bash
ls -lh data/scripture.db
```

2. **Optimize database:**
```bash
docker-compose exec backend sqlite3 /app/data/scripture.db "VACUUM;"
```

3. **Add indexes:**
```sql
CREATE INDEX IF NOT EXISTS idx_search_text ON verses(search_text);
```

### Frontend Issues

#### White Screen / No Display

**Symptoms:**
- Browser shows blank page
- No errors in console

**Solutions:**

1. **Check frontend is running:**
```bash
docker-compose ps frontend
curl http://localhost:3000
```

2. **Rebuild frontend:**
```bash
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

3. **Check browser console:**
   - Press F12
   - Look for JavaScript errors
   - Check Network tab for failed requests

#### Styles Not Loading

**Symptoms:**
- Page displays but looks broken
- No CSS styling

**Solutions:**

1. **Hard refresh:**
   - Ctrl+Shift+R (Chrome/Firefox)
   - Cmd+Shift+R (Mac)

2. **Clear cache:**
   - Browser settings → Clear cache
   - Or use incognito mode

3. **Check nginx logs:**
```bash
docker-compose logs frontend
```

#### API Calls Failing

**Symptoms:**
- "Failed to fetch" errors
- Network errors in console

**Solutions:**

1. **Check backend connection:**
```bash
curl http://localhost:8000/health
```

2. **CORS issues:**
   - Check browser console for CORS errors
   - Verify CORS settings in backend/app/main.py

3. **Proxy configuration:**
   - Check nginx.conf
   - Verify proxy_pass settings

### Data Issues

#### Database Corrupted

**Symptoms:**
- "database disk image is malformed"
- SQLite errors

**Solutions:**

1. **Backup and recreate:**
```bash
# Stop services
docker-compose down

# Backup if possible
cp data/scripture.db data/scripture.db.backup

# Remove corrupted database
rm data/scripture.db

# Restart
docker-compose up -d
```

2. **Recover if possible:**
```bash
sqlite3 data/scripture.db.backup ".recover" | sqlite3 data/scripture.db
```

#### Lost Data After Restart

**Symptoms:**
- Verses missing after restart
- Database empty

**Solutions:**

1. **Check volume mounts:**
```bash
docker-compose config | grep volumes
```

2. **Verify data directory:**
```bash
ls -la data/
```

3. **Use named volumes:**
```yaml
# In docker-compose.yml
volumes:
  - scripture-data:/app/data

volumes:
  scripture-data:
```

### Network Issues

#### Cannot Access from Other Devices

**Symptoms:**
- Works on localhost but not from other computers
- Mobile devices can't connect

**Solutions:**

1. **Find your IP:**
```bash
ip addr show  # Linux
ipconfig      # Windows
ifconfig      # Mac
```

2. **Update CORS origins:**
```python
# In backend/app/main.py
allow_origins=["http://192.168.1.100:3000"]  # Your IP
```

3. **Firewall:**
```bash
# Allow ports
sudo ufw allow 3000
sudo ufw allow 8000
```

#### Port Conflicts

**Symptoms:**
- "Address already in use"
- Services won't start

**Solutions:**

1. **Find what's using the port:**
```bash
lsof -i :8000
lsof -i :3000
```

2. **Kill the process:**
```bash
kill -9 <PID>
```

3. **Change ports:**
```yaml
# In docker-compose.yml
ports:
  - "8080:8000"  # Use different external port
```

## Debug Mode

### Enable Verbose Logging

```yaml
# docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

```python
# backend/app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Access Container Shell

```bash
# Backend
docker-compose exec backend bash

# Frontend (minimal Alpine image)
docker-compose exec frontend sh
```

### Run Manual Tests

```bash
# Test Python imports
docker-compose exec backend python3 -c "from app import config; print('OK')"

# Test database
docker-compose exec backend sqlite3 /app/data/scripture.db ".tables"

# Test Whisper
docker-compose exec backend python3 -c "import whisper; print('Whisper OK')"
```

## Getting Help

If you're still experiencing issues:

1. **Collect information:**
```bash
# System info
docker version
docker-compose version
uname -a

# Service status
docker-compose ps

# Logs
docker-compose logs > logs.txt
```

2. **Search existing issues:**
   - GitHub Issues tab
   - Check closed issues too

3. **Create new issue:**
   - Include error messages
   - Attach logs
   - Describe steps to reproduce
   - Include system information

4. **Community:**
   - Check discussions
   - Ask in relevant forums
   - Stack Overflow

## Prevention Tips

1. **Regular backups:**
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose exec backend sqlite3 /app/data/scripture.db ".backup /app/data/backup-$DATE.db"
```

2. **Monitor logs:**
```bash
# Set up log monitoring
docker-compose logs -f | grep -i error
```

3. **Test before production:**
   - Always test on staging environment
   - Verify all features work
   - Load test if needed

4. **Keep updated:**
```bash
# Pull latest images
docker-compose pull
docker-compose up -d
```

5. **Document changes:**
   - Keep notes on configuration changes
   - Document custom modifications
   - Maintain changelog

## Advanced Debugging

### Network Traffic Analysis

```bash
# Install tcpdump in container
docker-compose exec backend apt-get install tcpdump

# Capture WebSocket traffic
docker-compose exec backend tcpdump -i any -A port 8000
```

### Performance Profiling

```python
# Add to backend code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Memory Profiling

```python
# Install memory-profiler
pip install memory-profiler

# Use decorator
from memory_profiler import profile

@profile
def your_function():
    pass
```

## Conclusion

Most issues can be resolved by:
1. Checking logs
2. Verifying services are running
3. Ensuring proper configuration
4. Rebuilding containers if needed

Always start with the simple solutions before diving into complex debugging.
