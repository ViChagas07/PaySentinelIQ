// ============================================================
// PaySentinelIQ — Realtime Notifications WebSocket Hook
// Connects to /ws/notifications?token=JWT and feeds new
// notifications into the AlertStore for instant UI updates.
//
// Security:
// - Passes the JWT access token from the auth store as a query
//   parameter (?token=<JWT>).  The server validates it before
//   accepting the connection.
// - Falls back to polling when the WebSocket is unavailable.
// - Exponential backoff reconnection (max 30s).
// ============================================================

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAlertStore, useAuthStore } from "@/stores";
import { queryKeys } from "@/hooks/useApi";
import type { Notification } from "@/types";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "wss://paysentineliq-production.up.railway.app/ws/notifications";

interface WsNotificationMessage {
  type: "new_notification" | "notification_read" | "connected" | "pong";
  data?: Notification;
  notification_id?: string;
  channel?: string;
  user_id?: string;
  message?: string;
}

/**
 * Hook that establishes an authenticated WebSocket connection to the
 * notifications channel and integrates with the Zustand alert store
 * and TanStack Query caches.
 *
 * @param enabled - Whether the WS connection should be active.
 */
export function useRealtimeNotifications(enabled = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const queryClient = useQueryClient();
  const addNotification = useAlertStore((s) => s.addNotification);
  const markNotificationRead = useAlertStore((s) => s.markNotificationRead);
  const token = useAuthStore((s) => s.token);

  const buildUrl = useCallback(() => {
    // Append JWT token as query param for server-side authentication
    const url = new URL(WS_BASE_URL, window.location.origin);
    if (token) {
      url.searchParams.set("token", token);
    }
    // Use ws:// for http:// pages, wss:// for https:// pages
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    url.protocol = protocol;
    return url.toString();
  }, [token]);

  const connect = useCallback(() => {
    if (!enabled || typeof window === "undefined") return;

    // Don't connect if there's no auth token yet
    const currentToken = useAuthStore.getState().token;
    if (!currentToken) {
      // Retry after a short delay — the token may arrive soon (e.g. during SSR)
      reconnectTimeoutRef.current = setTimeout(() => connect(), 1000);
      return;
    }

    try {
      const wsUrl = WS_BASE_URL.includes("?")
        ? `${WS_BASE_URL}&token=${encodeURIComponent(currentToken)}`
        : `${WS_BASE_URL}?token=${encodeURIComponent(currentToken)}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        // Heartbeat ping — server replies with {"type":"pong"}
        ws.send("ping");
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: WsNotificationMessage = JSON.parse(event.data as string);

          switch (msg.type) {
            case "new_notification": {
              if (msg.data) {
                addNotification(msg.data);
                queryClient.invalidateQueries({
                  queryKey: queryKeys.notifications.all,
                });
              }
              break;
            }
            case "notification_read": {
              if (msg.notification_id) {
                markNotificationRead(msg.notification_id);
                queryClient.invalidateQueries({
                  queryKey: queryKeys.notifications.all,
                });
              }
              break;
            }
            case "connected":
            case "pong":
              // Heartbeat acknowledged — no action needed
              break;
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = (event) => {
        wsRef.current = null;

        // code 4001 means auth failure — do not retry
        if (event.code === 4001) {
          console.warn(
            "WebSocket closed with code 4001 (auth failure). " +
            "The user may need to re-authenticate."
          );
          return;
        }

        // Exponential backoff reconnection (max 30s)
        const delay = Math.min(
          1000 * 2 ** reconnectAttemptsRef.current,
          30000
        );
        reconnectAttemptsRef.current += 1;

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        // onclose will be called after onerror, triggering reconnect
        ws.close();
      };
    } catch {
      // WebSocket not available — polling fallback already in useApi
    }
  }, [enabled, addNotification, markNotificationRead, queryClient]);

  // Heartbeat: send ping every 30s to keep connection alive
  useEffect(() => {
    if (!enabled) return;

    const heartbeatInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30_000);

    return () => clearInterval(heartbeatInterval);
  }, [enabled]);

  // Connect on mount / token change, cleanup on unmount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounted");
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connect, token]);
}
