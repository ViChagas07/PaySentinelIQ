// ============================================================
// PaySentinelIQ — Product Preview Section
// Fake interactive dashboard preview with glassmorphism styling
// ============================================================

"use client";

import { useRef } from "react";
import { useTranslations } from "next-intl";
import { motion, useInView } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  MoreHorizontal,
  LayoutDashboard,
  ShieldCheck,
  BarChart3,
  Users,
  Settings,
  Bell,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Mock data (static, no API)
// ---------------------------------------------------------------------------

const STAT_CARDS = [
  {
    labelKey: "preview.statPayrolls",
    value: "1,247",
    trend: "up" as const,
    trendValue: "+12.4%",
    iconColor: "text-[#00C48C]",
    bgColor: "bg-[#00C48C]/10",
  },
  {
    labelKey: "preview.statFraud",
    value: "23",
    trend: "down" as const,
    trendValue: "-5",
    iconColor: "text-[#D63B3B]",
    bgColor: "bg-[#D63B3B]/10",
  },
  {
    labelKey: "preview.statConfidence",
    value: "96.4%",
    trend: "up" as const,
    trendValue: "+0.8%",
    iconColor: "text-[#1E6FFF]",
    bgColor: "bg-[#1E6FFF]/10",
    isProgress: true,
  },
];

const CHART_BARS = [
  { label: "Jan", height: 42 },
  { label: "Feb", height: 58 },
  { label: "Mar", height: 73 },
  { label: "Apr", height: 51 },
  { label: "May", height: 88 },
  { label: "Jun", height: 67 },
  { label: "Jul", height: 95 },
  { label: "Aug", height: 62 },
];

const TABLE_ROWS = [
  {
    document: "Payroll_Q2_2026.pdf",
    type: "Payroll",
    riskScore: 2.1,
    status: "verified" as const,
  },
  {
    document: "Invoice_ACME_May.xlsx",
    type: "Invoice",
    riskScore: 8.7,
    status: "flagged" as const,
  },
  {
    document: "Contract_DevOps_2026.doc",
    type: "Document",
    riskScore: 16.3,
    status: "flagged" as const,
  },
  {
    document: "BankSlip_0531_2026.png",
    type: "Bank Slip",
    riskScore: 3.4,
    status: "processing" as const,
  },
];

const SIDEBAR_ICONS = [
  { icon: LayoutDashboard, active: true },
  { icon: ShieldCheck, active: false },
  { icon: BarChart3, active: false },
  { icon: Users, active: false },
  { icon: Bell, active: false },
  { icon: Settings, active: false },
];

// ---------------------------------------------------------------------------
// Animation variants
// ---------------------------------------------------------------------------

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const itemFadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  },
};

const barVariants = {
  hidden: { height: 0 },
  visible: (h: number) => ({
    height: `${h}%`,
    transition: { duration: 0.7, ease: "easeOut" as const, delay: 0.1 },
  }),
};

const rowVariants = {
  hidden: { opacity: 0, x: -12 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: 0.3 + i * 0.1, duration: 0.4, ease: "easeOut" as const },
  }),
};

// ---------------------------------------------------------------------------
// Risk score color helper
// ---------------------------------------------------------------------------

function riskColorClass(score: number) {
  if (score < 5) return "text-[#00C48C]";
  if (score <= 15) return "text-[#FF8C00]";
  return "text-[#D63B3B]";
}

function statusBadge(status: string) {
  const map: Record<string, { labelKey: string; className: string; icon: typeof CheckCircle2 }> = {
    verified: {
      labelKey: "preview.statusVerified",
      className: "text-[#00C48C] bg-[#00C48C]/10 border-[#00C48C]/20",
      icon: CheckCircle2,
    },
    flagged: {
      labelKey: "preview.statusFlagged",
      className: "text-[#D63B3B] bg-[#D63B3B]/10 border-[#D63B3B]/20",
      icon: AlertTriangle,
    },
    processing: {
      labelKey: "preview.statusProcessing",
      className: "text-[#FF8C00] bg-[#FF8C00]/10 border-[#FF8C00]/20",
      icon: Clock,
    },
  };
  return map[status];
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FakeSidebar() {
  return (
    <div className="hidden w-[60px] shrink-0 flex-col items-center gap-5 border-r border-white/[0.05] bg-[#060C1C]/60 py-4 sm:flex">
      {SIDEBAR_ICONS.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-xl transition-colors",
              item.active
                ? "bg-[#1E6FFF]/15 text-[#1E6FFF]"
                : "text-white/25 hover:bg-white/[0.04] hover:text-white/50"
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
        );
      })}
    </div>
  );
}

function StatCards() {
  const t = useTranslations("landing");
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-60px" });

  return (
    <div ref={ref} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {STAT_CARDS.map((card, idx) => (
        <div
          key={idx}
          className={cn(
            "relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.03] p-4 backdrop-blur-sm"
          )}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-white/40">{t(card.labelKey)}</span>
            {card.trend === "up" ? (
              <ArrowUpRight className="h-3.5 w-3.5 text-[#00C48C]" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5 text-[#D63B3B]" />
            )}
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-white">
              {inView ? (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.15, duration: 0.4 }}
                >
                  {card.value}
                </motion.span>
              ) : (
                "—"
              )}
            </span>
            <span
              className={cn(
                "text-xs font-medium",
                card.trend === "up" ? "text-[#00C48C]" : "text-[#D63B3B]"
              )}
            >
              {card.trendValue}
            </span>
          </div>
          {card.isProgress && (
            <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF]"
                initial={{ width: "0%" }}
                animate={inView ? { width: "96.4%" } : { width: "0%" }}
                transition={{ delay: 0.6, duration: 1, ease: "easeOut" }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function FakeChart() {
  const t = useTranslations("landing");
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-60px" });

  return (
    <div
      ref={ref}
      className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 backdrop-blur-sm"
    >
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-medium text-white/50">{t("preview.chartTitle") || "Monthly Analysis Volume"}</span>
        <span className="text-[10px] text-white/25">{t("preview.chartSubtitle") || "Last 8 months"}</span>
      </div>
      <div className="flex items-end justify-between gap-1" style={{ height: 140 }}>
        {CHART_BARS.map((bar, idx) => (
          <div key={idx} className="flex flex-1 flex-col items-center justify-end gap-1.5">
            <motion.div
              className="relative w-full max-w-[28px] overflow-hidden rounded-t-md"
              custom={bar.height}
              initial="hidden"
              animate={inView ? "visible" : "hidden"}
              variants={barVariants}
              style={{ height: inView ? `${bar.height}%` : "0%" }}
            >
              <div className="absolute inset-0 bg-gradient-to-t from-[#1E6FFF] to-[#6A4DFF]" />
              <div className="absolute inset-0 animate-pulse bg-gradient-to-t from-transparent via-white/[0.06] to-transparent" />
            </motion.div>
            <span className="text-[10px] text-white/30">{bar.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function FakeTable() {
  const t = useTranslations("landing");
  const ref = useRef(null);
  const inView = useInView(ref, { margin: "-40px" });

  return (
    <div
      ref={ref}
      className="overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-sm"
    >
      {/* Table header */}
      <div className="grid grid-cols-4 gap-3 border-b border-white/[0.05] px-4 py-2.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-white/30">
          {t("preview.colDocument")}
        </span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-white/30">
          {t("preview.colType")}
        </span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-white/30">
          {t("preview.colRisk")}
        </span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-white/30">
          {t("preview.colStatus")}
        </span>
      </div>

      {/* Table rows */}
      {TABLE_ROWS.map((row, idx) => {
        const badge = statusBadge(row.status);
        const BadgeIcon = badge?.icon;
        return (
          <motion.div
            key={idx}
            custom={idx}
            initial="hidden"
            animate={inView ? "visible" : "hidden"}
            variants={rowVariants}
            className="grid grid-cols-4 items-center gap-3 border-b border-white/[0.03] px-4 py-3 transition-colors hover:bg-white/[0.02]"
          >
            <div className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 shrink-0 text-white/25" />
              <span className="truncate text-xs text-white/80">{row.document}</span>
            </div>
            <span className="text-xs text-white/50">{row.type}</span>
            <span className={cn("text-xs font-semibold", riskColorClass(row.riskScore))}>
              {row.riskScore}%
            </span>
            {badge && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium",
                  badge.className
                )}
              >
                <BadgeIcon className="h-2.5 w-2.5" />
                {t(badge.labelKey)}
              </span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function ProductPreview() {
  const t = useTranslations("landing");
  const sectionRef = useRef(null);
  const inView = useInView(sectionRef, { margin: "-120px" });

  return (
    <section
      id="preview"
      ref={sectionRef}
      className="relative w-full overflow-hidden bg-[#0B1026] py-20 lg:py-28"
    >
      {/* Background gradient overlay */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute left-1/2 top-0 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-b from-[#1E6FFF]/4 via-transparent to-transparent blur-[100px]" />
        <div className="absolute bottom-0 left-0 right-0 h-64 bg-gradient-to-t from-[#050816]/80 to-transparent" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          className="mb-12 text-center lg:mb-16"
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <h2 className="text-3xl font-bold text-white md:text-4xl lg:text-5xl">
            {t("preview.title")}
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-base text-white/40 md:text-lg">
            {t("preview.subtitle")}
          </p>
        </motion.div>

        {/* Dashboard preview frame */}
        <motion.div
          className={cn(
            "relative mx-auto max-w-5xl overflow-hidden rounded-2xl",
            "border border-white/[0.08] bg-[#050816]/80 backdrop-blur-xl shadow-2xl"
          )}
          initial={{ opacity: 0, y: 40, scale: 0.97 }}
          animate={inView ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 40, scale: 0.97 }}
          transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          {/* Breathing glow animation */}
          <motion.div
            className="pointer-events-none absolute inset-0 rounded-2xl"
            animate={{
              boxShadow: [
                "0 0 30px rgba(30,111,255,0.06), inset 0 0 30px rgba(30,111,255,0.02)",
                "0 0 50px rgba(30,111,255,0.12), inset 0 0 50px rgba(30,111,255,0.04)",
                "0 0 30px rgba(30,111,255,0.06), inset 0 0 30px rgba(30,111,255,0.02)",
              ],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          {/* macOS-style top bar */}
          <div className="flex items-center gap-2 border-b border-white/[0.06] bg-[#070D1F]/70 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-[#D63B3B]" />
            <span className="h-3 w-3 rounded-full bg-[#FF8C00]" />
            <span className="h-3 w-3 rounded-full bg-[#00C48C]" />
            <span className="ml-3 text-[10px] font-medium text-white/20">
              PaySentinelIQ — Dashboard
            </span>
            <MoreHorizontal className="ml-auto h-3.5 w-3.5 text-white/15" />
          </div>

          {/* Dashboard body */}
          <div className="flex">
            <FakeSidebar />

            {/* Main content */}
            <div className="flex-1 space-y-4 p-4 sm:p-5">
              <StatCards />
              <FakeChart />
              <FakeTable />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
