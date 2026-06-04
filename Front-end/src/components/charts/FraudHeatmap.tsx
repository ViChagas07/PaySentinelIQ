// ============================================================
// PaySentinelIQ — Fraud Detection Heatmap
// Shows ONLY real department risk data from user activity.
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { PSI_CHART_COLORS, tooltipStyle } from "./ChartTheme";
import { useDashboardHeatmap } from "@/hooks/useApi";

interface DepartmentRisk {
  name: string;
  payrolls: number;
  riskScore: number;
  flaggedCount: number;
  riskLevel: "low" | "medium" | "high";
}

const riskColorMap = {
  low: PSI_CHART_COLORS.secondary,
  medium: PSI_CHART_COLORS.warning,
  high: PSI_CHART_COLORS.danger,
};

const riskLabelKeyMap: Record<string, string> = {
  low: "riskLowLabel",
  medium: "riskMediumLabel",
  high: "riskHighLabel",
};

// ── Chart Component ── /

export function FraudHeatmap() {
  const t = useTranslations("charts");

  const { data: heatmapData, isLoading } = useDashboardHeatmap();

  const payrollsLabel = t("payrolls");
  const riskScoreLabel = t("riskScore");
  const flaggedLabel = t("flagged");
  const payrollCountLabel = t("payrollCount");

  // ── Custom Tooltip ── //

  function CustomTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const data = payload[0]?.payload as DepartmentRisk;
    if (!data) return null;

    return (
      <div style={tooltipStyle.contentStyle}>
        <p style={{ ...tooltipStyle.labelStyle, fontSize: "13px", fontWeight: 600 }}>
          {data.name}
        </p>
        <div className="space-y-1 mt-1">
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-psi-text-secondary">{payrollsLabel}:</span>
            <span className="font-semibold text-psi-text-primary">{data.payrolls}</span>
          </div>
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-psi-text-secondary">{riskScoreLabel}:</span>
            <span className="font-semibold" style={{ color: riskColorMap[data.riskLevel] }}>
              {data.riskScore}/10
            </span>
          </div>
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-psi-text-secondary">{flaggedLabel}:</span>
            <span className="font-semibold text-psi-fraud">{data.flaggedCount}</span>
          </div>
        </div>
      </div>
    );
  }

  // Transform for bubble chart: X=payrolls, Y=riskScore, Z(size)=flaggedCount
  const chartData = ((heatmapData || []) as DepartmentRisk[]).map((d) => ({
    ...d,
    z: Math.max(d.flaggedCount * 25, 100),
  }));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="h-64 w-full"
    >
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="h-8 w-8 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
        </div>
      ) : (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={PSI_CHART_COLORS.grid}
            strokeOpacity={0.3}
          />

          <XAxis
            dataKey="payrolls"
            name={payrollCountLabel}
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            label={{
              value: payrollCountLabel,
              position: "bottom",
              offset: 0,
              fill: PSI_CHART_COLORS.textSecondary,
              fontSize: 10,
            }}
          />

          <YAxis
            dataKey="riskScore"
            name={riskScoreLabel}
            domain={[0, 10]}
            axisLine={false}
            tickLine={false}
            tick={{ fill: PSI_CHART_COLORS.textSecondary, fontSize: 11 }}
            label={{
              value: riskScoreLabel,
              angle: -90,
              position: "left",
              offset: 0,
              fill: PSI_CHART_COLORS.textSecondary,
              fontSize: 10,
            }}
          />

          <ZAxis dataKey="z" range={[40, 400]} />

          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3" }} />

          <Scatter data={chartData}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={riskColorMap[entry.riskLevel]}
                fillOpacity={0.7}
                stroke={riskColorMap[entry.riskLevel]}
                strokeWidth={1}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      )}

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2">
        {(["low", "medium", "high"] as const).map((level) => (
          <div key={level} className="flex items-center gap-1.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: riskColorMap[level] }}
            />
            <span className="text-[11px] text-psi-text-secondary">
              {t(riskLabelKeyMap[level])}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
