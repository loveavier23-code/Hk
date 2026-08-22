import { useEffect, useRef, useState } from "react";
import type { Snapshot } from "../types";

const API_BASE = ""; // same origin (FastAPI serves the dashboard + API)

/** Fetch the current snapshot once (for first paint before WS connects). */
export async function fetchState(): Promise<Snapshot | null> {
  try {
    const r = await fetch(`${API_BASE}/api/state`);
    return (await r.json()) as Snapshot;
  } catch {
    return null;
  }
}

export async function api(path: string, method = "POST", body?: unknown) {
  const r = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return r.json().catch(() => ({}));
}

export const actions = {
  start: () => api("/api/start"),
  stop: () => api("/api/stop"),
  closeAll: () => api("/api/close_all"),
  closePosition: (symbol: string) => api(`/api/close_position/${symbol}`),
  reset: () => api("/api/reset"),
  updateConfig: (body: unknown) => api("/api/config", "POST", body),
};

/**
 * Live state hook: opens a WebSocket to /ws, returns the latest snapshot,
 * connection status, and a manual reconnect trigger.
 */
export function useBotState() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [retry, setRetry] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimer = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/ws`;

    const connect = () => {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => !cancelled && setConnected(true);
      ws.onmessage = (ev) => {
        if (cancelled) return;
        try {
          setSnapshot(JSON.parse(ev.data));
        } catch {
          /* ignore */
        }
      };
      ws.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        retryTimer.current = window.setTimeout(() => setRetry((r) => r + 1), 1500);
      };
      ws.onerror = () => ws.close();
    };
    connect();

    // fetch once immediately for a fast first paint
    fetchState().then((s) => s && setSnapshot(s));

    return () => {
      cancelled = true;
      if (retryTimer.current) clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retry]);

  return { snapshot, connected };
}
