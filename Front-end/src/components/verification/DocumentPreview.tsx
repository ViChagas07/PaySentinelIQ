// ============================================================
// PaySentinelIQ — Document Preview Panel
// Renders a real uploaded document for verification.
// When no document is active, shows a centred empty state
// with file-upload and Google-Drive options.
// ============================================================

"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import {
  FileText, Upload, X, FolderOpen, Loader2, AlertCircle, Check,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useGooglePicker, fetchGoogleFileContent } from "@/hooks/useGooglePicker";
import { useAnalysisStore, generateId, type UploadedFile } from "@/stores/analysis-store";

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
  const tc = useTranslations("common");

  // ── Store integration ──
  const files = useAnalysisStore((s) => s.files);
  const maxFiles = useAnalysisStore((s) => s.maxFiles);
  const addFile = useAnalysisStore((s) => s.addFile);
  const removeFile = useAnalysisStore((s) => s.removeFile);
  const updateFileProgress = useAnalysisStore((s) => s.updateFileProgress);

  // ── Local state ──
  const [error, setError] = useState<string | null>(null);
  const [showDrive, setShowDrive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Google Drive ──
  const {
    openPicker,
    loading: googleLoading,
    error: googleError,
    token,
    isConfigured,
  } = useGooglePicker();

  const tokenRef = useRef<string | null>(null);
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // ── Handlers ──

  /** Trigger native file dialog */
  const triggerFileDialog = useCallback(() => {
    inputRef.current?.click();
  }, []);

  /** Validate incoming file against constraints */
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
    [ta]
  );

  /** Process files from native file input */
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null);
      const incoming = Array.from(e.target.files ?? []);

      if (files.length + incoming.length > maxFiles) {
        setError(ta("upload.maxFilesError", { max: maxFiles }));
        e.target.value = "";
        return;
      }

      for (const file of incoming) {
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
          e.target.value = "";
          return;
        }
      }

      incoming.forEach((file) => {
        const id = generateId();
        const uploaded: UploadedFile = {
          id,
          name: file.name,
          size: file.size,
          type: file.type,
          progress: 0,
          status: "pending",
        };
        addFile(uploaded);

        // Simulate upload progress
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 30;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
          }
          updateFileProgress(id, Math.min(100, progress));
        }, 300);
      });

      e.target.value = "";
    },
    [files.length, maxFiles, addFile, updateFileProgress, validateFile, ta]
  );

  /** Remove a file */
  const handleRemove = useCallback(
    (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      removeFile(id);
    },
    [removeFile]
  );

  /** Trigger Google Drive picker */
  const handleDriveUpload = useCallback(() => {
    if (files.length >= maxFiles) {
      setError(ta("upload.maxFilesError", { max: maxFiles }));
      return;
    }

    openPicker(async (picked) => {
      if (!picked.length) return;

      const accessToken = tokenRef.current;
      if (!accessToken) {
        setError(ta("drive.tokenExpired"));
        return;
      }

      try {
        let imported = 0;
        for (const pf of picked) {
          if (files.length + imported >= maxFiles) break;

          const blob = await fetchGoogleFileContent(pf.url, accessToken);
          const id = generateId();
          addFile({
            id,
            name: pf.name,
            size: blob.size,
            type: pf.mimeType || "application/pdf",
            progress: 100,
            status: "done",
          });
          imported++;
        }
      } catch (err: any) {
        setError(err.message || ta("drive.failedToImport"));
      }
    });
  }, [files.length, maxFiles, openPicker, addFile, ta]);

  const hasContent = files.length > 0;

  if (!hasContent) {
    return (
      <EmptyState
        onUpload={triggerFileDialog}
        onDriveUpload={handleDriveUpload}
        showDrive={showDrive}
        setShowDrive={setShowDrive}
        googleLoading={googleLoading}
        googleError={googleError}
        isGoogleConfigured={isConfigured}
        error={error}
        onClearError={() => setError(null)}
      />
    );
  }

  // ── File thumbnails / preview list ──
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <p className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider">
          {t("uploadedDocuments", { count: files.length })}
        </p>
        <AnimatePresence>
          {files.map((file) => (
            <FilePreviewCard
              key={file.id}
              file={file}
              onRemove={(e) => handleRemove(file.id, e)}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Add more button */}
      {files.length < maxFiles && (
        <div className="px-4 pb-4 pt-1 border-t border-psi-border">
          <Button
            variant="outline"
            size="sm"
            onClick={triggerFileDialog}
            className="w-full"
          >
            <Upload className="h-3.5 w-3.5 mr-1.5" />
            {t("uploadDocument")}
          </Button>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        className="hidden"
        onChange={handleFileChange}
        aria-label={t("uploadDocument")}
      />

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

// ── Empty State ── //

function EmptyState({
  onUpload,
  onDriveUpload,
  showDrive,
  setShowDrive,
  googleLoading,
  googleError,
  isGoogleConfigured,
  error,
  onClearError,
}: {
  onUpload: () => void;
  onDriveUpload: () => void;
  showDrive: boolean;
  setShowDrive: (v: boolean) => void;
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

      {/* Upload button */}
      <Button variant="primary" size="sm" onClick={onUpload}>
        <Upload className="h-3.5 w-3.5 mr-1.5" />
        {t("uploadDocument")}
      </Button>

      {/* Divider + Google Drive option */}
      {isGoogleConfigured && (
        <div className="w-full max-w-[240px] pt-2">
          <div className="relative flex items-center gap-3 mb-2">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-psi-border/40 to-transparent" />
            <span className="text-[10px] font-medium text-psi-text-secondary/50 uppercase tracking-wider">
              {tc("or")}
            </span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-psi-border/40 to-transparent" />
          </div>

          {!showDrive ? (
            <button
              onClick={() => setShowDrive(true)}
              className="flex items-center gap-2 w-full rounded-lg border border-psi-border/60 bg-psi-graphite/30 px-3 py-2 text-sm text-psi-text-secondary hover:border-psi-electric/40 hover:text-psi-text-primary transition-all"
            >
              <FolderOpen className="h-4 w-4 shrink-0" />
              <span className="flex-1 text-left text-xs">{ta("drive.title")}</span>
            </button>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-2"
            >
              <button
                onClick={onDriveUpload}
                disabled={googleLoading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-psi-electric/10 border border-psi-electric/30 px-4 py-2.5 text-sm font-medium text-psi-electric hover:bg-psi-electric/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {googleLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FolderOpen className="h-4 w-4" />
                )}
                {ta("source.openDrive")}
              </button>
              <button
                onClick={() => setShowDrive(false)}
                className="w-full text-xs text-psi-text-secondary/60 hover:text-psi-text-secondary transition-colors"
              >
                {tc("cancel")}
              </button>
            </motion.div>
          )}
        </div>
      )}

      {/* Google config warning */}
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

      {/* Validation / error banner */}
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

// ── File Preview Card (shown when files are uploaded) ── //

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
        isDone
          ? "border-psi-emerald/30 bg-psi-emerald/5"
          : isError
          ? "border-psi-fraud/30 bg-psi-fraud/5"
          : "border-psi-border bg-psi-graphite/40"
      )}
    >
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          isPdf ? "bg-psi-fraud/10" : "bg-psi-electric/10"
        )}
      >
        {isPdf ? (
          <FileText className="h-4 w-4 text-psi-fraud" />
        ) : (
          <FileText className="h-4 w-4 text-psi-electric" />
        )}
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
          <span className="text-[11px] text-psi-text-secondary">
            {Math.round(file.progress)}%
          </span>
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
