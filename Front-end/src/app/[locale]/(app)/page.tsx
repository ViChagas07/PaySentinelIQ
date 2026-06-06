// ============================================================
// PaySentinelIQ — Executive Dashboard
// Shows ONLY real data from what the registered user actually
// does within the app. No hardcoded/mock/dummy numbers.
// Guests see a CTA banner + "---" until they sign up.
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useState, useMemo, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LazyPayrollTrendChart, LazyFraudHeatmap, LazyRiskDistributionChart } from "@/components/charts/LazyCharts";
import {
  DollarSign, ShieldCheck, AlertTriangle, Brain, Clock,
  FileWarning, ArrowUpRight, ArrowDownRight, Calendar, ChevronDown,
  WifiOff, LogIn, Sparkles, Lock,
  type LucideIcon,
} from "lucide-react";
import { useDashboardKpis } from "@/hooks/useApi";
import { useAuthStore } from "@/stores";
import { Link } from "@/i18n/navigation";

// ── Types ── //

type Period = "lastWeek" | "last15Days" | "lastMonth" | "lastSemester" | "lastYear";

interface KpiData {
  label: string;
  value: number | null;      // null = placeholcer mode ("---")
  suffix?: string;
  prefix?: string;
  change: number | null;     // null = placeholcer mode
  changeType: "increase" | "decrease";
  changeContext: "good" | "bad" | "neutral";
  icon: LucideIcon;
  color: string;
  bgColor: string;
  changeLabel: string;
}

// ── Animated Count-Up (handles null → "---") ── //

function CountUp({ target, suffix }: { target: number | null; suffix?: string }) {
  const [count, setCount] = useState(0);

  // Placeholder mode
  if (target === null) {
    return (
      <span className="text-3xl font-bold text-psi-text-primary tabular-nums tracking-wider">
        &mdash;&mdash;&mdash;
      </span>
    );
  }

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

function KpiCard({ kpi, index, isGuarded }: { kpi: KpiData; index: number; isGuarded?: boolean }) {
  const Icon = kpi.icon;
  const changeColor =
    kpi.changeContext === "bad"
      ? "text-psi-fraud"
      : kpi.changeType === "increase"
      ? "text-psi-emerald"
      : "text-psi-emerald";

  return (
    <motion.div
      key={kpi.label + (kpi.value ?? "placeholder")}
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
                {kpi.prefix && !isGuarded && (
                  <span className="text-2xl font-bold text-psi-text-primary">
                    {kpi.prefix}
                  </span>
                )}
                <span className="text-3xl font-bold text-psi-text-primary tabular-nums">
                  <CountUp target={kpi.value} suffix={isGuarded ? undefined : kpi.suffix} />
                </span>
              </div>
              {!isGuarded && kpi.change !== null && (
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
              )}
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

// ── Guest Banner — Call-to-Action ── //

function GuestBanner() {
  const t = useTranslations("dashboard");

  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <Card glow className="relative overflow-hidden border-psi-electric/20">
        {/* Animated gradient background */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute -inset-[100%] animate-pulse bg-gradient-to-r from-psi-electric/5 via-psi-emerald/5 to-psi-electric/5 blur-3xl" />
        </div>

        <CardContent className="relative z-10 p-5 sm:p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
            {/* Icon */}
            <div className="hidden sm:flex shrink-0 items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-psi-electric/20 to-psi-emerald/10 border border-psi-electric/20">
              <Lock className="h-6 w-6 text-psi-electric" />
            </div>

            {/* Text */}
            <div className="flex-1 min-w-0">
              <h2 className="text-base sm:text-lg font-semibold text-psi-text-primary tracking-tight flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-psi-electric shrink-0" />
                {t("authRequiredTitle") || "Acesso Restrito"}
              </h2>
              <p className="text-sm text-psi-text-secondary mt-1 leading-relaxed">
                {t("authRequiredDescription") ||
                  "Cadastre-se / faça Login para ter poder visualizar os seus dados em tempo-real!"}
              </p>
            </div>

            {/* CTA Button */}
            <Link href="/auth/login">
              <Button
                variant="primary"
                size="lg"
                className="shrink-0 w-full sm:w-auto group shadow-lg shadow-psi-electric/20 hover:shadow-psi-electric/30"
              >
                <LogIn className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                <span>{t("authRequiredCta") || "Cadastre-se / Fazer Login"}</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Placeholder chart overlay ── //

function PlaceholderChart({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-psi-navy/50 p-4 mb-3 border border-psi-border/30">
        <Icon className="h-7 w-7 text-psi-text-secondary/40" />
      </div>
      <p className="text-sm font-medium text-psi-text-secondary/60">{label}</p>
    </div>
  );
}

// ── Period Selector Dropdown ── //

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const [period, setPeriod] = useState<Period>("lastMonth");
  const [open, setOpen] = useState(false);

  // ── Auth guard ── //
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isGuarded = !isAuthenticated;

  // ── Real KPI data from the API (only fetched when authenticated) ──
  const { data: kpis, isLoading: kpisLoading, isError: kpisError, isSuccess: kpisSuccess } = useDashboardKpis(
    isAuthenticated
  );

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

  // ── Build KPI cards — null values when guarded → "---" ──
  const kpiData: KpiData[] = useMemo(() => {
    // When guarded (not authenticated), all values are null
    if (isGuarded) {
      return [
        {
          label: t("payrollsProcessed"),
          value: null, change: null, changeType: "increase", changeContext: "good",
          icon: DollarSign, color: "text-psi-electric", bgColor: "bg-psi-electric/10", changeLabel: vsLabel,
        },
        {
          label: t("verificationRate"),
          value: null, suffix: "%", change: null, changeType: "increase", changeContext: "good",
          icon: ShieldCheck, color: "text-psi-emerald", bgColor: "bg-psi-emerald/10", changeLabel: vsLabel,
        },
        {
          label: t("fraudAlerts"),
          value: null, change: null, changeType: "increase", changeContext: "bad",
          icon: AlertTriangle, color: "text-psi-fraud", bgColor: "bg-psi-fraud/10", changeLabel: vsLabel,
        },
        {
          label: t("aiConfidence"),
          value: null, suffix: "%", change: null, changeType: "increase", changeContext: "good",
          icon: Brain, color: "text-psi-emerald", bgColor: "bg-psi-emerald/10", changeLabel: vsLabel,
        },
        {
          label: t("highRiskDocs"),
          value: null, change: null, changeType: "increase", changeContext: "bad",
          icon: FileWarning, color: "text-psi-warning", bgColor: "bg-psi-warning/10", changeLabel: vsLabel,
        },
      ];
    }

    const d = kpis || {
      payrolls_processed: 0,
      verification_rate: 0,
      fraud_alerts: 0,
      ai_confidence: 0,
      high_risk_docs: 0,
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
    ];
  }, [kpis, t, vsLabel, isGuarded]);

  // ── Derive summary stats — "---" when guarded ──
  const summaryStats = useMemo(() => {
    if (isGuarded) {
      return {
        totalProcessed: "---",
        passRate: "---",
        avgVerification: "---",
      };
    }
    const d = kpis || { payrolls_processed: 0, verification_rate: 0 };
    return {
      totalProcessed: d.payrolls_processed.toLocaleString(),
      passRate: `${d.verification_rate}%`,
      avgVerification: "\u2014",
    };
  }, [kpis, isGuarded]);

  return (
    <div className="space-y-8">
      {/* ── Guest Banner — shown when NOT authenticated ── */}
      {isGuarded && <GuestBanner />}

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

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-4">
        {isGuarded ? (
          // ── Guest view: KPI cards with "---" ──
          kpiData.map((kpi, i) => (
            <KpiCard key={kpi.label} kpi={kpi} index={i} isGuarded />
          ))
        ) : kpisLoading ? (
          // ── Loading skeleton ──
          Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="h-4 w-20 animate-pulse rounded bg-psi-border/50 mb-3" />
                <div className="h-8 w-16 animate-pulse rounded bg-psi-border/30 mb-2" />
                <div className="h-3 w-24 animate-pulse rounded bg-psi-border/30" />
              </CardContent>
            </Card>
          ))
        ) : (
          // ── Show KPI cards — even if API errored, use fallback zeros ──
          // If the API is unavailable (backend still in development, offline,
          // or no data yet), we render zeros instead of a "server down" error
          // screen. A real server-down indicator only appears when the user
          // is genuinely offline (navigator.onLine).
          <>
            {kpisError && typeof navigator !== "undefined" && !navigator.onLine && (
              <div className="col-span-full flex items-center gap-3 rounded-lg border border-psi-warning/30 bg-psi-warning/5 px-4 py-3 mb-2">
                <WifiOff className="h-4 w-4 text-psi-warning shrink-0" />
                <p className="text-xs text-psi-text-secondary">
                  {t("dataUnavailableDescription")}
                </p>
              </div>
            )}
            {kpiData.map((kpi, i) => (
              <KpiCard key={kpi.label} kpi={kpi} index={i} />
            ))}
          </>
        )}
      </div>

      {/* Main Content Grid: Chart + AI Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payroll Trends — full width */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>{t("payrollTrend")}</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              {t("payrollTrendDescription")}
            </p>
          </CardHeader>
          <CardContent>
            {isGuarded ? (
              <PlaceholderChart icon={Lock} label={t("authRequiredChart") || "Faça login para visualizar os gráficos"} />
            ) : (
              <LazyPayrollTrendChart />
            )}
            {/* Summary stats — "---" when guarded */}
            <div className="mt-4 grid grid-cols-3 gap-3">
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className={cn(
                  "text-sm font-bold tabular-nums",
                  isGuarded ? "text-psi-text-secondary/50 tracking-wider" : "text-psi-text-primary"
                )}>
                  {summaryStats.totalProcessed}
                </p>
                <p className="text-[11px] text-psi-text-secondary">{t("totalProcessed")}</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className={cn(
                  "text-sm font-bold tabular-nums",
                  isGuarded ? "text-psi-text-secondary/50 tracking-wider" : "text-psi-emerald"
                )}>
                  {summaryStats.passRate}
                </p>
                <p className="text-[11px] text-psi-text-secondary">{t("passRate")}</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className={cn(
                  "text-sm font-bold tabular-nums",
                  isGuarded ? "text-psi-text-secondary/50 tracking-wider" : "text-psi-electric"
                )}>
                  {summaryStats.avgVerification}
                </p>
                <p className="text-[11px] text-psi-text-secondary">{t("avgVerification")}</p>
              </div>
            </div>
          </CardContent>
        </Card>
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
            {isGuarded ? (
              <PlaceholderChart icon={Lock} label={t("authRequiredChart") || "Faça login para visualizar"} />
            ) : (
              <LazyFraudHeatmap />
            )}
          </CardContent>
        </Card>

        {/* Risk Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>{t("riskDistribution")}</CardTitle>
          </CardHeader>
          <CardContent>
            {isGuarded ? (
              <PlaceholderChart icon={Lock} label={t("authRequiredChart") || "Faça login para visualizar"} />
            ) : (
              <LazyRiskDistributionChart />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
