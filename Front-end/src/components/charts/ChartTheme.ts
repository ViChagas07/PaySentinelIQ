// ============================================================
// PaySentinelIQ — Recharts Dark Theme Configuration
// ============================================================

/**
 * Shared Recharts configuration for PSI dark theme.
 * All charts inherit these defaults for consistent branding.
 */

export const PSI_CHART_COLORS = {
  primary: "#1E6FFF",        // Electric Blue
  secondary: "#00C48C",      // Emerald
  warning: "#FF8C00",        // Warning Orange
  danger: "#D63B3B",         // Fraud Red
  textPrimary: "#F4F6FA",
  textSecondary: "#8BA3CC",
  grid: "#1E2D45",
  background: "#111827",
};

export const psiChartDefaults = {
  // Axis
  axisStroke: PSI_CHART_COLORS.grid,
  tickFill: PSI_CHART_COLORS.textSecondary,
  tickFontSize: 11,

  // Grid
  gridStroke: PSI_CHART_COLORS.grid,
  gridOpacity: 0.4,

  // Tooltip
  tooltipBg: "#111827",
  tooltipBorder: "#1E2D45",
  tooltipText: "#F4F6FA",

  // Legend
  legendText: PSI_CHART_COLORS.textSecondary,

  // Common
  radius: 8,
  animationDuration: 800,
};

/**
 * Generates gradient IDs and definitions for area/bar charts.
 */
export function getGradientDefs(id: string, color: string) {
  return {
    id: `gradient-${id}`,
    startColor: color,
    endColor: `${color}10`,
  };
}

/**
 * Standard tooltip wrapper style.
 */
export const tooltipStyle = {
  contentStyle: {
    backgroundColor: psiChartDefaults.tooltipBg,
    border: `1px solid ${psiChartDefaults.tooltipBorder}`,
    borderRadius: "8px",
    color: psiChartDefaults.tooltipText,
    fontSize: "13px",
    boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
  },
  labelStyle: {
    color: PSI_CHART_COLORS.textSecondary,
    fontWeight: 500,
    marginBottom: "4px",
  },
};
