// ============================================================
// PaySentinelIQ — Identity & Command Center (Profile)
// Enterprise-grade user profile with AI command center aesthetics
// All sections show empty/loading/placeholder states
// ============================================================

"use client";

import { useState, useRef } from "react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Switch } from "@/components/ui/Switch";
import { Separator } from "@/components/ui/Separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar";
import { useAuthStore } from "@/stores";
import { useActiveStatus } from "@/hooks/useActiveStatus";
import {
  // Hero icons
  User, Mail, Shield, Camera, Award, Zap, Flame, Search,
  // Section icons
  KeyRound, Fingerprint, Monitor, Clock, Globe, Bell,
  // Form & input icons
  Phone, Calendar, Briefcase, Building2, MapPin, Languages,
  // AI & security
  Brain, Lock, Eye, AlertTriangle, CheckCircle,
  // Activity
  Upload, FileText, BarChart3, Settings, Flag,
  // Navigation
  ChevronRight, ChevronDown, LogOut,
  // Other
  Sparkles, Radio, Gauge,
} from "lucide-react";

// ── Color mapping for activity types ── //
const ACTIVITY_COLORS: Record<string, { bg: string; icon: string; dot: string }> = {
  upload:      { bg: "bg-psi-electric/10",   icon: "text-psi-electric",   dot: "bg-psi-electric" },
  fraud:       { bg: "bg-psi-fraud/10",      icon: "text-psi-fraud",      dot: "bg-psi-fraud" },
  report:      { bg: "bg-psi-emerald/10",    icon: "text-psi-emerald",    dot: "bg-psi-emerald" },
  analysis:    { bg: "bg-psi-warning/10",    icon: "text-psi-warning",    dot: "bg-psi-warning" },
  flag:        { bg: "bg-purple-500/10",     icon: "text-purple-400",     dot: "bg-purple-400" },
  settings:    { bg: "bg-psi-electric/10",   icon: "text-psi-electric",   dot: "bg-psi-electric" },
};

const ACTIVITY_ICONS: Record<string, React.ElementType> = {
  upload:    Upload,
  fraud:     AlertTriangle,
  report:    BarChart3,
  analysis:  FileText,
  flag:      Flag,
  settings:  Settings,
};

// ── Animated Counter ── //
function AnimatedMetricCard({
  icon: Icon,
  label,
  value,
  subtitle,
  delay = 0,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  subtitle: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: "easeOut" }}
    >
      <Card variant="interactive" glow className="group h-full">
        <CardContent className="p-5">
          <div className="flex items-start justify-between mb-3">
            <p className="text-xs font-semibold text-psi-text-secondary uppercase tracking-widest truncate pr-2">
              {label}
            </p>
            <div className="rounded-lg bg-psi-electric/10 p-2 shrink-0 group-hover:bg-psi-electric/20 transition-colors">
              <Icon className="h-5 w-5 text-psi-electric" />
            </div>
          </div>
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-3xl font-bold text-psi-text-primary tabular-nums tracking-tight">
              {value}
            </span>
          </div>
          <p className="text-xs text-psi-text-secondary/50 italic">{subtitle}</p>
          {/* Mini animated pulse bar */}
          <div className="mt-3 h-1 w-full rounded-full bg-psi-border/20 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-psi-electric/40 to-psi-emerald/40"
              initial={{ width: "0%" }}
              animate={{ width: `${40 + Math.random() * 50}%` }}
              transition={{ duration: 1.5, delay: delay + 0.5, ease: "easeOut" }}
            />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Timeline Item ── //
function TimelineItem({
  icon: Icon,
  color,
  title,
  time,
  isLast = false,
}: {
  icon: React.ElementType;
  color: keyof typeof ACTIVITY_COLORS;
  title: string;
  time: string;
  isLast?: boolean;
}) {
  const c = ACTIVITY_COLORS[color] || ACTIVITY_COLORS.analysis;
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex gap-4 group"
    >
      {/* Timeline bar + icon */}
      <div className="flex flex-col items-center shrink-0">
        <div className={cn("w-9 h-9 rounded-xl flex items-center justify-center ring-1 ring-white/[0.06] transition-all duration-300 group-hover:scale-110", c.bg)}>
          <Icon className={cn("h-4 w-4", c.icon)} />
        </div>
        {!isLast && <div className="w-px flex-1 mt-1.5 bg-gradient-to-b from-psi-border/40 to-transparent" />}
      </div>
      {/* Content */}
      <div className="pb-6 flex-1 min-w-0">
        <p className="text-sm font-medium text-psi-text-primary group-hover:text-psi-electric transition-colors">
          {title}
        </p>
        <p className="text-xs text-psi-text-secondary/60 mt-0.5">{time}</p>
      </div>
    </motion.div>
  );
}

// ── AI Orb Animation ── //
function AIOrb({ className }: { className?: string }) {
  return (
    <div className={cn("relative flex items-center justify-center", className)} aria-hidden="true">
      <motion.div
        className="absolute inset-0 rounded-full bg-psi-electric/20 blur-xl"
        animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute inset-2 rounded-full bg-psi-emerald/10 blur-lg"
        animate={{ scale: [1, 1.25, 1], opacity: [0.2, 0.5, 0.2] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      />
      <Brain className="h-5 w-5 text-psi-electric relative z-10" />
    </div>
  );
}

// ============================================================
// Main Page Component
// ============================================================

export default function ProfilePage() {
  const t = useTranslations("profile");
  const tc = useTranslations("common");
  const tset = useTranslations("settings");
  const user = useAuthStore((s) => s.user);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isActive, lastActiveAt } = useActiveStatus();

  // ── Local state for toggles/selections ── //
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [predictiveAlerts, setPredictiveAlerts] = useState(true);
  const [smartAlerts, setSmartAlerts] = useState(true);
  const [anomalyRecs, setAnomalyRecs] = useState(true);
  const [emailNotif, setEmailNotif] = useState(true);
  const [pushNotif, setPushNotif] = useState(true);
  const [fraudAlert, setFraudAlert] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);
  const [complianceUpd, setComplianceUpd] = useState(true);
  const [systemUpd, setSystemUpd] = useState(true);
  const [selectedAI, setSelectedAI] = useState("gemini");
  const [selectedSensitivity, setSelectedSensitivity] = useState("medium");
  const [selectedExplanation, setSelectedExplanation] = useState("balanced");

  // ── Activity timeline (real data — currently empty) ── //
  const activities: {
    icon: React.ElementType;
    color: "upload" | "fraud" | "report" | "analysis" | "flag" | "settings";
    title: string;
    time: string;
  }[] = [];

  // ── AI model selection options ── //
  const aiModels = [
    { value: "gemini", label: t("aiPreferences.modelGemini") || "Gemini" },
    { value: "openai", label: t("aiPreferences.modelOpenAI") || "OpenAI" },
    { value: "local", label: t("aiPreferences.modelLocal") || "Local AI" },
  ];

  const sensitivities = [
    { value: "low", label: t("aiPreferences.sensitivityLow") || "Low" },
    { value: "medium", label: t("aiPreferences.sensitivityMedium") || "Medium" },
    { value: "high", label: t("aiPreferences.sensitivityHigh") || "High" },
  ];

  const explanations = [
    { value: "simple", label: t("aiPreferences.explanationSimple") || "Simple" },
    { value: "balanced", label: t("aiPreferences.explanationBalanced") || "Balanced" },
    { value: "detailed", label: t("aiPreferences.explanationDetailed") || "Detailed" },
  ];

  // ── Format last-seen timestamp into a human-readable string ── //
  function formatLastSeen(dt: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - dt.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr  = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return t("status.justNow") || "just now";
    if (diffMin < 60) return t("status.minutesAgo", { count: diffMin }) || `${diffMin}m ago`;
    if (diffHr < 24)  return t("status.hoursAgo", { count: diffHr }) || `${diffHr}h ago`;
    if (diffDay < 7)  return t("status.daysAgo", { count: diffDay }) || `${diffDay}d ago`;
    return dt.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const userInitials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() || "U";

  return (
    <div className="space-y-8">
      {/* ═══════════════════════════════════════════════════════
         BACKGROUND — Animated cyber grid + aura orbs
         ═══════════════════════════════════════════════════════ */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        {/* Grid pattern */}
        <svg className="absolute w-full h-full opacity-[0.025]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="profile-grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#1E6FFF" strokeWidth="0.4" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#profile-grid)" />
        </svg>
        {/* Animated data flow lines */}
        <svg className="absolute top-0 right-0 w-1/2 h-full opacity-[0.04]" viewBox="0 0 400 800" preserveAspectRatio="none">
          <motion.path
            d="M 200 0 Q 300 200 200 400 T 200 800"
            stroke="#1E6FFF"
            strokeWidth="1"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
          />
          <motion.path
            d="M 300 0 Q 150 250 300 500 T 300 800"
            stroke="#10B981"
            strokeWidth="0.6"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 5, repeat: Infinity, ease: "linear", delay: 1 }}
          />
        </svg>
        {/* Floating AI nodes */}
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full bg-psi-electric/20"
            style={{ top: `${15 + i * 30}%`, left: `${10 + i * 35}%` }}
            animate={{
              opacity: [0.1, 0.5, 0.1],
              scale: [1, 1.5, 1],
              boxShadow: [
                "0 0 0px rgba(30, 111, 255, 0)",
                "0 0 8px rgba(30, 111, 255, 0.3)",
                "0 0 0px rgba(30, 111, 255, 0)",
              ],
            }}
            transition={{ duration: 3 + i, repeat: Infinity, ease: "easeInOut", delay: i * 1.2 }}
          />
        ))}
        {/* Aura orbs */}
        <div className="absolute top-0 -left-32 w-[500px] h-[500px] bg-psi-electric/[0.04] rounded-full blur-[150px]" />
        <div className="absolute bottom-0 -right-32 w-[400px] h-[400px] bg-psi-emerald/[0.03] rounded-full blur-[120px]" />
      </div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 0 — Hero: Profile Identity + Metrics
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <Card glow className="relative overflow-hidden border-psi-electric/20">
          {/* Animated gradient sweep */}
          <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
            <div className="absolute -inset-[200%] animate-pulse bg-gradient-to-r from-psi-electric/[0.03] via-psi-emerald/[0.02] to-psi-electric/[0.03] blur-3xl" />
          </div>
          <CardContent className="relative z-10 p-6 sm:p-8">
            <div className="flex flex-col lg:flex-row gap-8">
              {/* ── Left: Avatar + Identity ── */}
              <div className="flex flex-col items-center lg:items-start gap-5 shrink-0">
                {/* Avatar with animated ring */}
                <div className="relative group/avatar">
                  <motion.div
                    className="absolute -inset-1 rounded-full bg-gradient-to-r from-psi-electric via-psi-emerald to-psi-electric opacity-70 blur-[2px]"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
                  />
                  <div className="relative rounded-full bg-psi-graphite p-1">
                    <Avatar className="h-24 w-24 ring-2 ring-white/[0.08]">
                      <AvatarImage src={user?.avatar_url || undefined} alt={user?.full_name || "User"} />
                      <AvatarFallback className="bg-gradient-to-br from-psi-electric/30 to-psi-emerald/20 text-2xl font-bold text-white">
                        {userInitials}
                      </AvatarFallback>
                    </Avatar>
                  </div>
                  {/* Upload button overlay */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-psi-electric text-white shadow-lg shadow-psi-electric/30 flex items-center justify-center hover:bg-psi-electric/90 transition-all hover:scale-110 z-20"
                    aria-label="Change profile photo"
                  >
                    <Camera className="h-4 w-4" />
                  </button>
                  <input ref={fileInputRef} type="file" accept="image/*" className="hidden" />
                </div>

                <div className="text-center lg:text-left space-y-1.5">
                  <h1 className="text-xl font-bold text-psi-text-primary tracking-tight">
                    {user?.full_name || tc("name") || "User"}
                  </h1>
                  <p className="text-sm text-psi-electric font-medium">
                    {user?.role || "Fraud Analyst"}
                  </p>
                  <div className="flex items-center gap-2 justify-center lg:justify-start text-xs text-psi-text-secondary">
                    <Building2 className="h-3.5 w-3.5" />
                    <span>{user?.tenant?.name || "PaySentinelIQ"}</span>
                  </div>
                  <div className="flex items-center gap-2 justify-center lg:justify-start text-xs text-psi-text-secondary/70">
                    <Mail className="h-3.5 w-3.5" />
                    <span>{user?.email || "analyst@paysentineliq.com"}</span>
                  </div>
                  {/* Status — dynamic active / last-seen */}
                  <div className="flex items-center gap-2 justify-center lg:justify-start pt-1">
                    {isActive ? (
                      <Badge variant="success" dot className="text-[10px]">
                        {t("status.online") || "Online"}
                      </Badge>
                    ) : (
                      <Badge variant="warning" dot className="text-[10px]">
                        {t("status.lastSeen", { time: formatLastSeen(lastActiveAt!) }) ||
                          `Last seen ${formatLastSeen(lastActiveAt!)}`}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* ── Right: Metrics Grid ── */}
              <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 gap-3">
                <AnimatedMetricCard
                  icon={FileText}
                  label={t("metrics.documentsAnalyzed") || "Documents Analyzed"}
                  value="———"
                  subtitle={t("metrics.documentsAnalyzed") || "Awaiting data"}
                  delay={0.1}
                />
                <AnimatedMetricCard
                  icon={AlertTriangle}
                  label={t("metrics.fraudDetections") || "Fraud Detections"}
                  value="———"
                  subtitle={t("metrics.fraudDetections") || "Awaiting data"}
                  delay={0.15}
                />
                <AnimatedMetricCard
                  icon={Zap}
                  label={t("metrics.aiUsage") || "AI Usage"}
                  value="———"
                  subtitle={t("metrics.aiUsage") || "Awaiting data"}
                  delay={0.2}
                />
                <AnimatedMetricCard
                  icon={Flame}
                  label={t("metrics.loginStreak") || "Login Streak"}
                  value="———"
                  subtitle={t("metrics.loginStreak") || "Awaiting data"}
                  delay={0.25}
                />
                <AnimatedMetricCard
                  icon={Search}
                  label={t("metrics.riskInvestigations") || "Risk Investigations"}
                  value="———"
                  subtitle={t("metrics.riskInvestigations") || "Awaiting data"}
                  delay={0.3}
                />
                <AnimatedMetricCard
                  icon={Award}
                  label={tc("total") || "Total Score"}
                  value="———"
                  subtitle={tc("status") || "Awaiting data"}
                  delay={0.35}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 1 — Personal Information
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("personalInfo.title") || "Personal Information"}</CardTitle>
            </div>
            <CardDescription>{t("personalInfo.description") || "Manage your personal details"}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {/* First Name */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("name") || "First Name"}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder={user?.full_name?.split(" ")[0] || "John"}
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Last Name */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("name") || "Last Name"}
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder={user?.full_name?.split(" ").slice(1).join(" ") || "Doe"}
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Email */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("email") || "Email"}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="email"
                    placeholder={user?.email || "analyst@company.com"}
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Phone */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("phonePlaceholder") || "Phone"}
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="tel"
                    placeholder={tc("phonePlaceholder") || "+1 (555) 000-0000"}
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Birth Date */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("date") || "Birth Date"}
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder="1990-01-01"
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Job Title */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tset("account.jobTitle") || "Job Title"}
                </label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder="Fraud Analyst"
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Department */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tset("account.department") || "Department"}
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder="Fraud Intelligence"
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Company */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("role") || "Company"}
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder="PaySentinelIQ"
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Country */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("languages") || "Country"}
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <input
                    type="text"
                    placeholder="United States"
                    className="w-full h-10 pl-9 pr-3 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary placeholder-psi-text-secondary/30 focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all"
                  />
                </div>
              </div>

              {/* Timezone */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tset("account.timezone") || "Timezone"}
                </label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <select className="w-full h-10 pl-9 pr-8 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary appearance-none focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all cursor-pointer">
                    <option value="America/Sao_Paulo">Brasília (UTC-3)</option>
                    <option value="America/New_York">New York (UTC-5)</option>
                    <option value="America/Chicago">Chicago (UTC-6)</option>
                    <option value="America/Los_Angeles">Los Angeles (UTC-8)</option>
                    <option value="Europe/London">London (UTC+0)</option>
                    <option value="Europe/Paris">Paris (UTC+1)</option>
                    <option value="Asia/Tokyo">Tokyo (UTC+9)</option>
                    <option value="Asia/Shanghai">Shanghai (UTC+8)</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 pointer-events-none" />
                </div>
              </div>

              {/* Language */}
              <div className="group relative">
                <label className="block text-xs font-medium text-psi-text-secondary mb-1.5">
                  {tc("language") || "Language"}
                </label>
                <div className="relative">
                  <Languages className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 group-focus-within:text-psi-electric transition-colors" />
                  <select className="w-full h-10 pl-9 pr-8 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-psi-text-primary appearance-none focus:outline-none focus:border-psi-electric/40 focus:ring-1 focus:ring-psi-electric/20 transition-all cursor-pointer">
                    <option value="en">English</option>
                    <option value="pt-BR">Português (Brasil)</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                    <option value="ja">日本語</option>
                    <option value="zh">中文</option>
                    <option value="ru">Русский</option>
                    <option value="ar">العربية</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary/40 pointer-events-none" />
                </div>
              </div>
            </div>

            {/* Save button */}
            <div className="flex justify-end mt-6">
              <Button variant="primary" size="md" disabled>
                <CheckCircle className="h-4 w-4" />
                {tset("actions.saveSettings") || "Save Changes"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 2 — Security Center
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("securityCenter.title") || "Security Center"}</CardTitle>
            </div>
            <CardDescription>{t("securityCenter.description") || "Manage your account security"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* ── Password Card ── */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-psi-electric/10 flex items-center justify-center">
                    <KeyRound className="h-5 w-5 text-psi-electric" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-psi-text-primary">
                      {t("securityCenter.passwordCardTitle") || "Password"}
                    </h4>
                    <p className="text-xs text-psi-text-secondary/70 mt-0.5">
                      {t("securityCenter.passwordCardDesc") || "Change your account password"}
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm" disabled>
                  <Lock className="h-3.5 w-3.5" />
                  {t("securityCenter.changePassword") || "Change Password"}
                </Button>
              </div>
            </div>

            {/* ── Two-Factor Auth Card ── */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-psi-emerald/10 flex items-center justify-center">
                    <Fingerprint className="h-5 w-5 text-psi-emerald" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-psi-text-primary">
                      {t("securityCenter.twoFactorCardTitle") || "Two-Factor Authentication (2FA)"}
                    </h4>
                    <p className="text-xs text-psi-text-secondary/70 mt-0.5">
                      {t("securityCenter.twoFactorCardDesc") || "Add an extra layer of security"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "text-xs font-medium transition-colors",
                    twoFactorEnabled ? "text-psi-emerald" : "text-psi-text-secondary/50"
                  )}>
                    {twoFactorEnabled
                      ? (t("securityCenter.enable") || "Enabled")
                      : (t("securityCenter.disable") || "Disabled")}
                  </span>
                  <Switch
                    checked={twoFactorEnabled}
                    onCheckedChange={setTwoFactorEnabled}
                    aria-label="Toggle two-factor authentication"
                  />
                </div>
              </div>
            </div>

            {/* ── Active Sessions Card ── */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-psi-warning/10 flex items-center justify-center">
                    <Monitor className="h-5 w-5 text-psi-warning" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-psi-text-primary">
                      {t("securityCenter.sessionsCardTitle") || "Active Sessions"}
                    </h4>
                    <p className="text-xs text-psi-text-secondary/70 mt-0.5">
                      {t("securityCenter.sessionsCardDesc") || "Manage connected devices"}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="mb-3 rounded-2xl bg-psi-electric/5 p-3 ring-1 ring-psi-electric/10">
                  <Monitor className="h-6 w-6 text-psi-electric/40" />
                </div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("securityCenter.noSessions") || "No active sessions"}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1">
                  {t("securityCenter.noSessionsDesc") || "Session data will appear when you log in from other devices"}
                </p>
              </div>
            </div>

            {/* ── Recent Login Activity ── */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-psi-electric/10 flex items-center justify-center">
                    <Clock className="h-5 w-5 text-psi-electric" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-psi-text-primary">
                      {t("securityCenter.recentActivityTitle") || "Recent Login Activity"}
                    </h4>
                    <p className="text-xs text-psi-text-secondary/70 mt-0.5">
                      {t("securityCenter.recentActivityDesc") || "Review recent sign-ins"}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="mb-3 rounded-2xl bg-psi-electric/5 p-3 ring-1 ring-psi-electric/10">
                  <Clock className="h-6 w-6 text-psi-electric/40" />
                </div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("securityCenter.noActivity") || "No recent login activity"}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1">
                  {t("securityCenter.noActivityDesc") || "Login history will appear here"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 3 — AI Preferences
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("aiPreferences.title") || "AI Preferences"}</CardTitle>
            </div>
            <CardDescription>{t("aiPreferences.description") || "Personalize AI behavior"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AI Model Select */}
            <div>
              <label className="block text-xs font-semibold text-psi-text-secondary uppercase tracking-wider mb-2">
                {t("aiPreferences.preferredModel") || "Preferred AI Model"}
              </label>
              <div className="flex flex-wrap gap-2">
                {aiModels.map((model) => (
                  <button
                    key={model.value}
                    onClick={() => setSelectedAI(model.value)}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200",
                      selectedAI === model.value
                        ? "border-psi-electric/40 bg-psi-electric/10 text-psi-electric shadow-lg shadow-psi-electric/10"
                        : "border-white/[0.06] bg-white/[0.02] text-psi-text-secondary hover:border-white/[0.12] hover:text-psi-text-primary"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <Brain className="h-3.5 w-3.5" />
                      {model.label}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Analysis Sensitivity */}
            <div>
              <label className="block text-xs font-semibold text-psi-text-secondary uppercase tracking-wider mb-2">
                {t("aiPreferences.analysisSensitivity") || "Analysis Sensitivity"}
              </label>
              <div className="flex flex-wrap gap-2">
                {sensitivities.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setSelectedSensitivity(s.value)}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200",
                      selectedSensitivity === s.value
                        ? "border-psi-warning/40 bg-psi-warning/10 text-psi-warning shadow-lg shadow-psi-warning/10"
                        : "border-white/[0.06] bg-white/[0.02] text-psi-text-secondary hover:border-white/[0.12] hover:text-psi-text-primary"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <Gauge className="h-3.5 w-3.5" />
                      {s.label}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Explanation Level */}
            <div>
              <label className="block text-xs font-semibold text-psi-text-secondary uppercase tracking-wider mb-2">
                {t("aiPreferences.explanationLevel") || "AI Explanation Level"}
              </label>
              <div className="flex flex-wrap gap-2">
                {explanations.map((e) => (
                  <button
                    key={e.value}
                    onClick={() => setSelectedExplanation(e.value)}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium border transition-all duration-200",
                      selectedExplanation === e.value
                        ? "border-psi-emerald/40 bg-psi-emerald/10 text-psi-emerald shadow-lg shadow-psi-emerald/10"
                        : "border-white/[0.06] bg-white/[0.02] text-psi-text-secondary hover:border-white/[0.12] hover:text-psi-text-primary"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <Eye className="h-3.5 w-3.5" />
                      {e.label}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <Separator />

            {/* Toggles */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <Sparkles className="h-4 w-4 text-psi-electric/70 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-psi-text-primary">
                      {t("aiPreferences.predictiveSuggestions") || "Enable Predictive Suggestions"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60">
                      AI suggests actions based on your usage patterns
                    </p>
                  </div>
                </div>
                <Switch checked={predictiveAlerts} onCheckedChange={setPredictiveAlerts} />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <Bell className="h-4 w-4 text-psi-electric/70 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-psi-text-primary">
                      {t("aiPreferences.smartAlerts") || "Enable Smart Alerts"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60">
                      Intelligent alert prioritization and grouping
                    </p>
                  </div>
                </div>
                <Switch checked={smartAlerts} onCheckedChange={setSmartAlerts} />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-4 w-4 text-psi-electric/70 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-psi-text-primary">
                      {t("aiPreferences.anomalyRecommendations") || "Enable Anomaly Recommendations"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60">
                      Get AI recommendations when anomalies are detected
                    </p>
                  </div>
                </div>
                <Switch checked={anomalyRecs} onCheckedChange={setAnomalyRecs} />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 4 — Notification Center
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("notificationCenter.title") || "Notification Center"}</CardTitle>
            </div>
            <CardDescription>{t("notificationCenter.description") || "Control notification preferences"}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Email Notifications */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <Mail className="h-4 w-4 text-psi-electric/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.emailNotifications") || "Email Notifications"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.emailNotificationsDesc") || "Receive notifications via email"}
                    </p>
                  </div>
                </div>
                <Switch checked={emailNotif} onCheckedChange={setEmailNotif} className="shrink-0 ml-2" />
              </div>

              {/* Push Notifications */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <Radio className="h-4 w-4 text-psi-emerald/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.pushNotifications") || "Push Notifications"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.pushNotificationsDesc") || "Receive browser push notifications"}
                    </p>
                  </div>
                </div>
                <Switch checked={pushNotif} onCheckedChange={setPushNotif} className="shrink-0 ml-2" />
              </div>

              {/* Fraud Alerts */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <AlertTriangle className="h-4 w-4 text-psi-fraud/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.fraudAlerts") || "Fraud Alerts"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.fraudAlertsDesc") || "Get alerts for detected fraud"}
                    </p>
                  </div>
                </div>
                <Switch checked={fraudAlert} onCheckedChange={setFraudAlert} className="shrink-0 ml-2" />
              </div>

              {/* Weekly Reports */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <BarChart3 className="h-4 w-4 text-psi-warning/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.weeklyReports") || "Weekly Reports"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.weeklyReportsDesc") || "Receive weekly summary reports"}
                    </p>
                  </div>
                </div>
                <Switch checked={weeklyReport} onCheckedChange={setWeeklyReport} className="shrink-0 ml-2" />
              </div>

              {/* Compliance Updates */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <Shield className="h-4 w-4 text-purple-400/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.complianceUpdates") || "Compliance Updates"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.complianceUpdatesDesc") || "Get compliance notifications"}
                    </p>
                  </div>
                </div>
                <Switch checked={complianceUpd} onCheckedChange={setComplianceUpd} className="shrink-0 ml-2" />
              </div>

              {/* System Updates */}
              <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                <div className="flex items-start gap-3 min-w-0">
                  <Settings className="h-4 w-4 text-psi-text-secondary/70 mt-0.5 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-psi-text-primary truncate">
                      {t("notificationCenter.systemUpdates") || "System Updates"}
                    </p>
                    <p className="text-xs text-psi-text-secondary/60 truncate">
                      {t("notificationCenter.systemUpdatesDesc") || "Receive system maintenance notices"}
                    </p>
                  </div>
                </div>
                <Switch checked={systemUpd} onCheckedChange={setSystemUpd} className="shrink-0 ml-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════════════════════════════════════════════
         SECTION 5 — Activity History (Timeline)
         ═══════════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
      >
        <Card glow>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-psi-electric" />
              <CardTitle>{t("activityHistory.title") || "Activity History"}</CardTitle>
            </div>
            <CardDescription>{t("activityHistory.description") || "Your recent actions"}</CardDescription>
          </CardHeader>
          <CardContent>
            {activities.length > 0 ? (
              <div className="pl-1">
                {activities.map((activity, i) => (
                  <TimelineItem
                    key={i}
                    icon={activity.icon}
                    color={activity.color}
                    title={activity.title}
                    time={activity.time}
                    isLast={i === activities.length - 1}
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-2xl bg-psi-electric/5 p-4 ring-1 ring-psi-electric/10">
                  <Clock className="h-8 w-8 text-psi-electric/40" />
                </div>
                <p className="text-sm font-medium text-psi-text-primary">
                  {t("activityHistory.noActivityTitle") || "No Recent Activity"}
                </p>
                <p className="text-xs text-psi-text-secondary/60 mt-1">
                  {t("activityHistory.noActivityDesc") || "Your recent actions will appear here"}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>


    </div>
  );
}
