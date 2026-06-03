// ============================================================
// PaySentinelIQ — Live AI Insights Feed
// Shows ONLY real fraud alerts from user activity.
// No hardcoded/mock data.
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { AlertTriangle, Brain, ShieldCheck, Clock } from "lucide-react";
import { useAIInsightFeed } from "@/hooks/useApi";

// ── Risk level config ── /

type RiskLevel = "low" | "medium" | "high" | "critical";

const riskStyles: Record<RiskLevel, { dot: string; border: string; badge: "success" | "warning" | "destructive" }> = {
  low:    { dot: "bg-psi-emerald",          border: "border-l-psi-emerald/50", badge: "success" },
  medium: { dot: "bg-psi-warning",          border: "border-l-psi-warning/50", badge: "warning" },
  high:   { dot: "bg-psi-fraud",            border: "border-l-psi-fraud/50",   badge: "destructive" },
  critical: { dot: "bg-psi-fraud animate-pulse-alert", border: "border-l-psi-fraud/70", badge: "destructive" },
};

const riskIcons: Record<RiskLevel, React.ReactNode> = {
  low:      <ShieldCheck className="h-4 w-4" />,
  medium:   <Clock className="h-4 w-4" />,
  high:     <AlertTriangle className="h-4 w-4" />,
  critical: <AlertTriangle className="h-4 w-4" />,
};

const riskLabelKeys: Record<RiskLevel, string> = {
  low: "riskLow",
  medium: "riskMedium",
  high: "riskHigh",
  critical: "riskCritical",
};

function getRiskLevel(score: number): RiskLevel {
  if (score >= 85) return "critical";
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

function getCategoryLabel(category: string): string {
  const map: Record<string, string> = {
    salary_discrepancy: "catSalaryAnomaly",
    ghost_employee: "catGhostEmployee",
    tax_evasion: "catTaxAnomaly",
    document_forgery: "catDocumentForgery",
    timesheet_fraud: "catTimesheetFraud",
    compliance_violation: "catCompliance",
    duplicate_payment: "catDuplicatePayment",
    identity_mismatch: "catIdentityMismatch",
    unauthorized_deduction: "catUnauthorizedDeduction",
  };
  return map[category] || "catOther";
}

function timeAgo(dateStr: string, t: (key: string, params?: Record<string, unknown>) => string): string {
  if (!dateStr) return "";
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return t("justNow");
  if (diffMin < 60) return t("minAgo", { count: diffMin });
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return t("hoursAgo", { count: diffHours });
  const diffDays = Math.floor(diffHours / 24);
  return t("daysAgo", { count: diffDays });
}

// ── Individual Insight Row ── //

function InsightRow({
  title, riskLevel, category, timeAgoStr, index, t,
}: {
  title: string; riskLevel: RiskLevel; category: string; timeAgoStr: string; index: number;
  t: (key: string, params?: Record<string, unknown>) => string;
}) {
  const style = riskStyles[riskLevel];

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className={cn(
        "flex items-start gap-3 py-3 border-b border-psi-border last:border-0 pl-3 border-l-2",
        style.border
      )}
    >
      <span className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", style.dot)} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-0.5">
          <Badge variant={style.badge} className="text-[10px] py-0 px-1.5">
            {t(riskLabelKeys[riskLevel])}
          </Badge>
          <Badge variant="outline" className="text-[10px] py-0 px-1.5">
            {t(getCategoryLabel(category))}
          </Badge>
        </div>
        <p className="text-sm text-psi-text-primary leading-snug">{title}</p>
        <p className="text-xs text-psi-text-secondary mt-1 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {timeAgoStr}
        </p>
      </div>
    </motion.div>
  );
}

// ── Feed Component using real API data ── //

export function LiveAIInsightFeed() {
  const t = useTranslations("dashboard");
  const { data: feedData, isLoading } = useAIInsightFeed();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{t("liveInsights")}</CardTitle>
          <Badge variant="primary" dot>
            {t("live")}
          </Badge>
        </div>
        <p className="text-xs text-psi-text-secondary">
          {t("liveInsightsDescription")}
        </p>
      </CardHeader>
      <CardContent>
        <div className="max-h-[420px] overflow-y-auto -mr-2 pr-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
            </div>
          ) : !feedData || feedData.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-xs text-psi-text-secondary/50">{t("emptyInsights")}</p>
            </div>
          ) : (
            feedData.map((insight: any, i: number) => (
              <InsightRow
                key={insight.id || i}
                title={insight.title}
                riskLevel={getRiskLevel(insight.risk_score)}
                category={insight.category}
                timeAgoStr={timeAgo(insight.created_at, t)}
                index={i}
                t={t}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
