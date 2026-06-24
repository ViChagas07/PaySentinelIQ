"use client";

export const dynamic = "force-dynamic";

import { useState, useCallback, useId } from "react";
import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { useSearchParams } from "next/navigation";
import { useSettingsStore, type PrimaryColor, type FontSize, type ElementSize, type ThemeMode, type DigestFrequency, type BackgroundColor } from "@/stores/settings-store";
import { useAuthStore } from "@/stores";
import {
  Settings, Palette, Globe, Accessibility, Bell, Shield, User,
  Wrench, Moon, Sun, Monitor, Check, ChevronDown, Save, RotateCcw,
  Type, Maximize, Minimize, Languages, Eye, Keyboard, Volume2,
  Smartphone, Mail, Clock, AlertTriangle, Key, Trash2,
  LogIn, UserPlus, FileText, Gavel, Download, Database, Fingerprint,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/Switch";
import { Label } from "@/components/ui/Label";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Link } from "@/i18n/navigation";

/* ═══════════════════════════════════════════════════
   Section Nav Button
   ═══════════════════════════════════════════════════ */

function SectionButton({
  id, active, icon: Icon, label, onClick,
}: {
  id: string; active: boolean; icon: React.ElementType;
  label: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      aria-current={active ? "true" : undefined}
      className={cn(
        "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-left transition-colors",
        "text-sm font-medium",
        "hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
        active
          ? "bg-psi-electric/10 text-psi-electric border border-psi-electric/30"
          : "text-psi-text-secondary border border-transparent"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{label}</span>
    </button>
  );
}

/* ═══════════════════════════════════════════════════
   Toggle Switch
   ═══════════════════════════════════════════════════ */

function Toggle({ checked, onChange, disabled, id }: {
  checked: boolean; onChange: (checked: boolean) => void; disabled?: boolean; id?: string;
}) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
        checked ? "bg-psi-electric" : "bg-psi-border",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span className={cn(
        "inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform",
        checked ? "translate-x-5" : "translate-x-0.5"
      )} />
    </button>
  );
}

/* ═══════════════════════════════════════════════════
   Color Picker
   ═══════════════════════════════════════════════════ */

const COLORS: { key: PrimaryColor; name: string; hex: string }[] = [
  { key: "blue", name: "blue", hex: "#1E6FFF" },
  { key: "green", name: "green", hex: "#00C48C" },
  { key: "purple", name: "purple", hex: "#8B5CF6" },
  { key: "orange", name: "orange", hex: "#FF8C00" },
  { key: "red", name: "red", hex: "#D63B3B" },
  { key: "teal", name: "teal", hex: "#14B8A6" },
];

function ColorPicker({
  t,
}: {
  t: (key: string) => string;
}) {
  const primaryColor = useSettingsStore((s) => s.primaryColor);
  const setPrimaryColor = useSettingsStore((s) => s.setPrimaryColor);

  return (
    <div className="flex flex-wrap gap-3">
      {COLORS.map((color) => (
        <button
          key={color.key}
          onClick={() => setPrimaryColor(color.key)}
          className={cn(
            "relative h-9 w-9 rounded-full transition-all",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
            primaryColor === color.key
              ? "ring-2 ring-offset-2 ring-psi-electric ring-offset-psi-graphite scale-110"
              : "hover:scale-105"
          )}
          style={{ backgroundColor: color.hex }}
          title={t(color.name)}
          aria-label={t(color.name)}
        >
          {primaryColor === color.key && (
            <Check className="absolute inset-0 m-auto h-4 w-4 text-white drop-shadow-sm" />
          )}
        </button>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Background Color Picker
   ═══════════════════════════════════════════════════ */

const BG_COLORS: { key: BackgroundColor; name: string; hex: string }[] = [
  { key: "navy", name: "navy", hex: "#0A1628" },
  { key: "charcoal", name: "charcoal", hex: "#1a1a2e" },
  { key: "slate", name: "slate", hex: "#0f172a" },
  { key: "midnight", name: "midnight", hex: "#0d1117" },
  { key: "espresso", name: "espresso", hex: "#1c1917" },
  { key: "forest", name: "forest", hex: "#081c15" },
];

function BackgroundColorPicker({
  t,
}: {
  t: (key: string) => string;
}) {
  const backgroundColor = useSettingsStore((s) => s.backgroundColor);
  const setBackgroundColor = useSettingsStore((s) => s.setBackgroundColor);

  return (
    <div className="flex flex-wrap gap-3">
      {BG_COLORS.map((color) => (
        <button
          key={color.key}
          onClick={() => setBackgroundColor(color.key)}
          className={cn(
            "relative h-9 w-9 rounded-full transition-all border border-white/10",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
            backgroundColor === color.key
              ? "ring-2 ring-offset-2 ring-psi-electric ring-offset-psi-graphite scale-110"
              : "hover:scale-105"
          )}
          style={{ backgroundColor: color.hex }}
          title={t(color.name)}
          aria-label={t(color.name)}
        >
          {backgroundColor === color.key && (
            <Check className="absolute inset-0 m-auto h-4 w-4 text-white drop-shadow-sm" />
          )}
        </button>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Privacy & Data Section
   ═══════════════════════════════════════════════════ */

function PrivacySection({
  t, tc,
}: {
  t: (key: string) => string;
  tc: (key: string) => string;
}) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState("");
  const [showDeletionModal, setShowDeletionModal] = useState(false);
  const [deletionConfirm, setDeletionConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deletionMsg, setDeletionMsg] = useState("");

  // ── Client-side PDF Export (jsPDF) ──
  const handleExport = async () => {
    setExporting(true);
    setExportMsg("");
    try {
      const { default: jsPDF } = await import("jspdf");

      const doc = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      // Colors — PaySentinelIQ brand
      const navy = "#0A1628";
      const electric = "#1E6FFF";
      const textPrimary = "#F8FAFC";
      const textSecondary = "#94A3B8";

      // ── Brand header ──
      doc.setFillColor(navy);
      doc.rect(0, 0, 210, 36, "F");
      doc.setTextColor(electric);
      doc.setFontSize(20);
      doc.setFont("helvetica", "bold");
      doc.text("PaySentinelIQ", 14, 18);
      doc.setFontSize(9);
      doc.setTextColor(textSecondary);
      doc.text("Data Export Report", 14, 28);

      // ── Export metadata ──
      const exportDate = new Date().toISOString();
      doc.setFontSize(8);
      doc.setTextColor(textSecondary);
      doc.text(`Generated: ${new Date(exportDate).toLocaleString()}`, 14, 44);
      doc.text(`User ID: ${user?.id || "N/A"}`, 14, 50);
      doc.text(`Email: ${user?.email || "N/A"}`, 14, 56);

      // ── Separator ──
      doc.setDrawColor(electric);
      doc.setLineWidth(0.3);
      doc.line(14, 62, 196, 62);

      // ── Section 1: Account Info ──
      doc.setFontSize(11);
      doc.setTextColor(electric);
      doc.setFont("helvetica", "bold");
      doc.text("Account Information", 14, 72);

      doc.setFontSize(9);
      doc.setTextColor(textPrimary);
      doc.setFont("helvetica", "normal");
      const details = [
        `Name: ${user?.full_name || "N/A"}`,
        `Email: ${user?.email || "N/A"}`,
        `Role: ${user?.role?.replace(/_/g, " ") || "N/A"}`,
        `Tenant ID: ${user?.tenant_id || "N/A"}`,
        `Account Created: ${user?.created_at ? new Date(user.created_at).toLocaleString() : "N/A"}`,
        `Last Login: ${user?.last_login ? new Date(user.last_login).toLocaleString() : "N/A"}`,
        `MFA Enabled: ${user?.mfa_enabled ? "Yes" : "No"}`,
      ];
      let y = 80;
      details.forEach((line) => {
        doc.text(line, 14, y);
        y += 6;
      });

      // ── Section 2: Summary ──
      y += 4;
      doc.setFontSize(11);
      doc.setTextColor(electric);
      doc.setFont("helvetica", "bold");
      doc.text("Platform Summary", 14, y);
      y += 8;

      doc.setFontSize(9);
      doc.setTextColor(textPrimary);
      doc.setFont("helvetica", "normal");
      doc.text("This document contains a summary of data associated with your PaySentinelIQ account.", 14, y);
      y += 5;
      doc.text("For a complete data export including all documents and verification records,", 14, y);
      y += 5;
      doc.text("please contact our support team at support@paysentineliq.com.", 14, y);

      // ── Section 3: Export timestamp ──
      y += 8;
      doc.setFontSize(9);
      doc.setTextColor(textSecondary);
      doc.text(`Export completed at: ${new Date().toISOString()}`, 14, y);

      // ── Footer ──
      doc.setFontSize(7);
      doc.setTextColor(textSecondary);
      doc.text("© 2026 PaySentinelIQ. All rights reserved.", 14, 292);
      doc.text("This document was generated automatically. If you believe there is an error,", 14, 297);
      doc.text("please contact support@paysentineliq.com.", 14, 302);

      // ── Download ──
      const filename = `paysentineliq-export-${user?.id || "user"}-${Date.now()}.pdf`;
      doc.save(filename);
      setExportMsg(t("privacy.exportSuccess"));
    } catch {
      setExportMsg(t("privacy.exportError"));
    } finally {
      setExporting(false);
    }
  };

  // ── Account Deletion ──
  const handleDeletion = async () => {
    if (!deletionConfirm) return;
    setDeleting(true);
    setDeletionMsg("");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) throw new Error("API URL not configured");

      const res = await fetch(`${apiUrl}/account`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${useAuthStore.getState().token}`,
        },
        body: JSON.stringify({ confirm: true }),
      });
      if (!res.ok) throw new Error("Deletion failed");
      setDeletionMsg(t("privacy.deletionRequested"));
      setShowDeletionModal(false);
    } catch {
      setDeletionMsg("Failed. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (iso: string) => new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

  return (
    <div className="space-y-8">
      {/* ── Policy Documents ── */}
      <section>
        <h3 className="text-sm font-semibold text-psi-text-primary mb-1">{t("privacy.policyDocuments")}</h3>
        <p className="text-xs text-psi-text-secondary mb-4">{t("privacy.policyDocumentsDescription")}</p>
        <div className="flex flex-wrap gap-3">
          <a
            href="/en/privacy-policy"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-psi-border bg-white/[0.02] text-sm text-psi-text-secondary hover:text-white hover:border-white/[0.15] hover:bg-white/[0.04] transition-all"
          >
            <FileText className="h-4 w-4 text-psi-electric/70" />
            {t("privacy.viewPrivacyPolicy")}
          </a>
          <a
            href="/en/privacy-policy#terms"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-psi-border bg-white/[0.02] text-sm text-psi-text-secondary hover:text-white hover:border-white/[0.15] hover:bg-white/[0.04] transition-all"
          >
            <Gavel className="h-4 w-4 text-psi-electric/70" />
            {t("privacy.viewTermsOfService")}
          </a>
        </div>
      </section>

      {/* ── Consent History ── */}
      <section>
        <h3 className="text-sm font-semibold text-psi-text-primary mb-1">{t("privacy.consentHistory")}</h3>
        <p className="text-xs text-psi-text-secondary mb-4">{t("privacy.consentHistoryDescription")}</p>
        <p className="text-xs text-psi-text-secondary/60 italic">
          {t("privacy.loadingConsentRecords") || "Loading consent records..."}
        </p>
      </section>

      {/* ── Data Export ── */}
      <section>
        <h3 className="text-sm font-semibold text-psi-text-primary mb-1">{t("privacy.dataExport")}</h3>
        <p className="text-xs text-psi-text-secondary mb-4">{t("privacy.dataExportDescription")}</p>
        <button
          onClick={handleExport}
          disabled={exporting || !isAuthenticated}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-psi-electric text-white text-sm font-medium hover:bg-psi-electric/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {exporting ? (
            <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {exporting ? t("privacy.exporting") : t("privacy.exportDataButton")}
        </button>
        {exportMsg && (
          <p className={cn("mt-3 text-xs", exportMsg.includes("failed") || exportMsg.includes("Failed") ? "text-psi-fraud" : "text-psi-emerald")}>
            {exportMsg}
          </p>
        )}
      </section>

      {/* ── Account Deletion ── */}
      <section>
        <h3 className="text-sm font-semibold text-psi-text-primary mb-1">{t("privacy.accountDeletion")}</h3>
        <p className="text-xs text-psi-text-secondary mb-4">{t("privacy.accountDeletionDescription")}</p>
        <button
          onClick={() => { setShowDeletionModal(true); setDeletionConfirm(false); setDeletionMsg(""); }}
          disabled={!isAuthenticated}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-psi-fraud/40 bg-psi-fraud/[0.04] text-sm font-medium text-psi-fraud hover:bg-psi-fraud/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <Trash2 className="h-4 w-4" />
          {t("privacy.requestDeletionButton")}
        </button>
        {deletionMsg && (
          <p className="mt-3 text-xs text-psi-emerald">{deletionMsg}</p>
        )}
      </section>

      {/* ── Deletion Confirmation Modal ── */}
      {showDeletionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setShowDeletionModal(false)}>
          <div
            className="w-full max-w-md rounded-2xl border border-psi-border bg-psi-graphite p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-psi-fraud/10">
                <AlertTriangle className="h-5 w-5 text-psi-fraud" />
              </div>
              <h3 className="text-lg font-semibold text-white">{t("privacy.deletionConfirmTitle")}</h3>
            </div>
            <p className="text-sm text-psi-text-secondary leading-relaxed mb-5">{t("privacy.deletionConfirmMessage")}</p>
            <label className="flex items-start gap-3 mb-5 cursor-pointer">
              <input
                type="checkbox"
                checked={deletionConfirm}
                onChange={(e) => setDeletionConfirm(e.target.checked)}
                className="mt-0.5 rounded border-psi-border bg-psi-navy/50 accent-psi-fraud h-4 w-4"
              />
              <span className="text-xs text-psi-text-secondary">{t("privacy.deletionConfirmCheckbox")}</span>
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeletionModal(false)}
                className="flex-1 px-4 py-2.5 rounded-lg border border-psi-border text-sm text-psi-text-secondary hover:bg-white/5 transition-colors"
              >
                {tc("cancel")}
              </button>
              <button
                onClick={handleDeletion}
                disabled={!deletionConfirm || deleting}
                className="flex-1 px-4 py-2.5 rounded-lg bg-psi-fraud text-white text-sm font-medium hover:bg-psi-fraud/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                {deleting ? (
                  <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto block" />
                ) : (
                  t("privacy.requestDeletionButton")
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Settings Page
   ═══════════════════════════════════════════════════ */

const SECTIONS = [
  { id: "appearance", icon: Palette },
  { id: "language", icon: Globe },
  { id: "accessibility", icon: Accessibility },
  { id: "notifications", icon: Bell },
  { id: "account", icon: User },
  { id: "security", icon: Shield },
  { id: "privacy", icon: Fingerprint },
  { id: "advanced", icon: Wrench },
] as const;

const FONT_SIZES: { key: FontSize; icon: React.ElementType }[] = [
  { key: "small", icon: Minimize },
  { key: "medium", icon: Type },
  { key: "large", icon: Type },
  { key: "xlarge", icon: Maximize },
];

const ELEMENT_SIZES: { key: ElementSize; label: string }[] = [
  { key: "compact", label: "compact" },
  { key: "comfortable", label: "comfortable" },
  { key: "spacious", label: "spacious" },
];

const THEMES: { key: ThemeMode; icon: React.ElementType; label: string }[] = [
  { key: "dark", icon: Moon, label: "dark" },
  { key: "light", icon: Sun, label: "light" },
  { key: "system", icon: Monitor, label: "system" },
];

const LANGUAGES: { code: string; labelKey: string }[] = [
  { code: "en", labelKey: "en" },
  { code: "pt-BR", labelKey: "pt-BR" },
  { code: "ja", labelKey: "ja" },
  { code: "zh", labelKey: "zh" },
  { code: "ar", labelKey: "ar" },
  { code: "es", labelKey: "es" },
  { code: "fr", labelKey: "fr" },
  { code: "ru", labelKey: "ru" },
  { code: "de", labelKey: "de" },
];

export default function SettingsPage() {
  const t = useTranslations("settings");
  const tc = useTranslations("common");
  const tz = useTranslations("timezones");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Restore active section from URL query param on mount (survives language changes)
  const [activeSection, setActiveSection] = useState<string>(
    () => searchParams.get("section") || "appearance"
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const store = useSettingsStore();
  const [
    theme, setTheme, primaryColor,
    backgroundColor, setBackgroundColor,
    boldText, setBoldText,
    fontSize, setFontSize,
    elementSize, setElementSize,
    locale, setLocale,
    highContrast, setHighContrast,
    reducedMotion, setReducedMotion,
    dyslexiaFont, setDyslexiaFont,
    screenReaderOptimized, setScreenReaderOptimized,
    keyboardNav, setKeyboardNav,
    focusIndicator, setFocusIndicator,
    emailAlerts, setEmailAlerts,
    pushNotifications, setPushNotifications,
    desktopAlerts, setDesktopAlerts,
    soundAlerts, setSoundAlerts,
    alertThreshold, setAlertThreshold,
    fraudAlertEmail, setFraudAlertEmail,
    digestFrequency, setDigestFrequency,
    timezone, setTimezone,
    developerMode, setDeveloperMode,
    resetAll,
  ] = [
    store.theme, store.setTheme, store.primaryColor,
    store.backgroundColor, store.setBackgroundColor,
    store.boldText, store.setBoldText,
    store.fontSize, store.setFontSize,
    store.elementSize, store.setElementSize,
    store.locale, store.setLocale,
    store.highContrast, store.setHighContrast,
    store.reducedMotion, store.setReducedMotion,
    store.dyslexiaFont, store.setDyslexiaFont,
    store.screenReaderOptimized, store.setScreenReaderOptimized,
    store.keyboardNav, store.setKeyboardNav,
    store.focusIndicator, store.setFocusIndicator,
    store.emailAlerts, store.setEmailAlerts,
    store.pushNotifications, store.setPushNotifications,
    store.desktopAlerts, store.setDesktopAlerts,
    store.soundAlerts, store.setSoundAlerts,
    store.alertThreshold, store.setAlertThreshold,
    store.fraudAlertEmail, store.setFraudAlertEmail,
    store.digestFrequency, store.setDigestFrequency,
    store.timezone, store.setTimezone,
    store.developerMode, store.setDeveloperMode,
    store.resetAll,
  ];

  // Auth state — determines if user sees the guest overlay or real form
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const authUser = useAuthStore((s) => s.user);

  // Language change handler with navigation — preserves active section
  const handleLanguageChange = useCallback((newLocale: string) => {
    setLocale(newLocale);
    router.replace(`${pathname}?section=${activeSection}`, { locale: newLocale });
  }, [setLocale, router, pathname, activeSection]);

  // Section change handler — updates state and URL (lightweight, no full navigation)
  const handleSectionChange = useCallback((section: string) => {
    setActiveSection(section);
    window.history.replaceState(null, "", `${pathname}?section=${section}`);
  }, [pathname]);

  // Save feedback
  const handleSave = useCallback(() => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }, 600);
  }, []);

  // Reset handler
  const handleReset = useCallback(() => {
    if (window.confirm(t("advanced.resetConfirm"))) {
      resetAll();
      router.replace(pathname, { locale: "en" });
    }
  }, [resetAll, router, pathname, t]);

  const sectionTitle = t(`sections.${activeSection}` as any);

  return (
    <div className="animate-slide-in-up">
      {/* Header */}
      <div className="mb-4 md:mb-6">
        <h1 className="flex items-center gap-3 text-xl md:text-2xl font-bold">
          <Settings className="h-6 w-6 text-psi-electric" />
          {t("title")}
        </h1>
        <p className="mt-1 text-sm text-psi-text-secondary">{t("description")}</p>
      </div>

      {/* Layout: Sidebar nav + Content */}
      <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
        {/* Section Navigation — Horizontal scroll on mobile */}
        <nav className="lg:w-56 shrink-0" aria-label="Settings sections">
          <div className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible pb-2 lg:pb-0 -mx-1 px-1">
            {SECTIONS.map(({ id, icon }) => (
              <SectionButton
                key={id}
                id={id}
                active={activeSection === id}
                icon={icon}
                label={t(`sections.${id}` as any)}
                onClick={() => handleSectionChange(id)}
              />
            ))}
          </div>
        </nav>

        {/* Content Panel */}
        <div className="flex-1 min-w-0">
          <div className="card-responsive">
            <h2 className="text-lg font-semibold mb-1">{sectionTitle}</h2>
            <p className="text-sm text-psi-text-secondary mb-4 md:mb-6">
              {t(`${activeSection}.description` as any)}
            </p>

            {/* ═══════════ APPEARANCE ═══════════ */}
            {activeSection === "appearance" && (
              <div className="space-y-6">
                {/* Theme */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t("appearance.theme")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("appearance.themeDescription")}</p>
                  <div className="flex flex-wrap gap-2">
                    {THEMES.map(({ key, icon: Icon, label }) => (
                      <button
                        key={key}
                        onClick={() => setTheme(key)}
                        className={cn(
                          "flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-all",
                          "hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
                          theme === key
                            ? "border-psi-electric bg-psi-electric/10 text-psi-electric"
                            : "border-psi-border text-psi-text-secondary"
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        {t(`appearance.${label}` as any)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Primary Color */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t("appearance.primaryColor")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("appearance.primaryColorDescription")}</p>
                  <ColorPicker t={(k) => t(`appearance.${k}` as any)} />
                </div>

                {/* Background Color */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t("appearance.backgroundColor")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("appearance.backgroundColorDescription")}</p>
                  <BackgroundColorPicker t={(k) => t(`appearance.backgroundColorOptions.${k}` as any)} />
                </div>

                {/* Bold Text */}
                <div className="flex items-center justify-between py-1">
                  <div>
                    <Label htmlFor="bold-text" className="text-sm font-medium">{t("appearance.boldText")}</Label>
                    <p className="text-xs text-psi-text-secondary">{t("appearance.boldTextDescription")}</p>
                  </div>
                  <Switch id="bold-text" checked={boldText} onCheckedChange={setBoldText} />
                </div>

                {/* Font Size */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t("appearance.fontSize")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("appearance.fontSizeDescription")}</p>
                  <div className="flex flex-wrap gap-2">
                    {FONT_SIZES.map(({ key, icon: Icon }) => (
                      <button
                        key={key}
                        onClick={() => setFontSize(key)}
                        className={cn(
                          "flex items-center gap-2 px-4 py-2 rounded-lg border text-sm transition-all",
                          "hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
                          fontSize === key
                            ? "border-psi-electric bg-psi-electric/10 text-psi-electric"
                            : "border-psi-border text-psi-text-secondary"
                        )}
                      >
                        <Icon className={cn("h-4 w-4", key === "xlarge" && "h-5 w-5")} />
                        {t(`appearance.${key}` as any)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Element Size */}
                <div>
                  <label className="block text-sm font-medium mb-2">{t("appearance.elementSize")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("appearance.elementSizeDescription")}</p>
                  <div className="flex flex-wrap gap-2">
                    {ELEMENT_SIZES.map(({ key, label }) => (
                      <button
                        key={key}
                        onClick={() => setElementSize(key)}
                        className={cn(
                          "px-4 py-2 rounded-lg border text-sm transition-all",
                          "hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
                          elementSize === key
                            ? "border-psi-electric bg-psi-electric/10 text-psi-electric"
                            : "border-psi-border text-psi-text-secondary"
                        )}
                      >
                        {t(`appearance.${label}` as any)}
                      </button>
                    ))}
                  </div>
                </div>

              </div>
            )}

            {/* ═══════════ LANGUAGE ═══════════ */}
            {activeSection === "language" && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">{t("language.selectLanguage")}</label>
                  <p className="text-xs text-psi-text-secondary mb-3">{t("language.selectLanguageDescription")}</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {LANGUAGES.map(({ code, labelKey }) => (
                      <button
                        key={code}
                        onClick={() => handleLanguageChange(code)}
                        className={cn(
                          "flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm transition-all",
                          "hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
                          locale === code
                            ? "border-psi-electric bg-psi-electric/10 text-psi-electric font-semibold"
                            : "border-psi-border text-psi-text-secondary"
                        )}
                      >
                        <span className="text-base leading-none" aria-hidden="true">
                          {code === "ar" ? "ع" : code === "zh" ? "中" : code === "ja" ? "日" : code === "ru" ? "Р" : code.toUpperCase().slice(0, 2)}
                        </span>
                        <span className="truncate">{t(`language.availableLanguages.${labelKey}` as any)}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Timezone */}
                <div>
                  <label className="block text-sm font-medium mb-2">{tc("date")} & {tc("time")}</label>
                  <p className="text-xs text-psi-text-secondary mb-2">{t("language.regionDescription")}</p>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full max-w-sm rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                  >
                    <option value="America/Sao_Paulo">{tz("America/Sao_Paulo")}</option>
                    <option value="America/New_York">{tz("America/New_York")}</option>
                    <option value="America/Chicago">{tz("America/Chicago")}</option>
                    <option value="America/Los_Angeles">{tz("America/Los_Angeles")}</option>
                    <option value="Europe/London">{tz("Europe/London")}</option>
                    <option value="Europe/Paris">{tz("Europe/Paris")}</option>
                    <option value="Europe/Moscow">{tz("Europe/Moscow")}</option>
                    <option value="Asia/Tokyo">{tz("Asia/Tokyo")}</option>
                    <option value="Asia/Shanghai">{tz("Asia/Shanghai")}</option>
                    <option value="Asia/Dubai">{tz("Asia/Dubai")}</option>
                    <option value="Australia/Sydney">{tz("Australia/Sydney")}</option>
                  </select>
                </div>
              </div>
            )}

            {/* ═══════════ ACCESSIBILITY ═══════════ */}
            {activeSection === "accessibility" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="high-contrast">{t("accessibility.highContrast")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.highContrastDescription")}</p>
                  </div>
                  <Switch id="high-contrast" checked={highContrast} onCheckedChange={setHighContrast} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="screen-reader">{t("accessibility.screenReader")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.screenReaderDescription")}</p>
                  </div>
                  <Switch id="screen-reader" checked={screenReaderOptimized} onCheckedChange={setScreenReaderOptimized} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="keyboard-nav">{t("accessibility.keyboardNav")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.keyboardNavDescription")}</p>
                  </div>
                  <Switch id="keyboard-nav" checked={keyboardNav} onCheckedChange={setKeyboardNav} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="focus-indicator">{t("accessibility.focusIndicator")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.focusIndicatorDescription")}</p>
                  </div>
                  <Switch id="focus-indicator" checked={focusIndicator} onCheckedChange={setFocusIndicator} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="dyslexia-font">{t("accessibility.dyslexiaFont")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.dyslexiaFontDescription")}</p>
                  </div>
                  <Switch id="dyslexia-font" checked={dyslexiaFont} onCheckedChange={setDyslexiaFont} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="reduced-motion">{t("accessibility.reducedMotion")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("accessibility.reducedMotionDescription")}</p>
                  </div>
                  <Switch id="reduced-motion" checked={reducedMotion} onCheckedChange={setReducedMotion} />
                </div>
              </div>
            )}

            {/* ═══════════ NOTIFICATIONS ═══════════ */}
            {activeSection === "notifications" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="email-alerts">{t("notifications.emailAlerts")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("notifications.emailAlertsDescription")}</p>
                  </div>
                  <Switch id="email-alerts" checked={emailAlerts} onCheckedChange={setEmailAlerts} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="push-notifications">{t("notifications.pushNotifications")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("notifications.pushNotificationsDescription")}</p>
                  </div>
                  <Switch id="push-notifications" checked={pushNotifications} onCheckedChange={setPushNotifications} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="desktop-alerts">{t("notifications.desktopAlerts")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("notifications.desktopAlertsDescription")}</p>
                  </div>
                  <Switch id="desktop-alerts" checked={desktopAlerts} onCheckedChange={setDesktopAlerts} />
                </div>
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="sound-alerts">{t("notifications.soundAlerts")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("notifications.soundAlertsDescription")}</p>
                  </div>
                  <Switch id="sound-alerts" checked={soundAlerts} onCheckedChange={setSoundAlerts} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t("notifications.alertThreshold")}</label>
                  <p className="text-xs text-psi-text-secondary mb-2">{t("notifications.alertThresholdDescription")}</p>
                  <div className="flex items-center gap-3 max-w-xs">
                    <input
                      type="range"
                      min={0} max={100} step={5}
                      value={alertThreshold}
                      onChange={(e) => setAlertThreshold(Number(e.target.value))}
                      className="flex-1 accent-psi-electric"
                    />
                    <span className="text-sm font-mono font-bold text-psi-electric w-10 text-right">{alertThreshold}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t("notifications.fraudAlertEmail")}</label>
                  <input
                    type="email"
                    value={fraudAlertEmail}
                    onChange={(e) => setFraudAlertEmail(e.target.value)}
                    placeholder={tc("emailPlaceholder")}
                    className="w-full max-w-sm rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t("notifications.digestFrequency")}</label>
                  <select
                    value={digestFrequency}
                    onChange={(e) => setDigestFrequency(e.target.value as DigestFrequency)}
                    className="w-full max-w-xs rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                  >
                    <option value="daily">{t("notifications.daily")}</option>
                    <option value="weekly">{t("notifications.weekly")}</option>
                    <option value="monthly">{t("notifications.monthly")}</option>
                    <option value="never">{t("notifications.never")}</option>
                  </select>
                </div>
              </div>
            )}

            {/* ═══════════ ACCOUNT ═══════════ */}
            {activeSection === "account" && (
              <>
                {isAuthenticated ? (
                  <div className="space-y-4">
                    <div className="responsive-grid-2">
                      <div>
                        <label className="block text-sm font-medium mb-1">{t("account.displayName")}</label>
                        <input
                          type="text" defaultValue={authUser?.full_name || ""}
                          className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">{t("account.jobTitle")}</label>
                        <input
                          type="text" defaultValue={authUser?.role?.replace("_", " ") || ""}
                          className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">{tc("email")}</label>
                        <input
                          type="email" defaultValue={authUser?.email || ""}
                          className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">{t("account.phone")}</label>
                        <input
                          type="tel" defaultValue=""
                          placeholder={tc("phonePlaceholder")}
                          className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Guest / Visitor — blurred form + avatar + login CTA */
                  <div className="space-y-4">
                    {/* Blurred dummy form */}
                    <div className="relative overflow-hidden rounded-xl border border-psi-border">
                      {/* Blur overlay */}
                      <div className="absolute inset-0 z-10 backdrop-blur-md bg-psi-navy/40" />
                      <div className="responsive-grid-2 p-4 select-none pointer-events-none opacity-30">
                        <div>
                          <label className="block text-sm font-medium mb-1">{t("account.displayName")}</label>
                          <div className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-secondary h-9" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">{t("account.jobTitle")}</label>
                          <div className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-secondary h-9" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">{tc("email")}</label>
                          <div className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-secondary h-9" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">{t("account.phone")}</label>
                          <div className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-secondary h-9" />
                        </div>
                      </div>
                    </div>

                    {/* Centered guest prompt */}
                    <div className="flex flex-col items-center text-center py-4">
                      {/* Avatar — same style as Navbar guest avatar */}
                      <Avatar className="h-16 w-16 border-2 border-psi-border ring-4 ring-psi-navy/80">
                        <AvatarFallback className="text-2xl font-bold bg-psi-border/50 text-psi-text-secondary">
                          <User className="h-8 w-8" />
                        </AvatarFallback>
                      </Avatar>

                      <h3 className="mt-4 text-base font-semibold text-psi-text-primary">
                        {t("account.guestTitle")}
                      </h3>
                      <p className="mt-1 text-sm text-psi-text-secondary max-w-xs">
                        {t("account.guestDescription")}
                      </p>

                      {/* CTA buttons */}
                      <div className="flex flex-wrap items-center gap-3 mt-5">
                        <Link
                          href="/auth/login"
                          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-psi-electric text-white text-sm font-medium hover:bg-psi-electric/90 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric"
                        >
                          <LogIn className="h-4 w-4" />
                          {t("account.signIn")}
                        </Link>
                        <Link
                          href="/auth/login"
                          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-psi-border text-psi-text-secondary text-sm font-medium hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric"
                        >
                          <UserPlus className="h-4 w-4" />
                          {t("account.signUp")}
                        </Link>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* ═══════════ SECURITY ═══════════ */}
            {activeSection === "security" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium">{t("security.twoFactor")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("security.twoFactorDescription")}</p>
                  </div>
                  <Switch checked={true} onCheckedChange={() => {}} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t("security.sessionTimeout")}</label>
                  <p className="text-xs text-psi-text-secondary mb-2">{t("security.sessionTimeoutDescription")}</p>
                  <select
                    defaultValue="30"
                    className="w-full max-w-xs rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric"
                  >
                    <option value="15">15 {t("security.minutes")}</option>
                    <option value="30">30 {t("security.minutes")}</option>
                    <option value="60">60 {t("security.minutes")}</option>
                    <option value="120">120 {t("security.minutes")}</option>
                  </select>
                </div>
                <div className="responsive-grid-2 pt-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">{t("security.currentPassword")}</label>
                    <input type="password" className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric" />
                  </div>
                  <div />
                  <div>
                    <label className="block text-sm font-medium mb-1">{t("security.newPassword")}</label>
                    <input type="password" className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">{t("security.confirmPassword")}</label>
                    <input type="password" className="w-full rounded-lg border border-psi-border bg-psi-graphite px-3 py-2 text-sm text-psi-text-primary focus:outline-none focus:ring-2 focus:ring-psi-electric" />
                  </div>
                </div>
              </div>
            )}

            {/* ═══════════ PRIVACY & DATA ═══════════ */}
            {activeSection === "privacy" && (
              <PrivacySection t={t} tc={tc} />
            )}

            {/* ═══════════ ADVANCED ═══════════ */}
            {activeSection === "advanced" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between py-1">
                  <div>
                    <label className="text-sm font-medium" htmlFor="dev-mode">{t("advanced.developerMode")}</label>
                    <p className="text-xs text-psi-text-secondary">{t("advanced.developerModeDescription")}</p>
                  </div>
                  <Switch id="dev-mode" checked={developerMode} onCheckedChange={setDeveloperMode} />
                </div>
                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    onClick={() => alert(tc("success"))}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-psi-border text-sm text-psi-text-secondary hover:bg-white/5 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                    {t("advanced.cacheClear")}
                  </button>
                  <button
                    onClick={() => alert(tc("success"))}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-psi-border text-sm text-psi-text-secondary hover:bg-white/5 transition-colors"
                  >
                    {t("advanced.exportData")}
                  </button>
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-psi-fraud/50 text-sm text-psi-fraud hover:bg-psi-fraud/10 transition-colors"
                  >
                    <RotateCcw className="h-4 w-4" />
                    {t("advanced.resetSettings")}
                  </button>
                </div>
              </div>
            )}

            {/* Save button row */}
            <div className="mt-6 pt-4 border-t border-psi-border flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className={cn(
                  "flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm transition-all",
                  saved
                    ? "bg-psi-emerald text-white"
                    : "bg-psi-electric text-white hover:bg-psi-electric/90",
                  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {saved ? (
                  <>
                    <Check className="h-4 w-4" />
                    {t("actions.saved")}
                  </>
                ) : saving ? (
                  <>
                    <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t("actions.saving")}
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    {t("actions.saveSettings")}
                  </>
                )}
              </button>
              <button
                onClick={handleReset}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-psi-border text-sm text-psi-text-secondary hover:bg-white/5 transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                {t("actions.resetToDefaults")}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
