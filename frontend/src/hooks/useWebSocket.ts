import { useEffect, useRef, useState, useCallback } from "react";

export interface WSEvent {
  event_type: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/**
 * Hook to subscribe to real-time task progress via WebSocket.
 */
export function useTaskWebSocket(taskId: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [events, setEvents] = useState<WSEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws/tasks/${taskId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (msg) => {
      try {
        const event: WSEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev.slice(-200), event]); // Keep last 200
      } catch {
        // ignore non-JSON messages
      }
    };

    // Ping to keep alive
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30_000);

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [taskId]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, connected, clearEvents };
}
