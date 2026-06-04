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
  ArrowRight, History, FileCheck, Barcode, CreditCard,
} from "lucide-react";
import { generateId } from "@/stores/analysis-store";

function generateMockBankSlipResult(fileName: string, locale: string): AnalysisResult {
  const riskScore = Math.floor(Math.random() * 100);
  return {
    id: generateId(),
    fileName, documentType: "bank-slip", riskScore,
    fraudProbability: Math.floor(Math.random() * 85) + 10,
    confidenceScore: Math.floor(Math.random() * 15) + 80,
    aiSummary: riskScore > 60
      ? "High-risk boleto detected. Barcode checksum validation failed. Issuer CNPJ does not match registered financial institution. Payment destination account flagged for PIX fraud in 3 previous incidents. Expiration date inconsistent with issuance date."
      : "Bank slip validated successfully. Barcode structure conforms to FEBRABAN standards. Issuer verified against Central Bank registry. Payment amount matches nominal value. No PIX fraud indicators found.",
    ocrData: { "Beneficiary": "TechServ Soluções Ltda", "CNPJ/CPF": "12.345.678/0001-99", "Amount": "R$ 1,847.50", "Due Date": "2026-06-15", "Barcode": "34191.79001 01043.510047 91020.150004 1 91230000184750", "Document Number": "BLT-2026-00482" },
    metadata: { "File Type": fileName.endsWith(".pdf") ? "PDF 1.7" : "PNG Image", "Created": "2026-05-08 09:15:22", "Modified": "2026-05-08 09:15:22", "Author": "Financeiro TechServ", "Pages": "1", "Barcode Format": "FEBRABAN Standard V5" },
    financialInconsistencies: riskScore > 30 ? ["Barcode nominal value differs from displayed amount by R$ 23.50", "Due date falls on a national holiday", "Collection agency not registered with BACEN"] : [],
    manipulationIndicators: riskScore > 50 ? ["Barcode digits 17-20 altered (visible Photoshop artifacts)", "Issuer logo low resolution — likely copied from web", "Watermark missing under UV light simulation", "MICR line font mismatch in payment slip"] : [],
    recommendedActions: riskScore > 60 ? ["Block payment immediately", "Report to BACEN fraud department", "Contact issuing bank for verification", "Cross-reference CNPJ with Receita Federal database"] : ["Payment approved — standard routing"],
    analysisTimeline: [
      { stage: "Barcode Decoding", duration: 0.9, status: "pass" }, { stage: "Checksum Validation", duration: 0.6, status: riskScore > 60 ? "fail" : "pass" },
      { stage: "Issuer Verification", duration: 1.4, status: riskScore > 40 ? "warn" : "pass" }, { stage: "PIX Fraud Scan", duration: 1.8, status: riskScore > 50 ? "fail" : "pass" },
      { stage: "Amount Consistency", duration: 0.7, status: riskScore > 30 ? "warn" : "pass" }, { stage: "Forgery Detection", duration: 2.2, status: riskScore > 60 ? "fail" : "pass" },
    ],
    statusIndicators: [
      { label: "Barcode Valid", value: riskScore < 70, severity: "critical" }, { label: "Issuer Registered", value: riskScore < 50, severity: "high" },
      { label: "Amount Match", value: riskScore < 40, severity: "high" }, { label: "PIX Destination Safe", value: riskScore < 80, severity: "critical" },
      { label: "Date Consistent", value: riskScore < 45, severity: "medium" }, { label: "Anti-Forgery Pass", value: riskScore < 60, severity: "high" },
    ],
    createdAt: new Date().toLocaleDateString(locale, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" }),
    processingDuration: +(Math.random() * 7 + 2.5).toFixed(1),
  };
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
  const { start: startPipeline } = useSimulatePipeline();

  const handleAnalyze = useCallback(() => {
    if (files.length === 0 || isProcessing) return;
    clearResults(); startPipeline();
    setTimeout(() => {
      const newResults = files.filter((f) => f.status === "done").map((f) => generateMockBankSlipResult(f.name, locale));
      newResults.forEach((r) => { addResult(r); addHistoryEntry({ id: r.id, fileName: r.fileName, documentType: "bank-slip", uploadDate: new Date().toLocaleDateString(locale, { month: "short", day: "numeric", year: "numeric" }), status: r.riskScore >= 70 ? "flagged" : "completed", riskScore: r.riskScore, processingDuration: r.processingDuration, aiSummary: r.aiSummary, resultId: r.id }); });
    }, 12000);
  }, [files, isProcessing, startPipeline, clearResults, addResult, addHistoryEntry, locale]);

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
