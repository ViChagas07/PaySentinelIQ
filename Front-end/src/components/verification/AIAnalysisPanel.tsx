// ============================================================
// PaySentinelIQ — AI Analysis Panel
// Right-side panel driven entirely by real verification data.
// No mock/simulated content — each tab shows genuine data or
// a transparent empty state.
// ============================================================

"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { RiskGauge } from "./RiskGauge";
import {
  ShieldCheck,
  AlertTriangle,
  Brain,
  ScanEye,
  FileText,
  Inbox,
} from "lucide-react";

// ── Public types (data comes from API, never hardcoded) ── //

export interface ExtractedField {
  field: string;
  value: string;
  confidence: number;
  status: "verified" | "suspicious" | "mismatch";
}

export interface FraudIndicatorItem {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
}

export interface MetadataItem {
  label: string;
  value: string;
  anomaly?: boolean;
}

export interface AIFinding {
  severity: "critical" | "high" | "medium" | "low";
  description: string;
}

export interface AISummary {
  summary: string;
  findings: AIFinding[];
  recommendedActions: string[];
  modelName: string;
  completedAt: string; // ISO date string
}

// ── Main Panel — accepts real data as props, never falls back to fake data ── //

export function AIAnalysisPanel({
  extractedFields = [],
  fraudIndicators = [],
  riskScore = 0,
  metadata = [],
  aiSummary,
}: {
  extractedFields?: ExtractedField[];
  fraudIndicators?: FraudIndicatorItem[];
  riskScore?: number;
  metadata?: MetadataItem[];
  aiSummary?: AISummary | null;
}) {
  const t = useTranslations("verification");

  const tabs = [
    { id: "fields", label: t("tabExtractedFields"), icon: ShieldCheck },
    { id: "fraud", label: t("tabFraudIndicators"), icon: AlertTriangle },
    { id: "metadata", label: t("tabMetadata"), icon: ScanEye },
    { id: "explanation", label: t("tabAIExplanation"), icon: Brain },
  ];

  const [activeTab, setActiveTab] = useState("fields");

  const hasAnyData =
    extractedFields.length > 0 ||
    fraudIndicators.length > 0 ||
    metadata.length > 0 ||
    aiSummary != null ||
    riskScore > 0;

  return (
    <div className="flex flex-col h-full">
      {/* ── Header ── */}
      <div className="px-6 py-4 border-b border-psi-border">
        <div className="flex items-center gap-2 mb-1">
          <Brain className="h-4 w-4 text-psi-electric" />
          <h2 className="text-base font-semibold text-psi-text-primary">{t("aiAnalysis")}</h2>
        </div>
        <p className="text-xs text-psi-text-secondary">
          {hasAnyData ? t("aiAnalysisDescription") : t("aiAnalysisIdle")}
        </p>
      </div>

      {/* ── Risk Score (only meaningful when > 0) ── */}
      <div className="flex justify-center py-5 border-b border-psi-border bg-psi-graphite/30">
        <RiskGauge score={riskScore} size={130} strokeWidth={8} label={t("riskScore")} />
      </div>

      {/* ── Tabs ── */}
      <div className="flex border-b border-psi-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-all border-b-2 -mb-px",
                isActive
                  ? "border-psi-electric text-psi-electric"
                  : "border-transparent text-psi-text-secondary hover:text-psi-text-primary"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.id === "fraud" && fraudIndicators.length > 0 && (
                <span className="ml-1 rounded-full bg-psi-fraud h-1.5 w-1.5 animate-pulse-alert" />
              )}
            </button>
          );
        })}
      </div>

      {/* ── Tab Content ── */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="p-4"
          >
            {/* ── Extracted Fields ── */}
            {activeTab === "fields" && (
              extractedFields.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs text-psi-text-secondary mb-3">
                    {t("fieldsDescription")}
                  </p>
                  {extractedFields.map((field) => (
                    <FieldRow key={field.field} field={field} />
                  ))}
                </div>
              ) : (
                <EmptyTab
                  icon={ShieldCheck}
                  message={t("noExtractedFields")}
                />
              )
            )}

            {/* ── Fraud Indicators ── */}
            {activeTab === "fraud" && (
              fraudIndicators.length > 0 ? (
                <div className="space-y-3">
                  <p className="text-xs text-psi-text-secondary mb-3">
                    {t("indicatorsDetected", { count: fraudIndicators.length })}
                  </p>
                  {fraudIndicators.map((indicator) => (
                    <FraudIndicatorCard key={indicator.id} indicator={indicator} />
                  ))}
                </div>
              ) : (
                <EmptyTab
                  icon={AlertTriangle}
                  message={t("noFraudIndicators")}
                />
              )
            )}

            {/* ── Metadata Analysis ── */}
            {activeTab === "metadata" && (
              metadata.length > 0 ? (
                <MetadataPanel items={metadata} />
              ) : (
                <EmptyTab
                  icon={ScanEye}
                  message={t("noMetadata")}
                />
              )
            )}

            {/* ── AI Explanation ── */}
            {activeTab === "explanation" && (
              aiSummary ? (
                <AIExplanationPanel summary={aiSummary} />
              ) : (
                <EmptyTab
                  icon={Brain}
                  message={t("noAIExplanation")}
                />
              )
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── Empty Tab ── //

function EmptyTab({ icon: Icon, message }: { icon: React.ElementType; message: string }) {
  const t = useTranslations("verification");

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-16 gap-3"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-psi-graphite/60 border border-psi-border">
        <Icon className="h-5 w-5 text-psi-text-secondary/40" />
      </div>
      <p className="text-sm text-psi-text-secondary/60 text-center max-w-[220px]">
        {message}
      </p>
    </motion.div>
  );
}

// ── Field Row ── //

function FieldRow({ field }: { field: ExtractedField }) {
  const t = useTranslations("verification");
  const statusConfig = {
    verified: {
      icon: ShieldCheck,
      color: "text-psi-emerald",
      bg: "bg-psi-emerald/10",
      border: "border-psi-emerald/20",
    },
    suspicious: {
      icon: AlertTriangle,
      color: "text-psi-warning",
      bg: "bg-psi-warning/10",
      border: "border-psi-warning/20",
    },
    mismatch: {
      icon: AlertTriangle,
      color: "text-psi-fraud",
      bg: "bg-psi-fraud/10",
      border: "border-psi-fraud/20",
    },
  };

  const config = statusConfig[field.status];
  const Icon = config.icon;

  return (
    <motion.div
      whileHover={{ x: 2 }}
      className={cn(
        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
        config.border,
        config.bg
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", config.color)} />
      <div className="min-w-0 flex-1">
        <p className="text-xs text-psi-text-secondary">{field.field}</p>
        <p className="text-sm font-medium text-psi-text-primary truncate">{field.value}</p>
      </div>
      <div className="text-right shrink-0">
        <span className="text-xs font-semibold text-psi-text-primary tabular-nums">
          {field.confidence}%
        </span>
        <p className="text-[10px] text-psi-text-secondary">{t("confidence")}</p>
      </div>
    </motion.div>
  );
}

// ── Fraud Indicator Card ── //

function FraudIndicatorCard({ indicator }: { indicator: FraudIndicatorItem }) {
  const t = useTranslations("verification");
  const severityStyles = {
    low: "border-l-psi-emerald",
    medium: "border-l-psi-warning",
    high: "border-l-psi-fraud",
    critical: "border-l-psi-fraud shadow-md shadow-psi-fraud/10",
  };

  const severityBadge = {
    low: "success" as const,
    medium: "warning" as const,
    high: "destructive" as const,
    critical: "destructive" as const,
  };

  const severityLabels: Record<string, string> = {
    low: t("severityLow"),
    medium: t("severityMedium"),
    high: t("severityHigh"),
    critical: t("severityCritical"),
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        "rounded-lg border border-psi-border bg-psi-graphite/60 p-3.5 border-l-2",
        severityStyles[indicator.severity]
      )}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <Badge variant={severityBadge[indicator.severity]} className="text-[10px] py-0 px-1.5">
          {severityLabels[indicator.severity]}
        </Badge>
        <span className="text-xs font-semibold text-psi-text-primary">{indicator.type}</span>
      </div>
      <p className="text-xs text-psi-text-secondary leading-relaxed">{indicator.description}</p>
    </motion.div>
  );
}

// ── Metadata Panel (fully data-driven) ── //

function MetadataPanel({ items }: { items: MetadataItem[] }) {
  const t = useTranslations("verification");
  return (
    <div className="space-y-2">
      <p className="text-xs text-psi-text-secondary mb-3">
        {t("metadataDescription")}
      </p>
      {items.map((item) => (
        <div
          key={item.label}
          className={cn(
            "flex items-center justify-between rounded-lg border px-3 py-2.5",
            item.anomaly
              ? "border-psi-warning/30 bg-psi-warning/5"
              : "border-psi-border bg-psi-graphite/30"
          )}
        >
          <span className="text-xs text-psi-text-secondary">{item.label}</span>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-psi-text-primary">{item.value}</span>
            {item.anomaly && (
              <AlertTriangle className="h-3.5 w-3.5 text-psi-warning" />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── AI Explanation Panel (fully data-driven) ── //

function AIExplanationPanel({ summary }: { summary: AISummary }) {
  const t = useTranslations("verification");
  return (
    <div className="space-y-4">
      {/* Summary */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-4 w-4 text-psi-electric" />
          <h4 className="text-sm font-semibold text-psi-text-primary">{t("reasoningSummary")}</h4>
        </div>
        <div className="rounded-lg border border-psi-border bg-psi-graphite/40 p-4">
          <p className="text-sm text-psi-text-secondary leading-relaxed">{summary.summary}</p>
          {summary.findings.length > 0 && (
            <div className="mt-3 pt-3 border-t border-psi-border space-y-2">
              {summary.findings.map((finding, i) => (
                <p
                  key={i}
                  className="text-xs text-psi-text-secondary flex items-start gap-2"
                >
                  <span
                    className={cn(
                      "mt-1 h-1.5 w-1.5 shrink-0 rounded-full",
                      finding.severity === "critical" || finding.severity === "high"
                        ? "bg-psi-fraud"
                        : finding.severity === "medium"
                        ? "bg-psi-warning"
                        : "bg-psi-emerald"
                    )}
                  />
                  {finding.description}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recommended Actions */}
      {summary.recommendedActions.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-psi-text-primary mb-2">{t("recommendedActions")}</h4>
          <div className="space-y-2">
            {summary.recommendedActions.map((action, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-lg border border-psi-border bg-psi-graphite/30 p-3"
              >
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-psi-electric/15 text-[10px] font-bold text-psi-electric">
                  {i + 1}
                </span>
                <p className="text-xs text-psi-text-secondary leading-relaxed">{action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center gap-2 text-xs text-psi-text-secondary pt-1">
        {summary.completedAt && (
          <>
            <span>{t("analysisCompleted", { time: summary.completedAt })}</span>
            <span className="text-psi-text-secondary/50">·</span>
          </>
        )}
        {summary.modelName && (
          <span>{t("modelInfo", { model: summary.modelName })}</span>
        )}
      </div>
    </div>
  );
}
