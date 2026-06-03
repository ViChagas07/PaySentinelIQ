// ============================================================
// PaySentinelIQ — Verification Center Page
// Split-panel: Document preview + AI analysis
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DocumentPreview } from "@/components/verification/DocumentPreview";
import { AIAnalysisPanel } from "@/components/verification/AIAnalysisPanel";
import { Clock, ArrowLeft, MoreHorizontal, Flag, CheckCircle, XCircle } from "lucide-react";

export default function VerificationCenterPage() {
  const t = useTranslations("verification");
  const tc = useTranslations("common");
  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" aria-label={tc("back")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
              {t("verificationCenter")}
            </h1>
            <p className="text-xs text-psi-text-secondary flex items-center gap-1 mt-0.5">
              <Clock className="h-3 w-3" />
              {t("documentInfo", { name: "Q1_2025_Payroll_Report.pdf", time: "2 hours ago" })}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="warning" dot>{t("needsReview")}</Badge>
          <div className="h-6 w-px bg-psi-border mx-1" />
          <Button variant="outline" size="sm">
            <Flag className="h-3.5 w-3.5 mr-1" />
            {t("flag")}
          </Button>
          <Button variant="outline" size="sm">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
          <Button variant="destructive" size="sm">
            <XCircle className="h-3.5 w-3.5 mr-1" />
            {t("reject")}
          </Button>
          <Button variant="success" size="sm">
            <CheckCircle className="h-3.5 w-3.5 mr-1" />
            {t("approve")}
          </Button>
        </div>
      </div>

      {/* Split Panel */}
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
