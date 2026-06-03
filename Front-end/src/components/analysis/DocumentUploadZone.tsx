"use client";

import { useState, useCallback, useRef } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Upload, FileText, X, Check, AlertCircle, FileWarning, FolderOpen, ChevronDown } from "lucide-react";
import { useAnalysisStore, generateId, type UploadedFile } from "@/stores/analysis-store";
import { FileSourceSelector } from "@/components/analysis/FileSourceSelector";
import { GoogleDriveUploadButton } from "@/components/analysis/GoogleDriveUploadButton";

const ALLOWED_TYPES = ["application/pdf", "image/png", "image/jpg", "image/jpeg"];
const MAX_SIZE = 20 * 1024 * 1024; // 20MB

const TYPE_LABELS: Record<string, string> = {
  "application/pdf": "application/pdf",
  "image/png": "image/png",
  "image/jpg": "image/jpg",
  "image/jpeg": "image/jpeg",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ═══════════════════════════════════════════════════
   Document Upload Zone
   ═══════════════════════════════════════════════════ */

export function DocumentUploadZone() {
  const t = useTranslations("analysis");
  const tc = useTranslations("common");
  const files = useAnalysisStore((s) => s.files);
  const maxFiles = useAnalysisStore((s) => s.maxFiles);
  const addFile = useAnalysisStore((s) => s.addFile);
  const removeFile = useAnalysisStore((s) => s.removeFile);
  const updateFileProgress = useAnalysisStore((s) => s.updateFileProgress);

  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSourceSelector, setShowSourceSelector] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  const validateAndAdd = useCallback(
    (fileList: FileList | File[]) => {
      setError(null);
      const incoming = Array.from(fileList);

      if (files.length + incoming.length > maxFiles) {
        setError(t("upload.maxFilesError", { max: maxFiles }));
        return;
      }

      for (const file of incoming) {
        if (!ALLOWED_TYPES.includes(file.type)) {
          setError(t("upload.unsupportedType", { name: file.name }));
          return;
        }
        if (file.size > MAX_SIZE) {
          setError(t("upload.fileTooLarge", { name: file.name }));
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
    },
    [files.length, maxFiles, addFile, updateFileProgress, t]
  );

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    dragCounter.current++; setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault(); e.stopPropagation();
      setIsDragging(false); dragCounter.current = 0;
      if (e.dataTransfer.files?.length) validateAndAdd(e.dataTransfer.files);
    },
    [validateAndAdd]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files?.length) validateAndAdd(e.target.files);
      e.target.value = "";
    },
    [validateAndAdd]
  );

  const canUpload = files.length < maxFiles;

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "relative rounded-xl border-2 border-dashed transition-all duration-300 cursor-pointer overflow-hidden",
          isDragging
            ? "border-psi-electric bg-psi-electric/5 scale-[1.02]"
            : canUpload
            ? "border-psi-border/60 hover:border-psi-electric/50 hover:bg-psi-electric/[0.03]"
            : "border-psi-border/30 bg-psi-border/5 cursor-not-allowed"
        )}
        onClick={() => canUpload && inputRef.current?.click()}
        onDragEnter={handleDragEnter}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-gradient-to-br from-psi-electric/10 via-transparent to-psi-electric/5"
          />
        )}

        <div className="flex flex-col items-center justify-center py-10 px-6 text-center relative z-10">
          <motion.div
            animate={isDragging ? { scale: 1.1, y: -4 } : { scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <div
              className={cn(
                "flex h-14 w-14 items-center justify-center rounded-2xl mb-4 transition-all duration-300",
                isDragging
                  ? "bg-psi-electric/20 text-psi-electric shadow-lg shadow-psi-electric/20"
                  : "bg-psi-border/20 text-psi-text-secondary"
              )}
            >
              <Upload className="h-6 w-6" />
            </div>
          </motion.div>

          <p className="text-sm font-semibold text-psi-text-primary">
            {isDragging ? t("upload.dropFiles") : t("upload.dragDrop")}
          </p>
          <p className="mt-1 text-xs text-psi-text-secondary">
            {tc("or")} <span className="text-psi-electric underline underline-offset-2">{t("upload.browseFiles")}</span>
          </p>
          <p className="mt-2 text-[11px] text-psi-text-secondary/60">
            {t("upload.supportedFormats", { maxFiles })}
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          multiple
          className="hidden"
          onChange={handleInputChange}
          aria-label={t("upload.ariaLabel")}
        />
      </motion.div>

      {/* Google Drive quick-action button */}
      {canUpload && (
        <div className="pt-1">
          <div className="relative flex items-center gap-3 mb-3">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-psi-border/40 to-transparent" />
            <span className="text-[11px] font-medium text-psi-text-secondary/60 uppercase tracking-widest">{tc("or")}</span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-psi-border/40 to-transparent" />
          </div>
          <GoogleDriveUploadButton />
        </div>
      )}

      {/* Advanced source selector toggle */}
      {canUpload && (
        <div>
          <button
            onClick={() => setShowSourceSelector(!showSourceSelector)}
            className="flex items-center gap-2 w-full rounded-lg border border-psi-border/60 bg-psi-graphite/40 px-4 py-2.5 text-sm text-psi-text-secondary hover:border-psi-electric/40 hover:text-psi-text-primary transition-all"
          >
            <FolderOpen className="h-4 w-4" />
            <span className="flex-1 text-left">{t("source.title")}</span>
            <motion.span animate={{ rotate: showSourceSelector ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="h-3.5 w-3.5" />
            </motion.span>
          </button>

          <AnimatePresence>
            {showSourceSelector && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="pt-3">
                  <FileSourceSelector onClose={() => setShowSourceSelector(false)} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud"
          >
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto hover:text-white">
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((file) => (
              <FileCard key={file.id} file={file} onRemove={() => removeFile(file.id)} />
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   File Card
   ═══════════════════════════════════════════════════ */

function FileCard({ file, onRemove }: { file: UploadedFile; onRemove: () => void }) {
  const t = useTranslations("analysis");
  const isPdf = file.type === "application/pdf";
  const isDone = file.status === "done";
  const isError = file.status === "error";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      className={cn(
        "flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-all",
        isDone ? "border-psi-emerald/30 bg-psi-emerald/5"
          : isError ? "border-psi-fraud/30 bg-psi-fraud/5"
          : "border-psi-border bg-psi-graphite/40"
      )}
    >
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", isPdf ? "bg-psi-fraud/10" : "bg-psi-electric/10")}>
        {isPdf ? <FileText className="h-4 w-4 text-psi-fraud" /> : <FileWarning className="h-4 w-4 text-psi-electric" />}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-psi-text-primary truncate">{file.name}</p>
        <p className="text-[11px] text-psi-text-secondary">
          {formatSize(file.size)} • {TYPE_LABELS[file.type] || file.type}
        </p>
        {!isDone && !isError && (
          <div className="mt-1 h-1 w-full rounded-full bg-psi-border/50 overflow-hidden">
            <motion.div className="h-full rounded-full bg-psi-electric" initial={{ width: 0 }} animate={{ width: `${file.progress}%` }} transition={{ duration: 0.3 }} />
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {isDone && <Check className="h-4 w-4 text-psi-emerald" />}
        {isError && <AlertCircle className="h-4 w-4 text-psi-fraud" />}
        {!isDone && !isError && <span className="text-[11px] text-psi-text-secondary">{Math.round(file.progress)}%</span>}
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="rounded p-1 text-psi-text-secondary hover:text-psi-fraud hover:bg-psi-fraud/10 transition-colors"
          aria-label={t("upload.removeFile", { name: file.name })}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </motion.div>
  );
}
