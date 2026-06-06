// ============================================================
// PaySentinelIQ — Active Status Hook
// Tracks whether the user is actively viewing the app
// and records the last active timestamp for "last seen" display
// ============================================================

"use client";

import { useState, useEffect, useCallback, useRef } from "react";

const STORAGE_KEY = "psi-last-active-at";

/**
 * Reads the stored last-active timestamp from localStorage.
 */
function readStoredLastActive(): Date | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const ts = Number(raw);
    return Number.isFinite(ts) ? new Date(ts) : null;
  } catch {
    return null;
  }
}

/**
 * Writes the current timestamp to localStorage.
 */
function persistLastActive(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, String(Date.now()));
  } catch {
    // localStorage may be unavailable (private browsing, quota, etc.)
  }
}

/**
 * Determines "active" = window focused + page visible + browser online.
 */
function computeIsActive(): boolean {
  if (typeof window === "undefined") return false;
  return (
    document.visibilityState === "visible" &&
    document.hasFocus() &&
    navigator.onLine
  );
}

export function useActiveStatus() {
  const [isActive, setIsActive] = useState<boolean>(computeIsActive);
  const [lastActiveAt, setLastActiveAt] = useState<Date | null>(
    () => readStoredLastActive() ?? new Date()
  );
  const lastActiveRef = useRef<Date | null>(lastActiveAt);

  const markInactive = useCallback(() => {
    const now = new Date();
    setLastActiveAt(now);
    lastActiveRef.current = now;
    persistLastActive();
  }, []);

  const markActive = useCallback(() => {
    const now = new Date();
    setLastActiveAt(now);
    lastActiveRef.current = now;
    persistLastActive();
  }, []);

  // ── Synchronise state with browser signals ── //
  useEffect(() => {
    // Initial sync
    setIsActive(computeIsActive());
    if (computeIsActive()) {
      const now = new Date();
      setLastActiveAt(now);
      lastActiveRef.current = now;
      persistLastActive();
    }

    const handleVisibilityChange = () => {
      const active = computeIsActive();
      setIsActive(active);
      if (active) {
        markActive();
      } else {
        markInactive();
      }
    };

    const handleFocus = () => {
      setIsActive(true);
      markActive();
    };

    const handleBlur = () => {
      setIsActive(false);
      markInactive();
    };

    const handleOnline = () => {
      const active = computeIsActive();
      setIsActive(active);
      if (active) markActive();
    };

    const handleOffline = () => {
      setIsActive(false);
      markInactive();
    };

    // Save last active before tab/page closes
    const handleBeforeUnload = () => {
      persistLastActive();
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", handleFocus);
    window.addEventListener("blur", handleBlur);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [markActive, markInactive]);

  return { isActive, lastActiveAt };
}
