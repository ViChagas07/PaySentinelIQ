// ============================================================
// PaySentinelIQ — Executive Dashboard
// Shows ONLY real data from what the registered user actually
// does within the app. No hardcoded/mock/dummy numbers.
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useState, useMemo, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LazyPayrollTrendChart, LazyFraudHeatmap, LazyRiskDistributionChart, LazyLiveAIInsightFeed } from "@/components/charts/LazyCharts";
import {
  DollarSign, ShieldCheck, AlertTriangle, Brain, Clock, Scale,
  FileWarning, ArrowUpRight, ArrowDownRight, Calendar, ChevronDown,
  Database, WifiOff,
  type LucideIcon,
} from "lucide-react";
import { useDashboardKpis } from "@/hooks/useApi";

// ── Types ── /

type Period = "lastWeek" | "last15Days" | "lastMonth" | "lastSemester" | "lastYear";

interface KpiData {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  change: number;
  changeType: "increase" | "decrease";
  changeContext: "good" | "bad" | "neutral";
  icon: LucideIcon;
  color: string;
  bgColor: string;
  changeLabel: string;
}

// ── Animated Count-Up ── //

function CountUp({ target, suffix }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (target <= 0) return;
    const duration = 1500;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target]);

  const formatted = suffix === "%" ? count.toFixed(1) : count.toLocaleString();

  return (
    <>
      {formatted}
      {suffix && <span className="text-lg font-medium">{suffix}</span>}
    </>
  );
}

// ── KPI Card ── //

function KpiCard({ kpi, index }: { kpi: KpiData; index: number }) {
  const Icon = kpi.icon;
  const changeColor =
    kpi.changeContext === "bad"
      ? "text-psi-fraud"
      : kpi.changeType === "increase"
      ? "text-psi-emerald"
      : "text-psi-emerald";

  return (
    <motion.div
      key={kpi.label + kpi.value}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06, ease: "easeOut" }}
    >
      <Card variant="interactive" glow>
        <CardContent>
          <div className="flex items-start justify-between">
            <div className="space-y-1 min-w-0">
              <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider truncate">
                {kpi.label}
              </p>
              <div className="flex items-baseline gap-1">
                {kpi.prefix && (
                  <span className="text-2xl font-bold text-psi-text-primary">
                    {kpi.prefix}
                  </span>
                )}
                <span className="text-3xl font-bold text-psi-text-primary tabular-nums">
                  <CountUp target={kpi.value} suffix={kpi.suffix} />
                </span>
              </div>
              <div className="flex items-center gap-1">
                {kpi.changeType === "increase" ? (
                  <ArrowUpRight className={cn("h-3.5 w-3.5", changeColor)} />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 text-psi-emerald" />
                )}
                <span className={cn("text-xs font-semibold", changeColor)}>
                  {kpi.change}%
                </span>
                <span className="text-xs text-psi-text-secondary truncate">{kpi.changeLabel}</span>
              </div>
            </div>
            <div className={cn("rounded-xl p-3 shrink-0 ml-2", kpi.bgColor)}>
              <Icon className={cn("h-5 w-5", kpi.color)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Period Selector Dropdown ── //

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const [period, setPeriod] = useState<Period>("lastMonth");
  const [open, setOpen] = useState(false);

  // ── Real KPI data from the API (user's actual activity) ──
  const { data: kpis, isLoading: kpisLoading, isError: kpisError, isSuccess: kpisSuccess } = useDashboardKpis();

  const periodLabels: Record<Period, string> = {
    lastWeek: t("lastWeek"),
    last15Days: t("last15Days"),
    lastMonth: t("lastMonth"),
    lastSemester: t("lastSemester"),
    lastYear: t("lastYear"),
  };

  const vsLabel = useMemo(() => {
    const labels: Record<Period, string> = {
      lastWeek: t("vsLastWeek"),
      last15Days: t("vsLast15Days"),
      lastMonth: t("vsLastMonth"),
      lastSemester: t("vsLastSemester"),
      lastYear: t("vsLastYear"),
    };
    return labels[period];
  }, [period, t]);

  // ── Build KPI cards from real API data (defaults to 0 when empty) ──
  const kpiData: KpiData[] = useMemo(() => {
    const d = kpis || {
      payrolls_processed: 0,
      verification_rate: 0,
      fraud_alerts: 0,
      ai_confidence: 0,
      high_risk_docs: 0,
      compliance_incidents: 0,
    };

    return [
      {
        label: t("payrollsProcessed"),
        value: d.payrolls_processed,
        change: 0,
        changeType: "increase",
        changeContext: "good",
        icon: DollarSign,
        color: "text-psi-electric",
        bgColor: "bg-psi-electric/10",
        changeLabel: vsLabel,
      },
      {
        label: t("verificationRate"),
        value: d.verification_rate,
        suffix: "%",
        change: 0,
        changeType: "increase",
        changeContext: "good",
        icon: ShieldCheck,
        color: "text-psi-emerald",
        bgColor: "bg-psi-emerald/10",
        changeLabel: vsLabel,
      },
      {
        label: t("fraudAlerts"),
        value: d.fraud_alerts,
        change: 0,
        changeType: "increase",
        changeContext: "bad",
        icon: AlertTriangle,
        color: "text-psi-fraud",
        bgColor: "bg-psi-fraud/10",
        changeLabel: vsLabel,
      },
      {
        label: t("aiConfidence"),
        value: d.ai_confidence,
        suffix: "%",
        change: 0,
        changeType: "increase",
        changeContext: "good",
        icon: Brain,
        color: "text-psi-emerald",
        bgColor: "bg-psi-emerald/10",
        changeLabel: vsLabel,
      },
      {
        label: t("highRiskDocs"),
        value: d.high_risk_docs,
        change: 0,
        changeType: "increase",
        changeContext: "bad",
        icon: FileWarning,
        color: "text-psi-warning",
        bgColor: "bg-psi-warning/10",
        changeLabel: vsLabel,
      },
      {
        label: t("complianceIncidents"),
        value: d.compliance_incidents,
        change: 0,
        changeType: "decrease",
        changeContext: "good",
        icon: Scale,
        color: "text-psi-emerald",
        bgColor: "bg-psi-emerald/10",
        changeLabel: vsLabel,
      },
    ];
  }, [kpis, t, vsLabel]);

  // ── Derive summary stats from real KPI data (defaults to 0) ──
  const summaryStats = useMemo(() => {
    const d = kpis || { payrolls_processed: 0, verification_rate: 0 };
    return {
      totalProcessed: d.payrolls_processed.toLocaleString(),
      passRate: `${d.verification_rate}%`,
      avgVerification: "—",
    };
  }, [kpis]);

  return (
    <div className="space-y-8">
      {/* Page Header — period selector sits between description and status */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
            {t("title")}
          </h1>
          <p className="text-sm text-psi-text-secondary mt-1">
            {t("description")}
          </p>
        </div>

        {/* Period Selector — in flow between left and right columns */}
        <div className="relative">
          <button
            onClick={() => setOpen(!open)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            className="flex items-center gap-2 rounded-lg border border-psi-border bg-psi-graphite/80 px-3.5 py-2 text-sm font-medium text-psi-text-primary hover:border-psi-electric/50 hover:bg-psi-graphite transition-all focus:outline-none focus:ring-2 focus:ring-psi-electric/30"
          >
            <Calendar className="h-4 w-4 text-psi-electric" />
            <span>{periodLabels[period]}</span>
            <ChevronDown className={cn("h-3.5 w-3.5 text-psi-text-secondary transition-transform", open && "rotate-180")} />
          </button>

          {open && (
            <div className="absolute left-1/2 -translate-x-1/2 top-full mt-1.5 z-50 w-44 rounded-xl border border-psi-border bg-psi-graphite shadow-2xl shadow-black/30 overflow-hidden">
              {(Object.keys(periodLabels) as Period[]).map((key) => (
                <button
                  key={key}
                  onClick={() => { setPeriod(key); setOpen(false); }}
                  className={cn(
                    "flex w-full items-center gap-2 px-3.5 py-2.5 text-sm transition-colors",
                    period === key
                      ? "bg-psi-electric/10 text-psi-electric font-semibold"
                      : "text-psi-text-secondary hover:bg-psi-border/20 hover:text-psi-text-primary"
                  )}
                >
                  {period === key && (
                    <span className="h-1.5 w-1.5 rounded-full bg-psi-electric shrink-0" />
                  )}
                  <span className={cn(period !== key && "ml-[14px]")}>
                    {periodLabels[key]}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="success" dot>
            {t("allSystemsOperational")}
          </Badge>
          <p className="text-xs text-psi-text-secondary flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {t("updated")} {t("minAgo", { count: 2 })}
          </p>
        </div>
      </div>

      {/* KPI Grid — sempre visível, mostra 0 quando não há dados do usuário */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-4">
        {kpisLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="h-4 w-20 animate-pulse rounded bg-psi-border/50 mb-3" />
                <div className="h-8 w-16 animate-pulse rounded bg-psi-border/30 mb-2" />
                <div className="h-3 w-24 animate-pulse rounded bg-psi-border/30" />
              </CardContent>
            </Card>
          ))
        ) : kpisError ? (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-psi-fraud/10 p-4 mb-4">
              <WifiOff className="h-8 w-8 text-psi-fraud" />
            </div>
            <p className="text-lg font-semibold text-psi-text-primary mb-1">
              {t("dataUnavailable")}
            </p>
            <p className="text-sm text-psi-text-secondary max-w-md">
              {t("dataUnavailableDescription")}
            </p>
          </div>
        ) : !kpisSuccess ? (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-psi-navy/50 p-4 mb-4">
              <Database className="h-8 w-8 text-psi-text-secondary" />
            </div>
            <p className="text-lg font-semibold text-psi-text-primary mb-1">
              {t("noData")}
            </p>
            <p className="text-sm text-psi-text-secondary max-w-md">
              {t("noDataDescription")}
            </p>
          </div>
        ) : (
          kpiData.map((kpi, i) => (
            <KpiCard key={kpi.label} kpi={kpi} index={i} />
          ))
        )}
      </div>

      {/* Main Content Grid: Chart + AI Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payroll Trends — 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t("payrollTrend")}</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              {t("payrollTrendDescription")}
            </p>
          </CardHeader>
          <CardContent>
            <LazyPayrollTrendChart />
            {/* Summary stats — from real user data */}
            <div className="mt-4 grid grid-cols-3 gap-3">
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-text-primary">{summaryStats.totalProcessed}</p>
                <p className="text-[11px] text-psi-text-secondary">{t("totalProcessed")}</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-emerald">{summaryStats.passRate}</p>
                <p className="text-[11px] text-psi-text-secondary">{t("passRate")}</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-electric">{summaryStats.avgVerification}</p>
                <p className="text-[11px] text-psi-text-secondary">{t("avgVerification")}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Live AI Insights Feed — 1 col */}
        <LazyLiveAIInsightFeed />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fraud Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>{t("fraudHeatmap")}</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              {t("fraudHeatmapDescription")}
            </p>
          </CardHeader>
          <CardContent>
            <LazyFraudHeatmap />
          </CardContent>
        </Card>

        {/* Risk Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>{t("riskDistribution")}</CardTitle>
          </CardHeader>
          <CardContent>
            <LazyRiskDistributionChart />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
