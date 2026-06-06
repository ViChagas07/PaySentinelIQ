// ============================================================
// PaySentinelIQ — Executive Dashboard
// Animated KPI cards, real Recharts visualizations, live AI feed
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { PayrollTrendChart } from "@/components/charts/PayrollTrendChart";
import { FraudHeatmap } from "@/components/charts/FraudHeatmap";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";
import {
  DollarSign,
  ShieldCheck,
  AlertTriangle,
  Brain,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  type LucideIcon,
} from "lucide-react";

// ── Types ── //

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
}

// ── Mock KPI Data ── //

const kpiData: KpiData[] = [
  {
    label: "Payrolls Processed",
    value: 12487,
    change: 12.5,
    changeType: "increase",
    changeContext: "good",
    icon: DollarSign,
    color: "text-psi-electric",
    bgColor: "bg-psi-electric/10",
  },
  {
    label: "Verification Rate",
    value: 98.4,
    suffix: "%",
    change: 0.8,
    changeType: "increase",
    changeContext: "good",
    icon: ShieldCheck,
    color: "text-psi-emerald",
    bgColor: "bg-psi-emerald/10",
  },
  {
    label: "Fraud Alerts",
    value: 23,
    change: 15.0,
    changeType: "increase",
    changeContext: "bad",
    icon: AlertTriangle,
    color: "text-psi-fraud",
    bgColor: "bg-psi-fraud/10",
  },
  {
    label: "AI Confidence",
    value: 96.7,
    suffix: "%",
    change: 2.1,
    changeType: "increase",
    changeContext: "good",
    icon: Brain,
    color: "text-psi-electric",
    bgColor: "bg-psi-electric/10",
  },
  {
    label: "High-Risk Docs",
    value: 7,
    change: 3,
    changeType: "decrease",
    changeContext: "good",
    icon: AlertTriangle,
    color: "text-psi-warning",
    bgColor: "bg-psi-warning/10",
  },
  {
    label: "Compliance Incidents",
    value: 2,
    change: 1,
    changeType: "decrease",
    changeContext: "good",
    icon: ShieldCheck,
    color: "text-psi-text-secondary",
    bgColor: "bg-psi-border/50",
  },
];

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
                <span className="text-xs text-psi-text-secondary truncate">vs last month</span>
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

// ── cn helper ── //
import { cn } from "@/lib/utils";

// ── Main Dashboard ── //

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
            Executive Dashboard
          </h1>
          <p className="text-sm text-psi-text-secondary mt-1">
            Real-time payroll verification and fraud intelligence overview
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="success" dot>
            All Systems Operational
          </Badge>
          <p className="text-xs text-psi-text-secondary flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Updated 2 min ago
          </p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpiData.map((kpi, i) => (
          <KpiCard key={kpi.label} kpi={kpi} index={i} />
        ))}
      </div>

      {/* Main Content Grid: Chart + AI Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payroll Trends — 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Payroll Verification Trends</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              Monthly payroll volume, flagged anomalies, and verification pass rate
            </p>
          </CardHeader>
          <CardContent>
            <PayrollTrendChart />
            {/* Summary stats */}
            <div className="mt-4 grid grid-cols-3 gap-3">
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-text-primary">$42.8M</p>
                <p className="text-[11px] text-psi-text-secondary">Total Processed</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-emerald">98.4%</p>
                <p className="text-[11px] text-psi-text-secondary">Pass Rate</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-psi-navy/50 border border-psi-border">
                <p className="text-sm font-bold text-psi-electric">2.3s</p>
                <p className="text-[11px] text-psi-text-secondary">Avg. Verification</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Live AI Insights Feed — 1 col */}
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fraud Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>Fraud Risk Heatmap</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              Risk concentration by department — bubble size indicates flagged count
            </p>
          </CardHeader>
          <CardContent>
            <FraudHeatmap />
          </CardContent>
        </Card>

        {/* Risk Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Score Distribution</CardTitle>
            <p className="text-xs text-psi-text-secondary">
              Payroll risk scoring histogram across all 2,863 entities
            </p>
          </CardHeader>
          <CardContent>
            <RiskDistributionChart />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
