// ============================================================
// PaySentinelIQ — Executive Intelligence Center (Reports)
// Premium enterprise-grade fraud intelligence reporting dashboard
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { cn, formatNumber } from "@/lib/utils";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  PSI_CHART_COLORS,
  psiChartDefaults,
  tooltipStyle,
} from "@/components/charts/ChartTheme";
import {
  ResponsiveContainer,
  LineChart,
  PieChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
  Pie,
} from "recharts";
import {
  FileText,
  AlertTriangle,
  Shield,
  DollarSign,
  Clock,
  CheckCircle,
  Brain,
  Download,
  FileSpreadsheet,
  Share2,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  PieChart as PieChartIcon,
  Activity,
} from "lucide-react";

// ============================================================
// Mock Data
// ============================================================

const FRAUD_TREND_DAYS = 30;
const fraudTrendData = Array.from({ length: FRAUD_TREND_DAYS }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (FRAUD_TREND_DAYS - 1 - i));
  return {
    date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    fraudGrowth: 40 + Math.sin(i * 0.5) * 15 + Math.random() * 10,
    documentsAnalyzed: 300 + Math.sin(i * 0.3) * 80 + Math.random() * 40,
    suspiciousActivity: 80 + Math.cos(i * 0.4) * 25 + Math.random() * 15,
  };
});

const riskDistributionData = [
  { name: "Low Risk", value: 58, color: PSI_CHART_COLORS.secondary },
  { name: "Medium Risk", value: 22, color: PSI_CHART_COLORS.warning },
  { name: "High Risk", value: 13, color: "#FF6B35" },
  { name: "Critical Risk", value: 7, color: PSI_CHART_COLORS.danger },
];

const fraudCausesData = [
  { cause: "Payroll Inconsistency", occurrences: 234, avgRiskScore: 87, trend: "up", change: 12 },
  { cause: "OCR Mismatch", occurrences: 189, avgRiskScore: 76, trend: "up", change: 8 },
  { cause: "Metadata Manipulation", occurrences: 145, avgRiskScore: 92, trend: "down", change: 3 },
  { cause: "Signature Anomaly", occurrences: 98, avgRiskScore: 71, trend: "up", change: 15 },
  { cause: "Payment Slip Mismatch", occurrences: 76, avgRiskScore: 64, trend: "neutral", change: 0 },
];

const kpiData = [
  { key: "documentsAnalyzed", icon: FileText, value: 12847, change: 12.3, trend: "up", color: PSI_CHART_COLORS.primary, sparkline: [40, 72, 58, 90, 75, 110, 95, 128, 105, 85, 130, 115] },
  { key: "fraudCasesDetected", icon: AlertTriangle, value: 847, change: 8.7, trend: "up", color: PSI_CHART_COLORS.danger, sparkline: [12, 18, 9, 22, 15, 28, 20, 24, 30, 18, 35, 27] },
  { key: "averageRiskScore", icon: Shield, value: 67.4, change: 3.2, trend: "down", color: PSI_CHART_COLORS.warning, sparkline: [72, 68, 70, 65, 63, 67, 64, 61, 66, 62, 60, 67.4] },
  { key: "preventedLosses", icon: DollarSign, value: 2400000, change: 15.1, trend: "up", color: PSI_CHART_COLORS.secondary, sparkline: [1.2, 1.5, 1.3, 1.8, 1.6, 2.0, 1.9, 2.2, 2.1, 2.3, 2.5, 2.4] },
  { key: "avgAnalysisTime", icon: Clock, value: 3.2, change: 22.5, trend: "down", color: PSI_CHART_COLORS.primary, sparkline: [5.8, 5.2, 4.9, 4.5, 4.1, 3.8, 3.6, 3.5, 3.4, 3.3, 3.2, 3.2] },
  { key: "successRate", icon: CheckCircle, value: 97.8, change: 1.2, trend: "up", color: PSI_CHART_COLORS.secondary, sparkline: [94, 94.5, 95.2, 95.8, 96.1, 96.5, 96.8, 97.0, 97.2, 97.4, 97.6, 97.8] },
];

// ============================================================
// Inline Sparkline Component
// ============================================================

function Sparkline({ data, color, height = 28 }: { data: number[]; color: string; height?: number }) {
  const width = 60;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  });
  const pathD = `M${points.join(" L")}`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="shrink-0">
      <path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.8" />
    </svg>
  );
}

// ============================================================
// Animated Counter (framer-motion count-up)
// ============================================================

function AnimatedCounter({ value, prefix, suffix, decimals = 0 }: { value: number; prefix?: string; suffix?: string; decimals?: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value <= 0) return;
    const duration = 1200;
    const steps = 50;
    const increment = value / steps;
    let current = 0;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      current += increment;
      if (step >= steps) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(current);
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  const formatted = decimals > 0 ? display.toFixed(decimals) : Math.round(display).toLocaleString();

  return (
    <span className="tabular-nums">
      {prefix}{formatted}{suffix}
    </span>
  );
}

// ============================================================
// Props for the chart tooltip
// ============================================================

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={tooltipStyle.contentStyle}>
      <p style={tooltipStyle.labelStyle}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, fontSize: "13px", fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : p.value}
        </p>
      ))}
    </div>
  );
}

// ============================================================
// Risk Distribution Pie Tooltip
// ============================================================

function RiskTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { color: string } }> }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div style={tooltipStyle.contentStyle}>
      <p style={{ color: p.payload.color, fontWeight: 600, fontSize: "13px" }}>
        {p.name}: {p.value}%
      </p>
    </div>
  );
}

// ============================================================
// Page Component
// ============================================================

export default function ReportsPage() {
  const t = useTranslations("reports");

  return (
    <div className="space-y-8">
      {/* ── Background Grid Layer ── */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        <svg className="absolute w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="reports-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke={PSI_CHART_COLORS.primary} strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#reports-grid)" />
        </svg>
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-psi-electric/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 -right-32 w-80 h-80 bg-psi-emerald/5 rounded-full blur-[120px]" />
      </div>

      {/* ── 1. Hero Card ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <Card glow className="relative overflow-hidden border-psi-electric/20">
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
            <div className="absolute -inset-[200%] animate-pulse bg-gradient-to-r from-psi-electric/[0.03] via-psi-emerald/[0.02] to-psi-electric/[0.03] blur-3xl" />
          </div>
          <CardContent className="relative z-10 p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row items-start gap-5">
              <div className="shrink-0 flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-psi-electric/20 to-psi-emerald/10 border border-psi-electric/20">
                <Brain className="h-7 w-7 text-psi-electric" />
              </div>
              <div className="flex-1 min-w-0 space-y-3">
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
                    {t("pageTitle") || "Executive Intelligence Center"}
                  </h1>
                  <Badge variant="primary" dot>
                    {t("aiGenerated") || "AI Generated"}
                  </Badge>
                </div>
                <p className="text-sm text-psi-text-primary/80 leading-relaxed max-w-3xl">
                  {t("pageDescription") || "Over the last 30 days, 428 documents were analyzed. 37 high-risk cases were identified. Main anomaly detected: payroll inconsistency and metadata manipulation."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── 2. KPI Cards ── */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.06 } } }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4"
      >
        {kpiData.map((kpi) => {
          const Icon = kpi.icon;
          const isUp = kpi.trend === "up";
          const isDown = kpi.trend === "down";
          const trendColor = kpi.key === "averageRiskScore" || kpi.key === "avgAnalysisTime"
            ? (isDown ? "text-psi-emerald" : "text-psi-fraud")
            : (isUp ? "text-psi-emerald" : "text-psi-fraud");

          return (
            <motion.div
              key={kpi.key}
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <Card variant="interactive" glow className="group h-full">
                <CardContent className="p-4 flex flex-col h-full">
                  <div className="flex items-start justify-between mb-3">
                    <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider truncate pr-2">
                      {t(kpi.key) || kpi.key}
                    </p>
                    <div className="rounded-lg bg-psi-electric/10 p-1.5 shrink-0 group-hover:bg-psi-electric/20 transition-colors">
                      <Icon className="h-3.5 w-3.5 text-psi-electric" />
                    </div>
                  </div>
                  <div className="flex items-baseline gap-1 mb-1">
                    <span className="text-2xl font-bold text-psi-text-primary tabular-nums">
                      {kpi.key === "preventedLosses" ? (
                        <AnimatedCounter value={kpi.value / 100000} prefix="$" suffix="M" decimals={1} />
                      ) : kpi.key === "averageRiskScore" ? (
                        <AnimatedCounter value={kpi.value} decimals={1} />
                      ) : kpi.key === "avgAnalysisTime" ? (
                        <><AnimatedCounter value={kpi.value} decimals={1} /><span className="text-sm font-medium text-psi-text-secondary ml-0.5">s</span></>
                      ) : kpi.key === "successRate" ? (
                        <><AnimatedCounter value={kpi.value} decimals={1} /><span className="text-sm font-medium text-psi-text-secondary">%</span></>
                      ) : (
                        <AnimatedCounter value={kpi.value} />
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mb-auto">
                    {isUp ? (
                      <ArrowUpRight className={cn("h-3 w-3", trendColor)} />
                    ) : isDown ? (
                      <ArrowDownRight className={cn("h-3 w-3", trendColor)} />
                    ) : (
                      <Minus className="h-3 w-3 text-psi-text-secondary" />
                    )}
                    <span className={cn("text-xs font-semibold", trendColor)}>
                      {kpi.change}%
                    </span>
                    <span className="text-[10px] text-psi-text-secondary">
                      {t("vsLastPeriod") || "vs last period"}
                    </span>
                  </div>
                  <div className="mt-2 flex justify-end">
                    <Sparkline data={kpi.sparkline} color={kpi.color} />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* ── 3 & 4: Risk Distribution + Fraud Trend ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Risk Distribution Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
          className="lg:col-span-2"
        >
          <Card glow className="h-full">
            <CardHeader>
              <div className="flex items-center gap-2">
                <PieChartIcon className="h-4 w-4 text-psi-electric" />
                <CardTitle>{t("riskDistribution") || "Risk Distribution"}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center">
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={riskDistributionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                      animationBegin={300}
                      animationDuration={1000}
                      animationEasing="ease-out"
                    >
                      {riskDistributionData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip content={<RiskTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap justify-center gap-4 mt-4">
                  {riskDistributionData.map((entry, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
                      <span className="text-xs text-psi-text-secondary">{entry.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Fraud Trend Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
          className="lg:col-span-3"
        >
          <Card glow className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-psi-electric" />
                  <CardTitle>{t("fraudTrendAnalysis") || "Fraud Trend Analysis"}</CardTitle>
                </div>
                <div className="hidden sm:flex items-center gap-1">
                  {(["today", "last7Days", "last30Days", "last90Days", "custom"] as const).map((period) => (
                    <button
                      key={period}
                      className={cn(
                        "px-2.5 py-1 text-xs font-medium rounded-md transition-all",
                        period === "last30Days"
                          ? "bg-psi-electric text-white"
                          : "text-psi-text-secondary hover:text-psi-text-primary hover:bg-psi-border/30"
                      )}
                    >
                      {t(period) || period}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={fraudTrendData} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="fraudGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={PSI_CHART_COLORS.danger} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={PSI_CHART_COLORS.danger} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="docGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={PSI_CHART_COLORS.primary} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={PSI_CHART_COLORS.primary} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="suspGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={PSI_CHART_COLORS.warning} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={PSI_CHART_COLORS.warning} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={psiChartDefaults.gridStroke} strokeOpacity={psiChartDefaults.gridOpacity} vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke={psiChartDefaults.axisStroke}
                    tick={{ fill: psiChartDefaults.tickFill, fontSize: psiChartDefaults.tickFontSize }}
                    tickLine={false}
                    axisLine={false}
                    interval={4}
                  />
                  <YAxis
                    stroke={psiChartDefaults.axisStroke}
                    tick={{ fill: psiChartDefaults.tickFill, fontSize: psiChartDefaults.tickFontSize }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    wrapperStyle={{ fontSize: "11px", color: psiChartDefaults.legendText, paddingTop: "8px" }}
                    iconType="circle"
                    iconSize={8}
                  />
                  <Area type="monotone" dataKey="documentsAnalyzed" stroke={PSI_CHART_COLORS.primary} fill="url(#docGradient)" strokeWidth={2} name="Documents Analyzed" dot={false} />
                  <Line type="monotone" dataKey="fraudGrowth" stroke={PSI_CHART_COLORS.danger} strokeWidth={2} name="Fraud Growth" dot={false} strokeDasharray="4 3" />
                  <Line type="monotone" dataKey="suspiciousActivity" stroke={PSI_CHART_COLORS.warning} strokeWidth={2} name="Suspicious Activity" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── 5. Top Fraud Causes Table ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.35, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("fraudCauses") || "Top Fraud Causes"}</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-psi-border/50">
                    <th className="text-left text-xs font-medium text-psi-text-secondary uppercase tracking-wider px-6 py-3">
                      {t("cause") || "Cause"}
                    </th>
                    <th className="text-right text-xs font-medium text-psi-text-secondary uppercase tracking-wider px-6 py-3">
                      {t("occurrences") || "Occurrences"}
                    </th>
                    <th className="text-right text-xs font-medium text-psi-text-secondary uppercase tracking-wider px-6 py-3">
                      {t("averageRisk") || "Avg Risk Score"}
                    </th>
                    <th className="text-right text-xs font-medium text-psi-text-secondary uppercase tracking-wider px-6 py-3">
                      {t("trend") || "Trend"}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {fraudCausesData.map((row, i) => (
                    <tr
                      key={row.cause}
                      className={cn(
                        "border-b border-psi-border/20 transition-colors hover:bg-psi-electric/[0.02] group",
                        i === fraudCausesData.length - 1 && "border-b-0"
                      )}
                    >
                      <td className="px-6 py-3.5">
                        <span className="text-psi-text-primary font-medium">{row.cause}</span>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <span className="text-psi-text-primary font-semibold tabular-nums">{formatNumber(row.occurrences)}</span>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold",
                            row.avgRiskScore >= 90 ? "bg-psi-fraud/10 text-psi-fraud" :
                            row.avgRiskScore >= 75 ? "bg-psi-warning/10 text-psi-warning" :
                            "bg-psi-emerald/10 text-psi-emerald"
                          )}
                        >
                          {row.avgRiskScore}%
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <Badge
                          variant={
                            row.trend === "up" ? "destructive" :
                            row.trend === "down" ? "success" : "default"
                          }
                          className="tabular-nums"
                        >
                          {row.trend === "up" ? <ArrowUpRight className="h-3 w-3" /> :
                           row.trend === "down" ? <ArrowDownRight className="h-3 w-3" /> :
                           <Minus className="h-3 w-3" />}
                          {row.change > 0 ? "+" : ""}{row.change}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── 6. AI Insights Card ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4, ease: "easeOut" }}
      >
        <Card glow className="relative overflow-hidden border-psi-electric/20">
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
            <div className="absolute top-0 right-0 w-64 h-64 bg-psi-electric/[0.04] rounded-full blur-[80px]" />
          </div>
          <CardContent className="relative z-10 p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row items-start gap-6">
              <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-psi-electric/20 to-psi-emerald/10 border border-psi-electric/20 signal-pulse">
                <Brain className="h-6 w-6 text-psi-electric" />
              </div>
              <div className="flex-1 min-w-0 space-y-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-psi-text-primary">
                    {t("aiInsightsTitle") || "AI Intelligence Summary"}
                  </h3>
                  <Badge variant="primary" dot>{t("aiGenerated") || "AI Generated"}</Badge>
                </div>
                <p className="text-sm text-psi-text-primary/80 leading-relaxed">
                  {t("aiInsightText") || "AI detected a 34% increase in payroll inconsistencies during the last two weeks. Recommended action: Review HR access logs and cross-reference with overtime records."}
                </p>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-psi-text-secondary">
                      {t("confidence") || "Confidence"}
                    </span>
                    <div className="w-32 h-2 rounded-full bg-psi-border/50 overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-psi-electric to-psi-emerald" style={{ width: "94%" }} />
                    </div>
                    <span className="text-xs font-bold text-psi-emerald tabular-nums">94%</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {["Review HR access logs", "Cross-reference overtime", "Escalate to compliance"].map((rec, i) => (
                      <Badge key={i} variant="outline" className="text-[11px]">
                        {rec}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── 7. Export Tools ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.45, ease: "easeOut" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-sm font-semibold text-psi-text-primary mr-2">
            {t("exportTools") || "Export & Share"}
          </h3>
          <Button variant="primary" size="sm">
            <Download className="h-4 w-4" />
            {t("exportPDF") || "Export PDF"}
          </Button>
          <Button variant="outline" size="sm">
            <FileSpreadsheet className="h-4 w-4" />
            {t("exportCSV") || "Export CSV"}
          </Button>
          <Button variant="secondary" size="sm">
            <Share2 className="h-4 w-4" />
            {t("shareReport") || "Share Report"}
          </Button>
          <Button variant="ghost" size="sm" className="relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-r from-psi-electric/5 to-psi-emerald/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            <FileText className="h-4 w-4 relative z-10" />
            <span className="relative z-10">{t("generateReport") || "Generate Executive Report"}</span>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
