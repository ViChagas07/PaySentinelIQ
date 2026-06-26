// ============================================================
// PaySentinelIQ — Document Preview Panel
// Renders a real uploaded document for verification.
// Empty state: upload button + Google Drive.
// With files: preview cards + add-more button.
// ============================================================

"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import {
  FileText, Upload, X, FolderOpen, Loader2, AlertCircle, Check,
  ShieldCheck, Sparkles, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useGooglePicker, fetchGoogleFileContent } from "@/hooks/useGooglePicker";
import { useAnalysisStore, generateId, type UploadedFile } from "@/stores/analysis-store";
import { useSimulatePipeline } from "@/components/analysis/AIProcessingPipeline";
import { useTriggerVerification } from "@/hooks/useApi";

const ALLOWED_TYPES = ["application/pdf", "image/png", "image/jpg", "image/jpeg"];
const MAX_SIZE = 20 * 1024 * 1024; // 20MB

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
  const ta = useTranslations("analysis");

  // ── Store ──
  const files = useAnalysisStore((s) => s.files);
  const maxFiles = useAnalysisStore((s) => s.maxFiles);
  const addFile = useAnalysisStore((s) => s.addFile);
  const removeFile = useAnalysisStore((s) => s.removeFile);
  const updateFileProgress = useAnalysisStore((s) => s.updateFileProgress);
  const clearFiles = useAnalysisStore((s) => s.clearFiles);

  // ── Pipeline ──
  const isProcessing = useAnalysisStore((s) => s.isProcessing);
  const currentStage = useAnalysisStore((s) => s.currentStage);
  const { start: startPipeline } = useSimulatePipeline();
  const triggerVerification = useTriggerVerification();

  // ── Local state ──
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  // ── Google Drive ──
  const {
    openPicker,
    loading: googleLoading,
    error: googleError,
    token,
    isConfigured,
  } = useGooglePicker();

  const tokenRef = useRef<string | null>(null);
  useEffect(() => { tokenRef.current = token; }, [token]);

  // ── Validate single file ──
  const validateFile = useCallback(
    (file: File): string | null => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        return ta("upload.unsupportedType", { name: file.name });
      }
      if (file.size > MAX_SIZE) {
        return ta("upload.fileTooLarge", { name: file.name });
      }
      return null;
    },
    [ta],
  );

  // ── Import file list into store ──
  const importFiles = useCallback(
    (fileList: File[]) => {
      setError(null);

      if (files.length + fileList.length > maxFiles) {
        setError(ta("upload.maxFilesError", { max: maxFiles }));
        return;
      }

      for (const file of fileList) {
        const err = validateFile(file);
        if (err) { setError(err); return; }
      }

      fileList.forEach((file) => {
        const id = generateId();
        addFile({
          id, name: file.name, size: file.size,
          type: file.type, progress: 0, status: "pending",
        });
        let p = 0;
        const iv = setInterval(() => {
          p += Math.random() * 30;
          if (p >= 100) { p = 100; clearInterval(iv); }
          updateFileProgress(id, Math.min(100, p));
        }, 300);
      });
    },
    [files.length, maxFiles, addFile, updateFileProgress, validateFile, ta],
  );

  // ── Native file input change ──
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const incoming = Array.from(e.target.files ?? []);
      if (incoming.length) importFiles(incoming);
      e.target.value = "";
    },
    [importFiles],
  );

  // ── Remove ──
  const handleRemove = useCallback(
    (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      removeFile(id);
    },
    [removeFile],
  );

  // ── Google Drive picker ──
  const handleDriveUpload = useCallback(() => {
    if (files.length >= maxFiles) {
      setError(ta("upload.maxFilesError", { max: maxFiles }));
      return;
    }
    openPicker(async (picked) => {
      if (!picked.length) return;
      const at = tokenRef.current;
      if (!at) { setError(ta("drive.tokenExpired")); return; }
      try {
        let n = 0;
        for (const pf of picked) {
          if (files.length + n >= maxFiles) break;
          const blob = await fetchGoogleFileContent(pf.url, at);
          addFile({
            id: generateId(), name: pf.name, size: blob.size,
            type: pf.mimeType || "application/pdf",
            progress: 100, status: "done",
          });
          n++;
        }
      } catch (err: any) {
        setError(err.message || ta("drive.failedToImport"));
      }
    });
  }, [files.length, maxFiles, openPicker, addFile, ta]);

  const hasContent = files.length > 0;

  // ── Start verification ──
  const handleStartVerification = useCallback(async () => {
    if (isProcessing || verifying || files.length === 0) return;
    setVerifying(true);
    setError(null);
    startPipeline();

    try {
      await triggerVerification.mutateAsync("mock-doc-id");
    } catch {
      // Backend might not be available — continue with client-side simulation
    } finally {
      // Pipeline stages run independently via startPipeline()
      // Wait briefly to let the animation play, then mark as resolving
      setTimeout(() => {
        setVerifying(false);
      }, 8000); // Match pipeline total duration
    }
  }, [isProcessing, verifying, files.length, startPipeline, triggerVerification]);

  // ──────────────────────────────────────────
  //  EMPTY STATE
  // ──────────────────────────────────────────
  if (!hasContent) {
    return (
      <EmptyState
        onFilesSelected={importFiles}
        onDriveUpload={handleDriveUpload}
        googleLoading={googleLoading}
        googleError={googleError}
        isGoogleConfigured={isConfigured}
        error={error}
        onClearError={() => setError(null)}
      />
    );
  }

  // ──────────────────────────────────────────
  //  WITH FILES
  // ──────────────────────────────────────────
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider">
          {t("uploadedDocuments", { count: files.length })}
        </p>
        <AnimatePresence>
          {files.map((f) => (
            <FilePreviewCard
              key={f.id}
              file={f}
              onRemove={(e) => handleRemove(f.id, e)}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* ═══ Start Verification Button ═══ */}
      <div className="px-4 pb-2">
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleStartVerification}
          disabled={isProcessing || verifying}
          className={cn(
            "w-full relative overflow-hidden rounded-xl px-4 py-3.5 font-semibold text-sm transition-all duration-300",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-psi-electric/50",
            isProcessing || verifying
              ? "bg-psi-graphite border border-psi-border/60 text-psi-text-secondary cursor-wait"
              : "bg-gradient-to-r from-psi-electric via-psi-cyan to-psi-emerald text-white shadow-lg shadow-psi-electric/20 hover:shadow-psi-electric/40 hover:brightness-110",
          )}
        >
          {/* Background glow on hover */}
          {!(isProcessing || verifying) && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0"
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
          )}

          <span className="relative z-10 flex items-center justify-center gap-2.5">
            {isProcessing || verifying ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t("verifying")}</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>{t("startVerification")}</span>
                <Zap className="h-3.5 w-3.5 text-white/60" />
              </>
            )}
          </span>
        </motion.button>
        {!(isProcessing || verifying) && (
          <p className="text-[10px] text-psi-text-secondary/50 text-center mt-1.5">
            {t("startVerificationDesc")}
          </p>
        )}
      </div>

      {/* Hidden input + Add-more bar */}
      <FileInput onFiles={importFiles}>
        {({ open }) =>
          files.length < maxFiles ? (
            <div className="px-4 pb-4 pt-1 border-t border-psi-border flex gap-2">
              <Button variant="outline" size="sm" onClick={open} className="flex-1">
                <Upload className="h-3.5 w-3.5 mr-1.5" />
                {t("uploadDocument")}
              </Button>
              {isConfigured && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDriveUpload}
                  disabled={googleLoading}
                  className="flex-1"
                >
                  {googleLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                  ) : (
                    <FolderOpen className="h-3.5 w-3.5 mr-1" />
                  )}
                  {ta("source.openDrive")}
                </Button>
              )}
            </div>
          ) : null
        }
      </FileInput>

      {/* Error banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mx-4 mb-3 flex items-center gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto hover:text-white">
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════
//  Empty State
// ═══════════════════════════════════════════════════

function EmptyState({
  onFilesSelected,
  onDriveUpload,
  googleLoading,
  googleError,
  isGoogleConfigured,
  error,
  onClearError,
}: {
  onFilesSelected: (files: File[]) => void;
  onDriveUpload: () => void;
  googleLoading: boolean;
  googleError: string | null;
  isGoogleConfigured: boolean;
  error: string | null;
  onClearError: () => void;
}) {
  const t = useTranslations("verification");
  const ta = useTranslations("analysis");
  const tc = useTranslations("common");

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
      {/* Icon */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-psi-electric/10"
      >
        <FileText className="h-8 w-8 text-psi-electric/60" />
      </motion.div>

      {/* Text */}
      <div className="text-center">
        <p className="text-sm font-medium text-psi-text-primary">
          {t("noDocumentTitle")}
        </p>
        <p className="text-xs text-psi-text-secondary mt-1 max-w-[280px]">
          {t("noDocumentDescription")}
        </p>
      </div>

      {/* BUTTONS: Upload + Google Drive */}
      <div className="flex flex-col items-center gap-3">
        {/* Native file upload — uses FileInput render-prop so the <input> is always in DOM */}
        <FileInput onFiles={onFilesSelected}>
          {({ open }) => (
            <Button variant="primary" size="sm" onClick={open}>
              <Upload className="h-3.5 w-3.5 mr-1.5" />
              {t("uploadDocument")}
            </Button>
          )}
        </FileInput>

        {/* Google Drive — single direct button */}
        {isGoogleConfigured && (
          <>
            <span className="text-xs text-psi-text-secondary/50">{tc("or")}</span>

          <button
            onClick={onDriveUpload}
            disabled={googleLoading}
            className="flex items-center gap-2 rounded-lg border border-psi-border/60 bg-psi-graphite/40 px-4 py-2.5 text-sm font-medium text-psi-text-secondary hover:border-psi-electric/40 hover:text-psi-electric hover:bg-psi-electric/[0.04] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {googleLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FolderOpen className="h-4 w-4" />
            )}
            {ta("source.openDrive")}
          </button>
          </>
        )}
      </div>

      {/* Google error */}
      <AnimatePresence>
        {googleError && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud max-w-[280px]"
          >
            <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>{googleError}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Validation error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud max-w-[280px]"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
            <button onClick={onClearError} className="ml-auto hover:text-white">
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════
//  FileInput — render-prop that ensures <input> is
//  always in the DOM so .click() works reliably.
// ═══════════════════════════════════════════════════

function FileInput({
  onFiles,
  children,
}: {
  onFiles: (files: File[]) => void;
  children: (api: { open: () => void }) => React.ReactNode;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const t = useTranslations("verification");

  const open = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const incoming = Array.from(e.target.files ?? []);
      if (incoming.length) onFiles(incoming);
      e.target.value = "";
    },
    [onFiles],
  );

  return (
    <>
      {children({ open })}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        className="hidden"
        onChange={handleChange}
        aria-label={t("uploadDocument")}
      />
    </>
  );
}

// ═══════════════════════════════════════════════════
//  File Preview Card
// ═══════════════════════════════════════════════════

function FilePreviewCard({
  file,
  onRemove,
}: {
  file: UploadedFile;
  onRemove: (e: React.MouseEvent) => void;
}) {
  const isDone = file.status === "done";
  const isError = file.status === "error";
  const isPdf = file.type === "application/pdf";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      className={cn(
        "flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-all",
        isDone ? "border-psi-emerald/30 bg-psi-emerald/5"
          : isError ? "border-psi-fraud/30 bg-psi-fraud/5"
          : "border-psi-border bg-psi-graphite/40",
      )}
    >
      <div className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
        isPdf ? "bg-psi-fraud/10" : "bg-psi-electric/10",
      )}>
        <FileText className={cn("h-4 w-4", isPdf ? "text-psi-fraud" : "text-psi-electric")} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-psi-text-primary truncate">{file.name}</p>
        <p className="text-[11px] text-psi-text-secondary">
          {formatSize(file.size)} &middot; {file.type}
        </p>
        {!isDone && !isError && (
          <div className="mt-1 h-1 w-full rounded-full bg-psi-border/50 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-psi-electric"
              initial={{ width: 0 }}
              animate={{ width: `${file.progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        {isDone && <Check className="h-4 w-4 text-psi-emerald" />}
        {isError && <AlertCircle className="h-4 w-4 text-psi-fraud" />}
        {!isDone && !isError && (
          <span className="text-[11px] text-psi-text-secondary">{Math.round(file.progress)}%</span>
        )}
        <button
          onClick={onRemove}
          className="rounded p-1 text-psi-text-secondary hover:text-psi-fraud hover:bg-psi-fraud/10 transition-colors"
          aria-label={`Remove ${file.name}`}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </motion.div>
  );
}

// ── Helpers ── //

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
