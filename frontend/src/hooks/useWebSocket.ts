import { useEffect, useRef } from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';

export const useWebSocket = (url: string = 'ws://localhost:8000/ws/telemetry') => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const { setData, setConnectionStatus } = useTelemetryStore();

  useEffect(() => {
    let isSubscribed = true;

    const connect = () => {
      console.log(`Connecting to ${url}...`);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isSubscribed) return;
        console.log('WebSocket connected');
        setConnectionStatus(true);
      };

      ws.onmessage = (event) => {
        if (!isSubscribed) return;
        try {
          const data = JSON.parse(event.data);
          setData(data);
        } catch (error) {
          console.error('Error parsing telemetry data:', error);
        }
      };

      ws.onclose = () => {
        if (!isSubscribed) return;
        console.log('WebSocket disconnected, retrying in 2s...');
        setConnectionStatus(false);
        wsRef.current = null;
        reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
    };

    connect();

    return () => {
      isSubscribed = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url, setData, setConnectionStatus]);

  const sendCommand = (cmd: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(cmd));
    }
  };

  return { sendCommand };
};
