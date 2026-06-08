// ============================================================
// PaySentinelIQ — OS / Browser Notification Hook
// Triggers native OS notifications (Windows, macOS, Linux, Android)
// when real-time in-app notifications arrive.
// ============================================================

"use client";

import { useEffect, useRef } from "react";
import type { Notification } from "@/types";

/** Map notification types to app routes for click-to-navigate. */
const TYPE_ROUTE_MAP: Record<string, string> = {
  payment: "/payroll",
  fraud_alert: "/fraud-intelligence",
  verification_complete: "/verification-center",
  compliance_alert: "/compliance",
  document_event: "/verification-center",
  ai_insight: "/fraud-intelligence",
  system: "/audit-logs",
  critical: "/fraud-intelligence",
};

const APP_ICON = "/PSI_Logo2.png";

/**
 * Show a native OS notification using the browser Notification API.
 * Gracefully degrades if the API is unavailable or permission is denied.
 */
export function showOsNotification(notification: Notification): void {
  if (typeof window === "undefined") return;
  if (!("Notification" in window)) return;
  if (Notification.permission !== "granted") return;

  try {
    const route = TYPE_ROUTE_MAP[notification.type] || "/notifications";
    const notif = new Notification("PaySentinelIQ", {
      body: notification.title,
      icon: APP_ICON,
      badge: APP_ICON,
      tag: notification.id, // Prevent duplicates
      requireInteraction: false,
      // Auto-close after ~5 seconds (browser default varies)
    });

    // Click action: navigate to the relevant page
    notif.onclick = () => {
      window.focus();
      if (window.location.pathname !== route) {
        window.location.href = route;
      }
      notif.close();
    };

    // Auto-close after 5 seconds
    setTimeout(() => notif.close(), 5000);
  } catch {
    // Notification API failed silently — non-critical
  }
}

/**
 * Hook that listens for new notifications from the store and triggers
 * native OS notifications for each one. Only fires for notifications
 * that arrived AFTER the hook was mounted (not historical ones).
 */
export function useOsNotifications(enabled: boolean, notifications: Notification[]): void {
  const seenIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled) return;
    if (typeof window === "undefined") return;
    if (!("Notification" in window)) return;
    if (Notification.permission !== "granted") return;

    // Find notifications we haven't seen yet
    for (const n of notifications) {
      if (!seenIdsRef.current.has(n.id)) {
        seenIdsRef.current.add(n.id);
        showOsNotification(n);
      }
    }
  }, [enabled, notifications]);
}
