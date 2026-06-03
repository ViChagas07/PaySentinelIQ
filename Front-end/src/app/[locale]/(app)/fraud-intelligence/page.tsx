// ============================================================
// PaySentinelIQ — Fraud Intelligence Center
// Shows ONLY real fraud data from user activity.
// No hardcoded/mock summary stats or dummy numbers.
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { FraudRiskTable } from "@/components/fraud/FraudRiskTable";
import { InvestigationTimeline } from "@/components/fraud/InvestigationTimeline";
import { Button } from "@/components/ui/Button";
import {
  AlertTriangle,
  TrendingUp,
  Clock,
  Download,
  BarChart3,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useFraudAlertStats } from "@/hooks/useApi";

export default function FraudIntelligencePage() {
  const t = useTranslations("fraud");
  const { data: stats } = useFraudAlertStats();

  const summaryCards = useMemo(() => {
    const s = stats || { new: 0, under_review: 0, escalated: 0, confirmed: 0, resolved: 0, total: 0 };
    return [
      {
        label: t("activeAlerts"),
        value: String(s.new + s.under_review),
        sub: t("newInReview", { new: s.new, review: s.under_review }),
        color: "text-psi-fraud",
        bg: "bg-psi-fraud/10",
        border: "border-psi-fraud/30",
        icon: <AlertTriangle className="h-4 w-4 text-psi-fraud animate-pulse-alert" />,
      },
      {
        label: t("statusEscalated"),
        value: String(s.escalated),
        sub: t("requiresImmediateAttention"),
        color: "text-psi-warning",
        bg: "bg-psi-warning/10",
        border: "border-psi-warning/30",
        icon: <TrendingUp className="h-4 w-4 text-psi-warning" />,
      },
      {
        label: t("confirmedFraud"),
        value: String(s.confirmed),
        sub: t("resolvedCases", { count: s.resolved }),
        color: "text-psi-fraud",
        bg: "bg-psi-fraud/10",
        border: "border-psi-fraud/30",
        icon: <ShieldCheck className="h-4 w-4 text-psi-fraud" />,
      },
      {
        label: t("totalAlerts"),
        value: String(s.total),
        sub: t("allTime"),
        color: "text-psi-emerald",
        bg: "bg-psi-emerald/10",
        border: "border-psi-emerald/30",
        icon: <BarChart3 className="h-4 w-4 text-psi-emerald" />,
      },
    ];
  }, [stats, t]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
            {t("pageTitle")}
          </h1>
          <p className="text-sm text-psi-text-secondary mt-1">
            {t("pageDescription")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {stats && stats.new > 0 && (
            <Badge variant="destructive" dot>
              {t("newAlerts", { count: stats.new })}
            </Badge>
          )}
          <Button variant="outline" size="sm">
            <Download className="h-3.5 w-3.5 mr-1" />
            {t("exportReport")}
          </Button>
        </div>
      </div>

      {/* Summary Cards — sempre visíveis, mostra 0 quando não há dados */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider">
                    {stat.label}
                  </span>
                  {stat.icon}
                </div>
                <p className={cn("text-2xl font-bold tabular-nums", stat.color)}>{stat.value}</p>
                <p className="text-[11px] text-psi-text-secondary mt-0.5">{stat.sub}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Fraud Risk Table — 2 cols */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t("riskTableTitle")}</CardTitle>
                <p className="text-xs text-psi-text-secondary mt-1">
                  {t("riskTableDescription")}
                </p>
              </div>
              <Button variant="outline" size="sm">
                <BarChart3 className="h-3.5 w-3.5 mr-1" />
                {t("viewAnalytics")}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <FraudRiskTable />
          </CardContent>
        </Card>

        {/* Investigation Timeline — 1 col */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>{t("investigationTimeline")}</CardTitle>
            <p className="text-xs text-psi-text-secondary mt-1">
              {t("noActivityDesc")}
            </p>
          </CardHeader>
          <CardContent>
            <InvestigationTimeline events={[]} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
