// ============================================================
// PaySentinelIQ — Realtime Notifications WebSocket Hook
// Connects to /ws/notifications and feeds new notifications
// into the AlertStore for instant UI updates.
// ============================================================

"use client";

import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAlertStore } from "@/stores";
import { queryKeys } from "@/hooks/useApi";
import type { Notification } from "@/types";

const WS_NOTIFICATIONS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/notifications";

interface WsNotificationMessage {
  type: "new_notification" | "notification_read" | "connected" | "pong";
  data?: Notification;
  notification_id?: string;
  channel?: string;
  message?: string;
}

/**
 * Hook that establishes a WebSocket connection to the notifications
 * channel and feeds new notifications into the Zustand alert store
 * and invalidates TanStack Query caches.
 *
 * Automatically reconnects on disconnection with exponential backoff.
 */
export function useRealtimeNotifications(enabled = true) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const queryClient = useQueryClient();
  const addNotification = useAlertStore((s) => s.addNotification);
  const markNotificationRead = useAlertStore((s) => s.markNotificationRead);

  const connect = useCallback(() => {
    if (!enabled || typeof window === "undefined") return;

    try {
      const ws = new WebSocket(WS_NOTIFICATIONS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        // Send initial ping
        ws.send("ping");
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const msg: WsNotificationMessage = JSON.parse(event.data as string);

          switch (msg.type) {
            case "new_notification": {
              if (msg.data) {
                // Feed into Zustand for immediate UI update
                addNotification(msg.data);
                // Invalidate query cache for background refresh
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

      ws.onclose = () => {
        wsRef.current = null;
        // Reconnect with exponential backoff (max 30s)
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
      // WebSocket not available — fall back to polling (already set in useApi)
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

  // Connect on mount, cleanup on unmount
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
  }, [connect]);
}
