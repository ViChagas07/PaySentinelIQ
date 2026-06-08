// ============================================================
// PaySentinelIQ — Security Black Box (Audit Logs)
// Enterprise-grade immutable activity timeline with SIEM-style
// intelligence, AI event tracking, and SOC-inspired UX.
// Shows only real data — displays empty state until events exist.
// ============================================================

"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  Users,
  Radio,
  X,
  Globe,
  DollarSign,
  Clock,
  Copy,
  ChevronDown,
  CheckSquare,
  Fingerprint,
  FileSearch,
  Inbox,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────── //

type DateRangePreset = "today" | "7d" | "30d" | "custom";

// ── Summary stat cards data (all zero until real data flows in) ── //

const STAT_CARDS = [
  { labelKey: "totalEvents", icon: Activity, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
  { labelKey: "highRiskEvents", icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/25" },
  { labelKey: "aiActions", icon: Brain, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
  { labelKey: "userActions", icon: Users, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25" },
  { labelKey: "activeSessions", icon: Radio, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25", pulse: true },
] as const;

// ── Dropdown Component ───────────────────────────────────── //

function FilterDropdown({
  options,
  value,
  onChange,
  className,
}: {
  options: readonly string[];
  value: string;
  onChange: (v: string) => void;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={cn(
          "flex items-center gap-2 rounded-lg border border-psi-border/50 bg-psi-graphite/60 px-3 py-2",
          "text-sm text-psi-text-primary hover:border-psi-electric/30 transition-colors whitespace-nowrap",
          "min-w-[130px] justify-between"
        )}
      >
        <span className="truncate">{value}</span>
        <ChevronDown className={cn("h-3.5 w-3.5 text-psi-text-secondary transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full min-w-[160px] rounded-lg border border-psi-border/50 bg-psi-graphite/95 backdrop-blur-xl p-1 shadow-xl shadow-black/40">
          {options.map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => { onChange(opt); setOpen(false); }}
              className={cn(
                "w-full rounded-md px-3 py-1.5 text-left text-sm transition-colors",
                value === opt
                  ? "bg-psi-electric/15 text-psi-electric"
                  : "text-psi-text-secondary hover:bg-white/[0.04] hover:text-psi-text-primary"
              )}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Date Chip ─────────────────────────────────────────────── //

function DateChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-lg px-3 py-1.5 text-xs font-medium transition-all",
        active
          ? "bg-psi-electric text-white shadow-sm"
          : "bg-psi-border/30 text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary"
      )}
    >
      {label}
    </button>
  );
}

// ── Empty State for Timeline ─────────────────────────────── //

function EmptyTimeline() {
  const t = useTranslations("auditLogs");
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
        <Inbox className="h-10 w-10 text-psi-electric/40" />
      </div>
      <p className="text-sm font-medium text-psi-text-primary mb-1">
        {t("noEvents") || "No events yet"}
      </p>
      <p className="text-xs text-psi-text-secondary max-w-xs">
        {t("emptyTimelineDescription") || "No events have been recorded yet. Timeline will populate as activities occur."}
      </p>
    </div>
  );
}

// ── Empty State for Heatmap ──────────────────────────────── //

function EmptyHeatmap() {
  const t = useTranslations("auditLogs");
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="grid grid-cols-12 gap-0.5 mb-4 opacity-20">
        {Array.from({ length: 84 }).map((_, i) => (
          <div key={i} className="h-2 w-2 rounded-sm bg-psi-border/30" />
        ))}
      </div>
      <p className="text-xs text-psi-text-secondary">
        {t("activityHeatmapEmpty") || "Activity data will appear here over time."}
      </p>
    </div>
  );
}

// ── Animated Counter ─────────────────────────────────────── //

function AnimatedCounter({ value }: { value: number }) {
  const [count, setCount] = useState(0);
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    let start = 0;
    const increment = Math.max(1, Math.floor(value / (1500 / 16)));
    const timer = setInterval(() => {
      start += increment;
      if (start >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(start);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [value]);

  return <>{count.toLocaleString()}</>;
}

// ── Main Page ────────────────────────────────────────────── //

export default function AuditLogsPage() {
  const t = useTranslations("auditLogs");

  // ── Filter State (all default/off) ── //
  const [dateRange, setDateRange] = useState<DateRangePreset>("7d");
  const [aiOnly, setAiOnly] = useState(false);

  // ── All zero — awaiting real data ── //
  const totalEvents = 0;
  const highRiskEvents = 0;
  const aiActionsCount = 0;
  const userActionsCount = 0;
  const activeSessions = 0;

  const summaryCards = useMemo(() => [
    { label: t("totalEvents") || "Total Events", value: totalEvents, icon: Activity, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
    { label: t("highRiskEvents") || "High-Risk Events", value: highRiskEvents, icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/25" },
    { label: t("aiActions") || "AI Actions", value: aiActionsCount, icon: Brain, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
    { label: t("userActions") || "User Actions", value: userActionsCount, icon: Users, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25" },
    { label: t("activeSessions") || "Active Sessions", value: activeSessions, icon: Radio, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25", pulse: false },
  ], [t]);

  // ── Render ── //
  return (
    <div className="relative">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
              {t("pageTitle") || "Security Black Box"}
            </h1>
            <Badge variant="outline" className="text-[10px]">
              {t("pageBadge") || "Immutable"}
            </Badge>
          </div>
          <p className="text-sm text-psi-text-secondary">
            {t("pageDescription") || "Immutable event timeline for audit and forensic analysis."}
          </p>
        </div>
      </motion.div>

      {/* Summary Cards — all show zero / empty */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6 place-items-center">
        {summaryCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07, duration: 0.4 }}
            >
              <Card className="relative overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-medium text-psi-text-secondary uppercase tracking-widest">
                      {stat.label}
                    </span>
                    <div className={cn("rounded-lg p-1.5", stat.bg)}>
                      <Icon className={cn("h-3.5 w-3.5", stat.color)} />
                    </div>
                  </div>
                  <p className={cn("text-2xl font-bold tabular-nums", stat.color)}>
                    {stat.value === 0 ? (
                      <span className="text-psi-text-secondary/30">—</span>
                    ) : (
                      <AnimatedCounter value={stat.value} />
                    )}
                  </p>
                  {stat.pulse && stat.value > 0 && (
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-psi-emerald opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-psi-emerald" />
                      </span>
                      <span className="text-[10px] text-psi-emerald font-medium">{t("live") || "Live"}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Grid Background Pattern (subtle) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10 opacity-[0.03]">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(30, 111, 255, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 111, 255, 0.3) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Timeline — takes 3 cols on desktop */}
        <div className="xl:col-span-3 space-y-6">
          {/* Filtering System */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="overflow-visible">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-psi-text-secondary uppercase tracking-wider mr-1">
                    {t("filters") || "Filters"}
                  </span>
                  <FilterDropdown
                    options={[t("allUsers") || "All Users"]}
                    value={t("allUsers") || "All Users"}
                    onChange={() => {}}
                  />
                  <FilterDropdown
                    options={[t("allEvents") || "All Events"]}
                    value={t("allEvents") || "All Events"}
                    onChange={() => {}}
                  />
                  <FilterDropdown
                    options={[t("allLevels") || "All Levels"]}
                    value={t("allLevels") || "All Levels"}
                    onChange={() => {}}
                  />
                  <FilterDropdown
                    options={[t("all") || "All"]}
                    value={t("all") || "All"}
                    onChange={() => {}}
                  />
                  <div className="flex items-center gap-1">
                    <DateChip label={t("today") || "Today"} active={dateRange === "today"} onClick={() => setDateRange("today")} />
                    <DateChip label={t("last7Days") || "7 Days"} active={dateRange === "7d"} onClick={() => setDateRange("7d")} />
                    <DateChip label={t("last30Days") || "30 Days"} active={dateRange === "30d"} onClick={() => setDateRange("30d")} />
                    <DateChip label={t("custom") || "Custom"} active={dateRange === "custom"} onClick={() => setDateRange("custom")} />
                  </div>
                  <label className="flex items-center gap-1.5 cursor-pointer ml-1">
                    <button
                      type="button"
                      role="checkbox"
                      aria-checked={aiOnly}
                      onClick={() => setAiOnly(!aiOnly)}
                      className={cn(
                        "h-4 w-4 rounded border transition-colors flex items-center justify-center",
                        aiOnly
                          ? "bg-psi-electric border-psi-electric text-white"
                          : "border-psi-border/50 bg-transparent hover:border-psi-electric/40"
                      )}
                    >
                      {aiOnly && <CheckSquare className="h-3 w-3" />}
                    </button>
                    <span className="text-xs text-psi-text-secondary whitespace-nowrap">{t("aiGeneratedOnly") || "AI only"}</span>
                  </label>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Timeline — empty state */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
          >
            <Card glow className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{t("timelineTitle") || "Event Timeline"}</CardTitle>
                    <CardDescription>
                      {t("realtime") || "real-time"}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                <EmptyTimeline />
              </CardContent>
            </Card>
          </motion.div>

          {/* Activity Heatmap — empty state */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <Card glow>
              <CardHeader>
                <CardTitle>{t("activityHeatmap") || "Activity Heatmap"}</CardTitle>
                <CardDescription>{t("activityHeatmapDesc") || "Event frequency over the last 12 weeks"}</CardDescription>
              </CardHeader>
              <CardContent>
                <EmptyHeatmap />
              </CardContent>
            </Card>
          </motion.div>

          {/* Suspicious Patterns — empty state */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>{t("suspiciousPatterns") || "Suspicious Patterns"}</CardTitle>
                <CardDescription>{t("aiDetectedPatterns") || "AI-detected behavioral anomalies requiring attention"}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
                    <Globe className="h-8 w-8 text-psi-electric/40" />
                  </div>
                  <p className="text-sm font-medium text-psi-text-primary mb-1">
                    {t("noPatterns") || "No suspicious patterns detected"}
                  </p>
                  <p className="text-xs text-psi-text-secondary max-w-xs">
                    {t("emptyPatternsDescription") || "No suspicious patterns detected yet. Patterns will appear as the system processes data."}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
