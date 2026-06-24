// ============================================================
// PaySentinelIQ — Payroll Verification Trends Chart
// Shows ONLY real data from user activity. No mock/dummy data.
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
} from "recharts";
import { PSI_CHART_COLORS, tooltipStyle } from "./ChartTheme";
import { useDashboardTrends } from "@/hooks/useApi";

// ── Chart Component ── /

export function PayrollTrendChart() {
  const t = useTranslations("charts");

  const { data: trendData, isLoading } = useDashboardTrends();

  const payrollsLabel = t("payrolls");
  const flaggedLabel = t("flagged");
  const passRateLabel = t("passRate");

  // ── Custom Tooltip ── //

  function CustomTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null;

    return (
      <div style={tooltipStyle.contentStyle}>
        <p style={tooltipStyle.labelStyle}>{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-psi-text-secondary">{entry.name}:</span>
            <span className="font-semibold text-psi-text-primary">
              {entry.name === passRateLabel
                ? `${entry.value}%`
                : entry.value.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="h-72 w-full"
    >
      {isLoading ? (
        <div className="flex items-center justify-center h-72">
          <div className="h-8 w-8 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
        </div>
      ) : (
      <ResponsiveContainer width="100%" height={288}>
        <ComposedChart
          data={trendData || []}
          margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PSI_CHART_COLORS.primary} stopOpacity={0.3} />
              <stop offset="100%" stopColor={PSI_CHART_COLORS.primary} stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="flaggedGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PSI_CHART_COLORS.danger} stopOpacity={0.25} />
              <stop offset="100%" stopColor={PSI_CHART_COLORS.danger} stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke={PSI_CHART_COLORS.grid}
            strokeOpacity={0.3}
            vertical={false}
          />

          <XAxis
            dataKey="month"
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            dy={8}
          />

          <YAxis
            yAxisId="left"
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            width={50}
          />

          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[96, 100]}
            tickFormatter={(v) => `${v}%`}
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            width={45}
          />

          <Tooltip content={<CustomTooltip />} />

          <Legend
            wrapperStyle={{
              color: PSI_CHART_COLORS.textSecondary,
              fontSize: 12,
              paddingTop: 12,
            }}
          />

          {/* Volume bars */}
          <Bar
            yAxisId="left"
            dataKey="volume"
            name={payrollsLabel}
            fill={PSI_CHART_COLORS.primary}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
          />

          {/* Flagged area */}
          <Area
            yAxisId="left"
            dataKey="flagged"
            name={flaggedLabel}
            fill="url(#flaggedGradient)"
            stroke={PSI_CHART_COLORS.danger}
            strokeWidth={1.5}
            strokeDasharray="4 4"
          />

          {/* Pass rate line */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="passRate"
            name={passRateLabel}
            stroke={PSI_CHART_COLORS.secondary}
            strokeWidth={2.5}
            dot={{ r: 3, fill: PSI_CHART_COLORS.secondary, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: PSI_CHART_COLORS.secondary, strokeWidth: 0 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
      )}
    </motion.div>
  );
}
