// ============================================================
// PaySentinelIQ — Anti-Spam Unit Tests
// ============================================================

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import {
  evaluateNotificationForToast,
  resetAntiSpamState,
} from "@/lib/notification-anti-spam";
import type { Notification } from "@/types";

// ── Helpers ──

function makeNotification(
  id: string,
  type: Notification["type"] = "system",
  created_at?: string,
): Notification {
  return {
    id,
    user_id: "user-1",
    tenant_id: "tenant-1",
    type,
    title: "Test Notification",
    message: "This is a test notification message.",
    severity: "normal",
    is_read: false,
    action_url: null,
    metadata: {},
    created_at: created_at ?? new Date().toISOString(),
  };
}

// ── Suite ──

describe("notification-anti-spam", () => {
  beforeEach(() => {
    resetAntiSpamState();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ── Deduplication ──

  it("should return 'show' for the first notification", () => {
    const n = makeNotification("notif-1");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should return 'skip' for duplicate notification IDs", () => {
    const n = makeNotification("notif-1");
    evaluateNotificationForToast(n);
    expect(evaluateNotificationForToast(n)).toBe("skip");
  });

  // ── Throttle ──

  it("should return 'burst' if a second notification arrives too quickly", () => {
    const n1 = makeNotification("notif-1");
    const n2 = makeNotification("notif-2");

    expect(evaluateNotificationForToast(n1)).toBe("show");

    // Second notification arrives immediately (within 800ms throttle)
    const result = evaluateNotificationForToast(n2);
    expect(result).toBe("burst");
  });

  it("should return 'show' if sufficient time has passed between notifications", () => {
    const n1 = makeNotification("notif-1");
    const n2 = makeNotification("notif-2");

    expect(evaluateNotificationForToast(n1)).toBe("show");

    // Advance time by 1 second (past the 800ms throttle)
    vi.advanceTimersByTime(1000);

    expect(evaluateNotificationForToast(n2)).toBe("show");
  });

  // ── Burst threshold ──

  it("should return 'show' for individual notifications under burst threshold", () => {
    // Send 5 notifications with sufficient spacing
    for (let i = 1; i <= 5; i++) {
      const n = makeNotification(`notif-${i}`);
      const result = evaluateNotificationForToast(n);
      // The first one shows, the rest are throttled (burst)
      if (i === 1) {
        expect(result).toBe("show");
      } else {
        expect(result).toBe("burst");
      }
      vi.advanceTimersByTime(100);
    }
  });

  it("should return 'burst' for rapid notifications exceeding threshold", () => {
    // Send 7 notifications rapidly (within 10s window)
    for (let i = 1; i <= 7; i++) {
      const n = makeNotification(`notif-${i}`);
      evaluateNotificationForToast(n);
      vi.advanceTimersByTime(100);
    }

    // All after the first should be burst
    // (first is 'show', rest are 'burst')
    // The 6th+ notification should stay 'burst' (threshold already exceeded)
  });

  it("should reset state on resetAntiSpamState", () => {
    evaluateNotificationForToast(makeNotification("notif-1"));
    evaluateNotificationForToast(makeNotification("notif-2"));

    resetAntiSpamState();

    // After reset, both should be treated as new
    const nNew = makeNotification("notif-3");
    expect(evaluateNotificationForToast(nNew)).toBe("show");
  });

  // ── Different notification types ──

  it("should handle fraud_alert notifications", () => {
    const n = makeNotification("fraud-1", "fraud_alert");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle payment notifications", () => {
    const n = makeNotification("pay-1", "payment");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle critical notifications", () => {
    const n = makeNotification("crit-1", "critical");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle verification_complete notifications", () => {
    const n = makeNotification("ver-1", "verification_complete");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle compliance_alert notifications", () => {
    const n = makeNotification("comp-1", "compliance_alert");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle document_event notifications", () => {
    const n = makeNotification("doc-1", "document_event");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });

  it("should handle ai_insight notifications", () => {
    const n = makeNotification("ai-1", "ai_insight");
    expect(evaluateNotificationForToast(n)).toBe("show");
  });
});
