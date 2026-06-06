// ============================================================
// PaySentinelIQ — Network Color System
// HSL-based intelligent color generation for the animated
// background network. Every color is derived from the user's
// chosen primary color in Settings → Appearance → Main Color.
// ============================================================

import type { PrimaryColor } from "@/stores/settings-store";

// ── Base hue for each primary color option ── //
const HUE_MAP: Record<PrimaryColor, number> = {
  blue:   217,  // #3B82F6 → hsl(217, 91%, 60%)
  green:  160,  // #10B981 → hsl(160, 84%, 39%)
  purple: 267,  // #A78BFA → hsl(267, 91%, 76%)
  orange:  30,  // #F97316 → hsl(30, 95%, 53%)
  red:      0,  // #EF4444 → hsl(0, 83%, 59%)
  teal:   172,  // #2DD4BF → hsl(172, 66%, 50%)
};

/**
 * Returns the base hue (0-360) for a given primary color name.
 */
export function getPrimaryHue(color: PrimaryColor): number {
  return HUE_MAP[color] ?? HUE_MAP.blue;
}

// ── Helper: clamp a hue to 0-360 ── //
function clampHue(h: number): number {
  return ((h % 360) + 360) % 360;
}

// ── Helper: build an hsla string ── //
function hsla(h: number, s: number, l: number, a: number): string {
  return `hsla(${clampHue(h)} deg, ${s}%, ${l}%, ${a})`;
}

// ── Helper: build an hsl string ── //
function hsl(h: number, s: number, l: number): string {
  return `hsl(${clampHue(h)} deg, ${s}%, ${l}%)`;
}

// ── Helper: build an rgba string from an hsla value ── //
// This converts to RGB for better browser compatibility with SVG
// (some SVG renderers handle rgba better than hsla)
function hslaToRgba(h: number, s: number, l: number, a: number): string {
  // Convert HSL to RGB
  const sNorm = s / 100;
  const lNorm = l / 100;
  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm;
  const x = c * (1 - Math.abs(((clampHue(h) / 60) % 2) - 1));
  const m = lNorm - c / 2;
  let r = 0, g = 0, b = 0;

  const hueSegment = clampHue(h) / 60;
  if (hueSegment < 1) { r = c; g = x; b = 0; }
  else if (hueSegment < 2) { r = x; g = c; b = 0; }
  else if (hueSegment < 3) { r = 0; g = c; b = x; }
  else if (hueSegment < 4) { r = 0; g = x; b = c; }
  else if (hueSegment < 5) { r = x; g = 0; b = c; }
  else { r = c; g = 0; b = x; }

  return `rgba(${Math.round((r + m) * 255)},${Math.round((g + m) * 255)},${Math.round((b + m) * 255)},${a})`;
}

// ── Exported interface for the full network color set ── //
export interface NetworkColorSet {
  /** Primary line colour (svg stroke) */
  line: string;
  /** Brighter line colour for pulsing connections */
  lineGlow: string;
  /** Node core colour (svg fill) */
  node: string;
  /** Node colour when glowing */
  nodeGlow: string;
  /** Node glow halo colour (radial gradient stop) */
  glowHalo: string;
  /** Grid line colour */
  grid: string;
  /** Blob colours (up to 5 variants) */
  blobs: string[];
  /** Reduced motion fallback gradient colours */
  fallbackGradients: string[];
  /** Base RGB values as comma-separated string for inline usage */
  rgb: string;
}

/**
 * Generates a full set of network colours from a primary color name.
 * Uses HSL manipulation to create intelligent variants:
 *
 * - Lines:        base hue, desaturated, ~45% lightness
 * - Line glow:    base hue, full sat, ~55% lightness
 * - Nodes:        base hue, med sat, ~65% lightness
 * - Node glow:    base hue -10, full sat, ~75% lightness
 * - Glow halo:    base hue, med sat, ~70% lightness
 * - Grid:         base hue, sat, ~55% lightness
 * - Blobs:        shifted hues for variety
 * - Fallback:     softer versions for reduced motion
 */
export function generateNetworkColors(color: PrimaryColor): NetworkColorSet {
  const h = getPrimaryHue(color);

  return {
    line:        hslaToRgba(h, 60, 45, 0.06),
    lineGlow:    hslaToRgba(h, 80, 60, 0.5),
    node:        hslaToRgba(h, 30, 65, 0.35),
    nodeGlow:    hslaToRgba(h, 85, 75, 0.85),
    glowHalo:    hslaToRgba(h, 60, 70, 0.15),
    grid:        hslaToRgba(h, 50, 55, 0.06),
    blobs: [
      hslaToRgba(h,       70, 55, 0.08),  // primary
      hslaToRgba(h + 30,  60, 50, 0.06),  // shifted
      hslaToRgba(h - 20,  65, 60, 0.06),  // shifted
      hslaToRgba(h + 15,  55, 45, 0.05),  // shifted
      hslaToRgba(h,       50, 50, 0.07),  // primary muted
    ],
    fallbackGradients: [
      hslaToRgba(h,       60, 55, 0.06),
      hslaToRgba(h + 30,  50, 50, 0.04),
      hslaToRgba(h - 20,  55, 60, 0.04),
    ],
    rgb: rgbFromHsla(h, 80, 60),
  };
}

/**
 * Converts a base colour to its RGB comma-separated string.
 * Used for --psi-primary-rgb style variables.
 */
function rgbFromHsla(h: number, s: number, l: number): string {
  const sNorm = s / 100;
  const lNorm = l / 100;
  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm;
  const x = c * (1 - Math.abs(((clampHue(h) / 60) % 2) - 1));
  const m = lNorm - c / 2;
  let r = 0, g = 0, b = 0;

  const hueSegment = clampHue(h) / 60;
  if (hueSegment < 1) { r = c; g = x; b = 0; }
  else if (hueSegment < 2) { r = x; g = c; b = 0; }
  else if (hueSegment < 3) { r = 0; g = c; b = x; }
  else if (hueSegment < 4) { r = 0; g = x; b = c; }
  else if (hueSegment < 5) { r = x; g = 0; b = c; }
  else { r = c; g = 0; b = x; }

  return `${Math.round((r + m) * 255)},${Math.round((g + m) * 255)},${Math.round((b + m) * 255)}`;
}

/**
 * For use in CSS custom property strings.
 * Returns an hsla() that works well in CSS.
 */
export function getCssHsla(color: PrimaryColor, sat: number, light: number, alpha: number): string {
  const h = getPrimaryHue(color);
  return hsla(h, sat, light, alpha);
}

/**
 * Returns a colour-shifted version of the primary hue for accent blobs.
 */
export function shiftHue(color: PrimaryColor, shift: number): number {
  return clampHue(getPrimaryHue(color) + shift);
}
