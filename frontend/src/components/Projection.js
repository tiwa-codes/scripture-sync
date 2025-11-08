import React, { useState, useEffect, useRef } from 'react';
import './Projection.css';

const Projection = () => {
  const [currentVerse, setCurrentVerse] = useState(null);
  const [locked, setLocked] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Projection WebSocket connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'verse_match' || data.type === 'manual_verse') {
          setCurrentVerse(data.verse);
        } else if (data.type === 'lock_status') {
          setLocked(data.locked);
        }
      };

      ws.onerror = (error) => {
        console.error('Projection WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('Projection WebSocket disconnected');
        setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div className="projection">
      {locked && <div className="lock-indicator">🔒</div>}
      
      {currentVerse ? (
        <div className="projection-content">
          <div className="projection-reference">
            {currentVerse.reference}
          </div>
          <div className="projection-text">
            {currentVerse.text}
          </div>
        </div>
      ) : (
        <div className="projection-placeholder">
          <div className="placeholder-icon">📖</div>
          <div className="placeholder-text">Scripture Sync</div>
          <div className="placeholder-subtext">Waiting for verse...</div>
        </div>
      )}
    </div>
  );
};

export default Projection;
