// ============================================================
// PaySentinelIQ — Security Black Box (Audit Logs)
// Enterprise-grade immutable activity timeline with SIEM-style
// intelligence, AI event tracking, and SOC-inspired UX.
// ============================================================

"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { useState, useMemo, useRef, useEffect } from "react";
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
  RefreshCw,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { useAuditLogs } from "@/hooks/useApi";
import type { AuditLogEntry } from "@/types";

// ── Types ────────────────────────────────────────────────── //

type DateRangePreset = "today" | "7d" | "30d" | "custom";

// ── Helper Functions ─────────────────────────────────────── //

function getEventIcon(action: string): React.ElementType {
  if (action.includes("ai")) return Brain;
  if (action.startsWith("user.")) return Users;
  if (action.startsWith("fraud.")) return AlertTriangle;
  if (action.startsWith("document.")) return FileSearch;
  if (action.startsWith("payroll.")) return DollarSign;
  if (action.startsWith("compliance.")) return CheckSquare;
  if (action.startsWith("report.")) return Activity;
  return Activity;
}

function getBadgeInfo(action: string): { label: string; variant: "default" | "primary" | "success" | "warning" | "destructive" | "outline" } {
  if (action.startsWith("fraud.")) return { label: "Critical", variant: "destructive" };
  if (action === "document.flagged") return { label: "Flagged", variant: "warning" };
  if (action.includes("verified") || action.includes("approved")) return { label: "Success", variant: "success" };
  if (action.includes("uploaded") || action.startsWith("payroll.")) return { label: "Action", variant: "primary" };
  return { label: "Info", variant: "outline" };
}

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Stat cards data ──────────────────────────────────────── //

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

// ── Loading Skeleton ─────────────────────────────────────── //

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-24 rounded-xl bg-psi-graphite/60 border border-psi-border/20" />
        ))}
      </div>
      <div className="h-12 rounded-xl bg-psi-graphite/60 border border-psi-border/20" />
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-psi-graphite/60 border border-psi-border/20" />
        ))}
      </div>
    </div>
  );
}

// ── Error State ──────────────────────────────────────────── //

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="mb-4 rounded-2xl bg-psi-fraud/10 p-4 ring-1 ring-psi-fraud/20">
        <AlertTriangle className="h-10 w-10 text-psi-fraud" />
      </div>
      <p className="text-sm font-medium text-psi-text-primary mb-1">
        Failed to load audit logs
      </p>
      <p className="text-xs text-psi-text-secondary max-w-xs mb-4">
        {message}
      </p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw className="h-3.5 w-3.5" />
        Retry
      </Button>
    </div>
  );
}

// ── Timeline Item ────────────────────────────────────────── //

function TimelineItem({ entry }: { entry: AuditLogEntry }) {
  const Icon = getEventIcon(entry.action);
  const badge = getBadgeInfo(entry.action);

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="group flex items-start gap-3 py-3 px-4 rounded-lg hover:bg-white/[0.02] transition-colors"
    >
      <div className="rounded-lg p-2 bg-psi-graphite/60 ring-1 ring-psi-border/20 shrink-0">
        <Icon className="h-4 w-4 text-psi-text-secondary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium text-psi-text-primary truncate">
            {entry.action}
          </p>
          <Badge variant={badge.variant} className="shrink-0 text-[10px]">
            {badge.label}
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-0.5">
          <span className="text-xs text-psi-text-secondary">{entry.user_name}</span>
          <span className="text-psi-border/30 text-[10px]">•</span>
          <span className="text-xs text-psi-text-secondary">{formatTimestamp(entry.created_at)}</span>
          <span className="text-psi-border/30 text-[10px]">•</span>
          <span className="text-[10px] text-psi-text-secondary/50 font-mono">{entry.ip_address}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ── Timeline List ────────────────────────────────────────── //

function TimelineList({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) {
    return <EmptyTimeline />;
  }

  return (
    <div className="divide-y divide-psi-border/10">
      <AnimatePresence>
        {entries.map((entry) => (
          <TimelineItem key={entry.id} entry={entry} />
        ))}
      </AnimatePresence>
    </div>
  );
}

// ── Activity Heatmap ─────────────────────────────────────── //

function ActivityHeatmap({ entries }: { entries: AuditLogEntry[] }) {
  const t = useTranslations("auditLogs");

  const { weeks, maxCount } = useMemo(() => {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    const start = new Date(today);
    start.setDate(start.getDate() - 83);
    start.setHours(0, 0, 0, 0);

    const dayCounts: Record<string, number> = {};
    for (let i = 0; i < 84; i++) {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      dayCounts[d.toISOString().split("T")[0]] = 0;
    }
    entries.forEach((e) => {
      const key = e.created_at.split("T")[0];
      if (key in dayCounts) dayCounts[key]++;
    });

    const max = Math.max(...Object.values(dayCounts), 1);

    const weekRows: { date: string; count: number }[][] = [];
    const current: { date: string; count: number }[] = [];
    const cursor = new Date(start);
    while (cursor <= today) {
      const ds = cursor.toISOString().split("T")[0];
      current.push({ date: ds, count: dayCounts[ds] });
      if (cursor.getDay() === 6 || +cursor >= +today) {
        weekRows.push([...current]);
        current.length = 0;
      }
      cursor.setDate(cursor.getDate() + 1);
    }
    if (current.length) weekRows.push(current);

    return { weeks: weekRows, maxCount: max };
  }, [entries]);

  if (weeks.length === 0 || weeks.every((w) => w.every((d) => d.count === 0))) {
    return <EmptyHeatmap />;
  }

  const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  return (
    <div className="space-y-2">
      <div className="flex gap-0.5">
        <div className="flex flex-col gap-0.5 mr-1">
          {dayLabels.map((l) => (
            <div key={l} className="h-3 text-[9px] text-psi-text-secondary/50 leading-3">{l}</div>
          ))}
        </div>
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-0.5">
            {week.map((day) => (
              <div key={day.date} className="relative group">
                <div
                  className={cn(
                    "h-3 w-3 rounded-sm transition-colors",
                    day.count === 0 ? "bg-psi-border/10" :
                    day.count / maxCount < 0.25 ? "bg-psi-electric/20" :
                    day.count / maxCount < 0.5 ? "bg-psi-electric/40" :
                    day.count / maxCount < 0.75 ? "bg-psi-electric/60" :
                    "bg-psi-electric"
                  )}
                />
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10 pointer-events-none">
                  <div className="bg-psi-graphite/95 border border-psi-border/50 rounded px-2 py-1 text-xs text-psi-text-primary whitespace-nowrap shadow-xl backdrop-blur-sm">
                    {day.date}: {day.count} events
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center justify-end gap-1 text-[10px] text-psi-text-secondary">
        <span>{t("less")}</span>
        {[0, 0.25, 0.5, 0.75, 1].map((l) => (
          <div
            key={l}
            className={cn(
              "h-2.5 w-2.5 rounded-sm",
              l === 0 ? "bg-psi-border/10" :
              l <= 0.25 ? "bg-psi-electric/20" :
              l <= 0.5 ? "bg-psi-electric/40" :
              l <= 0.75 ? "bg-psi-electric/60" :
              "bg-psi-electric"
            )}
          />
        ))}
        <span>{t("more")}</span>
      </div>
    </div>
  );
}

// ── Suspicious Patterns List ─────────────────────────────── //

function SuspiciousPatternsList({ entries }: { entries: AuditLogEntry[] }) {
  const t = useTranslations("auditLogs");

  const suspicious = useMemo(
    () => entries.filter((e) => {
      const a = e.action;
      return a.includes("fraud") || a.includes("alert") || a.includes("critical") || a === "document.flagged";
    }),
    [entries]
  );

  if (suspicious.length === 0) {
    return (
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
    );
  }

  return (
    <div className="divide-y divide-psi-border/10">
      <AnimatePresence>
        {suspicious.map((entry) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-start gap-3 py-3 px-4 rounded-lg hover:bg-white/[0.02] transition-colors"
          >
            <div className="rounded-lg p-2 bg-psi-fraud/10 ring-1 ring-psi-fraud/20 shrink-0">
              <AlertTriangle className="h-4 w-4 text-psi-fraud" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-psi-text-primary truncate">{entry.action}</p>
                <Badge variant="destructive" className="shrink-0 text-[10px]">{t("suspicious")}</Badge>
              </div>
              <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-0.5">
                <span className="text-xs text-psi-text-secondary">{entry.user_name}</span>
                <span className="text-psi-border/30 text-[10px]">•</span>
                <span className="text-xs text-psi-text-secondary">{formatTimestamp(entry.created_at)}</span>
              </div>
              {entry.details && Object.keys(entry.details).length > 0 && (
                <p className="text-[10px] text-psi-text-secondary/50 mt-1 truncate">
                  {JSON.stringify(entry.details).slice(0, 120)}
                </p>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────── //

export default function AuditLogsPage() {
  const t = useTranslations("auditLogs");

  // ── Filter State ── //
  const [dateRange, setDateRange] = useState<DateRangePreset>("7d");
  const [aiOnly, setAiOnly] = useState(false);

  // ── API params based on filters ── //
  const apiParams = useMemo(() => {
    const params: Record<string, string> = {};
    const now = new Date();

    if (dateRange === "today") {
      const d = new Date(now);
      d.setHours(0, 0, 0, 0);
      params.created_after = d.toISOString();
    } else if (dateRange === "7d") {
      const d = new Date(now);
      d.setDate(d.getDate() - 7);
      params.created_after = d.toISOString();
    } else if (dateRange === "30d") {
      const d = new Date(now);
      d.setDate(d.getDate() - 30);
      params.created_after = d.toISOString();
    }

    if (aiOnly) {
      params.action__icontains = "ai";
    }

    return params;
  }, [dateRange, aiOnly]);

  const { data, isLoading, error, refetch } = useAuditLogs(apiParams);

  // ── Derived Data ── //
  const items = data?.data ?? [];
  const total = data?.total ?? items.length;

  const stats = useMemo(() => {
    const highRisk = items.filter((i) => i.action.startsWith("fraud.") || i.action === "document.flagged").length;
    const aiCount = items.filter((i) => i.action.includes("ai")).length;
    const uniqueUsers = new Set(items.map((i) => i.user_name)).size;
    const uniqueIps = new Set(items.map((i) => i.ip_address)).size;
    return { total, highRisk, aiCount, uniqueUsers, uniqueIps };
  }, [items, total]);

  const summaryCards = useMemo(() => [
    { label: t("totalEvents") || "Total Events", value: stats.total, icon: Activity, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25", pulse: false },
    { label: t("highRiskEvents") || "High-Risk Events", value: stats.highRisk, icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/25", pulse: false },
    { label: t("aiActions") || "AI Actions", value: stats.aiCount, icon: Brain, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25", pulse: false },
    { label: t("userActions") || "User Actions", value: stats.uniqueUsers, icon: Users, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25", pulse: false },
    { label: t("activeSessions") || "Active Sessions", value: stats.uniqueIps, icon: Radio, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25", pulse: true },
  ], [t, stats]);

  // ── Loading State ── //
  if (isLoading) {
    return (
      <div className="relative">
        <div className="mb-6">
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
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  // ── Error State ── //
  if (error) {
    return (
      <div className="relative">
        <div className="mb-6">
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
        </div>
        <Card>
          <CardContent>
            <ErrorState message={error instanceof Error ? error.message : "An unknown error occurred"} onRetry={() => refetch()} />
          </CardContent>
        </Card>
      </div>
    );
  }

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

      {/* Summary Cards */}
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

          {/* Timeline */}
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
                  {items.length > 0 && (
                    <span className="text-xs text-psi-text-secondary tabular-nums">
                      {items.length} event{items.length !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                <TimelineList entries={items} />
              </CardContent>
            </Card>
          </motion.div>

          {/* Activity Heatmap */}
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
                <ActivityHeatmap entries={items} />
              </CardContent>
            </Card>
          </motion.div>

          {/* Suspicious Patterns */}
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
                <SuspiciousPatternsList entries={items} />
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
