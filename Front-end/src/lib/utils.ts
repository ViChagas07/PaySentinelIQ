import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS classes with conflict resolution.
 * Used throughout the PSI application for conditional styling.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formats a number with thousand separators.
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

/**
 * Formats currency with symbol.
 */
export function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Formats a percentage string from a 0-1 or 0-100 value.
 */
export function formatPercent(value: number, inputIsFraction = true): string {
  const percent = inputIsFraction ? value * 100 : value;
  return `${percent.toFixed(1)}%`;
}

/**
 * Truncates text with ellipsis.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

/**
 * Returns a risk-level CSS class for dynamic styling.
 */
export function riskColorClass(riskLevel: "low" | "medium" | "high" | "critical"): string {
  const map = {
    low: "text-psi-emerald bg-psi-emerald/10 border-psi-emerald/30",
    medium: "text-psi-warning bg-psi-warning/10 border-psi-warning/30",
    high: "text-psi-fraud bg-psi-fraud/10 border-psi-fraud/30",
    critical: "text-psi-fraud bg-psi-fraud/20 border-psi-fraud/50",
  };
  return map[riskLevel];
}
