// ============================================================
// PaySentinelIQ — Security Black Box (Audit Logs)
// Enterprise-grade immutable activity timeline with SIEM-style
// intelligence, AI event tracking, and SOC-inspired UX.
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
  Upload,
  Eye,
  FileText,
  LogIn,
  Archive,
  Bell,
  X,
  Globe,
  DollarSign,
  Clock,
  Copy,
  ChevronDown,
  ChevronUp,
  CheckSquare,
  Fingerprint,
  FileSearch,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────── //

type EventType = "login" | "ai" | "upload" | "alert" | "fraud" | "review" | "system";
type RiskLevel = "low" | "medium" | "high" | "critical" | "all";
type DateRangePreset = "today" | "7d" | "30d" | "custom";

interface TimelineEntry {
  id: number;
  time: string;
  title: string;
  type: EventType;
  user?: string;
  ip?: string;
  model?: string;
  score?: number;
  decision?: string;
  reason?: string;
  format?: string;
  regulation?: string;
  details?: string;
  fields?: string;
  document?: string;
  device?: string;
  confidence?: number;
  metadata?: Record<string, string>;
}

interface SidePanelEntry extends TimelineEntry {
  metadata: Record<string, string>;
}

// ── Event Type Configuration ─────────────────────────────── //

const EVENT_TYPE_CONFIG: Record<
  EventType,
  {
    color: string;
    bg: string;
    border: string;
    ring: string;
    icon: React.ElementType;
    badgeVariant: "primary" | "success" | "warning" | "destructive" | "default" | "outline";
    badgeLabel: string;
  }
> = {
  login: {
    color: "text-psi-emerald",
    bg: "bg-psi-emerald/15",
    border: "border-psi-emerald/25",
    ring: "ring-psi-emerald/30",
    icon: LogIn,
    badgeVariant: "success",
    badgeLabel: "Login",
  },
  ai: {
    color: "text-psi-electric",
    bg: "bg-psi-electric/15",
    border: "border-psi-electric/25",
    ring: "ring-psi-electric/30",
    icon: Brain,
    badgeVariant: "primary",
    badgeLabel: "AI Action",
  },
  upload: {
    color: "text-psi-warning",
    bg: "bg-psi-warning/15",
    border: "border-psi-warning/25",
    ring: "ring-psi-warning/30",
    icon: Upload,
    badgeVariant: "warning",
    badgeLabel: "Upload",
  },
  alert: {
    color: "text-psi-warning",
    bg: "bg-psi-warning/15",
    border: "border-psi-warning/25",
    ring: "ring-psi-warning/30",
    icon: Bell,
    badgeVariant: "warning",
    badgeLabel: "Alert",
  },
  fraud: {
    color: "text-psi-fraud",
    bg: "bg-psi-fraud/15",
    border: "border-psi-fraud/25",
    ring: "ring-psi-fraud/30",
    icon: AlertTriangle,
    badgeVariant: "destructive",
    badgeLabel: "Risk",
  },
  review: {
    color: "text-purple-400",
    bg: "bg-purple-500/15",
    border: "border-purple-500/25",
    ring: "ring-purple-500/30",
    icon: Eye,
    badgeVariant: "default",
    badgeLabel: "Review",
  },
  system: {
    color: "text-purple-400",
    bg: "bg-purple-500/15",
    border: "border-purple-500/25",
    ring: "ring-purple-500/30",
    icon: Archive,
    badgeVariant: "outline",
    badgeLabel: "System",
  },
};

// ── Mock Data ────────────────────────────────────────────── //

const MOCK_EVENTS: TimelineEntry[] = [
  { id: 1, time: "22:41", title: "User uploaded document", type: "upload", ip: "192.168.1.45", user: "Alice Johnson", details: "Filename: payroll_q2_2026.pdf", document: "payroll_q2_2026.pdf", device: "Chrome / Windows 11", metadata: { "File Size": "4.2 MB", "Document Type": "Payroll", "Upload Method": "Drag & Drop" } },
  { id: 2, time: "22:42", title: "AI started analysis", type: "ai", model: "FORGE-v4", details: "Analysis ID: A-28472", document: "payroll_q2_2026.pdf", device: "AI Server #3", metadata: { "Model Version": "FORGE-v4", "Analysis Layer": "7-layer verification", "Processing Node": "Node-03" } },
  { id: 3, time: "22:42", title: "OCR completed", type: "ai", details: "47 fields extracted", model: "FORGE-v4", document: "payroll_q2_2026.pdf", fields: "47", metadata: { "Extraction Rate": "99.2%", "Fields Found": "47", "Language": "English" } },
  { id: 4, time: "22:43", title: "Risk detected: High", type: "fraud", score: 87, details: "Risk Score: 87/100", user: "Alice Johnson", document: "payroll_q2_2026.pdf", metadata: { "Risk Threshold": "≥ 75", "Anomaly Type": "Salary Discrepancy", "Department": "Engineering" } },
  { id: 5, time: "22:43", title: "Document classified as suspicious", type: "fraud", reason: "metadata mismatch", details: "Classification: Suspicious", document: "payroll_q2_2026.pdf", metadata: { "Match Rate": "63%", "Expected vs Actual": "Hire date mismatch", "Confidence": "94%" } },
  { id: 6, time: "22:44", title: "Admin reviewed document", type: "review", user: "Dr. Eve", decision: "Flagged", details: "Decision: Flagged for investigation", document: "payroll_q2_2026.pdf", device: "Safari / macOS", metadata: { "Review Duration": "2m 34s", "Reviewer Role": "Security Analyst", "Action": "Flagged + Escalated" } },
  { id: 7, time: "22:45", title: "AI generated fraud report", type: "ai", score: 94, details: "Confidence: 94%", model: "FORGE-v4", document: "payroll_q2_2026.pdf", metadata: { "Report ID": "RPT-28472", "Sections": "Executive Summary, Risk Breakdown, Recommendations", "Processing Time": "1.2s" } },
  { id: 8, time: "22:46", title: "User logged in", type: "login", ip: "10.0.0.25", user: "Bob Smith", device: "Firefox / Linux", metadata: { "Auth Method": "SSO (SAML)", "Session ID": "sess_8f2a1b", "MFA Status": "Passed" } },
  { id: 9, time: "22:47", title: "System auto-archived document", type: "system", details: "Retention policy applied", document: "payroll_q2_2026_archive.pdf", metadata: { "Retention Class": "Regulatory (7 years)", "Archive Location": "us-east-1 / glacier", "Compression": "64% reduction" } },
  { id: 10, time: "22:48", title: "Payment slip analyzed", type: "upload", details: "Result: Legitimate ✓", document: "boleto_48291.pdf", device: "Chrome / Windows 11", metadata: { "Barcode": "34191.23456 78901.234567", "Issuer": "Banco do Brasil", "Amount": "R$ 15.240,00" } },
  { id: 11, time: "22:49", title: "Alert triggered", type: "alert", score: 85, details: "Threshold: 85% — Immediate attention required", metadata: { "Alert Type": "Automated Escalation", "Trigger": "Risk score ≥ 85", "Recipients": "security-team@company.com" } },
  { id: 12, time: "22:50", title: "AI model updated", type: "ai", model: "FORGE-v4.1", details: "Rolling update: v4.0 → v4.1", metadata: { "Update Type": "Hotfix", "Patch Notes": "Improved OCR accuracy +2.3%", "Deployment": "Canary (10% → 100%)" } },
  { id: 13, time: "22:51", title: "User downloaded report", type: "system", user: "Carol Davis", format: "PDF", details: "Format: PDF — 12 pages", document: "fraud_report_28472.pdf", device: "Chrome / macOS", metadata: { "Download Size": "3.8 MB", "Report Type": "Fraud Analysis", "Contains PII": "Yes — redacted" } },
  { id: 14, time: "22:52", title: "Compliance check passed", type: "system", regulation: "SOC 2", details: "All controls satisfied ✓", metadata: { "Framework": "SOC 2 Type II", "Control Set": "CC6, CC7, A1.2", "Next Audit": "2026-12-15" } },
  { id: 15, time: "22:53", title: "Session expired", type: "system", user: "Alice Johnson", details: "Timeout after 30 min inactivity", ip: "192.168.1.45", metadata: { "Session Duration": "2h 14m", "Pages Viewed": "47", "Last Action": "Document upload" } },
];

const MOCK_USERS = ["All Users", "Alice Johnson", "Bob Smith", "Carol Davis", "Dr. Eve"];
const MOCK_EVENT_TYPES = ["All Events", "Login", "Upload", "Analysis", "Alert", "Review", "System"];
const MOCK_RISK_LEVELS: RiskLevel[] = ["all", "low", "medium", "high", "critical"];
const MOCK_STATUSES = ["All", "Completed", "Pending", "Failed"];

// ── Seeded Random for Heatmap ────────────────────────────── //

function seededRandom(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

// ── Animated Counter ─────────────────────────────────────── //

function AnimatedCounter({ value, duration = 1500 }: { value: number; duration?: number }) {
  const [count, setCount] = useState(0);
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;
    let start = 0;
    const increment = Math.max(1, Math.floor(value / (duration / 16)));
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
  }, [value, duration]);

  return <>{count.toLocaleString()}</>;
}

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

function DateChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
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

// ── Heatmap ───────────────────────────────────────────────── //

function ActivityHeatmap() {
  const t = useTranslations("auditLogs");

  const { weeks, monthLabels } = useMemo(() => {
    const rng = seededRandom(28472);
    const today = new Date();
    const days: { count: number; date: Date }[] = [];
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 83);
    const dayOfWeek = startDate.getDay();
    startDate.setDate(startDate.getDate() - dayOfWeek);

    for (let i = 0; i < 84; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const rand = rng();
      let count = 0;
      if (rand > 0.55) count = Math.floor(rng() * 5) + 1;
      if (rand > 0.78) count = Math.floor(rng() * 10) + 6;
      if (rand > 0.92) count = Math.floor(rng() * 15) + 16;
      if (rand > 0.98) count = Math.floor(rng() * 30) + 31;
      days.push({ count, date });
    }

    const weeks: { count: number; date: Date }[][] = [];
    for (let w = 0; w < 12; w++) weeks.push(days.slice(w * 7, (w + 1) * 7));

    const months: { label: string; span: number }[] = [];
    let currentMonth = -1;
    let monthStart = 0;
    for (let w = 0; w < 12; w++) {
      const d = weeks[w][0]?.date;
      if (d) {
        const m = d.getMonth();
        if (m !== currentMonth) {
          if (currentMonth !== -1) months.push({ label: "", span: w - monthStart });
          currentMonth = m;
          monthStart = w;
        }
      }
    }
    if (currentMonth !== -1) months.push({ label: "", span: 12 - monthStart });

    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const dayLabels = ["Mon", "", "Wed", "", "Fri", "", ""];

    const labelRanges: { label: string; colStart: number; colSpan: number }[] = [];
    let mi = 0;
    while (mi < 12) {
      const d = weeks[mi]?.[0]?.date;
      if (!d) { mi++; continue; }
      const mn = monthNames[d.getMonth()];
      let span = 1;
      while (mi + span < 12 && weeks[mi + span]?.[0]?.date?.getMonth() === d.getMonth()) span++;
      labelRanges.push({ label: mn, colStart: mi + 1, colSpan: span });
      mi += span;
    }

    return { weeks, monthLabels: labelRanges, dayLabels };
  }, []);

  const [tooltip, setTooltip] = useState<{ count: number; date: string; x: number; y: number } | null>(null);

  const colorForCount = (count: number) => {
    if (count === 0) return "bg-psi-border/10 border border-psi-border/20";
    if (count <= 5) return "bg-psi-electric/20 border border-psi-electric/30";
    if (count <= 15) return "bg-psi-electric/40 border border-psi-electric/50";
    if (count <= 30) return "bg-psi-electric/70 border border-psi-electric/80";
    return "bg-psi-electric border border-psi-electric shadow-sm shadow-psi-electric/40";
  };

  return (
    <Card glow>
      <CardHeader>
        <CardTitle>{t("activityHeatmap") || "Activity Heatmap"}</CardTitle>
        <CardDescription>{t("activityHeatmapDesc") || "Event frequency over the last 12 weeks"}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto pb-2">
          <div className="min-w-[560px]">
            <div className="flex gap-0.5 mb-1 ml-8">
              {monthLabels.map((m, i) => (
                <div
                  key={i}
                  className="text-[10px] font-medium text-psi-text-secondary"
                  style={{ minWidth: `${m.colSpan * 14 + (m.colSpan - 1) * 2}px` }}
                >
                  {m.label}
                </div>
              ))}
            </div>
            <div className="flex gap-0.5">
              <div className="flex flex-col gap-0.5 mr-1.5 pt-[1px]">
                {["Mon", "", "Wed", "", "Fri", "", ""].map((d, i) => (
                  <div key={i} className="h-3 flex items-center">
                    <span className="text-[9px] text-psi-text-secondary leading-none">{d}</span>
                  </div>
                ))}
              </div>
              {weeks.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-0.5">
                  {week.map((day, di) => (
                    <div
                      key={di}
                      className={cn(
                        "h-3 w-3 rounded-[3px] cursor-pointer transition-all duration-150 hover:scale-150 hover:z-10 relative",
                        colorForCount(day.count)
                      )}
                      onMouseEnter={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        setTooltip({
                          count: day.count,
                          date: day.date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                          x: rect.left + rect.width / 2,
                          y: rect.top - 8,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  ))}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-1.5 mt-2 ml-8">
              <span className="text-[10px] text-psi-text-secondary">{t("less") || "Less"}</span>
              {[0, 1, 6, 16, 31].map((v, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-2.5 w-2.5 rounded-sm",
                    v === 0 ? "bg-psi-border/10 border border-psi-border/20" :
                    v <= 5 ? "bg-psi-electric/20 border border-psi-electric/30" :
                    v <= 15 ? "bg-psi-electric/40 border border-psi-electric/50" :
                    v <= 30 ? "bg-psi-electric/70 border border-psi-electric/80" :
                    "bg-psi-electric border border-psi-electric shadow-sm shadow-psi-electric/40"
                  )}
                />
              ))}
              <span className="text-[10px] text-psi-text-secondary">{t("more") || "More"}</span>
            </div>
          </div>
        </div>
        {tooltip && (
          <div
            className="fixed z-[100] px-2 py-1 rounded-md bg-psi-graphite/95 backdrop-blur-xl border border-psi-border/50 text-xs text-psi-text-primary shadow-xl pointer-events-none whitespace-nowrap"
            style={{ left: tooltip.x, top: tooltip.y, transform: "translate(-50%, -100%)" }}
          >
            {tooltip.count} {t("events") || "events"} — {tooltip.date}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Suspicious Patterns Card ─────────────────────────────── //

function SuspiciousPatternCard({
  icon: Icon,
  title,
  description,
  badge,
  badgeVariant,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  badge: string;
  badgeVariant: "destructive" | "warning" | "primary";
}) {
  return (
    <motion.div
      whileHover={{ y: -3, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="h-full"
    >
      <Card variant="interactive" glow className="h-full">
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            <div className={cn(
              "rounded-xl p-2.5 shrink-0",
              badgeVariant === "destructive" ? "bg-psi-fraud/15 text-psi-fraud" :
              badgeVariant === "warning" ? "bg-psi-warning/15 text-psi-warning" :
              "bg-psi-electric/15 text-psi-electric"
            )}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-psi-text-primary mb-1">{title}</h4>
              <p className="text-xs text-psi-text-secondary leading-relaxed mb-3">{description}</p>
              <Badge variant={badgeVariant} dot>{badge}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Main Page ────────────────────────────────────────────── //

export default function AuditLogsPage() {
  const t = useTranslations("auditLogs");

  // ── Filter State ── //
  const [userFilter, setUserFilter] = useState("All Users");
  const [eventTypeFilter, setEventTypeFilter] = useState("All Events");
  const [riskLevelFilter, setRiskLevelFilter] = useState<string>("All Levels");
  const [dateRange, setDateRange] = useState<DateRangePreset>("7d");
  const [statusFilter, setStatusFilter] = useState("All");
  const [aiOnly, setAiOnly] = useState(false);

  // ── Timeline State ── //
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<SidePanelEntry | null>(null);
  const [copied, setCopied] = useState(false);

  // ── Filter Logic ── //
  const filteredEvents = useMemo(() => {
    return MOCK_EVENTS.filter((e) => {
      if (userFilter !== "All Users" && e.user !== userFilter) return false;
      if (eventTypeFilter !== "All Events") {
        const typeMap: Record<string, EventType[]> = {
          "Login": ["login"],
          "Upload": ["upload"],
          "Analysis": ["ai"],
          "Alert": ["alert"],
          "Review": ["review"],
          "System": ["system"],
        };
        const matched = typeMap[eventTypeFilter];
        if (matched && !matched.includes(e.type)) return false;
        if (!matched) return false;
      }
      if (riskLevelFilter !== "All Levels") {
        if (e.type === "fraud" || e.score) {
          const score = e.score ?? 0;
          if (riskLevelFilter === "Low" && (score < 1 || score > 30)) return false;
          if (riskLevelFilter === "Medium" && (score < 31 || score > 60)) return false;
          if (riskLevelFilter === "High" && (score < 61 || score > 85)) return false;
          if (riskLevelFilter === "Critical" && score < 86) return false;
        } else if (riskLevelFilter !== "All Levels") {
          return false;
        }
      }
      if (aiOnly && e.type !== "ai") return false;
      return true;
    });
  }, [userFilter, eventTypeFilter, riskLevelFilter, aiOnly]);

  // ── Summary Stats ── //
  const totalEvents = useMemo(() => MOCK_EVENTS.length, []);
  const highRiskEvents = useMemo(() => MOCK_EVENTS.filter((e) => e.type === "fraud" || (e.score ?? 0) >= 85).length, []);
  const aiActions = useMemo(() => MOCK_EVENTS.filter((e) => e.type === "ai").length, []);
  const userActions = useMemo(() => MOCK_EVENTS.filter((e) => e.type === "login" || e.type === "upload" || e.type === "review").length, []);
  const activeSessions = 47;

  const summaryCards = useMemo(() => [
    { label: t("totalEvents") || "Total Events", value: totalEvents, icon: Activity, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
    { label: t("highRiskEvents") || "High-Risk Events", value: highRiskEvents, icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/25" },
    { label: t("aiActions") || "AI Actions", value: aiActions, icon: Brain, color: "text-psi-electric", bg: "bg-psi-electric/10", border: "border-psi-electric/25" },
    { label: t("userActions") || "User Actions", value: userActions, icon: Users, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25" },
    { label: t("activeSessions") || "Active Sessions", value: activeSessions, icon: Radio, color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/25", pulse: true },
  ], [t, totalEvents, highRiskEvents, aiActions, userActions]);

  // ── Handlers ── //
  const handleEntryClick = useCallback((entry: TimelineEntry) => {
    setSelectedEntry({
      ...entry,
      metadata: entry.metadata ?? {},
    });
  }, []);

  const handleCopyIp = useCallback(async (ip: string) => {
    try {
      await navigator.clipboard.writeText(ip);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* ignore */ }
  }, []);

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
            <Badge variant="primary" dot>{t("pageBadge") || "Immutable"}</Badge>
          </div>
          <p className="text-sm text-psi-text-secondary">
            {t("pageDescription") || "Immutable activity timeline tracking user actions, AI decisions, analyst reviews, and system events."}
          </p>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
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
                    <AnimatedCounter value={stat.value} />
                  </p>
                  {stat.pulse && (
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
                    options={MOCK_USERS}
                    value={userFilter}
                    onChange={setUserFilter}
                  />
                  <FilterDropdown
                    options={MOCK_EVENT_TYPES}
                    value={eventTypeFilter}
                    onChange={setEventTypeFilter}
                  />
                  <FilterDropdown
                    options={MOCK_RISK_LEVELS.map((r) => r === "all" ? "All Levels" : r.charAt(0).toUpperCase() + r.slice(1))}
                    value={riskLevelFilter}
                    onChange={setRiskLevelFilter}
                  />
                  <FilterDropdown
                    options={MOCK_STATUSES}
                    value={statusFilter}
                    onChange={setStatusFilter}
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
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setUserFilter("All Users");
                      setEventTypeFilter("All Events");
                      setRiskLevelFilter("All Levels");
                      setDateRange("7d");
                      setStatusFilter("All");
                      setAiOnly(false);
                    }}
                    className="text-xs"
                  >
                    {t("clearFilters") || "Clear"}
                  </Button>
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
                      {filteredEvents.length} {t("events") || "events"} — {t("realtime") || "real-time"}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="primary" dot>
                      {t("live") || "Live"}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                <div className="relative">
                  {/* Vertical timeline line */}
                  <div className="absolute left-[68px] top-2 bottom-2 w-px bg-gradient-to-b from-psi-electric/40 via-psi-electric/20 to-transparent" />

                  {filteredEvents.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                      <FileSearch className="h-10 w-10 text-psi-text-secondary/40 mb-3" />
                      <p className="text-sm text-psi-text-secondary">{t("noEvents") || "No events match your filters"}</p>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2"
                        onClick={() => {
                          setUserFilter("All Users");
                          setEventTypeFilter("All Events");
                          setRiskLevelFilter("All Levels");
                          setDateRange("7d");
                          setStatusFilter("All");
                          setAiOnly(false);
                        }}
                      >
                        {t("clearFilters") || "Clear Filters"}
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-0">
                      {filteredEvents.map((entry, i) => {
                        const cfg = EVENT_TYPE_CONFIG[entry.type];
                        const Icon = cfg.icon;
                        const isExpanded = expandedId === entry.id;

                        return (
                          <motion.div
                            key={entry.id}
                            initial={{ opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.03 }}
                            className="relative flex gap-4 pb-5 last:pb-0 group"
                          >
                            {/* Time */}
                            <div className="w-14 pt-1.5 shrink-0 text-right">
                              <span className="font-mono text-[11px] text-psi-text-secondary/60 leading-none">
                                {entry.time}
                              </span>
                            </div>

                            {/* Dot */}
                            <div className="relative flex items-start pt-[5px] shrink-0">
                              <div
                                className={cn(
                                  "w-2.5 h-2.5 rounded-full z-10 ring-[3px] transition-all duration-300",
                                  cfg.bg,
                                  cfg.ring
                                )}
                              />
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                              <motion.div
                                whileHover={{ y: -1 }}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                              >
                                <Card
                                  variant="interactive"
                                  className={cn(
                                    "cursor-pointer transition-all duration-200",
                                    selectedEntry?.id === entry.id && "border-psi-electric/40"
                                  )}
                                  onClick={() => handleEntryClick(entry)}
                                >
                                  <CardContent
                                    className="p-3.5"
                                    onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                                  >
                                    <div className="flex items-start gap-3">
                                      {/* Event Icon */}
                                      <div className={cn(
                                        "rounded-lg p-2 shrink-0 mt-0.5",
                                        cfg.bg,
                                        cfg.color
                                      )}>
                                        <Icon className="h-4 w-4" />
                                      </div>

                                      {/* Event Body */}
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between gap-2">
                                          <div className="min-w-0">
                                            <h4 className="text-sm font-semibold text-psi-text-primary leading-tight">
                                              {entry.title}
                                            </h4>
                                            <p className="text-xs text-psi-text-secondary mt-0.5 truncate max-w-md">
                                              {entry.details}
                                              {entry.user && <span className="ml-1.5">— {entry.user}</span>}
                                              {entry.ip && <span className="ml-1.5 font-mono text-[10px] opacity-70">{entry.ip}</span>}
                                            </p>
                                          </div>
                                          <Badge variant={cfg.badgeVariant} className="shrink-0 text-[10px]">
                                            {cfg.badgeLabel}
                                          </Badge>
                                        </div>

                                        {/* Expanded Details */}
                                        <AnimatePresence>
                                          {isExpanded && (
                                            <motion.div
                                              initial={{ height: 0, opacity: 0 }}
                                              animate={{ height: "auto", opacity: 1 }}
                                              exit={{ height: 0, opacity: 0 }}
                                              transition={{ duration: 0.2 }}
                                              className="overflow-hidden"
                                            >
                                              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 pt-2 border-t border-psi-border/30">
                                                {entry.ip && (
                                                  <div className="flex items-center gap-1.5">
                                                    <Fingerprint className="h-3 w-3 text-psi-text-secondary/50" />
                                                    <span className="text-[11px] text-psi-text-secondary font-mono">{entry.ip}</span>
                                                  </div>
                                                )}
                                                {entry.model && (
                                                  <div className="flex items-center gap-1.5">
                                                    <Brain className="h-3 w-3 text-psi-text-secondary/50" />
                                                    <span className="text-[11px] text-psi-text-secondary">{entry.model}</span>
                                                  </div>
                                                )}
                                                {entry.score !== undefined && (
                                                  <div className="flex items-center gap-1.5">
                                                    <AlertTriangle className="h-3 w-3 text-psi-text-secondary/50" />
                                                    <span className="text-[11px] text-psi-text-secondary">
                                                      {t("riskScore") || "Score"}: {entry.score}/100
                                                    </span>
                                                  </div>
                                                )}
                                                {entry.decision && (
                                                  <div className="flex items-center gap-1.5">
                                                    <Eye className="h-3 w-3 text-psi-text-secondary/50" />
                                                    <span className="text-[11px] text-psi-fraud font-medium">{entry.decision}</span>
                                                  </div>
                                                )}
                                                {entry.document && (
                                                  <div className="flex items-center gap-1.5">
                                                    <FileText className="h-3 w-3 text-psi-text-secondary/50" />
                                                    <span className="text-[11px] text-psi-text-secondary truncate max-w-[150px]">{entry.document}</span>
                                                  </div>
                                                )}
                                              </div>
                                            </motion.div>
                                          )}
                                        </AnimatePresence>
                                      </div>

                                      {/* Expand indicator */}
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setExpandedId(isExpanded ? null : entry.id);
                                        }}
                                        className="shrink-0 p-0.5 rounded text-psi-text-secondary/40 hover:text-psi-text-primary transition-colors"
                                      >
                                        {isExpanded ? (
                                          <ChevronUp className="h-3.5 w-3.5" />
                                        ) : (
                                          <ChevronDown className="h-3.5 w-3.5" />
                                        )}
                                      </button>
                                    </div>
                                  </CardContent>
                                </Card>
                              </motion.div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Activity Heatmap */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
          >
            <ActivityHeatmap />
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
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <SuspiciousPatternCard
                    icon={Globe}
                    title={t("patternRepeatedIp") || "Repeated Uploads from Same IP"}
                    description={t("patternRepeatedIpDesc") || "IP 192.168.1.45 uploaded 12 documents in 3 minutes. Possible automated scraping."}
                    badge={t("highConfidence") || "High Confidence"}
                    badgeVariant="destructive"
                  />
                  <SuspiciousPatternCard
                    icon={DollarSign}
                    title={t("patternPayrollAnomalies") || "Multiple Payroll Anomalies"}
                    description={t("patternPayrollAnomaliesDesc") || "3 payroll files show overtime inconsistencies in the same department. Cross-reference recommended."}
                    badge={t("mediumConfidence") || "Medium Confidence"}
                    badgeVariant="warning"
                  />
                  <SuspiciousPatternCard
                    icon={Clock}
                    title={t("patternUnusualFrequency") || "Unusual Upload Frequency"}
                    description={t("patternUnusualFrequencyDesc") || "Upload activity peaked at 3:00 AM (2.4x daily average). Possible off-hours data extraction."}
                    badge={t("aiFlagged") || "AI Flagged"}
                    badgeVariant="primary"
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Side Panel Column (desktop) */}
        <div className="hidden xl:block xl:col-span-1 relative">
          <AnimatePresence>
            {selectedEntry && (
              <motion.div
                key={selectedEntry.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="sticky top-6"
              >
                <EventDetailPanel
                  entry={selectedEntry}
                  onClose={() => setSelectedEntry(null)}
                  onCopyIp={handleCopyIp}
                  copied={copied}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Mobile Side Panel (overlay) */}
        <AnimatePresence>
          {selectedEntry && (
            <motion.div
              key="mobile-panel-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm xl:hidden"
              onClick={() => setSelectedEntry(null)}
            >
              <motion.div
                key="mobile-panel"
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-psi-graphite/95 backdrop-blur-2xl border-l border-psi-border/50 shadow-2xl overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <EventDetailPanel
                  entry={selectedEntry}
                  onClose={() => setSelectedEntry(null)}
                  onCopyIp={handleCopyIp}
                  copied={copied}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── Side Panel (Event Detail) ────────────────────────────── //

function EventDetailPanel({
  entry,
  onClose,
  onCopyIp,
  copied,
}: {
  entry: SidePanelEntry;
  onClose: () => void;
  onCopyIp: (ip: string) => void;
  copied: boolean;
}) {
  const t = useTranslations("auditLogs");
  const cfg = EVENT_TYPE_CONFIG[entry.type];
  const Icon = cfg.icon;

  const riskLabel = entry.score !== undefined
    ? entry.score >= 85 ? "Critical"
      : entry.score >= 61 ? "High"
        : entry.score >= 31 ? "Medium"
          : "Low"
    : null;

  const riskColor = riskLabel === "Critical" || riskLabel === "High"
    ? "bg-psi-fraud"
    : riskLabel === "Medium"
      ? "bg-psi-warning"
      : "bg-psi-emerald";

  return (
    <div className="p-5">
      {/* Close Button */}
      <div className="flex items-center justify-between mb-5">
        <Badge variant={cfg.badgeVariant} dot>{cfg.badgeLabel}</Badge>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-psi-text-secondary hover:text-psi-text-primary hover:bg-psi-border/30 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Event Title */}
      <div className="flex items-start gap-3 mb-5">
        <div className={cn("rounded-xl p-3", cfg.bg, cfg.color)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-bold text-psi-text-primary leading-tight">{entry.title}</h3>
          <p className="text-xs text-psi-text-secondary mt-0.5">{entry.time} UTC</p>
        </div>
      </div>

      {/* User with avatar */}
      {entry.user && (
        <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-psi-border/10 border border-psi-border/20">
          <div className="h-9 w-9 rounded-full bg-psi-electric/20 flex items-center justify-center text-psi-electric font-bold text-sm shrink-0">
            {entry.user.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-psi-text-primary">{entry.user}</p>
            <p className="text-[11px] text-psi-text-secondary">{t("userLabel") || "User"}</p>
          </div>
        </div>
      )}

      {/* Detail Fields */}
      <div className="space-y-3">
        {entry.ip && (
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-psi-border/5 border border-psi-border/10">
            <div className="flex items-center gap-2">
              <Fingerprint className="h-3.5 w-3.5 text-psi-text-secondary/50" />
              <span className="text-xs text-psi-text-secondary">{t("ipAddress") || "IP Address"}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-mono text-psi-text-primary">{entry.ip}</span>
              <button
                type="button"
                onClick={() => onCopyIp(entry.ip!)}
                className="p-1 rounded text-psi-text-secondary/50 hover:text-psi-electric transition-colors"
                title={t("copy") || "Copy"}
              >
                {copied ? (
                  <span className="text-[10px] text-psi-emerald">{t("copied") || "Copied!"}</span>
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </button>
            </div>
          </div>
        )}

        {entry.device && (
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-psi-border/5 border border-psi-border/10">
            <span className="text-xs text-psi-text-secondary">{t("device") || "Device"}</span>
            <span className="text-xs text-psi-text-primary">{entry.device}</span>
          </div>
        )}

        {entry.document && (
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-psi-border/5 border border-psi-border/10">
            <span className="text-xs text-psi-text-secondary">{t("document") || "Document"}</span>
            <span className="text-xs text-psi-text-primary truncate max-w-[160px] text-right">{entry.document}</span>
          </div>
        )}

        {entry.model && (
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-psi-border/5 border border-psi-border/10">
            <span className="text-xs text-psi-text-secondary">{t("aiModel") || "AI Model"}</span>
            <Badge variant="primary" className="text-[10px]">{entry.model}</Badge>
          </div>
        )}

        {/* Risk Score */}
        {entry.score !== undefined && (
          <div className="p-3 rounded-lg bg-psi-border/5 border border-psi-border/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-psi-text-secondary">{t("riskScore") || "Risk Score"}</span>
              <span className={cn("text-sm font-bold tabular-nums", riskLabel === "Critical" || riskLabel === "High" ? "text-psi-fraud" : riskLabel === "Medium" ? "text-psi-warning" : "text-psi-emerald")}>
                {entry.score}/100
              </span>
            </div>
            <div className="h-2 rounded-full bg-psi-border/20 overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all duration-500", riskColor)}
                style={{ width: `${entry.score}%` }}
              />
            </div>
            {riskLabel && (
              <p className="text-[10px] text-psi-text-secondary mt-1.5">
                {t("riskLevel") || "Risk Level"}: {riskLabel}
              </p>
            )}
          </div>
        )}

        {/* AI Reasoning */}
        {entry.reason && (
          <div className="p-3 rounded-lg bg-psi-electric/5 border border-psi-electric/15">
            <div className="flex items-center gap-2 mb-1.5">
              <Brain className="h-3.5 w-3.5 text-psi-electric" />
              <span className="text-xs font-medium text-psi-electric">{t("reasoning") || "AI Reasoning"}</span>
            </div>
            <p className="text-xs text-psi-text-secondary leading-relaxed">{entry.reason}</p>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-psi-border/5 border border-psi-border/10">
          <span className="text-xs text-psi-text-secondary">{t("timestamp") || "Timestamp"}</span>
          <span className="text-xs font-mono text-psi-text-primary">2026-06-05 {entry.time} UTC</span>
        </div>
      </div>

      {/* Metadata Section */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-semibold text-psi-text-secondary uppercase tracking-wider mb-2">
            {t("metadata") || "Metadata"}
          </h4>
          <div className="space-y-1.5">
            {Object.entries(entry.metadata).map(([key, value]) => (
              <div
                key={key}
                className="flex items-center justify-between py-1.5 px-2 rounded-md bg-psi-border/5"
              >
                <span className="text-[11px] text-psi-text-secondary">{key}</span>
                <span className="text-[11px] text-psi-text-primary font-medium text-right max-w-[160px] truncate">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confidence */}
      {entry.confidence !== undefined && (
        <div className="mt-4 p-3 rounded-lg bg-psi-emerald/5 border border-psi-emerald/15">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-psi-emerald font-medium">AI Confidence</span>
            <span className="text-sm font-bold text-psi-emerald">{entry.confidence}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-psi-border/20 overflow-hidden">
            <div
              className="h-full rounded-full bg-psi-emerald transition-all duration-500"
              style={{ width: `${entry.confidence}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
