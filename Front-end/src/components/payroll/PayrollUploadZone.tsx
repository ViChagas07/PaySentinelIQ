"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Scan,
  Upload,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import {
  analyzePayrollFile,
  type PayrollUploadedDocument,
} from "@/lib/payroll-upload";
import type { ExtraInfo } from "@/stores/analysis-store";

type Translate = (key: string) => string;

export interface PayrollUploadZoneProps {
  t: Translate;
  locale: string;
  extraInfo?: ExtraInfo;
  analyzeDocument: (formData: FormData) => Promise<unknown>;
  onDocumentChange: (document: PayrollUploadedDocument) => void;
}

function createUploadId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Drop zone + per-file analysis orchestration for the payment center.
 * Every file is analyzed through POST /documents/analyze independently and
 * reported as scanning -> done or error. Failures never become "done".
 */
export function PayrollUploadZone({
  t,
  locale,
  extraInfo,
  analyzeDocument,
  onDocumentChange,
}: PayrollUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [activeUploads, setActiveUploads] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const processFiles = useCallback(
    async (files: FileList | File[]) => {
      const incoming = Array.from(files);
      if (incoming.length === 0) return;

      setIsDragging(false);
      setActiveUploads((count) => count + incoming.length);

      try {
        await Promise.all(
          incoming.map(async (file) => {
            const id = createUploadId();
            const base = {
              id,
              name: file.name,
              size: file.size,
              type: file.type,
            };

            onDocumentChange({ ...base, status: "scanning" });

            const outcome = await analyzePayrollFile({
              file,
              extraInfo,
              locale,
              analyze: analyzeDocument,
            });

            if (outcome.status === "done") {
              onDocumentChange({
                ...base,
                status: "done",
                result: outcome.result,
              });
            } else {
              onDocumentChange({
                ...base,
                status: "error",
                errorCode: outcome.errorCode,
              });
            }
          }),
        );
      } finally {
        setActiveUploads((count) => Math.max(0, count - incoming.length));
      }
    },
    [analyzeDocument, extraInfo, locale, onDocumentChange],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        void processFiles(e.dataTransfer.files);
      }
    },
    [processFiles],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        void processFiles(e.target.files);
      }
      e.target.value = "";
    },
    [processFiles],
  );

  const scanning = activeUploads > 0;

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        className="hidden"
        onChange={handleFileSelect}
        aria-label={t("upload.selectFile")}
      />

      {/* Drop zone */}
      <motion.div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "relative cursor-pointer rounded-xl border-2 border-dashed p-8 sm:p-12 text-center transition-all duration-300",
          isDragging
            ? "border-psi-electric bg-psi-electric/5 shadow-lg shadow-psi-electric/10 scale-[1.01]"
            : "border-white/[0.08] bg-white/[0.02] hover:border-psi-electric/30 hover:bg-white/[0.04]"
        )}
        whileHover={{ scale: 1.005 }}
        role="button"
        tabIndex={0}
        aria-label={t("upload.dragDrop")}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
      >
        {/* Animated border glow when dragging */}
        {isDragging && (
          <motion.div
            className="absolute inset-0 rounded-xl pointer-events-none"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-psi-electric/20 via-psi-emerald/20 to-psi-electric/20 animate-pulse" />
          </motion.div>
        )}

        {/* Scanning animation */}
        {scanning ? (
          <div className="relative z-10 flex flex-col items-center gap-3">
            <motion.div
              className="relative w-16 h-16"
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <div className="absolute inset-0 rounded-full border-2 border-psi-electric/30 border-t-psi-electric" />
              <Scan className="absolute inset-0 m-auto h-6 w-6 text-psi-electric" />
            </motion.div>
            <p className="text-sm font-medium text-psi-electric">
              {t("upload.scanning")}
            </p>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col items-center gap-3">
            <div className="rounded-2xl bg-psi-electric/10 p-4 ring-1 ring-psi-electric/20 group-hover:bg-psi-electric/20 transition-colors">
              <Upload className="h-8 w-8 text-psi-electric" />
            </div>
            <div>
              <p className="text-sm font-semibold text-psi-text-primary">
                {t("upload.dragDrop")}
              </p>
              <p className="text-xs text-psi-text-secondary/60 mt-1">
                {t("upload.supportedFormats")}
              </p>
            </div>
            <Button variant="outline" size="sm" type="button">
              <FileText className="h-3.5 w-3.5" />
              {t("upload.selectFile")}
            </Button>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export interface PayrollDocumentItemProps {
  document: PayrollUploadedDocument;
  t: Translate;
  onRemove?: (id: string) => void;
}

/** One uploaded document with its real analysis status/result. */
export function PayrollDocumentItem({
  document,
  t,
  onRemove,
}: PayrollDocumentItemProps) {
  const result = document.result;
  const riskVariant =
    result && result.riskScore >= 70
      ? "destructive"
      : result && result.riskScore >= 40
        ? "warning"
        : "success";

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
    >
      <div
        className={cn(
          "shrink-0 w-8 h-8 rounded-lg flex items-center justify-center",
          document.status === "error"
            ? "bg-psi-fraud/10 text-psi-fraud"
            : document.status === "done"
              ? "bg-psi-emerald/10 text-psi-emerald"
              : "bg-psi-electric/10 text-psi-electric"
        )}
      >
        {document.status === "error" ? (
          <AlertTriangle className="h-4 w-4" />
        ) : document.status === "done" ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : (
          <Scan className="h-4 w-4 animate-pulse" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-psi-text-primary truncate">
            {document.name}
          </p>
          {document.status === "done" && result && (
            <Badge variant={riskVariant} className="shrink-0 text-[10px]">
              {result.riskScore}/100
            </Badge>
          )}
        </div>
        <p className="text-xs text-psi-text-secondary/60">
          {(document.size / 1024).toFixed(1)} KB
        </p>

        {document.status === "scanning" && (
          <p className="mt-1 text-xs text-psi-electric">
            {t("upload.scanning")}
          </p>
        )}

        {document.status === "done" && result && (
          <div className="mt-1.5 space-y-1">
            <p className="text-xs text-psi-text-secondary/70 line-clamp-2">
              {result.aiSummary}
            </p>
            {result.persistenceStatus === "failed" && (
              <p
                role="status"
                className="flex items-start gap-1.5 text-xs text-psi-warning"
              >
                <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                <span>{t("upload.persistenceWarning")}</span>
              </p>
            )}
          </div>
        )}

        {document.status === "error" && (
          <p role="alert" className="mt-1 text-xs text-psi-fraud">
            {t(`upload.error.${document.errorCode ?? "unknown"}`)}
          </p>
        )}
      </div>

      {onRemove && (
        <button
          type="button"
          onClick={() => onRemove(document.id)}
          className="shrink-0 p-1 rounded-md hover:bg-psi-border/30 text-psi-text-secondary/50 hover:text-psi-fraud transition-colors"
          aria-label={t("upload.removeDocument")}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </motion.div>
  );
}
