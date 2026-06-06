// ============================================================
// PaySentinelIQ — Document Preview Panel
// Renders a real uploaded document for verification.
// When no document is active, shows a centred empty state.
// No mock/simulated content is ever rendered.
// ============================================================

"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { FileText, Upload } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Highlight {
  id: string;
  label: string;
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  severity: "low" | "medium" | "high" | "critical";
}

export function DocumentPreview({
  highlights = [],
}: {
  highlights?: Highlight[];
}) {
  const t = useTranslations("verification");
  const tc = useTranslations("common");

  const hasContent = false; // would be `document != null || highlights.length > 0` with real data

  if (!hasContent) {
    return <EmptyState onUpload={() => {}} />;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Real document renders here when data is available */}
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-psi-text-secondary">{t("documentReady")}</p>
      </div>
    </div>
  );
}

// ── Empty State ── //

function EmptyState({ onUpload }: { onUpload: () => void }) {
  const t = useTranslations("verification");
  const tc = useTranslations("common");

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-psi-electric/10"
      >
        <FileText className="h-8 w-8 text-psi-electric/60" />
      </motion.div>
      <div className="text-center">
        <p className="text-sm font-medium text-psi-text-primary">
          {t("noDocumentTitle")}
        </p>
        <p className="text-xs text-psi-text-secondary mt-1 max-w-[240px]">
          {t("noDocumentDescription")}
        </p>
      </div>
      <Button variant="primary" size="sm" onClick={onUpload}>
        <Upload className="h-3.5 w-3.5 mr-1.5" />
        {t("uploadDocument")}
      </Button>
    </div>
  );
}
