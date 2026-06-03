// ============================================================
// PaySentinelIQ — Risk Score Distribution Chart
// Histogram-style bar chart showing risk score distribution
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { PSI_CHART_COLORS, tooltipStyle } from "./ChartTheme";
import { useDashboardRiskDistribution } from "@/hooks/useApi";

interface RiskBucket {
  range: string;
  count: number;
  color: string;
}

// ── Chart Component ── //

export function RiskDistributionChart() {
  const t = useTranslations("charts");
  const tc = useTranslations("common");

  const { data: riskBuckets, isLoading } = useDashboardRiskDistribution();

  const riskScoreLabel = t("riskScore");
  const payrollsLabel = t("payrolls");
  const riskScoreRangeLabel = t("riskScoreRange");
  const payrollsAnalyzedLabel = t("payrollsAnalyzed");
  const lowRiskLabel = t("riskLowLabel");
  const highRiskLabel = t("riskHighLabel");

  const displayBuckets = riskBuckets || [];
  const totalPayrolls = displayBuckets.reduce((sum, b) => sum + b.count, 0);

  // ── Custom Tooltip ── //

  function CustomTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const data = payload[0]?.payload as RiskBucket;
    if (!data) return null;

    return (
      <div style={tooltipStyle.contentStyle}>
        <p style={tooltipStyle.labelStyle}>
          {riskScoreLabel}: {data.range}
        </p>
        <div className="flex items-center gap-2 text-sm">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: data.color }}
          />
          <span className="text-psi-text-secondary">{payrollsLabel}:</span>
          <span className="font-semibold text-psi-text-primary">
            {data.count.toLocaleString()}
          </span>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
      </div>
    );
  }

  // Calculate realistic percentages from real data
  const lowRiskCount = displayBuckets
    .filter((b) => parseInt(b.range.split("-")[0]) < 4)
    .reduce((s, b) => s + b.count, 0);
  const highRiskCount = displayBuckets
    .filter((b) => parseInt(b.range.split("-")[0]) >= 6)
    .reduce((s, b) => s + b.count, 0);
  const lowRiskPct = totalPayrolls > 0 ? Math.round((lowRiskCount / totalPayrolls) * 100) : 0;
  const highRiskPct = totalPayrolls > 0 ? Math.round((highRiskCount / totalPayrolls) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="h-64 w-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={displayBuckets}
          margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
          barSize={48}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={PSI_CHART_COLORS.grid}
            strokeOpacity={0.3}
            vertical={false}
          />

          <XAxis
            dataKey="range"
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            label={{
              value: riskScoreRangeLabel,
              position: "bottom",
              offset: 0,
              fill: PSI_CHART_COLORS.textSecondary,
              fontSize: 10,
            }}
          />

          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(30, 111, 255, 0.05)" }} />

          <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={60}>
            {displayBuckets.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.color}
                fillOpacity={0.85}
                stroke={entry.color}
                strokeWidth={0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Summary stats — calculated from real data */}
      <div className="flex items-center justify-between mt-2 px-2">
        <span className="text-[11px] text-psi-text-secondary">
          {tc("total")}:{" "}
          <span className="font-semibold text-psi-text-primary">
            {totalPayrolls.toLocaleString()}
          </span>{" "}
          {payrollsAnalyzedLabel}
        </span>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-psi-emerald" />
            <span className="text-[11px] text-psi-text-secondary">
              {lowRiskLabel} ({lowRiskPct}%)
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-psi-fraud" />
            <span className="text-[11px] text-psi-text-secondary">
              {highRiskLabel} ({highRiskPct}%)
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
