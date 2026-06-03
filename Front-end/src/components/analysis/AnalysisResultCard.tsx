"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AnalysisResult } from "@/stores/analysis-store";
import { GlowCard, StatusPill, AnimatedProgress } from "@/components/shared/GlowCard";
import {
  ChevronDown, ShieldAlert, FileSearch, Eye, AlertTriangle,
  CheckCircle2, Clock, Zap, Download, ExternalLink,
} from "lucide-react";

function riskLabel(score: number): string {
  if (score >= 80) return "result.riskCritical";
  if (score >= 60) return "result.riskHigh";
  if (score >= 30) return "result.riskMedium";
  return "result.riskLow";
}

function riskVariant(score: number): "destructive" | "warning" | "success" {
  if (score >= 80) return "destructive";
  if (score >= 30) return "warning";
  return "success";
}

function riskGlowColor(score: number): "psi-fraud" | "psi-warning" | "psi-emerald" {
  if (score >= 80) return "psi-fraud";
  if (score >= 60) return "psi-warning";
  return "psi-emerald";
}

export function AnalysisResultCard({ result, index }: { result: AnalysisResult; index: number }) {
  const t = useTranslations("analysis");
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
    >
      <GlowCard glowColor={riskGlowColor(result.riskScore)} className="overflow-hidden" noPadding>
        {/* Header */}
        <div className="px-5 py-4 border-b border-psi-border/50">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3 min-w-0">
              <div className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
                result.riskScore >= 80 ? "bg-psi-fraud/10" : result.riskScore >= 60 ? "bg-psi-warning/10" : "bg-psi-emerald/10"
              )}>
                <ShieldAlert className={cn("h-5 w-5", result.riskScore >= 80 ? "text-psi-fraud" : result.riskScore >= 60 ? "text-psi-warning" : "text-psi-emerald")} />
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-semibold text-psi-text-primary truncate">{result.fileName}</h4>
                <p className="text-[11px] text-psi-text-secondary">
                  {t("result.analysisId")}: {result.id.slice(0, 12)}... • {result.createdAt}
                </p>
              </div>
            </div>
            <StatusPill label={t(riskLabel(result.riskScore) as any)} variant={riskVariant(result.riskScore)} />
          </div>
        </div>

        {/* Score gauges */}
        <div className="px-5 py-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary mb-1">{t("result.riskScore")}</p>
            <div className="flex items-end gap-1">
              <span className={cn("text-2xl font-bold", result.riskScore >= 80 ? "text-psi-fraud" : result.riskScore >= 60 ? "text-psi-warning" : "text-psi-emerald")}>{result.riskScore}</span>
              <span className="text-xs text-psi-text-secondary mb-1">/100</span>
            </div>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary mb-1">{t("result.fraudProbability")}</p>
            <span className="text-2xl font-bold text-psi-text-primary">{result.fraudProbability}%</span>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary mb-1">{t("result.aiConfidence")}</p>
            <span className="text-2xl font-bold text-psi-electric">{result.confidenceScore}%</span>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary mb-1">{t("result.duration")}</p>
            <span className="text-2xl font-bold text-psi-text-primary">{result.processingDuration}s</span>
          </div>
        </div>

        {/* Progress bars */}
        <div className="px-5 pb-2 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <AnimatedProgress value={result.riskScore} color="psi-fraud" height="h-1.5" showLabel={false} />
            <p className="text-[10px] text-psi-text-secondary mt-0.5">{t("result.risk")}</p>
          </div>
          <div>
            <AnimatedProgress value={result.fraudProbability} color="psi-warning" height="h-1.5" showLabel={false} />
            <p className="text-[10px] text-psi-text-secondary mt-0.5">{t("result.fraud")}</p>
          </div>
          <div>
            <AnimatedProgress value={result.confidenceScore} color="psi-emerald" height="h-1.5" showLabel={false} />
            <p className="text-[10px] text-psi-text-secondary mt-0.5">{t("result.confidence")}</p>
          </div>
        </div>

        {/* AI Summary */}
        <div className="px-5 py-3 border-t border-psi-border/30">
          <div className="flex items-start gap-2">
            <Zap className="h-3.5 w-3.5 text-psi-electric mt-0.5 shrink-0" />
            <p className="text-xs text-psi-text-secondary leading-relaxed">{result.aiSummary}</p>
          </div>
        </div>

        {/* Expand button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-center gap-1.5 border-t border-psi-border/30 py-2.5 text-xs text-psi-text-secondary hover:text-psi-text-primary hover:bg-psi-border/20 transition-colors"
        >
          {expanded ? t("result.hideDetails") : t("result.viewFullAnalysis")}
          <motion.span animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown className="h-3.5 w-3.5" />
          </motion.span>
        </button>

        {/* Expandable details */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="px-5 pb-5 space-y-4 border-t border-psi-border/20 pt-4">
                {result.financialInconsistencies.length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <AlertTriangle className="h-3.5 w-3.5 text-psi-warning" />
                      {t("result.financialInconsistencies")}
                    </h5>
                    <div className="space-y-1.5">
                      {result.financialInconsistencies.map((item, i) => (
                        <div key={i} className="flex items-start gap-2 rounded-md bg-psi-warning/5 border border-psi-warning/10 px-3 py-2">
                          <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-psi-warning shrink-0" />
                          <p className="text-xs text-psi-text-secondary">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.manipulationIndicators.length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <Eye className="h-3.5 w-3.5 text-psi-fraud" />
                      {t("result.manipulationIndicators")}
                    </h5>
                    <div className="space-y-1.5">
                      {result.manipulationIndicators.map((item, i) => (
                        <div key={i} className="flex items-start gap-2 rounded-md bg-psi-fraud/5 border border-psi-fraud/10 px-3 py-2">
                          <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-psi-fraud shrink-0" />
                          <p className="text-xs text-psi-text-secondary">{item}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {Object.keys(result.ocrData).length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <FileSearch className="h-3.5 w-3.5 text-psi-electric" />
                      {t("result.extractedData")}
                    </h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {Object.entries(result.ocrData).map(([key, value]) => (
                        <div key={key} className="rounded-md border border-psi-border/40 bg-psi-graphite/40 px-3 py-2">
                          <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary">{key}</p>
                          <p className="text-xs font-medium text-psi-text-primary mt-0.5">{value || "—"}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {Object.keys(result.metadata).length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <FileSearch className="h-3.5 w-3.5 text-psi-text-secondary" />
                      {t("result.documentMetadata")}
                    </h5>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {Object.entries(result.metadata).map(([key, value]) => (
                        <div key={key} className="rounded-md border border-psi-border/40 bg-psi-graphite/40 px-3 py-2">
                          <p className="text-[10px] uppercase tracking-wider text-psi-text-secondary">{key}</p>
                          <p className="text-xs font-medium text-psi-text-primary mt-0.5">{value || "—"}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.analysisTimeline.length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <Clock className="h-3.5 w-3.5 text-psi-text-secondary" />
                      {t("result.analysisTimeline")}
                    </h5>
                    <div className="space-y-1">
                      {result.analysisTimeline.map((step, i) => (
                        <div key={i} className="flex items-center justify-between rounded-md border border-psi-border/30 px-3 py-2">
                          <div className="flex items-center gap-2">
                            {step.status === "pass" ? <CheckCircle2 className="h-3.5 w-3.5 text-psi-emerald" />
                              : step.status === "warn" ? <AlertTriangle className="h-3.5 w-3.5 text-psi-warning" />
                              : <ShieldAlert className="h-3.5 w-3.5 text-psi-fraud" />}
                            <span className="text-xs text-psi-text-primary">{step.stage}</span>
                          </div>
                          <span className="text-[10px] text-psi-text-secondary">{step.duration}s</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.recommendedActions.length > 0 && (
                  <div>
                    <h5 className="flex items-center gap-2 text-xs font-semibold text-psi-text-primary mb-2">
                      <ShieldAlert className="h-3.5 w-3.5 text-psi-electric" />
                      {t("result.recommendedActions")}
                    </h5>
                    <div className="space-y-1.5">
                      {result.recommendedActions.map((action, i) => (
                        <div key={i} className="flex items-start gap-2 rounded-md bg-psi-electric/5 border border-psi-electric/10 px-3 py-2">
                          <span className="mt-0.5 text-[10px] font-bold text-psi-electric">{i + 1}.</span>
                          <p className="text-xs text-psi-text-secondary">{action}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h5 className="text-xs font-semibold text-psi-text-primary mb-2">{t("result.verificationChecklist")}</h5>
                  <div className="grid grid-cols-2 gap-1.5">
                    {result.statusIndicators.map((ind, i) => (
                      <div key={i} className="flex items-center gap-2 rounded px-2 py-1.5">
                        {ind.value ? <CheckCircle2 className="h-3.5 w-3.5 text-psi-emerald" /> : <AlertTriangle className="h-3.5 w-3.5 text-psi-fraud" />}
                        <span className="text-[11px] text-psi-text-secondary">{ind.label}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 pt-2">
                  <button className="inline-flex items-center gap-1.5 rounded-lg bg-psi-electric px-4 py-2 text-xs font-medium text-white hover:bg-psi-electric/90 transition-colors">
                    <Download className="h-3.5 w-3.5" />
                    {t("result.downloadReport")}
                  </button>
                  <button className="inline-flex items-center gap-1.5 rounded-lg border border-psi-border px-4 py-2 text-xs font-medium text-psi-text-secondary hover:bg-psi-border/30 transition-colors">
                    <ExternalLink className="h-3.5 w-3.5" />
                    {t("result.viewRawData")}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </GlowCard>
    </motion.div>
  );
}
