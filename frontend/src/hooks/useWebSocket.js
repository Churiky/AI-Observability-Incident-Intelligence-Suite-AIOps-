import { useState, useEffect } from 'react';

function useWebSocket(protocols) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  const protocolsKey = protocols ? protocols.join(',') : '';

  useEffect(() => {
    // Get WebSocket URL from environment or use default
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsHost = window.location.port === '3000' ? 'localhost:8000' : window.location.host;
    const wsUrl = `${wsProtocol}://${wsHost}/ws`;

    let ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      // Subscribe to protocols if needed
      if (protocols && protocols.length > 0) {
        ws.send(JSON.stringify({ type: 'subscribe', channels: protocols }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData(parsedData);
      } catch (e) {
        setData(event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Attempt to reconnect after a delay
      setTimeout(() => {
        ws = new WebSocket(wsUrl);
      }, 3000);
    };

    return () => {
      ws.close();
    };
  }, [protocolsKey]);

  return { data, lastMessage: data, isConnected };
}

export default useWebSocket;