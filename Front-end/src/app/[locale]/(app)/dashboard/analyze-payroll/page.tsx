"use client";

import { useCallback } from "react";
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
  ArrowRight, History, FileCheck,
} from "lucide-react";
import { useAnalyzeDocument } from "@/hooks/useApi";
import { mapPSIReportToAnalysisResult } from "@/lib/analysis-mapper";

export default function AnalyzePayrollPage() {
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

  const handleAnalyze = useCallback(async () => {
    if (files.length === 0 || isProcessing) return;
    clearResults();
    startPipeline();

    const doneFiles = files.filter((f) => f.status === "done");
    const newResults: AnalysisResult[] = [];

    for (const file of doneFiles) {
      try {
        const payload: any = {
          document_type: "contracheque",
        };

        // Map extraInfo fields to backend payload
        if (extraInfo.expectedSalary) {
          const sal = parseFloat(extraInfo.expectedSalary);
          if (!isNaN(sal)) payload.salario_bruto = sal;
        }
        if (extraInfo.employeeName) payload.nome_funcionario = extraInfo.employeeName;
        if (extraInfo.companyName) payload.razao_social = extraInfo.companyName;
        if (extraInfo.jobPosition) payload.cargo = extraInfo.jobPosition;
        if (extraInfo.payrollPeriod) payload.periodo = extraInfo.payrollPeriod;

        const report = await analyzeMutation.mutateAsync(payload);
        const result = mapPSIReportToAnalysisResult(report, file.name, "payroll", locale);
        newResults.push(result);
      } catch (err) {
        console.error("Analysis failed for", file.name, err);
        // Fallback: show a basic error result
        newResults.push({
          id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          fileName: file.name,
          documentType: "payroll",
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
        documentType: "payroll",
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
        className="relative overflow-hidden rounded-2xl border border-psi-border bg-gradient-to-br from-psi-navy via-psi-navy to-psi-electric/5 p-6 md:p-8">
        <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-psi-electric/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-40 w-40 rounded-full bg-psi-emerald/8 blur-3xl" />
        <div className="relative z-10 flex flex-col lg:flex-row items-start gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Badge variant="primary" className="text-[10px]">{t("payroll.badgeAI")}</Badge>
              <Badge variant="success" className="text-[10px]">{t("payroll.badgePayroll")}</Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-psi-text-primary tracking-tight">{t("payroll.heroTitle")}</h1>
            <p className="mt-2 text-sm text-psi-text-secondary max-w-2xl leading-relaxed">{t("payroll.heroDescription")}</p>
            <div className="flex flex-wrap items-center gap-4 mt-4 text-xs text-psi-text-secondary">
              <span className="flex items-center gap-1.5"><Brain className="h-3.5 w-3.5 text-psi-electric" /> {t("payroll.feature1")}</span>
              <span className="flex items-center gap-1.5"><ShieldAlert className="h-3.5 w-3.5 text-psi-emerald" /> {t("payroll.feature2")}</span>
              <span className="flex items-center gap-1.5"><Zap className="h-3.5 w-3.5 text-psi-warning" /> {t("payroll.feature3")}</span>
            </div>
          </div>
          <div className="hidden lg:flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-psi-electric/10 border border-psi-electric/20">
            <FileText className="h-10 w-10 text-psi-electric" />
          </div>
        </div>
      </motion.div>

      {/* ═══════════ SECTION 2 — DOCUMENT UPLOAD ═══════════ */}
      <GlowCard glowColor="psi-electric">
        <div className="pt-3">
          <div className="flex items-center gap-2 mb-4">
            <Upload className="h-4 w-4 text-psi-electric" />
            <h2 className="text-base font-semibold text-psi-text-primary">{t("payroll.uploadTitle")}</h2>
            <span className="text-[11px] text-psi-text-secondary ml-auto">{t("payroll.filesCount", { count: files.length })}</span>
          </div>
          <DocumentUploadZone />
        </div>
      </GlowCard>

      {/* ═══════════ SECTION 3 — EXTRA INFO FORM ═══════════ */}
      <GlowCard glowColor="psi-emerald">
        <div className="pt-3">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-psi-emerald" />
            <h2 className="text-base font-semibold text-psi-text-primary">{t("payroll.extraTitle")}</h2>
            <span className="text-[11px] text-psi-text-secondary ml-auto">{t("payroll.extraOptional")}</span>
          </div>
          <ExtraInfoForm documentType="payroll" />
        </div>
      </GlowCard>

      {/* Start Analysis Button */}
      {!isProcessing && !showResults && (
        <div className="flex justify-center">
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={handleAnalyze} disabled={!canAnalyze}
            className={cn("inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-sm transition-all",
              canAnalyze ? "bg-gradient-to-r from-psi-electric to-psi-electric/80 text-white shadow-lg shadow-psi-electric/25 hover:shadow-xl hover:shadow-psi-electric/30"
                : "bg-psi-border/30 text-psi-text-secondary/50 cursor-not-allowed")}>
            <Brain className="h-5 w-5" /> {t("payroll.startButton")} <ArrowRight className="h-4 w-4" />
          </motion.button>
        </div>
      )}

      {/* ═══════════ SECTION 4 — AI PROCESSING ═══════════ */}
      {isProcessing && (
        <GlowCard glowColor="psi-electric" glowIntensity="high">
          <AIProcessingPipeline />
        </GlowCard>
      )}

      {/* ═══════════ SECTION 5 — ANALYSIS RESULTS ═══════════ */}
      {showResults && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          <div className="flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-psi-emerald" />
            <h2 className="text-lg font-semibold text-psi-text-primary">{t("payroll.resultsTitle")}</h2>
            <StatusPill label={t("payroll.documentsCount", { count: results.length })} variant="info" />
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
