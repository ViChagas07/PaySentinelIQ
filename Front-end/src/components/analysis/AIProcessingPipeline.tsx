"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useAnalysisStore, type AnalysisStage } from "@/stores/analysis-store";
import {
  Loader2, CheckCircle2, Clock, Brain, ScanEye, ShieldCheck,
  FileSearch, BarChart3, FileCheck, Sparkles,
} from "lucide-react";

/* ═══════════════════════════════════════════════════
   AI Processing Pipeline
   ═══════════════════════════════════════════════════ */

const STAGE_KEYS: AnalysisStage[] = [
  "uploading", "ocr", "metadata", "fraud-detection",
  "financial-check", "risk-analysis", "report-generation",
];

const STAGE_DURATIONS: Record<number, number> = {
  0: 1200, 1: 2000, 2: 1500, 3: 2500, 4: 2000, 5: 1800, 6: 1500,
};

const STAGE_ICONS: Record<string, React.ElementType> = {
  uploading: Clock,
  ocr: ScanEye,
  metadata: FileSearch,
  "fraud-detection": ShieldCheck,
  "financial-check": BarChart3,
  "risk-analysis": Brain,
  "report-generation": FileCheck,
};

function useStageData(t: ReturnType<typeof useTranslations<"analysis">>) {
  return useMemo(() => STAGE_KEYS.map((stage) => ({
    stage,
    label: t(`pipeline.stages.${stage === "fraud-detection" ? "fraudDetection" : stage === "financial-check" ? "financialCheck" : stage === "risk-analysis" ? "riskAnalysis" : stage === "report-generation" ? "reportGeneration" : stage}` as any),
    icon: STAGE_ICONS[stage],
    description: t(`pipeline.stages.${stage === "fraud-detection" ? "fraudDetection" : stage === "financial-check" ? "financialCheck" : stage === "risk-analysis" ? "riskAnalysis" : stage === "report-generation" ? "reportGeneration" : stage}Desc` as any),
  })), [t]);
}

export function AIProcessingPipeline({ onComplete }: { onComplete?: () => void }) {
  const t = useTranslations("analysis");
  const STAGES = useStageData(t);

  const currentStage = useAnalysisStore((s) => s.currentStage);
  const setStage = useAnalysisStore((s) => s.setStage);
  const stageProgress = useAnalysisStore((s) => s.stageProgress);
  const setStageProgress = useAnalysisStore((s) => s.setStageProgress);
  const isProcessing = useAnalysisStore((s) => s.isProcessing);
  const [elapsed, setElapsed] = useState(0);
  const progressRef = useRef(0);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stageIndex = STAGES.findIndex((s) => s.stage === currentStage);

  useEffect(() => {
    if (isProcessing) {
      timerRef.current = setInterval(() => setElapsed((p) => p + 0.1), 100);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isProcessing]);

  useEffect(() => {
    if (!isProcessing || currentStage === "complete" || currentStage === "idle") return;

    const interval = setInterval(() => {
      progressRef.current = Math.min(100, progressRef.current + Math.random() * 8);
      setStageProgress(progressRef.current);
    }, 200);

    return () => clearInterval(interval);
  }, [currentStage, isProcessing, setStageProgress]);

  if (!isProcessing && currentStage === "idle") return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-psi-electric/10"
        >
          <Brain className="h-5 w-5 text-psi-electric" />
        </motion.div>
        <div>
          <h3 className="text-base font-semibold text-psi-text-primary">
            {currentStage === "complete" ? t("pipeline.complete") : t("pipeline.title")}
          </h3>
          <p className="text-xs text-psi-text-secondary">
            {currentStage === "complete"
              ? t("pipeline.completedIn", { time: elapsed.toFixed(1) })
              : `${t("pipeline.stageOf", { current: stageIndex + 1, total: STAGES.length })} • ${elapsed.toFixed(1)}s ${t("pipeline.elapsed")}`}
          </p>
        </div>
      </div>

      {/* Global progress bar */}
      <div className="relative">
        <div className="h-1.5 w-full rounded-full bg-psi-border/50 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-psi-electric to-psi-emerald"
            animate={{
              width: currentStage === "complete"
                ? "100%"
                : `${((stageIndex + stageProgress / 100) / STAGES.length) * 100}%`,
            }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* Stage timeline */}
      <div className="space-y-0">
        {STAGES.map((stage, idx) => {
          const isComplete = idx < stageIndex;
          const isCurrent = idx === stageIndex;
          const isPending = idx > stageIndex;
          const Icon = stage.icon;

          return (
            <motion.div
              key={stage.stage}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="relative flex gap-3"
            >
              {idx < STAGES.length - 1 && (
                <div className="absolute left-[15px] top-8 bottom-0 w-px">
                  <motion.div
                    className={cn(
                      "h-full w-px",
                      isComplete ? "bg-psi-emerald" : isCurrent ? "bg-psi-border" : "bg-psi-border/30"
                    )}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: isComplete || isCurrent ? 1 : 0 }}
                    transition={{ duration: 0.5 }}
                    style={{ transformOrigin: "top" }}
                  />
                </div>
              )}

              <motion.div
                animate={
                  isCurrent && !isComplete
                    ? { boxShadow: ["0 0 0 0 rgba(30,111,255,0.4)", "0 0 0 8px rgba(30,111,255,0)", "0 0 0 0 rgba(30,111,255,0)"] }
                    : {}
                }
                transition={{ duration: 2, repeat: Infinity }}
                className={cn(
                  "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all duration-300",
                  isComplete && "bg-psi-emerald/20 text-psi-emerald",
                  isCurrent && "bg-psi-electric/20 text-psi-electric ring-2 ring-psi-electric/30",
                  isPending && "bg-psi-border/20 text-psi-text-secondary/40"
                )}
              >
                {isComplete ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : isCurrent ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Icon className="h-3.5 w-3.5" />
                )}
              </motion.div>

              <div className="pb-5 flex-1 min-w-0">
                <p
                  className={cn(
                    "text-sm font-medium transition-colors",
                    isComplete && "text-psi-emerald",
                    isCurrent && "text-psi-text-primary",
                    isPending && "text-psi-text-secondary/40"
                  )}
                >
                  {stage.label}
                </p>
                <p
                  className={cn(
                    "text-xs transition-colors",
                    isComplete && "text-psi-emerald/70",
                    isCurrent && "text-psi-text-secondary",
                    isPending && "text-psi-text-secondary/30"
                  )}
                >
                  {isComplete ? t("pipeline.completedLabel") : isCurrent ? stage.description : t("pipeline.waiting")}
                </p>
                {isCurrent && (
                  <div className="mt-1.5 h-1 w-full rounded-full bg-psi-border/30 overflow-hidden max-w-[200px]">
                    <motion.div
                      className="h-full rounded-full bg-psi-electric"
                      animate={{ width: `${stageProgress}%` }}
                      transition={{ duration: 0.2 }}
                    />
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Complete state */}
      <AnimatePresence>
        {currentStage === "complete" && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-3 rounded-xl border border-psi-emerald/30 bg-psi-emerald/5 px-4 py-3"
          >
            <Sparkles className="h-5 w-5 text-psi-emerald" />
            <div>
              <p className="text-sm font-semibold text-psi-emerald">{t("pipeline.complete")}</p>
              <p className="text-xs text-psi-text-secondary">
                {t("pipeline.allStagesPassed", { count: STAGES.length })}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Simulated pipeline runner
   ═══════════════════════════════════════════════════ */

export function useSimulatePipeline() {
  const t = useTranslations("analysis");
  const STAGES = useStageData(t);

  const setStage = useAnalysisStore((s) => s.setStage);
  const setStageProgress = useAnalysisStore((s) => s.setStageProgress);
  const setIsProcessing = useAnalysisStore((s) => s.setIsProcessing);
  const isProcessing = useAnalysisStore((s) => s.isProcessing);

  const start = () => {
    if (isProcessing) return;
    setIsProcessing(true);
    setStageProgress(0);
    setStage("uploading");

    let currentIdx = 1;
    const advance = () => {
      if (currentIdx >= STAGES.length) {
        setStage("complete");
        setIsProcessing(false);
        return;
      }
      const stage = STAGES[currentIdx];
      setStage(stage.stage);
      setStageProgress(0);
      currentIdx++;
      setTimeout(advance, STAGE_DURATIONS[currentIdx - 1] || 1500);
    };

    setTimeout(advance, STAGE_DURATIONS[0]);
  };

  return { start, isProcessing };
}
