// ============================================================
// PaySentinelIQ — Executive Intelligence Center (Reports)
// Enterprise-grade fraud intelligence reporting dashboard
// Data-driven — shows empty states until real data is available
// ============================================================

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

// ============================================================
// Empty State Component
// ============================================================

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

// ============================================================
// Skeleton shimmer for KPI cards
// ============================================================

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
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#1E6FFF" strokeWidth="0.5" />
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
                  <Badge variant="outline" className="text-[10px]">
                    {t("pageBadge") || "Intelligence Report"}
                  </Badge>
                </div>
                <p className="text-sm text-psi-text-secondary leading-relaxed max-w-3xl">
                  {t("pageDescription") || "Awaiting data. Reports will appear here after documents are analyzed."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ── 2. KPI Cards — empty/loading state ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.06, ease: "easeOut" }}
          >
            <Card variant="interactive" glow className="group h-full">
              <CardContent className="p-4 flex flex-col h-full">
                <div className="flex items-start justify-between mb-3">
                  <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider truncate pr-2">
                    {[t("documentsAnalyzed"), t("fraudCasesDetected"), t("averageRiskScore"), t("preventedLosses"), t("avgAnalysisTime"), t("successRate")][i] || "—"}
                  </p>
                  <div className="rounded-lg bg-psi-electric/10 p-1.5 shrink-0">
                    {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] && (
                      <span className="text-psi-electric">
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === FileText && <FileText className="h-3.5 w-3.5" />}
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === AlertTriangle && <AlertTriangle className="h-3.5 w-3.5" />}
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === BarChart3 && <BarChart3 className="h-3.5 w-3.5" />}
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === DollarSign && <DollarSign className="h-3.5 w-3.5" />}
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === Clock && <Clock className="h-3.5 w-3.5" />}
                        {[FileText, AlertTriangle, BarChart3, DollarSign, Clock, CheckCircle][i] === CheckCircle && <CheckCircle className="h-3.5 w-3.5" />}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-baseline gap-1 mb-1 mt-auto">
                  <span className="text-2xl font-bold text-psi-text-secondary/40 tabular-nums tracking-wider">
                    ———
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-psi-text-secondary/40 italic">
                    {t("vsLastPeriod") || "awaiting data"}
                  </span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* ── 3 & 4: Charts — empty state ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Risk Distribution */}
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
              <EmptySection
                icon={PieChartIcon}
                title={t("riskDistribution") || "Risk Distribution"}
                description={t("noDataAvailable") || "No data available yet"}
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* Fraud Trend */}
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
              <EmptySection
                icon={TrendingUp}
                title={t("fraudTrendAnalysis") || "Fraud Trend Analysis"}
                description={t("noDataAvailable") || "No data available yet"}
              />
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* ── 5. Top Fraud Causes Table — empty state ── */}
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
            <EmptySection
              icon={Inbox}
              title={t("fraudCauses") || "Top Fraud Causes"}
              description={t("noDataAvailable") || "No data available yet"}
            />
          </CardContent>
        </Card>
      </motion.div>

      {/* ── 6. AI Insights Card — empty state ── */}
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
                <p className="text-sm text-psi-text-secondary leading-relaxed">
                  {t("aiInsightText") || "AI insights will be generated automatically as documents are analyzed. No data available yet."}
                </p>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-psi-text-secondary">
                      {t("confidence") || "Confidence"}
                    </span>
                    <div className="w-32 h-2 rounded-full bg-psi-border/20 overflow-hidden">
                      <div className="h-full rounded-full bg-psi-border/10" style={{ width: "0%" }} />
                    </div>
                    <span className="text-xs font-bold text-psi-text-secondary/40 tabular-nums">—%</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-[11px] text-psi-text-secondary/50">
                      {t("recommendations") || "Recommendations"} — {t("notAvailable") || "N/A"}
                    </Badge>
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
          <Button variant="primary" size="sm" disabled>
            <Download className="h-4 w-4" />
            {t("exportPDF") || "Export PDF"}
          </Button>
          <Button variant="outline" size="sm" disabled>
            <FileSpreadsheet className="h-4 w-4" />
            {t("exportCSV") || "Export CSV"}
          </Button>
          <Button variant="secondary" size="sm" disabled>
            <Share2 className="h-4 w-4" />
            {t("shareReport") || "Share Report"}
          </Button>
          <Button variant="ghost" size="sm" disabled className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-psi-electric/5 to-psi-emerald/5 opacity-0" />
            <FileText className="h-4 w-4 relative z-10" />
            <span className="relative z-10">{t("generateReport") || "Generate Executive Report"}</span>
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
