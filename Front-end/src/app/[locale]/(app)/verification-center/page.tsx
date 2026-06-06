// ============================================================
// PaySentinelIQ — Verification Center Page
// Split-panel: Document preview + AI analysis
// Drives entirely from real user-activity data. No mock data.
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { DocumentPreview } from "@/components/verification/DocumentPreview";
import { AIAnalysisPanel } from "@/components/verification/AIAnalysisPanel";
import { FileSearch } from "lucide-react";

export default function VerificationCenterPage() {
  const t = useTranslations("verification");

  // ── Real data feeds -------------------------------------------------- //
  // In a production integration, these would come from a backend API or
  // user-activity store. For now, they remain empty so the UI never shows
  // fabricated content — only genuine empty/loading states.
  const activeVerification = null; // { document, extractedFields, fraudIndicators, riskScore, metadata, analysis }

  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
      {/* ─── Top Bar ─── */}
      <div className="flex items-center gap-3 shrink-0">
        <FileSearch className="h-5 w-5 text-psi-electric" />
        <div>
          <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
            {t("verificationCenter")}
          </h1>
          {!activeVerification && (
            <p className="text-xs text-psi-text-secondary mt-0.5">
              {t("noActiveVerification")}
            </p>
          )}
        </div>
      </div>

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
          <AIAnalysisPanel />
        </div>
      </motion.div>
    </div>
  );
}
