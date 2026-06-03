"use client";

import { useEffect, useCallback } from "react";

// Announce messages to screen readers via a hidden live region
let announcerElement: HTMLDivElement | null = null;

function getAnnouncer(): HTMLDivElement {
  if (!announcerElement && typeof document !== "undefined") {
    announcerElement = document.getElementById("a11y-announcer") as HTMLDivElement;
    if (!announcerElement) {
      announcerElement = document.createElement("div");
      announcerElement.id = "a11y-announcer";
      announcerElement.setAttribute("aria-live", "polite");
      announcerElement.setAttribute("aria-atomic", "true");
      document.body.appendChild(announcerElement);
    }
  }
  return announcerElement!;
}

/**
 * Hook that returns an announce function for screen reader announcements.
 * Uses a visually hidden aria-live region.
 *
 * @param politeness - "polite" (default) or "assertive"
 */
export function useAnnounce(politeness: "polite" | "assertive" = "polite") {
  useEffect(() => {
    const el = getAnnouncer();
    el.setAttribute("aria-live", politeness);
  }, [politeness]);

  const announce = useCallback(
    (message: string) => {
      const el = getAnnouncer();
      // Clear then set to trigger re-announcement of the same message
      el.textContent = "";
      // Force reflow
      void el.offsetHeight;
      el.textContent = message;
    },
    []
  );

  return announce;
}

/**
 * Imperative announce function for use outside React components
 * (e.g., in Zustand subscribers, event handlers)
 */
export function announceToScreenReader(
  message: string,
  politeness: "polite" | "assertive" = "polite"
) {
  const el = getAnnouncer();
  el.setAttribute("aria-live", politeness);
  el.textContent = "";
  void el.offsetHeight;
  el.textContent = message;
}
