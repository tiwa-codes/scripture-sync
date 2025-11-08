import React, { useState, useEffect, useRef } from 'react';
import './Dashboard.css';

const Dashboard = () => {
  const [currentVerse, setCurrentVerse] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [matchScore, setMatchScore] = useState(null);
  const [latency, setLatency] = useState(null);
  const [locked, setLocked] = useState(false);
  const [verses, setVerses] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'verse_match') {
          setTranscription(data.text);
          setCurrentVerse(data.verse);
          setMatchScore(data.score);
          setLatency(data.latency_ms);
        } else if (data.type === 'manual_verse') {
          setCurrentVerse(data.verse);
          setTranscription('Manual selection');
        } else if (data.type === 'lock_status') {
          setLocked(data.locked);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    fetch('/verses/?limit=50')
      .then(res => res.json())
      .then(data => setVerses(data.verses))
      .catch(err => console.error('Error loading verses:', err));

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleLockToggle = async () => {
    const newLocked = !locked;
    try {
      await fetch('/lock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          locked: newLocked,
          verse_id: currentVerse?.id
        })
      });
      setLocked(newLocked);
    } catch (err) {
      console.error('Error toggling lock:', err);
    }
  };

  const handleManualSelection = async (verseId) => {
    try {
      await fetch('/verses/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verse_id: verseId })
      });
    } catch (err) {
      console.error('Error setting manual verse:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      
      if (data.matches && data.matches.length > 0) {
        const match = data.matches[0];
        setCurrentVerse(match);
        setMatchScore(match.score);
        setLatency(data.latency_ms);
      }
    } catch (err) {
      console.error('Error searching:', err);
    }
  };

  const handleTestTranscription = async () => {
    const testText = "For God so loved the world";
    try {
      await fetch(`/transcribe?text=${encodeURIComponent(testText)}`, {
        method: 'POST'
      });
    } catch (err) {
      console.error('Error testing transcription:', err);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Scripture Sync Dashboard</h1>
        <div className="status-indicators">
          <span className={`status-badge ${connectionStatus}`}>
            {connectionStatus === 'connected' ? '● Connected' : '○ Disconnected'}
          </span>
          {locked && <span className="status-badge locked">🔒 Locked</span>}
        </div>
      </header>

      <div className="dashboard-content">
        <div className="main-panel">
          <div className="current-verse-card">
            <h2>Current Verse</h2>
            {currentVerse ? (
              <>
                <div className="verse-reference">{currentVerse.reference}</div>
                <div className="verse-text">{currentVerse.text}</div>
                <div className="verse-metadata">
                  {matchScore && (
                    <span className="metadata-item">
                      Match: {(matchScore * 100).toFixed(1)}%
                    </span>
                  )}
                  {latency && (
                    <span className="metadata-item">
                      Latency: {latency.toFixed(0)}ms
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div className="no-verse">No verse selected</div>
            )}
          </div>

          <div className="transcription-card">
            <h3>Latest Transcription</h3>
            <div className="transcription-text">
              {transcription || 'Waiting for audio...'}
            </div>
          </div>

          <div className="controls">
            <button 
              className={`control-btn ${locked ? 'locked' : ''}`}
              onClick={handleLockToggle}
            >
              {locked ? '🔒 Unlock' : '🔓 Lock Current Verse'}
            </button>
            <button 
              className="control-btn test-btn"
              onClick={handleTestTranscription}
            >
              🎤 Test Transcription
            </button>
            <a 
              href="/projection" 
              target="_blank" 
              rel="noopener noreferrer"
              className="control-btn projection-btn"
            >
              📺 Open Projection View
            </a>
          </div>
        </div>

        <div className="side-panel">
          <div className="search-section">
            <h3>Search Verses</h3>
            <div className="search-box">
              <input
                type="text"
                placeholder="Search for verses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button onClick={handleSearch}>Search</button>
            </div>
          </div>

          <div className="verses-list">
            <h3>Quick Select</h3>
            <div className="verses-scroll">
              {verses.map((verse) => (
                <div 
                  key={verse.id}
                  className="verse-item"
                  onClick={() => handleManualSelection(verse.id)}
                >
                  <div className="verse-item-ref">{verse.reference}</div>
                  <div className="verse-item-text">{verse.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
