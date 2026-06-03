"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  FolderOpen, Loader2, AlertCircle, Check, ExternalLink, LogIn,
} from "lucide-react";
import { useGooglePicker, fetchGoogleFileContent } from "@/hooks/useGooglePicker";
import { useAnalysisStore, generateId } from "@/stores/analysis-store";

/* ═══════════════════════════════════════════════════
   Google Drive Upload Button
   Prominent OAuth-based file picker from Google Drive.
   Uses NEXT_PUBLIC_GOOGLE_CLIENT_ID from .env.local
   ═══════════════════════════════════════════════════ */

export function GoogleDriveUploadButton() {
  const t = useTranslations("analysis");
  const [status, setStatus] = useState<"idle" | "connecting" | "importing" | "done" | "error">("idle");
  const [statusMsg, setStatusMsg] = useState("");
  const [pickedCount, setPickedCount] = useState(0);

  const addFile = useAnalysisStore((s) => s.addFile);
  const maxFiles = useAnalysisStore((s) => s.maxFiles);
  const files = useAnalysisStore((s) => s.files);

  const {
    openPicker,
    loading: googleLoading,
    error: googleError,
    token,
    isConfigured,
  } = useGooglePicker();

  // Keep the latest token in a ref so the picker callback
  // always has access to it (avoids closure staleness).
  const tokenRef = useRef<string | null>(null);
  useEffect(() => { tokenRef.current = token; }, [token]);

  const canUpload = files.length < maxFiles;

  const handleConnect = useCallback(() => {
    if (!canUpload) {
      setStatus("error");
      setStatusMsg(t("upload.maxFilesError", { max: maxFiles }));
      return;
    }

    setStatus("connecting");
    setStatusMsg(t("drive.connecting"));

    openPicker(async (picked) => {
      if (!picked.length) {
        setStatus("idle");
        setStatusMsg("");
        return;
      }

      setPickedCount(picked.length);
      setStatus("importing");
      setStatusMsg(t("drive.importing", { count: picked.length }));

      try {
        let imported = 0;

        // Read token from ref – by the time the user picks files
        // the OAuth flow has completed and the ref is up to date.
        const accessToken = tokenRef.current;

        for (const pf of picked) {
          if (files.length + imported >= maxFiles) {
            setStatusMsg(t("drive.someSkipped", { count: imported }));
            break;
          }

          if (!accessToken) {
            setStatus("error");
            setStatusMsg(t("drive.tokenExpired"));
            return;
          }

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

        setStatus("done");
        setStatusMsg(t("drive.imported", { count: imported }));
        // Reset back to idle after a moment
        setTimeout(() => {
          setStatus("idle");
          setStatusMsg("");
        }, 2500);
      } catch (err: any) {
        setStatus("error");
        setStatusMsg(err.message || t("drive.failedToImport"));
      }
    });
  }, [canUpload, openPicker, addFile, files.length, maxFiles, t]);

  if (!isConfigured) {
    return (
      <div className="rounded-xl border border-psi-fraud/30 bg-psi-fraud/5 px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-psi-fraud">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{t("drive.notConfigured")}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Main button */}
      <motion.button
        onClick={handleConnect}
        disabled={status === "connecting" || status === "importing" || googleLoading}
        whileHover={status === "idle" && canUpload ? { scale: 1.01 } : undefined}
        whileTap={status === "idle" && canUpload ? { scale: 0.99 } : undefined}
        className={cn(
          "relative flex w-full items-center gap-4 overflow-hidden rounded-xl border-2 px-5 py-4 text-left transition-all duration-300",
          status === "idle" && canUpload
            ? "border-psi-border/60 bg-gradient-to-r from-psi-graphite/60 to-psi-graphite/30 hover:border-psi-electric/40 hover:bg-psi-electric/[0.03] cursor-pointer"
            : status === "done"
            ? "border-psi-emerald/30 bg-psi-emerald/5 cursor-default"
            : status === "error"
            ? "border-psi-fraud/30 bg-psi-fraud/5 cursor-default"
            : "border-psi-border/30 bg-psi-border/10 cursor-default opacity-60",
        )}
      >
        {/* Animated background pulse while connecting */}
        {(status === "connecting" || status === "importing") && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-psi-electric/5 via-psi-electric/10 to-psi-electric/5"
            animate={{ x: ["-100%", "100%", "-100%"] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
          />
        )}

        {/* Google Drive icon */}
        <div
          className={cn(
            "relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-xl transition-all",
            status === "idle"
              ? "bg-psi-electric/10 text-psi-electric"
              : status === "done"
              ? "bg-psi-emerald/10 text-psi-emerald"
              : "bg-psi-border/20 text-psi-text-secondary",
          )}
        >
          {status === "idle" && <FolderOpen className="h-6 w-6" />}
          {status === "connecting" && <Loader2 className="h-6 w-6 animate-spin" />}
          {status === "importing" && <Loader2 className="h-6 w-6 animate-spin" />}
          {status === "done" && <Check className="h-6 w-6" />}
          {status === "error" && <AlertCircle className="h-6 w-6" />}
        </div>

        {/* Text content */}
        <div className="relative z-10 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p
              className={cn(
                "text-sm font-semibold transition-colors",
                status === "idle"
                  ? "text-psi-text-primary"
                  : status === "done"
                  ? "text-psi-emerald"
                  : status === "error"
                  ? "text-psi-fraud"
                  : "text-psi-text-secondary",
              )}
            >
              {status === "idle" && t("drive.title")}
              {status === "connecting" && t("drive.connecting")}
              {status === "importing" && t("drive.importing", { count: pickedCount })}
              {status === "done" && t("drive.imported", { count: pickedCount })}
              {status === "error" && t("drive.errorTitle")}
            </p>
            {status === "idle" && (
              <LogIn className="h-3.5 w-3.5 text-psi-electric/60 shrink-0" />
            )}
          </div>
          <p className="mt-0.5 text-xs text-psi-text-secondary/80 leading-relaxed">
            {status === "idle" && t("drive.description")}
            {status === "idle" && !canUpload && (
              <span className="block text-psi-warning text-[11px] mt-0.5">
                {t("upload.maxFilesError", { max: maxFiles })}
              </span>
            )}
            {(status === "connecting" || status === "importing") && (
              <span className="text-psi-electric/70">{t("drive.pleaseWait")}</span>
            )}
            {status === "done" && (
              <span className="text-psi-emerald/70">{t("drive.importSuccess")}</span>
            )}
            {status === "error" && (
              <span className="text-psi-fraud/70">{t("drive.tryAgain")}</span>
            )}
          </p>
        </div>

        {/* Right side indicator */}
        <div className="relative z-10 shrink-0">
          {status === "idle" && (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-psi-electric/10">
              <ExternalLink className="h-4 w-4 text-psi-electric" />
            </div>
          )}
          {(status === "connecting" || status === "importing") && (
            <div className="flex h-8 w-8 items-center justify-center">
              <Loader2 className="h-4 w-4 animate-spin text-psi-electric" />
            </div>
          )}
          {status === "done" && (
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-psi-emerald/20">
              <Check className="h-4 w-4 text-psi-emerald" />
            </div>
          )}
        </div>
      </motion.button>

      {/* Error detail */}
      <AnimatePresence>
        {googleError && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="flex items-start gap-2 rounded-lg border border-psi-fraud/30 bg-psi-fraud/10 px-3 py-2 text-xs text-psi-fraud">
              <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              <span>{googleError}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
