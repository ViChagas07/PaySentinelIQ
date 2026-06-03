"use client";

import { useEffect, type RefObject } from "react";

/**
 * Trap focus within a container element.
 * Used for modals, dropdowns, slide-out panels.
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement | null>,
  enabled: boolean
) {
  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    const container = containerRef.current;
    const focusableSelector =
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

    function getFocusableElements(): HTMLElement[] {
      return Array.from(container.querySelectorAll<HTMLElement>(focusableSelector));
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab") return;

      const focusable = getFocusableElements();
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    container.addEventListener("keydown", handleKeyDown);
    // Focus the first element when trap is enabled
    const firstFocusable = getFocusableElements()[0];
    if (firstFocusable) firstFocusable.focus();

    return () => {
      container.removeEventListener("keydown", handleKeyDown);
    };
  }, [enabled, containerRef]);
}

/**
 * Roving tabindex pattern for lists (menus, tabs, radio groups).
 * Only one item has tabindex="0", others have tabindex="-1".
 * Arrow keys move focus between items.
 */
export function useRovingTabIndex(
  containerRef: RefObject<HTMLElement | null>,
  itemSelector: string,
  enabled: boolean,
  orientation: "horizontal" | "vertical" = "vertical"
) {
  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    const container = containerRef.current;

    function getItems(): HTMLElement[] {
      return Array.from(container.querySelectorAll<HTMLElement>(itemSelector));
    }

    function setTabIndexForItem(index: number) {
      const items = getItems();
      items.forEach((item, i) => {
        item.tabIndex = i === index ? 0 : -1;
      });
      items[index]?.focus();
    }

    function handleKeyDown(e: KeyboardEvent) {
      const items = getItems();
      if (items.length === 0) return;

      const currentIndex = items.findIndex(
        (item) => item === document.activeElement || item.tabIndex === 0
      );
      const resolvedIndex = currentIndex >= 0 ? currentIndex : 0;

      const nextKey = orientation === "horizontal" ? "ArrowRight" : "ArrowDown";
      const prevKey = orientation === "horizontal" ? "ArrowLeft" : "ArrowUp";

      if (e.key === nextKey) {
        e.preventDefault();
        const next = (resolvedIndex + 1) % items.length;
        setTabIndexForItem(next);
      } else if (e.key === prevKey) {
        e.preventDefault();
        const prev = (resolvedIndex - 1 + items.length) % items.length;
        setTabIndexForItem(prev);
      } else if (e.key === "Home") {
        e.preventDefault();
        setTabIndexForItem(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setTabIndexForItem(items.length - 1);
      }
    }

    container.addEventListener("keydown", handleKeyDown);
    return () => container.removeEventListener("keydown", handleKeyDown);
  }, [enabled, containerRef, itemSelector, orientation]);
}

/**
 * Utility: trigger click on Enter/Space for keyboard accessibility.
 * Usage: <div role="button" tabIndex={0} onKeyDown={handleKeyboardClick} onClick={handler}>
 */
export function handleKeyboardClick(
  e: React.KeyboardEvent,
  onClick?: (e: React.MouseEvent | React.KeyboardEvent) => void
) {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    onClick?.(e);
  }
}
