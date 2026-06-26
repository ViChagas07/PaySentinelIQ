"use client";

import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { useTranslations, useLocale } from "next-intl";
import { cn } from "@/lib/utils";
import { useAnalysisStore, type AnalysisResult, type HistoryEntry } from "@/stores/analysis-store";
import { DocumentUploadZone } from "@/components/analysis/DocumentUploadZone";
import { AIProcessingPipeline, useSimulatePipeline } from "@/components/analysis/AIProcessingPipeline";
import { AnalysisResultCard } from "@/components/analysis/AnalysisResultCard";
import { DocumentHistory } from "@/components/analysis/DocumentHistory";
import { ExtraInfoForm } from "@/components/analysis/ExtraInfoForm";
import { GlowCard, StatusPill } from "@/components/shared/GlowCard";
import { Badge } from "@/components/ui/Badge";
import {
  FileText, Upload, Brain, ShieldAlert, Sparkles, Zap,
  ArrowRight, History, FileCheck, Barcode, CreditCard,
} from "lucide-react";
import { useAnalyzeDocument, useSaveAnalysis } from "@/hooks/useApi";
import { mapPSIReportToAnalysisResult } from "@/lib/analysis-mapper";

function getReadableError(error: unknown): string {
  if (error instanceof Error) {
    if (error.message.includes("422")) {
      return "O documento enviado não pôde ser processado. Verifique se é um PDF válido de boleto bancário e tente novamente.";
    }
    if (error.message.includes("413")) {
      return "O arquivo é muito grande. O tamanho máximo permitido é 10MB.";
    }
    if (error.message.includes("401") || error.message.includes("403")) {
      return "Sua sessão expirou. Faça login novamente para continuar.";
    }
    if (error.message.includes("500") || error.message.includes("502")) {
      return "Erro interno do servidor. Tente novamente em alguns minutos.";
    }
    if (error.message.includes("network") || error.message.includes("fetch")) {
      return "Erro de conexão. Verifique sua internet e tente novamente.";
    }
    return error.message;
  }
  return "Ocorreu um erro inesperado. Tente novamente.";
}

export default function AnalyzeBankSlipPage() {
  const t = useTranslations("analysis");
  const tc = useTranslations("common");
  const locale = useLocale();
  const files = useAnalysisStore((s) => s.files);
  const results = useAnalysisStore((s) => s.results);
  const addResult = useAnalysisStore((s) => s.addResult);
  const clearResults = useAnalysisStore((s) => s.clearResults);
  const history = useAnalysisStore((s) => s.history);
  const addHistoryEntry = useAnalysisStore((s) => s.addHistoryEntry);
  const removeHistoryEntry = useAnalysisStore((s) => s.removeHistoryEntry);
  const isProcessing = useAnalysisStore((s) => s.isProcessing);
  const currentStage = useAnalysisStore((s) => s.currentStage);
  const resetAll = useAnalysisStore((s) => s.resetAll);
  const extraInfo = useAnalysisStore((s) => s.extraInfo);
  const { start: startPipeline } = useSimulatePipeline();

  const analyzeMutation = useAnalyzeDocument();
  const saveAnalysis = useSaveAnalysis();
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = useCallback(async () => {
    if (files.length === 0 || isProcessing) return;
    clearResults();
    setError(null);
    startPipeline();

    const doneFiles = files.filter((f) => f.status === "done");
    const newResults: AnalysisResult[] = [];

    for (const file of doneFiles) {
      try {
        const payload: any = {
          document_id: file.id,
          document_type: "boleto",
        };

        if (extraInfo.companyName) payload.razao_social = extraInfo.companyName;
        if (extraInfo.expectedAmount) {
          const amt = parseFloat(extraInfo.expectedAmount);
          if (!isNaN(amt)) payload.valor_nominal = amt;
        }
        if (extraInfo.recipientName) payload.beneficiario = extraInfo.recipientName;
        if (extraInfo.suspiciousObservations) payload.linha_digitavel = extraInfo.suspiciousObservations;

        const report = await analyzeMutation.mutateAsync(payload);
        const result = mapPSIReportToAnalysisResult(report, file.name, "bank-slip", locale);
        newResults.push(result);

        // Persist analysis to the database so dashboard/history reflect real data
        try {
          await saveAnalysis.mutateAsync({
            document_type: "BOLETO",
            file_name: file.name,
            file_size: file.size,
            risk_level: result.riskScore >= 80 ? "CRITICAL" : result.riskScore >= 60 ? "HIGH" : result.riskScore >= 30 ? "MEDIUM" : "LOW",
            risk_score: result.riskScore,
            confidence_score: result.confidenceScore,
            fraud_probability: result.fraudProbability,
            is_fraudulent: result.riskScore >= 70,
            fraud_indicators: result.manipulationIndicators.length > 0 ? result.manipulationIndicators : undefined,
            analysis_result: report,
            amount: undefined,
            ai_summary: result.aiSummary,
            processing_duration: result.processingDuration,
            status: result.riskScore >= 70 ? "flagged" : "completed",
          });
        } catch (saveErr) {
          // Non-blocking — user already sees the result
          console.error("Failed to persist analysis:", saveErr);
        }
      } catch (err) {
        console.error("Analysis failed for", file.name, err);
        setError(getReadableError(err));
        // Fallback: show a basic error result
        newResults.push({
          id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          fileName: file.name,
          documentType: "bank-slip",
          riskScore: 0,
          fraudProbability: 0,
          confidenceScore: 0,
          aiSummary: `Analysis failed: ${err instanceof Error ? err.message : "Unknown error"}. Please try again.`,
          ocrData: {},
          metadata: {},
          financialInconsistencies: [],
          manipulationIndicators: [],
          recommendedActions: ["Retry analysis or contact support"],
          analysisTimeline: [],
          statusIndicators: [],
          createdAt: new Date().toLocaleDateString(locale, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" }),
          processingDuration: 0,
        });
      }
    }

    newResults.forEach((r) => {
      addResult(r);
      addHistoryEntry({
        id: r.id,
        fileName: r.fileName,
        documentType: "bank-slip",
        uploadDate: new Date().toLocaleDateString(locale, { month: "short", day: "numeric", year: "numeric" }),
        status: r.riskScore >= 70 ? "flagged" : "completed",
        riskScore: r.riskScore,
        processingDuration: r.processingDuration,
        aiSummary: r.aiSummary,
        resultId: r.id,
      });
    });
  }, [files, isProcessing, startPipeline, clearResults, addResult, addHistoryEntry, locale, extraInfo, analyzeMutation]);

  const showResults = results.length > 0 && !isProcessing && currentStage === "complete";
  const canAnalyze = files.filter((f) => f.status === "done").length > 0 && !isProcessing;

  return (
    <div className="space-y-8 animate-slide-in-up">
      {/* ═══════════ SECTION 1 — HERO HEADER ═══════════ */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-psi-border bg-gradient-to-br from-psi-navy via-psi-navy to-psi-warning/5 p-6 md:p-8">
        <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-psi-warning/8 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-40 w-40 rounded-full bg-psi-fraud/5 blur-3xl" />
        <div className="relative z-10 flex flex-col lg:flex-row items-start gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Badge variant="warning" className="text-[10px]">{t("bankSlip.badgeAI")}</Badge>
              <Badge variant="destructive" className="text-[10px]">{t("bankSlip.badgeBankSlip")}</Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-psi-text-primary tracking-tight">{t("bankSlip.heroTitle")}</h1>
            <p className="mt-2 text-sm text-psi-text-secondary max-w-2xl leading-relaxed">{t("bankSlip.heroDescription")}</p>
            <div className="flex flex-wrap items-center gap-4 mt-4 text-xs text-psi-text-secondary">
              <span className="flex items-center gap-1.5"><Barcode className="h-3.5 w-3.5 text-psi-warning" /> {t("bankSlip.feature1")}</span>
              <span className="flex items-center gap-1.5"><CreditCard className="h-3.5 w-3.5 text-psi-fraud" /> {t("bankSlip.feature2")}</span>
              <span className="flex items-center gap-1.5"><Zap className="h-3.5 w-3.5 text-psi-electric" /> {t("bankSlip.feature3")}</span>
            </div>
          </div>
          <div className="hidden lg:flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-psi-warning/10 border border-psi-warning/20">
            <Barcode className="h-10 w-10 text-psi-warning" />
          </div>
        </div>
      </motion.div>

      {/* ═══════════ SECTION 2 — DOCUMENT UPLOAD ═══════════ */}
      <GlowCard glowColor="psi-warning">
        <div className="pt-3">
          <div className="flex items-center gap-2 mb-4">
            <Upload className="h-4 w-4 text-psi-warning" />
            <h2 className="text-base font-semibold text-psi-text-primary">{t("bankSlip.uploadTitle")}</h2>
            <span className="text-[11px] text-psi-text-secondary ml-auto">{t("bankSlip.filesCount", { count: files.length })}</span>
          </div>
          <DocumentUploadZone />
        </div>
      </GlowCard>

      {/* ═══════════ SECTION 3 — EXTRA INFO FORM ═══════════ */}
      <GlowCard glowColor="psi-warning">
        <div className="pt-3">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-psi-warning" />
            <h2 className="text-base font-semibold text-psi-text-primary">{t("bankSlip.extraTitle")}</h2>
            <span className="text-[11px] text-psi-text-secondary ml-auto">{t("bankSlip.extraOptional")}</span>
          </div>
          <ExtraInfoForm documentType="bank-slip" />
        </div>
      </GlowCard>

      {/* Start Analysis Button */}
      {!isProcessing && !showResults && (
        <div className="flex justify-center">
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={handleAnalyze} disabled={!canAnalyze}
            className={cn("inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-sm transition-all",
              canAnalyze ? "bg-gradient-to-r from-psi-warning to-psi-warning/80 text-white shadow-lg shadow-psi-warning/25 hover:shadow-xl hover:shadow-psi-warning/30"
                : "bg-psi-border/30 text-psi-text-secondary/50 cursor-not-allowed")}>
            <Brain className="h-5 w-5" /> {t("bankSlip.startButton")} <ArrowRight className="h-4 w-4" />
          </motion.button>
        </div>
      )}

      {/* ═══════════ SECTION 4 — AI PROCESSING ═══════════ */}
      {isProcessing && (
        <GlowCard glowColor="psi-warning" glowIntensity="high">
          <AIProcessingPipeline />
        </GlowCard>
      )}

      {/* ═══════════ ERROR BLOCK ═══════════ */}
      {error && (
        <div className="mt-4 rounded-lg border border-red-500/50 bg-red-950/30 p-4 backdrop-blur-sm">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-red-400">
                {t("errorTitle") || "Falha na Análise"}
              </p>
              <p className="mt-1 text-sm text-red-300/80">
                {error}
              </p>
              <p className="mt-2 text-xs text-red-400/60">
                {t("errorHint") || "Verifique o documento e tente novamente. Se o problema persistir, entre em contato com o suporte."}
              </p>
            </div>
            <button
              onClick={() => setError(null)}
              className="flex-shrink-0 text-red-400/60 hover:text-red-400 transition-colors"
              aria-label="Fechar erro"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* ═══════════ SECTION 5 — ANALYSIS RESULTS ═══════════ */}
      {showResults && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-psi-emerald" />
            <h2 className="text-lg font-semibold text-psi-text-primary">{t("bankSlip.resultsTitle")}</h2>
            <StatusPill label={t("bankSlip.documentsCount", { count: results.length })} variant="info" />
          </div>
          {results.map((result, idx) => <AnalysisResultCard key={result.id} result={result} index={idx} />)}
          <div className="flex justify-center pt-2">
            <button onClick={() => resetAll()} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-psi-border text-sm text-psi-text-secondary hover:bg-psi-border/20 transition-colors">
              <FileText className="h-4 w-4" /> {t("newAnalysis")}
            </button>
          </div>
        </motion.div>
      )}

      {/* ═══════════ SECTION 6 — DOCUMENT HISTORY ═══════════ */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        <GlowCard>
          <div className="pt-3">
            <div className="flex items-center gap-2 mb-4">
              <History className="h-4 w-4 text-psi-text-secondary" />
              <h2 className="text-base font-semibold text-psi-text-primary">{t("historyTitle")}</h2>
              <span className="text-[11px] text-psi-text-secondary ml-auto">{tc("entries", { count: history.length })}</span>
            </div>
            <DocumentHistory entries={history} onRemove={removeHistoryEntry} onReopen={() => {}} />
          </div>
        </GlowCard>
      </motion.div>
    </div>
  );
}
