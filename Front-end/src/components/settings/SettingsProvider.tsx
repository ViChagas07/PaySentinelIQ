"use client";

import { useEffect } from "react";
import { useSettingsStore, type PrimaryColor, type BackgroundColor } from "@/stores/settings-store";

const PRIMARY_COLOR_MAP: Record<PrimaryColor, { light: string; dark: string; rgb: string }> = {
  blue:    { light: "#1E6FFF", dark: "#3B82F6", rgb: "30,111,255" },
  green:   { light: "#00C48C", dark: "#10B981", rgb: "0,196,140" },
  purple:  { light: "#8B5CF6", dark: "#A78BFA", rgb: "139,92,246" },
  orange:  { light: "#FF8C00", dark: "#F97316", rgb: "255,140,0" },
  red:     { light: "#D63B3B", dark: "#EF4444", rgb: "214,59,59" },
  teal:    { light: "#14B8A6", dark: "#2DD4BF", rgb: "20,184,166" },
};

const BACKGROUND_COLOR_MAP: Record<BackgroundColor, { dark: { bg: string; card: string; border: string }; light: { bg: string; card: string; border: string } }> = {
  navy:     { dark: { bg: "#0A1628", card: "#111827", border: "#1E2D45" }, light: { bg: "#F8FAFC", card: "#FFFFFF", border: "#E2E8F0" } },
  charcoal: { dark: { bg: "#1a1a2e", card: "#222240", border: "#333355" }, light: { bg: "#F0F0F5", card: "#FFFFFF", border: "#D4D4E0" } },
  slate:    { dark: { bg: "#0f172a", card: "#1e293b", border: "#334155" }, light: { bg: "#F1F5F9", card: "#FFFFFF", border: "#CBD5E1" } },
  midnight: { dark: { bg: "#0d1117", card: "#161b22", border: "#30363d" }, light: { bg: "#F5F5F5", card: "#FFFFFF", border: "#D0D0D0" } },
  espresso: { dark: { bg: "#1c1917", card: "#292524", border: "#44403c" }, light: { bg: "#FAF8F5", card: "#FFFFFF", border: "#E7E0D8" } },
  forest:   { dark: { bg: "#081c15", card: "#1b4332", border: "#2d6a4f" }, light: { bg: "#F0FAF5", card: "#FFFFFF", border: "#C6E8D5" } },
};

const FONT_SIZE_MAP = {
  small: "14px",
  medium: "16px",
  large: "18px",
  xlarge: "20px",
};

const FONT_SIZE_SCALE = {
  small: { base: "14px", h1: "1.75rem", h2: "1.5rem", h3: "1.25rem" },
  medium: { base: "16px", h1: "2rem", h2: "1.75rem", h3: "1.5rem" },
  large: { base: "18px", h1: "2.25rem", h2: "2rem", h3: "1.75rem" },
  xlarge: { base: "20px", h1: "2.5rem", h2: "2.25rem", h3: "2rem" },
};

const SPACING_SCALE = {
  compact: { xs: "0.25rem", sm: "0.5rem", md: "0.75rem", lg: "1rem", xl: "1.25rem", "2xl": "1.5rem" },
  comfortable: { xs: "0.5rem", sm: "0.75rem", md: "1rem", lg: "1.5rem", xl: "2rem", "2xl": "2.5rem" },
  spacious: { xs: "0.75rem", sm: "1rem", md: "1.5rem", lg: "2rem", xl: "3rem", "2xl": "4rem" },
};

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const theme = useSettingsStore((s) => s.theme);
  const primaryColor = useSettingsStore((s) => s.primaryColor);
  const backgroundColor = useSettingsStore((s) => s.backgroundColor);
  const boldText = useSettingsStore((s) => s.boldText);
  const fontSize = useSettingsStore((s) => s.fontSize);
  const elementSize = useSettingsStore((s) => s.elementSize);
  const highContrast = useSettingsStore((s) => s.highContrast);
  const reducedMotion = useSettingsStore((s) => s.reducedMotion);
  const dyslexiaFont = useSettingsStore((s) => s.dyslexiaFont);
  const focusIndicator = useSettingsStore((s) => s.focusIndicator);

  useEffect(() => {
    const root = document.documentElement;
    const palette = PRIMARY_COLOR_MAP[primaryColor] || PRIMARY_COLOR_MAP.blue;

    // Theme
    const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    root.classList.toggle("dark", isDark);
    root.classList.toggle("light", !isDark);

    // Primary color — the single source of truth for all accent-derived tokens
    const primary = isDark ? palette.dark : palette.light;
    root.style.setProperty("--color-psi-electric", primary);
    root.style.setProperty("--color-psi-electric-contrast", primary);
    root.style.setProperty("--color-primary", primary);
    root.style.setProperty("--color-accent", primary);
    root.style.setProperty("--color-ring", primary);
    root.style.setProperty("--psi-primary-rgb", palette.rgb);

    // Reset any previously overridden semantic tokens back to CSS defaults,
    // then re-apply only if the selected color coincides with that semantic role.
    // (Uses empty string to remove the inline-style override, letting the
    //  stylesheet's var(--color-psi-*) chain take over again.)
    const resetSemantic = (name: string) => root.style.setProperty(name, "");

    if (primaryColor === "green") {
      root.style.setProperty("--color-success", primary);
      root.style.setProperty("--color-success-foreground", "#FFFFFF");
    } else {
      resetSemantic("--color-success");
      resetSemantic("--color-success-foreground");
    }

    if (primaryColor === "red") {
      root.style.setProperty("--color-destructive", primary);
      root.style.setProperty("--color-destructive-foreground", "#FFFFFF");
    } else {
      resetSemantic("--color-destructive");
      resetSemantic("--color-destructive-foreground");
    }

    if (primaryColor === "orange") {
      root.style.setProperty("--color-warning", primary);
    } else {
      resetSemantic("--color-warning");
    }

    // Background color — overrides body background, card surface, and border
    const bgPalette = BACKGROUND_COLOR_MAP[backgroundColor] || BACKGROUND_COLOR_MAP.navy;
    const bg = isDark ? bgPalette.dark : bgPalette.light;

    // Semantic tokens (used by components with bg-background, bg-card, border-border etc.)
    root.style.setProperty("--color-background", bg.bg);
    root.style.setProperty("--color-card", bg.card);
    root.style.setProperty("--color-popover", bg.card);
    root.style.setProperty("--color-border", bg.border);
    root.style.setProperty("--color-input", bg.border);
    root.style.setProperty("--color-secondary", bg.border);

    // ═══════════════════════════════════════════════════════════════════
    // RAW PALETTE OVERRIDES — critical for legacy components that use
    // bg-psi-navy, bg-psi-graphite, border-psi-border directly instead
    // of the semantic chain (bg-background, bg-card, border-border).
    // These override the @theme definitions in globals.css so that ALL
    // components — including AppLayout, Sidebar, and Navbar — reflect
    // the user's chosen background palette immediately.
    // ═══════════════════════════════════════════════════════════════════
    if (isDark) {
      root.style.setProperty("--color-psi-navy", bg.bg);
      root.style.setProperty("--color-psi-graphite", bg.card);
      root.style.setProperty("--color-psi-border", bg.border);
      // The light palette raw vars are restored to their defaults
      // so that switching themes later works correctly.
      root.style.setProperty("--color-light-bg", bgPalette.light.bg);
      root.style.setProperty("--color-light-surface", bgPalette.light.card);
      root.style.setProperty("--color-light-border", bgPalette.light.border);
    } else {
      root.style.setProperty("--color-light-bg", bg.bg);
      root.style.setProperty("--color-light-surface", bg.card);
      root.style.setProperty("--color-light-border", bg.border);
      // Restore dark palette raw vars so they reflect the chosen palette
      // when the user switches back to dark mode.
      root.style.setProperty("--color-psi-navy", bgPalette.dark.bg);
      root.style.setProperty("--color-psi-graphite", bgPalette.dark.card);
      root.style.setProperty("--color-psi-border", bgPalette.dark.border);
    }

    // Font size
    const sizes = FONT_SIZE_SCALE[fontSize] || FONT_SIZE_SCALE.medium;
    root.style.setProperty("--font-size-base", sizes.base);
    root.style.fontSize = sizes.base;

    // Bold text
    root.style.setProperty("--font-weight-base", boldText ? "600" : "400");
    root.style.setProperty("--font-weight-heading", boldText ? "800" : "700");
    if (boldText) {
      root.classList.add("bold-text");
    } else {
      root.classList.remove("bold-text");
    }

    // Element spacing
    const spacing = SPACING_SCALE[elementSize] || SPACING_SCALE.comfortable;
    root.style.setProperty("--spacing-xs", spacing.xs);
    root.style.setProperty("--spacing-sm", spacing.sm);
    root.style.setProperty("--spacing-md", spacing.md);
    root.style.setProperty("--spacing-lg", spacing.lg);
    root.style.setProperty("--spacing-xl", spacing.xl);
    root.style.setProperty("--spacing-2xl", spacing["2xl"]);

    // High contrast
    if (highContrast) {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }

    // Reduced motion
    if (reducedMotion) {
      root.classList.add("reduced-motion");
    } else {
      root.classList.remove("reduced-motion");
    }

    // Dyslexia font
    if (dyslexiaFont) {
      root.classList.add("dyslexia-font");
    } else {
      root.classList.remove("dyslexia-font");
    }

    // Focus indicator
    if (!focusIndicator) {
      root.classList.add("no-focus-indicator");
    } else {
      root.classList.remove("no-focus-indicator");
    }

    // Theme system listener
    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = (e: MediaQueryListEvent) => {
        root.classList.toggle("dark", e.matches);
        root.classList.toggle("light", !e.matches);
      };
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme, primaryColor, backgroundColor, boldText, fontSize, elementSize, highContrast, reducedMotion, dyslexiaFont, focusIndicator]);

  return <>{children}</>;
}
