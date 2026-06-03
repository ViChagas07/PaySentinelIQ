"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  HardDrive, FolderOpen, Image, Smartphone, ChevronRight,
  Loader2, AlertCircle, X,
} from "lucide-react";
import { useGooglePicker, type PickedFile, fetchGoogleFileContent } from "@/hooks/useGooglePicker";
import { useAnalysisStore, generateId, type UploadedFile } from "@/stores/analysis-store";

/* ═══════════════════════════════════════════════════
   File Source Selector
   Offers: Device Storage, Google Drive, Google Photos
   ═══════════════════════════════════════════════════ */

type SourceTab = "device" | "drive" | "photos";

export function FileSourceSelector({ onClose }: { onClose?: () => void }) {
  const t = useTranslations("analysis");
  const [activeTab, setActiveTab] = useState<SourceTab>("device");
  const [pickedFiles, setPickedFiles] = useState<PickedFile[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "importing" | "done" | "error">("idle");
  const [statusMsg, setStatusMsg] = useState("");

  const addFile = useAnalysisStore((s) => s.addFile);
  const updateFileProgress = useAnalysisStore((s) => s.updateFileProgress);
  const maxFiles = useAnalysisStore((s) => s.maxFiles);
  const files = useAnalysisStore((s) => s.files);

  const { openPicker, loading: googleLoading, error: googleError, token } = useGooglePicker();

  const sources: { key: SourceTab; label: string; icon: React.ElementType; desc: string }[] = [
    { key: "device", label: t("source.device"), icon: HardDrive, desc: t("source.deviceDesc") },
    { key: "drive", label: t("source.drive"), icon: FolderOpen, desc: t("source.driveDesc") },
    { key: "photos", label: t("source.photos"), icon: Image, desc: t("source.photosDesc") },
  ];

  // Handle device file input
  const handleDeviceFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const incoming = Array.from(e.target.files);
    if (files.length + incoming.length > maxFiles) {
      setStatus("error");
      setStatusMsg(t("upload.maxFilesError", { max: maxFiles }));
      return;
    }
    importDeviceFiles(incoming);
    e.target.value = "";
  };

  const importDeviceFiles = (fileList: File[]) => {
    setStatus("importing");
    fileList.forEach((file, idx) => {
      const id = generateId();
      const uploaded: UploadedFile = {
        id,
        name: file.name,
        size: file.size,
        type: file.type,
        progress: idx === 0 ? 100 : 0,
        status: "pending",
      };
      addFile(uploaded);
      // Simulate upload
      let p = 0;
      const interval = setInterval(() => {
        p += Math.random() * 40;
        if (p >= 100) { p = 100; clearInterval(interval); }
        updateFileProgress(id, Math.min(100, p));
      }, 200);
    });
    setStatus("done");
    setStatusMsg(t("upload.filesAdded", { count: fileList.length }));
    setTimeout(() => onClose?.(), 800);
  };

  // Handle Google Drive pick
  const handleDrivePick = () => {
    setStatus("loading");
    setStatusMsg("");
    openPicker(async (picked) => {
      setPickedFiles(picked);
      setStatus("importing");
      setStatusMsg(t("upload.importingFromGoogle", { count: picked.length }));

      try {
        for (const pf of picked) {
          if (!token) continue;
          const blob = await fetchGoogleFileContent(pf.url, token);
          const file = new File([blob], pf.name, { type: pf.mimeType || "application/pdf" });
          const id = generateId();
          addFile({ id, name: pf.name, size: blob.size, type: pf.mimeType || "application/pdf", progress: 100, status: "done" });
        }
        setStatus("done");
        setStatusMsg(t("upload.importedFromGoogle", { count: picked.length }));
        setTimeout(() => onClose?.(), 1000);
      } catch (err: any) {
        setStatus("error");
        setStatusMsg(err.message || t("upload.failedToImport"));
      }
    });
  };

  // Handle Google Photos pick
  const handlePhotosPick = () => {
    handleDrivePick(); // Same picker, Photos tab is included
  };

  const canAdd = files.length < maxFiles;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      className="space-y-4"
    >
      {/* Source tabs */}
      <div className="grid grid-cols-3 gap-2">
        {sources.map((src) => (
          <button
            key={src.key}
            onClick={() => setActiveTab(src.key)}
            className={cn(
              "flex flex-col items-center gap-2 rounded-xl border p-4 transition-all",
              activeTab === src.key
                ? "border-psi-electric bg-psi-electric/5 text-psi-electric shadow-lg shadow-psi-electric/5"
                : "border-psi-border/60 text-psi-text-secondary hover:border-psi-border hover:bg-psi-border/10"
            )}
          >
            <div className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl transition-colors",
              activeTab === src.key ? "bg-psi-electric/10" : "bg-psi-border/10"
            )}>
              <src.icon className="h-5 w-5" />
            </div>
            <span className="text-xs font-semibold leading-tight">{src.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="rounded-xl border border-psi-border bg-psi-graphite/40 p-4 min-h-[120px]">
        {/* Device tab */}
        {activeTab === "device" && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Smartphone className="h-10 w-10 text-psi-text-secondary mb-3" />
            <p className="text-sm font-medium text-psi-text-primary">{t("source.deviceDesc")}</p>
            <p className="text-xs text-psi-text-secondary mt-1">
              {t("upload.supportedFormats", { maxFiles })}
            </p>
            {canAdd ? (
              <label className="mt-4 inline-flex items-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white cursor-pointer hover:bg-psi-electric/90 transition-colors">
                <HardDrive className="h-4 w-4" />
                {t("source.browseFiles")}
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  multiple
                  className="hidden"
                  onChange={handleDeviceFiles}
                />
              </label>
            ) : (
              <p className="mt-4 text-xs text-psi-text-secondary">{t("upload.maxFilesError", { max: maxFiles })}</p>
            )}
          </div>
        )}

        {/* Google Drive tab */}
        {activeTab === "drive" && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <FolderOpen className="h-10 w-10 text-psi-text-secondary mb-3" />
            <p className="text-sm font-medium text-psi-text-primary">{t("source.driveDesc")}</p>
            <p className="text-xs text-psi-text-secondary mt-1">
              {t("source.driveHint")}
            </p>
            {canAdd ? (
              <button
                onClick={handleDrivePick}
                disabled={googleLoading || status === "loading" || status === "importing"}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white hover:bg-psi-electric/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {googleLoading || status === "loading" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FolderOpen className="h-4 w-4" />
                )}
                {t("source.openDrive")}
              </button>
            ) : (
              <p className="mt-4 text-xs text-psi-text-secondary">{t("upload.maxFilesError", { max: maxFiles })}</p>
            )}
          </div>
        )}

        {/* Google Photos tab */}
        {activeTab === "photos" && (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Image className="h-10 w-10 text-psi-text-secondary mb-3" />
            <p className="text-sm font-medium text-psi-text-primary">{t("source.photosDesc")}</p>
            <p className="text-xs text-psi-text-secondary mt-1">
              {t("source.photosHint")}
            </p>
            {canAdd ? (
              <button
                onClick={handlePhotosPick}
                disabled={googleLoading || status === "loading" || status === "importing"}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white hover:bg-psi-electric/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {googleLoading || status === "loading" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Image className="h-4 w-4" />
                )}
                {t("source.openPhotos")}
              </button>
            ) : (
              <p className="mt-4 text-xs text-psi-text-secondary">{t("upload.maxFilesError", { max: maxFiles })}</p>
            )}
          </div>
        )}
      </div>

      {/* Google error */}
      {googleError && (
        <div className="flex items-start gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud">
          <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{googleError}</span>
        </div>
      )}

      {/* Status */}
      <AnimatePresence>
        {status !== "idle" && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium",
              status === "loading" || status === "importing"
                ? "border border-psi-electric/30 bg-psi-electric/5 text-psi-electric"
                : status === "done"
                ? "border border-psi-emerald/30 bg-psi-emerald/5 text-psi-emerald"
                : "border border-psi-fraud/30 bg-psi-fraud/5 text-psi-fraud"
            )}
          >
            {(status === "loading" || status === "importing") && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            {status === "done" && <ChevronRight className="h-3.5 w-3.5" />}
            {status === "error" && <AlertCircle className="h-3.5 w-3.5" />}
            {statusMsg}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
