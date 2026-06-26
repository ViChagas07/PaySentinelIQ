// ============================================================
// PaySentinelIQ — Verification Center Page
// Split-panel: Document preview + AI analysis
// Driven by real fraud-alert data from useFraudAlerts()
// ============================================================

"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { useFraudAlerts } from "@/hooks/useApi";
import { DocumentPreview } from "@/components/verification/DocumentPreview";
import { AIAnalysisPanel } from "@/components/verification/AIAnalysisPanel";
import { useAnalysisStore } from "@/stores/analysis-store";
import type {
  ExtractedField,
  FraudIndicatorItem,
  MetadataItem,
  AISummary,
  AIFinding,
} from "@/components/verification/AIAnalysisPanel";
import { FileSearch, Loader2, AlertCircle } from "lucide-react";
import type { FraudAlert } from "@/types";
import { cn } from "@/lib/utils";

// ── Helpers ──────────────────────────────────────────────── //

function toExtractedFields(alert: FraudAlert): ExtractedField[] {
  return alert.flagged_fields.map((f) => ({
    field: f.field_name,
    value: f.detected_value,
    confidence: f.confidence,
    status: f.confidence >= 80 ? "verified" : f.confidence >= 50 ? "suspicious" : "mismatch",
  }));
}

function toFraudIndicators(alert: FraudAlert): FraudIndicatorItem[] {
  return alert.flagged_fields.map((f, i) => ({
    id: `${alert.id}-${i}`,
    type: f.field_name,
    severity: f.confidence >= 80 ? "high" : f.confidence >= 50 ? "medium" : "low",
    description: f.explanation || alert.description,
  }));
}

function toMetadata(alert: FraudAlert): MetadataItem[] {
  const items: MetadataItem[] = [
    { label: "Document Type", value: alert.document_type.replace(/_/g, " ") },
    { label: "Status", value: alert.status.replace(/_/g, " ") },
    { label: "AI Confidence", value: `${alert.ai_confidence}%` },
    { label: "Created", value: new Date(alert.created_at).toLocaleDateString() },
  ];
  if (alert.resolved_at) {
    items.push({ label: "Resolved", value: new Date(alert.resolved_at).toLocaleDateString() });
  }
  return items;
}

function toAISummary(alert: FraudAlert): AISummary | null {
  if (!alert.ai_explanation) return null;
  const findings: AIFinding[] = alert.flagged_fields.map((f) => ({
    severity: f.confidence >= 80 ? "high" : f.confidence >= 50 ? "medium" : "low",
    description: f.explanation,
  }));
  return {
    summary: alert.ai_explanation,
    findings,
    recommendedActions: [],
    modelName: "PaySentinelIQ AI",
    completedAt: alert.resolved_at || alert.created_at,
  };
}

// ═══════════════════════════════════════════════════════════
//  Page Component
// ═══════════════════════════════════════════════════════════

export default function VerificationCenterPage() {
  const t = useTranslations("verification");
  const { data, isLoading, error } = useFraudAlerts({ page_size: 20 });

  const alerts = data?.data ?? [];
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // ── Pipeline results (from analysis-store) ──
  const storeResults = useAnalysisStore((s) => s.results);
  const isProcessing = useAnalysisStore((s) => s.isProcessing);
  const currentStage = useAnalysisStore((s) => s.currentStage);
  const latestResult = storeResults.length > 0 ? storeResults[storeResults.length - 1] : null;

  // Auto-select first open/active alert whenever the list changes
  useEffect(() => {
    if (alerts.length === 0) {
      setSelectedId(null);
      return;
    }
    if (selectedId && alerts.some((a) => a.id === selectedId)) return;
    const open = alerts.find(
      (a) => a.status === "new" || a.status === "under_review",
    );
    setSelectedId(open?.id ?? alerts[0].id);
  }, [alerts, selectedId]);

  const activeVerification = alerts.find((a) => a.id === selectedId) ?? null;

  // ── Loading ── //
  if (isLoading) {
    return (
      <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
        <div className="flex items-center gap-3 shrink-0">
          <FileSearch className="h-5 w-5 text-psi-electric" />
          <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
            {t("verificationCenter")}
          </h1>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-psi-electric" />
            <p className="text-sm text-psi-text-secondary">Loading alerts...</p>
          </div>
        </div>
      </div>
    );
  }

  // ── Error ── //
  if (error) {
    return (
      <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
        <div className="flex items-center gap-3 shrink-0">
          <FileSearch className="h-5 w-5 text-psi-electric" />
          <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
            {t("verificationCenter")}
          </h1>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 max-w-sm text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-psi-fraud/10">
              <AlertCircle className="h-6 w-6 text-psi-fraud" />
            </div>
            <p className="text-sm font-medium text-psi-fraud">Failed to load alerts</p>
            <p className="text-xs text-psi-text-secondary">
              {error instanceof Error ? error.message : "An unexpected error occurred"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
      {/* ─── Top Bar ─── */}
      <div className="flex items-center gap-3 shrink-0">
        <FileSearch className="h-5 w-5 text-psi-electric" />
        <div>
          <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
            {t("verificationCenter")}
          </h1>
          {alerts.length > 0 ? (
            <p className="text-xs text-psi-text-secondary mt-0.5">
              {alerts.length} alert{alerts.length !== 1 ? "s" : ""} available
            </p>
          ) : (
            <p className="text-xs text-psi-text-secondary mt-0.5">
              {t("noActiveVerification")}
            </p>
          )}
        </div>
      </div>

      {/* ─── Alert Selector ─── */}
      {alerts.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1 shrink-0 scrollbar-thin">
          {alerts.map((alert) => {
            const isSelected = selectedId === alert.id;
            return (
              <button
                key={alert.id}
                onClick={() => setSelectedId(alert.id)}
                className={cn(
                  "flex shrink-0 items-center gap-3 rounded-lg border px-3 py-2 text-left transition-all",
                  isSelected
                    ? "border-psi-electric bg-psi-electric/10"
                    : "border-psi-border bg-psi-graphite/40 hover:border-psi-border/80",
                )}
              >
                <div className="min-w-0">
                  <p className="text-xs font-medium text-psi-text-primary truncate max-w-[160px]">
                    {alert.document_type.replace(/_/g, " ")}
                  </p>
                  <p className="text-[10px] text-psi-text-secondary mt-0.5 capitalize">
                    {alert.anomaly_category.replace(/_/g, " ")}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <span
                    className={cn(
                      "text-[11px] font-bold tabular-nums",
                      alert.risk_score >= 70
                        ? "text-psi-fraud"
                        : alert.risk_score >= 40
                          ? "text-psi-warning"
                          : "text-psi-emerald",
                    )}
                  >
                    {alert.risk_score}
                  </span>
                  <span
                    className={cn(
                      "text-[9px] uppercase tracking-wider rounded px-1.5 py-0.5 border",
                      alert.status === "new" && "border-psi-electric/40 text-psi-electric bg-psi-electric/10",
                      alert.status === "under_review" && "border-psi-warning/40 text-psi-warning bg-psi-warning/10",
                      alert.status === "escalated" && "border-psi-fraud/40 text-psi-fraud bg-psi-fraud/10",
                      alert.status === "confirmed_fraud" && "border-psi-fraud/60 text-psi-fraud bg-psi-fraud/20",
                      alert.status === "false_positive" && "border-psi-emerald/40 text-psi-emerald bg-psi-emerald/10",
                      alert.status === "resolved" && "border-psi-text-secondary/30 text-psi-text-secondary bg-psi-text-secondary/10",
                    )}
                  >
                    {alert.status.replace(/_/g, " ")}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* ─── Split Panel ─── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-hidden min-h-0"
      >
        {/* Left: Document Preview */}
        <div className="rounded-xl border border-psi-border bg-psi-graphite overflow-hidden flex flex-col">
          <DocumentPreview />
        </div>

        {/* Right: AI Analysis Panel */}
        <div className="rounded-xl border border-psi-border bg-psi-graphite overflow-hidden flex flex-col">
          <AIAnalysisPanel
            extractedFields={
              activeVerification
                ? toExtractedFields(activeVerification)
                : isProcessing && currentStage !== "complete"
                  ? [{ field: "Status", value: currentStage.replace(/-/g, " "), confidence: 50, status: "suspicious" as const }]
                  : latestResult
                    ? [
                        { field: t("fieldEmployeeName"), value: latestResult.fileName, confidence: 85, status: "verified" as const },
                        { field: "Document Type", value: latestResult.documentType, confidence: 90, status: "verified" as const },
                        { field: "Risk Score", value: `${latestResult.riskScore}%`, confidence: 80, status: latestResult.riskScore >= 60 ? "suspicious" as const : "verified" as const },
                      ]
                    : []
            }
            fraudIndicators={
              activeVerification
                ? toFraudIndicators(activeVerification)
                : latestResult
                  ? latestResult.manipulationIndicators.map((desc, i) => ({
                      id: `store-${i}`,
                      type: "Fraud Indicator",
                      severity: (i % 2 === 0 ? "high" : "medium") as "high" | "medium",
                      description: desc,
                    }))
                  : []
            }
            riskScore={activeVerification?.risk_score ?? latestResult?.riskScore ?? 0}
            metadata={
              activeVerification
                ? toMetadata(activeVerification)
                : latestResult
                  ? [
                      { label: "File", value: latestResult.fileName },
                      { label: "Type", value: latestResult.documentType },
                      { label: "Confidence", value: `${latestResult.confidenceScore}%` },
                      { label: "Fraud Probability", value: `${latestResult.fraudProbability}%` },
                    ]
                  : []
            }
            aiSummary={
              activeVerification
                ? toAISummary(activeVerification)
                : latestResult
                  ? { summary: latestResult.aiSummary, findings: [], recommendedActions: latestResult.recommendedActions, modelName: "PaySentinelIQ AI", completedAt: new Date().toISOString() }
                  : null
            }
          />
        </div>
      </motion.div>
    </div>
  );
}
