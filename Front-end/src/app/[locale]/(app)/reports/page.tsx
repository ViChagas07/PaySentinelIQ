"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  FileText,
  AlertTriangle,
  DollarSign,
  Clock,
  CheckCircle,
  Brain,
  Download,
  FileSpreadsheet,
  Share2,
  PieChart as PieChartIcon,
  Activity,
  BarChart3,
  TrendingUp,
  Inbox,
} from "lucide-react";
import {
  useDashboardKpis,
  useDashboardTrends,
  useDashboardRiskDistribution,
  useFraudAlertStats,
  useAnalysisStats,
} from "@/hooks/useApi";
import { useAuthStore } from "@/stores";
import { useMemo } from "react";

function EmptySection({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
        <Icon className="h-8 w-8 text-psi-electric/40" />
      </div>
      <h3 className="text-base font-semibold text-psi-text-primary mb-1">{title}</h3>
      <p className="text-sm text-psi-text-secondary max-w-md">{description}</p>
    </div>
  );
}

function KpiSkeleton() {
  return (
    <div className="animate-pulse">
      <Card className="h-full">
        <CardContent className="p-4">
          <div className="h-3 w-24 rounded bg-psi-border/30 mb-4" />
          <div className="h-8 w-16 rounded bg-psi-border/20 mb-3" />
          <div className="h-3 w-20 rounded bg-psi-border/20 mb-3" />
          <div className="h-7 w-14 rounded bg-psi-border/10" />
        </CardContent>
      </Card>
    </div>
  );
}

function KpiCard({ label, value, subtext, icon: Icon, delay }: { label: string; value: React.ReactNode; subtext: string; icon: React.ElementType; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
    >
      <Card variant="interactive" glow className="group h-full">
        <CardContent className="p-4 flex flex-col h-full">
          <div className="flex items-start justify-between mb-3">
            <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider truncate pr-2">
              {label}
            </p>
            <div className="rounded-lg bg-psi-electric/10 p-1.5 shrink-0">
              <Icon className="h-3.5 w-3.5 text-psi-electric" />
            </div>
          </div>
          <div className="flex items-baseline gap-1 mb-1 mt-auto">
            <span className="text-2xl font-bold text-psi-text-primary tabular-nums tracking-wider">
              {value}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-psi-text-secondary/60">{subtext}</span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

const KPI_LABELS = ["documentsAnalyzed", "fraudCasesDetected", "averageRiskScore", "preventedLosses", "avgAnalysisTime", "successRate"] as const;
const KPI_ICONS = [FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle] as const;

export default function ReportsPage() {
  const t = useTranslations("reports");
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  // Only fetch when authenticated (prevents 401 errors on page load)
  const { data: kpis, isLoading: kpisLoading, isError: kpisError } = useDashboardKpis(isAuthenticated);
  const { data: trends, isLoading: trendsLoading } = useDashboardTrends(isAuthenticated);
  const { data: riskDistribution, isLoading: riskLoading } = useDashboardRiskDistribution(isAuthenticated);
  const { data: alertStats, isLoading: alertStatsLoading } = useFraudAlertStats(isAuthenticated);
  const { data: analysisStats } = useAnalysisStats(isAuthenticated);

  const hasData = useMemo(() => {
    const fromKpis = !!kpis && kpis.payrolls_processed > 0;
    const fromAnalysis = !!analysisStats && analysisStats.total_documents > 0;
    return fromKpis || fromAnalysis;
  }, [kpis, analysisStats]);

  return (
    <div className="space-y-8">
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        <svg className="absolute w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="reports-grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#1E6FFF" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#reports-grid)" />
        </svg>
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-psi-electric/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 -right-32 w-80 h-80 bg-psi-emerald/5 rounded-full blur-[120px]" />
      </div>

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
                  <Badge variant="outline" className="text-[10px]">
                    {t("pageBadge") || "Intelligence Report"}
                  </Badge>
                </div>
                <p className="text-sm text-psi-text-secondary leading-relaxed max-w-3xl">
                  {hasData
                    ? t("pageDescriptionWithData", { documents: kpis!.payrolls_processed.toLocaleString(), fraudCases: kpis!.fraud_alerts }) || `${kpis!.payrolls_processed.toLocaleString()} documents analyzed \u2022 ${kpis!.fraud_alerts} fraud cases detected`
                    : t("pageDescription") || "Awaiting data. Reports will appear here after documents are analyzed."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpisLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.06, ease: "easeOut" }}
              >
                <KpiSkeleton />
              </motion.div>
            ))
          : (
              // Show KPIs with zeros when error or no data yet
              ([
                { value: (analysisStats?.total_documents || 0).toLocaleString(), subtext: t("totalDocuments") || "total documents" },
                { value: (analysisStats?.fraudulent_count || 0).toLocaleString(), subtext: `0% ${t("rate") || "rate"}` },
                { value: `${analysisStats?.avg_confidence_score ? (analysisStats.avg_confidence_score * 100).toFixed(0) : 0}%`, subtext: t("confidenceScore") || "confidence score" },
                { value: `R$ ${(analysisStats?.losses_prevented || 0).toLocaleString()}`, subtext: t("lossesPrevented") || "losses prevented" },
                { value: (analysisStats?.high_risk_count || 0).toLocaleString(), subtext: t("highRiskDocuments") || "high risk documents" },
                { value: `${analysisStats?.pass_rate || 0}%`, subtext: t("successRate") || "success rate" },
              ] as { value: string; subtext: string }[]).map((item, i) => (
                <KpiCard
                  key={i}
                  label={t(KPI_LABELS[i] as any) || KPI_LABELS[i]}
                  value={item.value}
                  subtext={item.subtext}
                  icon={KPI_ICONS[i]}
                  delay={0.1 * i}
                />
              ))
            )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
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
              {riskLoading
                ? <div className="animate-pulse space-y-4 py-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="space-y-1">
                        <div className="h-3 w-16 rounded bg-psi-border/20" />
                        <div className="h-3 w-full rounded bg-psi-border/10" />
                      </div>
                    ))}
                  </div>
                : riskDistribution && riskDistribution.length > 0
                  ? <div className="space-y-3">
                      {(() => {
                        const maxCount = Math.max(...riskDistribution.map(r => r.count), 1);
                        return riskDistribution.map((item) => (
                          <div key={item.range} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-psi-text-secondary">{item.range}</span>
                              <span className="font-semibold text-psi-text-primary">{item.count}</span>
                            </div>
                            <div className="h-2.5 rounded-full bg-psi-border/20 overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all duration-700 ease-out"
                                style={{ width: `${(item.count / maxCount) * 100}%`, backgroundColor: item.color || "#1E6FFF" }}
                              />
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  : <EmptySection
                      icon={PieChartIcon}
                      title={t("riskDistribution") || "Risk Distribution"}
                      description={t("noDataAvailable") || "No data available yet"}
                    />}
            </CardContent>
          </Card>
        </motion.div>

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
              </div>
            </CardHeader>
            <CardContent>
              {trendsLoading
                ? <div className="animate-pulse space-y-3 py-4">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <div key={i} className="grid grid-cols-[80px_1fr_1fr] gap-2 items-center">
                        <div className="h-3 w-16 rounded bg-psi-border/20" />
                        <div className="h-3 rounded bg-psi-border/10" />
                        <div className="h-3 rounded bg-psi-border/10" />
                      </div>
                    ))}
                  </div>
                : trends && trends.length > 0
                  ? <div className="space-y-2">
                      <div className="grid grid-cols-[80px_1fr_1fr] gap-2 items-center mb-2">
                        <span className="text-[10px] font-semibold uppercase text-psi-text-secondary/60">{t("trendMonth") || "Month"}</span>
                        <span className="text-[10px] font-semibold uppercase text-emerald-500/80">{t("trendVolume") || "Volume"}</span>
                        <span className="text-[10px] font-semibold uppercase text-red-500/80">{t("trendFlagged") || "Flagged"}</span>
                      </div>
                      {(() => {
                        const maxVal = Math.max(...trends.map(d => Math.max(d.volume, d.flagged)), 1);
                        return trends.map((item) => (
                          <div key={item.month} className="grid grid-cols-[80px_1fr_1fr] gap-2 items-center">
                            <span className="text-xs text-psi-text-secondary font-medium">{item.month}</span>
                            <div className="relative h-4 rounded bg-emerald-500/10 overflow-hidden">
                              <div
                                className="h-full rounded bg-emerald-500 transition-all duration-500"
                                style={{ width: `${(item.volume / maxVal) * 100}%` }}
                              />
                            </div>
                            <div className="relative h-4 rounded bg-red-500/10 overflow-hidden">
                              <div
                                className="h-full rounded bg-red-500 transition-all duration-500"
                                style={{ width: `${(item.flagged / maxVal) * 100}%` }}
                              />
                            </div>
                          </div>
                        ));
                      })()}
                      <div className="flex items-center gap-4 pt-2 text-xs text-psi-text-secondary/60">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> {t("trendVolume") || "Volume"}</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> {t("trendFlagged") || "Flagged"}</span>
                      </div>
                    </div>
                  : <EmptySection
                      icon={TrendingUp}
                      title={t("fraudTrendAnalysis") || "Fraud Trend Analysis"}
                      description={t("noDataAvailable") || "No data available yet"}
                    />}
            </CardContent>
          </Card>
        </motion.div>
      </div>

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
          <CardContent>
            {alertStatsLoading
              ? <div className="animate-pulse space-y-3 py-4">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-psi-border/20" />
                      <div className="h-3 w-20 rounded bg-psi-border/20" />
                      <div className="h-3 w-8 rounded bg-psi-border/20 ml-auto" />
                      <div className="h-2 w-24 rounded bg-psi-border/10" />
                    </div>
                  ))}
                </div>
              : alertStats && alertStats.total > 0
                ? (() => {
                    const statusItems: { labelKey: string; key: "total" | "new" | "under_review" | "escalated" | "confirmed" | "resolved"; color: string }[] = [
                      { labelKey: "statusTotal", key: "total", color: "bg-psi-electric" },
                      { labelKey: "statusNew", key: "new", color: "bg-yellow-500" },
                      { labelKey: "statusUnderReview", key: "under_review", color: "bg-blue-500" },
                      { labelKey: "statusEscalated", key: "escalated", color: "bg-orange-500" },
                      { labelKey: "statusConfirmed", key: "confirmed", color: "bg-red-500" },
                      { labelKey: "statusResolved", key: "resolved", color: "bg-emerald-500" },
                    ];
                    return (
                      <div className="space-y-3">
                        {statusItems.map(({ labelKey, key, color }) => {
                          const value = alertStats[key];
                          const pct = (value / alertStats.total) * 100;
                          return (
                            <div key={key} className="flex items-center gap-3">
                              <div className={cn("w-2.5 h-2.5 rounded-full shrink-0", color)} />
                              <span className="flex-1 text-sm text-psi-text-secondary">{t(labelKey) || labelKey}</span>
                              <span className="text-sm font-semibold text-psi-text-primary tabular-nums">{value}</span>
                              <div className="w-28 h-2 rounded-full bg-psi-border/20 overflow-hidden">
                                <div className={cn("h-full rounded-full transition-all duration-500", color)} style={{ width: `${pct}%` }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()
                : <EmptySection
                    icon={Inbox}
                    title={t("fraudCauses") || "Top Fraud Causes"}
                    description={t("noDataAvailable") || "No data available yet"}
                  />}
          </CardContent>
        </Card>
      </motion.div>

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
              <div className="shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-psi-electric/20 to-psi-emerald/10 border border-psi-electric/20">
                <Brain className="h-6 w-6 text-psi-electric" />
              </div>
              <div className="flex-1 min-w-0 space-y-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-psi-text-primary">
                    {t("aiInsightsTitle") || "AI Intelligence Summary"}
                  </h3>
                  <Badge variant="outline" className="text-[10px]">{t("aiGenerated") || "AI Generated"}</Badge>
                </div>
                {kpisLoading
                  ? <div className="animate-pulse space-y-2">
                      <div className="h-4 w-full rounded bg-psi-border/20" />
                      <div className="h-4 w-3/4 rounded bg-psi-border/20" />
                      <div className="h-4 w-1/2 rounded bg-psi-border/20" />
                    </div>
                  : kpis && kpis.payrolls_processed > 0
                    ? <>
                        <p className="text-sm text-psi-text-secondary leading-relaxed">
                          {t.rich("aiInsightTextWithData", {
                            documents: kpis.payrolls_processed.toLocaleString(),
                            fraudCases: kpis.fraud_alerts,
                            fraudRate: Math.round((kpis.fraud_alerts / kpis.payrolls_processed) * 100),
                            preventedIncidents: kpis.compliance_incidents,
                            verificationRate: kpis.verification_rate,
                            aiConfidence: kpis.ai_confidence,
                            highRiskDocs: kpis.high_risk_docs,
                          }) || `Analysis of ${kpis.payrolls_processed.toLocaleString()} documents detected ${kpis.fraud_alerts} fraud cases (${Math.round((kpis.fraud_alerts / kpis.payrolls_processed) * 100)}% rate), prevented ${kpis.compliance_incidents} compliance incidents. Verification success rate is ${kpis.verification_rate}% with AI confidence at ${kpis.ai_confidence}%. ${kpis.high_risk_docs} documents flagged as high-risk.`}
                        </p>
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-medium text-psi-text-secondary">
                              {t("confidence") || "Confidence"}
                            </span>
                            <div className="w-32 h-2 rounded-full bg-psi-border/20 overflow-hidden">
                              <div className="h-full rounded-full bg-psi-electric transition-all duration-500" style={{ width: `${kpis.ai_confidence}%` }} />
                            </div>
                            <span className="text-xs font-bold text-psi-text-primary tabular-nums">{kpis.ai_confidence}%</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline" className="text-[11px] text-psi-electric/80">
                              {kpis.fraud_alerts} {t("alerts") || "Alerts"}
                            </Badge>
                            <Badge variant="outline" className="text-[11px] text-emerald-500/80">
                              {kpis.verification_rate}% {t("rate") || "Rate"}
                            </Badge>
                            {alertStats && (
                              <Badge variant="outline" className="text-[11px] text-yellow-500/80">
                                {alertStats.under_review} {t("underReview") || "Under Review"}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </>
                    : <p className="text-sm text-psi-text-secondary leading-relaxed">
                        {t("aiInsightText") || "AI insights will be generated automatically as documents are analyzed. No data available yet."}
                      </p>}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.45, ease: "easeOut" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-sm font-semibold text-psi-text-primary mr-2">
            {t("exportTools") || "Export & Share"}
          </h3>
          <Button variant="primary" size="sm" disabled={!hasData}>
            <Download className="h-4 w-4" />
            {t("exportPDF") || "Export PDF"}
          </Button>
          <Button variant="outline" size="sm" disabled={!hasData}>
            <FileSpreadsheet className="h-4 w-4" />
            {t("exportCSV") || "Export CSV"}
          </Button>
          <Button variant="secondary" size="sm" disabled={!hasData}>
            <Share2 className="h-4 w-4" />
            {t("shareReport") || "Share Report"}
          </Button>
          <Button variant="ghost" size="sm" disabled={!hasData} className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-psi-electric/5 to-psi-emerald/5 opacity-0" />
            <FileText className="h-4 w-4 relative z-10" />
            <span className="relative z-10">{t("generateReport") || "Generate Executive Report"}</span>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
