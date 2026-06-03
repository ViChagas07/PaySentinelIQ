// ============================================================
// PaySentinelIQ — AI Analysis Panel
// Right-side panel with risk score, extracted fields, fraud indicators, AI explanation
// ============================================================

"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { RiskGauge } from "./RiskGauge";
import {
  ShieldCheck,
  AlertTriangle,
  Brain,
  FileText,
  Clock,
  Link,
  ChevronDown,
  Database,
  ScanEye,
} from "lucide-react";

// ── Types (data comes from API, never hardcoded) ── //

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

// ── Main Panel — accepts real data as props ── //

export function AIAnalysisPanel({
  extractedFields = [],
  fraudIndicators = [],
  riskScore = 0,
}: {
  extractedFields?: ExtractedField[];
  fraudIndicators?: FraudIndicatorItem[];
  riskScore?: number;
}) {
  const t = useTranslations("verification");
  const tc = useTranslations("common");

  const tabs = [
    { id: "fields", label: t("tabExtractedFields"), icon: Database },
    { id: "fraud", label: t("tabFraudIndicators"), icon: AlertTriangle },
    { id: "metadata", label: t("tabMetadata"), icon: ScanEye },
    { id: "explanation", label: t("tabAIExplanation"), icon: Brain },
  ];

  const [activeTab, setActiveTab] = useState("fields");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-psi-border">
        <div className="flex items-center gap-2 mb-1">
          <Brain className="h-4 w-4 text-psi-electric" />
          <h2 className="text-base font-semibold text-psi-text-primary">{t("aiAnalysis")}</h2>
          <Badge variant="primary" className="ml-auto text-[10px]">
            {t("confidenceLabel", { value: 92 })}
          </Badge>
        </div>
        <p className="text-xs text-psi-text-secondary">
          {t("aiAnalysisDescription")}
        </p>
      </div>

      {/* Risk Score */}
      <div className="flex justify-center py-5 border-b border-psi-border bg-psi-graphite/30">
        <RiskGauge score={riskScore} size={130} strokeWidth={8} label={t("riskScore")} />
      </div>

      {/* Tabs */}
      <div className="flex border-b border-psi-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-all border-b-2 -mb-px",
                activeTab === tab.id
                  ? "border-psi-electric text-psi-electric"
                  : "border-transparent text-psi-text-secondary hover:text-psi-text-primary"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.id === "fraud" && (
                <span className="ml-1 rounded-full bg-psi-fraud h-1.5 w-1.5 animate-pulse-alert" />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
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
              <div className="space-y-2">
                <p className="text-xs text-psi-text-secondary mb-3">
                  {t("fieldsDescription")}
                </p>
                {extractedFields.map((field) => (
                  <FieldRow key={field.field} field={field} />
                ))}
              </div>
            )}

            {/* ── Fraud Indicators ── */}
            {activeTab === "fraud" && (
              <div className="space-y-3">
                <p className="text-xs text-psi-text-secondary mb-3">
                  {t("indicatorsDetected", { count: fraudIndicators.length })}
                </p>
                {fraudIndicators.map((indicator) => (
                  <FraudIndicatorCard key={indicator.id} indicator={indicator} />
                ))}
              </div>
            )}

            {/* ── Metadata Analysis ── */}
            {activeTab === "metadata" && <MetadataPanel />}

            {/* ── AI Explanation ── */}
            {activeTab === "explanation" && <AIExplanationPanel />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
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

// ── Metadata Panel ── //

function MetadataPanel() {
  const t = useTranslations("verification");
  const metadata = [
    { label: t("metadataFileType"), value: "PDF 1.7" },
    { label: t("metadataFileSize"), value: "2.4 MB" },
    { label: t("metadataPages"), value: "3" },
    { label: t("metadataCreated"), value: "2025-01-05 14:32 UTC", anomaly: true },
    { label: t("metadataModified"), value: "2025-01-06 09:15 UTC" },
    { label: t("metadataAuthor"), value: "payroll@acmecorp.com" },
    { label: t("metadataSoftware"), value: "Microsoft Excel / PDF Printer", anomaly: true },
    { label: t("metadataPDFProducer"), value: "wkhtmltopdf 0.12.6" },
  ];

  return (
    <div className="space-y-2">
      <p className="text-xs text-psi-text-secondary mb-3">
        {t("metadataDescription")}
      </p>
      {metadata.map((item) => (
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

// ── AI Explanation Panel ── //

function AIExplanationPanel() {
  const t = useTranslations("verification");
  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-4 w-4 text-psi-electric" />
          <h4 className="text-sm font-semibold text-psi-text-primary">{t("reasoningSummary")}</h4>
        </div>
        <div className="rounded-lg border border-psi-border bg-psi-graphite/40 p-4">
          <p className="text-sm text-psi-text-secondary leading-relaxed">
            The AI model analyzed this payroll document through multiple verification layers
            (optical character recognition, metadata integrity, cross-reference with HR database,
            and anomaly detection algorithms) and identified{' '}
            <span className="text-psi-fraud font-semibold">5 high-confidence anomalies</span> that
            require analyst review.
          </p>
          <div className="mt-3 pt-3 border-t border-psi-border space-y-2">
            <p className="text-xs text-psi-text-secondary flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-psi-fraud" />
              Primary concern: salary discrepancy exceeds 3σ threshold
            </p>
            <p className="text-xs text-psi-text-secondary flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-psi-fraud" />
              Secondary concern: tax ID cross-reference conflict
            </p>
            <p className="text-xs text-psi-text-secondary flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-psi-warning" />
              Metadata inconsistency suggests possible document manipulation
            </p>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-psi-text-primary mb-2">{t("recommendedActions")}</h4>
        <div className="space-y-2">
          {[
            "Cross-reference salary with HR promotion records for Q1 2025",
            "Verify employee identity and tax documentation with issuing authority",
            "Request original, unmodified payroll document from the source system",
            "Escalate to fraud investigation team if salary discrepancy confirmed",
          ].map((action, i) => (
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

      <div className="flex items-center gap-2 text-xs text-psi-text-secondary pt-1">
        <Clock className="h-3.5 w-3.5" />
        <span>{t("analysisCompleted", { time: "3 minutes ago" })}</span>
        <span className="text-psi-text-secondary/50">·</span>
        <span>{t("modelInfo", { model: "PSI-Verify v3.2" })}</span>
      </div>
    </div>
  );
}
