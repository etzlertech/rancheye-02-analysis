import React, { createContext, useContext, useEffect, useState } from 'react';

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [ws, setWs] = useState(null);
  const [stats, setStats] = useState({
    analyses_today: 0,
    analyses_week: 0,
    active_alerts: 0,
    pending_tasks: 0,
    cost_today: 0.0,
    cost_week: 0.0,
    cost_all_time: 0.0,
  });
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Create WebSocket connection
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'stats_update') {
          setStats(data.data);
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      // Reconnect after 5 seconds
      setTimeout(() => {
        window.location.reload();
      }, 5000);
    };

    setWs(websocket);

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ ws, stats, connected }}>
      {children}
    </WebSocketContext.Provider>
  );
};