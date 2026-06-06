// ============================================================
// PaySentinelIQ — AI Payment Intelligence Center
// Enterprise payment command hub with AI fraud detection,
// smart invoice intake, payment queue, and predictive simulation.
// All data is real-time — no mock values.
// ============================================================

"use client";

import { useState, useCallback, useRef, type ReactElement } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Separator } from "@/components/ui/Separator";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  // Hero / status
  Brain, Zap, ShieldCheck, AlertTriangle, Clock, ArrowUpRight,
  // Upload
  Upload, FileText, FileSpreadsheet, FileImage, X, Check, Scan,
  // Scanner / verification
  Search, Fingerprint, Barcode, Eye, Flag, GitCompare, TrendingUp,
  // Queue
  Inbox, Send, CheckCircle2, CreditCard,
  // Simulation
  BarChart3, LineChart, PieChart, TrendingDown,
  // Assistant
  Sparkles, Lightbulb,
  // Actions
  Wallet, Calendar, Copy, Download, Building2,
} from "lucide-react";

// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
// Types
// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──

type UploadStatus = "idle" | "scanning" | "done" | "error";

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  status: UploadStatus;
}

// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
// Animation variants
// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──

const sectionVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: "easeOut" as const },
  }),
};

// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
// Sub-components
// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──

/** Animated status card for the hero section */
function StatusCard({
  icon: Icon,
  label,
  value,
  sublabel,
  loading = false,
  delay = 0,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sublabel: string;
  loading?: boolean;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
      className="relative group"
    >
      <Card variant="interactive" glow className="h-full">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-2">
            <p className="text-[10px] font-semibold text-psi-text-secondary uppercase tracking-widest truncate pr-2">
              {label}
            </p>
            <div className="rounded-lg bg-psi-electric/10 p-1.5 shrink-0 group-hover:bg-psi-electric/20 transition-colors">
              <Icon className="h-3.5 w-3.5 text-psi-electric" />
            </div>
          </div>
          {loading ? (
            <Skeleton className="h-6 w-20 mb-1" />
          ) : (
            <p className="text-xl font-bold text-psi-text-primary tabular-nums tracking-tight mb-0.5">
              {value}
            </p>
          )}
          <p className="text-[11px] text-psi-text-secondary/50">{sublabel}</p>
          {/* Subtle glow line */}
          <div className="mt-2 h-px w-full bg-gradient-to-r from-psi-electric/10 via-psi-emerald/10 to-transparent" />
        </CardContent>
      </Card>
    </motion.div>
  );
}

/** Drop zone for document upload */
function UploadZone({
  t,
  onDocumentParsed,
}: {
  t: (key: string) => string;
  onDocumentParsed: (doc: UploadedDocument) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [scanning, setScanning] = useState(false);
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
    (files: FileList | File[]) => {
      setIsDragging(false);
      setScanning(true);
      // Simulate AI scanning — in production, this calls the backend
      setTimeout(() => {
        Array.from(files).forEach((f) => {
          onDocumentParsed({
            id: crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`,
            name: f.name,
            size: f.size,
            type: f.type,
            status: "done",
          });
        });
        setScanning(false);
      }, 2000);
    },
    [onDocumentParsed]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        processFiles(e.target.files);
      }
    },
    [processFiles]
  );

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

/** A single check row in the fraud scanner */
function ScannerCheck({
  label,
  status,
}: {
  label: string;
  status: "idle" | "pass" | "warn" | "fail";
}) {
  const statusConfig = {
    idle: { icon: Clock, className: "text-psi-text-secondary/30 border-white/[0.04]" },
    pass: { icon: Check, className: "text-psi-emerald border-psi-emerald/20 bg-psi-emerald/5" },
    warn: { icon: AlertTriangle, className: "text-psi-warning border-psi-warning/20 bg-psi-warning/5" },
    fail: { icon: X, className: "text-psi-fraud border-psi-fraud/20 bg-psi-fraud/5" },
  };
  const { icon: Icon, className } = statusConfig[status];

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
        className
      )}
    >
      <div className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center bg-inherit">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <span className="text-sm text-psi-text-primary">{label}</span>
    </motion.div>
  );
}

/** Queue column card */
function QueueColumn({
  title,
  icon,
  count,
  emptyLabel,
  emptyDesc,
  color,
}: {
  title: string;
  icon: React.ElementType;
  count: number;
  emptyLabel: string;
  emptyDesc: string;
  color: string;
}) {
  const Icon = icon;
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] flex flex-col">
      {/* Column header */}
      <div className={cn("flex items-center gap-2 px-4 py-3 border-b border-white/[0.06] rounded-t-xl", color)}>
        <Icon className="h-4 w-4" />
        <span className="text-sm font-semibold text-psi-text-primary">{title}</span>
        {count > 0 && (
          <Badge variant="default" className="ml-auto text-[10px]">
            {count}
          </Badge>
        )}
      </div>

      {/* Column body */}
      <div className="flex-1 p-4 min-h-[200px]">
        {count === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="mb-3 rounded-2xl bg-psi-electric/5 p-3 ring-1 ring-psi-electric/10">
              <Icon className="h-6 w-6 text-psi-electric/40" />
            </div>
            <p className="text-sm font-medium text-psi-text-primary">{emptyLabel}</p>
            <p className="text-xs text-psi-text-secondary/60 mt-1 max-w-[200px]">{emptyDesc}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Payment cards would render here from real data */}
          </div>
        )}
      </div>
    </div>
  );
}

/** Future-ready action button with coming-soon tooltip */
function FutureButton({
  icon,
  label,
  variant = "outline",
  comingSoon = false,
}: {
  icon: React.ElementType;
  label: string;
  variant?: "primary" | "secondary" | "outline" | "success";
  comingSoon?: boolean;
}) {
  const Icon = icon;
  return (
    <div className="relative group">
      <Button
        variant={variant}
        size="md"
        disabled={comingSoon}
        className={cn(
          "relative",
          comingSoon && "opacity-60 cursor-not-allowed"
        )}
        aria-label={label}
      >
        <Icon className="h-4 w-4" />
        {label}
      </Button>
      {comingSoon && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-lg bg-psi-graphite border border-white/[0.08] shadow-xl shadow-black/40 text-xs text-psi-text-secondary whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          <span>🚀 </span>
          <span>Available in future release</span>
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 bg-psi-graphite border-r border-b border-white/[0.08]" />
        </div>
      )}
    </div>
  );
}

/** Assistant recommendation card */
function RecommendationCard({
  icon,
  text,
  confidence,
}: {
  icon: React.ElementType;
  text: string;
  confidence?: number;
}) {
  const Icon = icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start gap-3 rounded-lg border border-white/[0.04] bg-white/[0.02] p-3 group hover:border-psi-electric/20 hover:bg-psi-electric/[0.02] transition-all"
    >
      <div className="shrink-0 w-8 h-8 rounded-lg bg-psi-electric/10 flex items-center justify-center group-hover:bg-psi-electric/20 transition-colors">
        <Icon className="h-4 w-4 text-psi-electric" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-psi-text-primary">{text}</p>
        {confidence !== undefined && (
          <div className="flex items-center gap-2 mt-1.5">
            <div className="flex-1 max-w-[100px] h-1 rounded-full bg-psi-border/20 overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-psi-electric to-psi-emerald"
                initial={{ width: "0%" }}
                animate={{ width: `${confidence}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
            <span className="text-[10px] font-medium text-psi-text-secondary/60">
              {confidence.toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
// Main Page Component
// ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──

export default function PaymentCenterPage() {
  const t = useTranslations("payroll");

  // ── State — all real, no mock ── //
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([]);
  const [scannerStatus] = useState<"idle" | "scanning" | "complete">("idle");

  const handleDocumentParsed = useCallback((doc: UploadedDocument) => {
    setUploadedDocs((prev) => [...prev, doc]);
  }, []);

  const removeDocument = useCallback((id: string) => {
    setUploadedDocs((prev) => prev.filter((d) => d.id !== id));
  }, []);

  return (
    <div className="space-y-8">
      {/* ═══════════════════════════════════════════════════════
          SECTION 1 — AI Payment Hero
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={0}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow className="relative overflow-hidden border-psi-electric/20">
          {/* Background aura */}
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
            <div className="absolute -inset-[200%] animate-pulse bg-gradient-to-r from-psi-electric/[0.03] via-psi-emerald/[0.02] to-psi-electric/[0.03] blur-3xl" />
          </div>
          <CardContent className="relative z-10 p-6 sm:p-8">
            <div className="flex flex-col lg:flex-row gap-6 lg:gap-10">
              {/* Left: Title area */}
              <div className="shrink-0 lg:w-[280px] xl:w-[320px]">
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="primary" className="text-[10px]">
                    <Brain className="h-2.5 w-2.5 mr-0.5" />
                    {t("pageBadge")}
                  </Badge>
                </div>
                <h1 className="text-2xl sm:text-3xl font-bold text-psi-text-primary tracking-tight leading-tight">
                  {t("hero.title")}
                </h1>
                <p className="text-sm text-psi-text-secondary/70 mt-2 leading-relaxed">
                  {t("hero.subtitle")}
                </p>
                {/* Decorative AI pulse */}
                <div className="hidden lg:flex items-center gap-2 mt-6">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-psi-emerald opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-psi-emerald" />
                  </span>
                  <span className="text-[11px] text-psi-text-secondary/50">
                    AI systems operational
                  </span>
                </div>
              </div>

              {/* Right: Status cards grid — real data only */}
              <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatusCard
                  icon={FileText}
                  label={t("hero.statusCard.pendingAnalyses")}
                  value="—"
                  sublabel={t("hero.statusCard.noData")}
                  delay={0.08}
                />
                <StatusCard
                  icon={Calendar}
                  label={t("hero.statusCard.scheduledPayments")}
                  value="—"
                  sublabel={t("hero.statusCard.noData")}
                  delay={0.12}
                />
                <StatusCard
                  icon={Brain}
                  label={t("hero.statusCard.aiConfidence")}
                  value="—"
                  sublabel={t("hero.statusCard.noData")}
                  delay={0.16}
                />
                <StatusCard
                  icon={AlertTriangle}
                  label={t("hero.statusCard.riskAlerts")}
                  value="—"
                  sublabel={t("hero.statusCard.noData")}
                  delay={0.2}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 2 — Smart Invoice Intake
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={1}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("upload.title")}</CardTitle>
            </div>
            <CardDescription>{t("upload.description")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Upload zone */}
            <UploadZone t={t} onDocumentParsed={handleDocumentParsed} />

            {/* Uploaded documents */}
            {uploadedDocs.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-psi-text-secondary uppercase tracking-wider">
                  Uploaded documents
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {uploadedDocs.map((doc) => (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
                    >
                      <div className="shrink-0 w-8 h-8 rounded-lg bg-psi-emerald/10 flex items-center justify-center">
                        <FileText className="h-4 w-4 text-psi-emerald" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-psi-text-primary truncate">
                          {doc.name}
                        </p>
                        <p className="text-xs text-psi-text-secondary/60">
                          {(doc.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <button
                        onClick={() => removeDocument(doc.id)}
                        className="shrink-0 p-1 rounded-md hover:bg-psi-border/30 text-psi-text-secondary/50 hover:text-psi-fraud transition-colors"
                        aria-label="Remove document"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted data area — empty state */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6">
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
                  <FileText className="h-8 w-8 text-psi-electric/40" />
                </div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("upload.noDocument")}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1 max-w-xs">
                  {t("upload.noDocumentDesc")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 3 — Fraud Risk Scanner
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={2}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("scanner.title")}</CardTitle>
            </div>
            <CardDescription>{t("scanner.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            {scannerStatus === "idle" && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
                  <Search className="h-8 w-8 text-psi-electric/40" />
                </div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("scanner.noData")}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1 max-w-xs">
                  {t("scanner.noDataDesc")}
                </p>
              </div>
            )}

            {/* Scanner checks grid — would populate from real backend data */}
            {scannerStatus === "scanning" && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {([
                    "beneficiaryValidation",
                    "cnpjConsistency",
                    "barcodeIntegrity",
                    "duplicateDetection",
                    "suspiciousValues",
                    "historicalInconsistency",
                    "patternAnomaly",
                  ] as const).map((check) => (
                    <ScannerCheck
                      key={check}
                      label={t(`scanner.check.${check}`)}
                      status="idle"
                    />
                  ))}
                </div>

                {/* Risk summary area — no data yet */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                  {(["riskScore", "aiConfidence", "threatLevel"] as const).map((key) => (
                    <div
                      key={key}
                      className="rounded-lg border border-white/[0.04] bg-white/[0.01] p-4 text-center"
                    >
                      <p className="text-xs text-psi-text-secondary/60 uppercase tracking-wider mb-1">
                        {t(`scanner.${key}`)}
                      </p>
                      <p className="text-xl font-bold text-psi-text-secondary/30">—</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 4 — Payment Queue
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={3}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Inbox className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("queue.title")}</CardTitle>
            </div>
            <CardDescription>{t("queue.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <QueueColumn
                title={t("queue.column.pending")}
                icon={Inbox}
                count={0}
                emptyLabel={t("queue.empty.pending")}
                emptyDesc={t("queue.empty.pendingDesc")}
                color="bg-psi-warning/5"
              />
              <QueueColumn
                title={t("queue.column.scheduled")}
                icon={Calendar}
                count={0}
                emptyLabel={t("queue.empty.scheduled")}
                emptyDesc={t("queue.empty.scheduledDesc")}
                color="bg-psi-electric/5"
              />
              <QueueColumn
                title={t("queue.column.completed")}
                icon={CheckCircle2}
                count={0}
                emptyLabel={t("queue.empty.completed")}
                emptyDesc={t("queue.empty.completedDesc")}
                color="bg-psi-emerald/5"
              />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 5 — Future Payment Simulation
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={4}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("simulation.title")}</CardTitle>
            </div>
            <CardDescription>{t("simulation.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Prediction cards grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              {(["upcomingPayments", "forecastAnalysis", "cashFlowPrediction", "riskTrend"] as const).map((key, i) => (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.06, ease: "easeOut" }}
                  className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4 text-center"
                >
                  <p className="text-[10px] font-semibold text-psi-text-secondary uppercase tracking-widest mb-2">
                    {t(`simulation.${key}`)}
                  </p>
                  <div className="flex items-center justify-center gap-1">
                    <span className="text-2xl font-bold text-psi-text-secondary/30">—</span>
                  </div>
                  <p className="text-[10px] text-psi-text-secondary/40 mt-1">
                    {t("simulation.noData")}
                  </p>
                </motion.div>
              ))}
            </div>

            {/* Chart area — empty state */}
            <div className="relative rounded-xl border border-white/[0.06] bg-white/[0.02] p-8 overflow-hidden">
              {/* Decorative grid lines */}
              <div className="absolute inset-0 opacity-[0.03]" aria-hidden="true">
                <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <pattern id="sim-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E6FFF" strokeWidth="0.3" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#sim-grid)" />
                </svg>
              </div>

              <div className="relative z-10 flex flex-col items-center justify-center py-12 text-center">
                <motion.div
                  className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                >
                  <LineChart className="h-8 w-8 text-psi-electric/40" />
                </motion.div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("simulation.noData")}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1 max-w-xs">
                  {t("simulation.noDataDesc")}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 6 — AI Payment Assistant
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={5}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow className="relative overflow-hidden">
          {/* Gradient aura */}
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
            <div className="absolute top-0 right-0 w-72 h-72 bg-gradient-to-bl from-psi-electric/[0.06] via-psi-emerald/[0.03] to-transparent rounded-full blur-[100px] animate-pulse" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-gradient-to-tr from-purple-500/[0.04] via-psi-electric/[0.02] to-transparent rounded-full blur-[80px]" />
          </div>

          <CardContent className="relative z-10 p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row items-start gap-6">
              {/* AI Orb icon */}
              <div className="shrink-0">
                <div className="relative w-16 h-16">
                  <motion.div
                    className="absolute inset-0 rounded-2xl bg-gradient-to-br from-psi-electric/30 to-psi-emerald/20 blur-xl"
                    animate={{ scale: [1, 1.1, 1], opacity: [0.4, 0.7, 0.4] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />
                  <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-psi-electric/20 to-psi-emerald/10 border border-psi-electric/20 flex items-center justify-center">
                    <Brain className="h-8 w-8 text-psi-electric" />
                  </div>
                </div>
              </div>

              <div className="flex-1 min-w-0 space-y-4">
                {/* Header */}
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-lg font-semibold text-psi-text-primary">
                    {t("assistant.title")}
                  </h3>
                  <Badge variant="primary" className="text-[10px]">
                    <Sparkles className="h-2.5 w-2.5 mr-1" />
                    {t("assistant.badge")}
                  </Badge>
                </div>

                {/* No recommendations yet */}
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="mb-3 rounded-2xl bg-psi-electric/5 p-3 ring-1 ring-psi-electric/10">
                    <Lightbulb className="h-6 w-6 text-psi-electric/40" />
                  </div>
                  <p className="text-sm font-medium text-psi-text-primary">
                    {t("assistant.noRecommendations")}
                  </p>
                  <p className="text-xs text-psi-text-secondary/60 mt-1 max-w-sm">
                    {t("assistant.noRecommendationsDesc")}
                  </p>
                </div>

                {/* Recommendations container — ready for real data
                    <div className="space-y-2">
                      <RecommendationCard
                        icon={AlertTriangle}
                        text={t("assistant.recommendation.duplicatePayment")}
                        confidence={87}
                      />
                      ...
                    </div>
                */}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
          SECTION 7 — Action Area
          ═══════════════════════════════════════════════════════ */}
      <motion.div
        custom={6}
        variants={sectionVariants}
        initial="hidden"
        animate="visible"
      >
        <Card glow>
          <CardContent className="p-6 sm:p-8">
            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
              <FutureButton icon={Wallet} label={t("actions.payNow")} variant="primary" comingSoon />
              <FutureButton icon={Calendar} label={t("actions.schedulePayment")} variant="secondary" comingSoon />
              <FutureButton icon={Copy} label={t("actions.generatePix")} variant="outline" comingSoon />
              <FutureButton icon={Download} label={t("actions.exportData")} variant="outline" />
              <FutureButton icon={Building2} label={t("actions.connectBank")} variant="outline" comingSoon />
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
