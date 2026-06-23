// ============================================================
// PaySentinelIQ — Notification Anti-Spam / Grouping Service
//
// Prevents toast flooding by:
// 1. Deduplicating identical notification IDs
// 2. Grouping burst notifications (>5 in 10s) into a single
//    summary toast
// 3. Throttling the toast show rate
// ============================================================

"use client";

import { toast } from "sonner";
import type { Notification } from "@/types";

// ── Constants ──

const BURST_WINDOW_MS = 10_000; // 10 seconds
const BURST_THRESHOLD = 5; // if >5 notifications arrive within the window, group
const MIN_TOAST_INTERVAL_MS = 800; // minimum interval between individual toasts

// ── State (module‑level, shared across hook instances) ──

let recentNotifications: Notification[] = [];
let burstTimer: ReturnType<typeof setTimeout> | null = null;
let lastToastTime = 0;
let isBursting = false;

// ── Helpers ──

function getBurstCount(): number {
  const now = Date.now();
  recentNotifications = recentNotifications.filter(
    (n) => now - new Date(n.created_at).getTime() < BURST_WINDOW_MS,
  );
  return recentNotifications.length;
}

function showBurstSummary() {
  const count = recentNotifications.length;
  if (count === 0) return;

  isBursting = true;

  toast.warning(
    `${count} New Notifications`,
    {
      description: `You received ${count} notifications in the last few seconds.`,
      id: "psi-toast-burst-summary",
      duration: 6000,
      action: {
        label: "View All",
        onClick: () => {
          // Router push handled outside; dispatch a custom event
          window.dispatchEvent(new CustomEvent("psi:navigate", { detail: { path: "/notifications" } }));
        },
      },
    },
  );

  // Reset burst state
  recentNotifications = [];
  isBursting = false;
}

// ── Public API ──

/**
 * Evaluate whether a notification toast should be shown individually,
 * or if a burst is in progress and the notification should be grouped.
 *
 * Returns `true` if the notification was consumed (added to burst or shown),
 * `false` if it should be skipped.
 */
export function evaluateNotificationForToast(
  notification: Notification,
): "show" | "burst" | "skip" {
  // 1. Deduplication: if we've already tracked this ID, skip
  if (recentNotifications.some((n) => n.id === notification.id)) {
    return "skip";
  }

  // 2. Add to recent tracking
  recentNotifications.push(notification);

  // 3. Check if we're still bursting
  const burstCount = getBurstCount();

  if (isBursting) {
    // Already showing a burst toast — just track
    return "burst";
  }

  if (burstCount > BURST_THRESHOLD) {
    // Threshold exceeded — show burst summary instead of individual
    if (burstTimer) clearTimeout(burstTimer);

    // Debounce burst summary to allow more notifications to arrive
    burstTimer = setTimeout(() => {
      showBurstSummary();
      burstTimer = null;
    }, 500);

    return "burst";
  }

  // 4. Throttle individual toasts
  const now = Date.now();
  if (now - lastToastTime < MIN_TOAST_INTERVAL_MS) {
    // Too soon — defer to burst logic (add to burst queue)
    // Reset burst window timer
    if (burstTimer) clearTimeout(burstTimer);
    burstTimer = setTimeout(() => {
      if (getBurstCount() > 0) {
        showBurstSummary();
      }
      burstTimer = null;
    }, BURST_WINDOW_MS);
    return "burst";
  }

  lastToastTime = now;
  return "show";
}

/**
 * Reset the anti-spam state (e.g., on logout or disconnect).
 */
export function resetAntiSpamState() {
  recentNotifications = [];
  if (burstTimer) {
    clearTimeout(burstTimer);
    burstTimer = null;
  }
  lastToastTime = 0;
  isBursting = false;
}
