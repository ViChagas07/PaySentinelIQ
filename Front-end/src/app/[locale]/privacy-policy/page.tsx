// ============================================================
// PaySentinelIQ — Privacy Policy & Terms of Use
// LGPD-compliant, premium design inspired by Stripe/Vercel/Notion
// ============================================================

"use client";

import { useTranslations, useLocale } from "next-intl";
import { motion } from "framer-motion";
import { Link } from "@/i18n/navigation";
import Image from "next/image";
import {
  Shield, Lock, FileText, Eye, Download, Trash2,
  Database, Server, Globe, Mail, AlertTriangle,
  FileCheck, UserCheck, Clock, Key, ExternalLink,
  ChevronRight, Gavel, Fingerprint, ScanEye,
  Cookie, Bell, ShieldCheck, ClipboardList, BadgeCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AppName } from "@/components/shared/AppName";
import { LandingNav } from "@/components/landing/LandingNav";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { useAuthStore } from "@/stores";

// ── Section wrapper ── //

function Section({
  id,
  icon: Icon,
  title,
  children,
  delay = 0,
}: {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ margin: "-40px" }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className="scroll-mt-28"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-psi-electric/10">
          <Icon className="h-4.5 w-4.5 text-psi-electric" />
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-white">{title}</h2>
      </div>
      <div className="prose prose-invert prose-sm max-w-none
        prose-headings:text-white prose-headings:font-semibold
        prose-p:text-white/75 prose-p:leading-relaxed
        prose-li:text-white/75 prose-li:leading-relaxed
        prose-strong:text-white/90 prose-strong:font-semibold
        prose-a:text-psi-electric prose-a:no-underline hover:prose-a:underline
        prose-code:bg-white/[0.06] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-white/80 prose-code:text-xs
        space-y-4
      ">
        {children}
      </div>
    </motion.section>
  );
}

// ── Badge ── //

function ComplianceBadge({
  icon: Icon,
  label,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3.5 py-1.5 text-xs text-white/60">
      <Icon className="h-3.5 w-3.5 text-psi-emerald/70" />
      <span>{label}</span>
    </div>
  );
}

// ── Table of Contents link ── //

function TocLink({ href, label }: { href: string; label: string }) {
  return (
    <li>
      <a
        href={href}
        className="flex items-center gap-1.5 text-sm text-white/50 hover:text-white transition-colors group py-1"
      >
        <ChevronRight className="h-3.5 w-3.5 text-psi-electric/40 group-hover:text-psi-electric transition-colors" />
        {label}
      </a>
    </li>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════

export default function PrivacyPolicyPage() {
  const t = useTranslations("privacy");
  const tc = useTranslations("common");
  const locale = useLocale();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  // Navigation: show app nav if authenticated, landing nav otherwise
  const Nav = isAuthenticated ? null : LandingNav; // LandingNav handles auth state internally

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#050816]">
      {/* Background */}
      <div className="pointer-events-none fixed inset-0" aria-hidden="true">
        <div className="absolute -left-40 top-0 h-[600px] w-[600px] rounded-full bg-[#6A4DFF] opacity-[0.03] blur-[120px]" />
        <div className="absolute -right-40 top-1/3 h-[500px] w-[500px] rounded-full bg-[#00E5FF] opacity-[0.02] blur-[100px]" />
        <div className="absolute bottom-0 left-1/4 h-[400px] w-[400px] rounded-full bg-[#1E6FFF] opacity-[0.03] blur-[100px]" />
        <div
          className="absolute inset-0 opacity-[0.01]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />
      </div>

      {/* Navigation */}
      <LandingNav />

      {/* Content */}
      <main className="relative z-10 mx-auto max-w-4xl px-4 pt-28 pb-24 sm:px-6 lg:px-8">
        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="mb-16 text-center"
        >
          {/* Logo */}
          <div className="mb-6">
            <Image
              src="/PSI_Logo2.png"
              alt={tc("appName")}
              width={64}
              height={64}
              className="mx-auto h-16 w-auto object-contain drop-shadow-[0_0_20px_rgba(56,189,248,0.2)]"
            />
          </div>

          {/* Title */}
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 tracking-tight">
            {t("pageTitle")}
          </h1>
          <p className="text-sm sm:text-base text-white/50 max-w-xl mx-auto leading-relaxed">
            {t("pageSubtitle")}
          </p>

          {/* Version & last updated */}
          <div className="mt-5 flex items-center justify-center gap-4 text-xs text-white/30">
            <span>{t("version")}: 1.0.0</span>
            <span className="w-1 h-1 rounded-full bg-white/10" />
            <span>{t("lastUpdated")}: {t("effectiveDate")}</span>
          </div>

          {/* Compliance badges */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <ComplianceBadge icon={ShieldCheck} label="LGPD Compliant" />
            <ComplianceBadge icon={BadgeCheck} label="SOC 2 Ready" />
            <ComplianceBadge icon={Lock} label="TLS 1.3" />
            <ComplianceBadge icon={Fingerprint} label="MFA Protected" />
            <ComplianceBadge icon={Database} label="Encrypted at Rest" />
          </div>
        </motion.div>

        {/* ── Table of Contents ── */}
        <motion.nav
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="mb-16 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6"
        >
          <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider mb-4">
            {t("tableOfContents")}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1">
            <ul className="space-y-0.5">
              <TocLink href="#introduction" label={t("tocIntroduction")} />
              <TocLink href="#data-collected" label={t("tocDataCollected")} />
              <TocLink href="#purpose" label={t("tocPurpose")} />
              <TocLink href="#sharing" label={t("tocSharing")} />
              <TocLink href="#security" label={t("tocSecurity")} />
              <TocLink href="#retention" label={t("tocRetention")} />
              <TocLink href="#rights" label={t("tocRights")} />
              <TocLink href="#deletion" label={t("tocDeletion")} />
            </ul>
            <ul className="space-y-0.5">
              <TocLink href="#export" label={t("tocExport")} />
              <TocLink href="#consent" label={t("tocConsent")} />
              <TocLink href="#cookies" label={t("tocCookies")} />
              <TocLink href="#minors" label={t("tocMinors")} />
              <TocLink href="#terms" label={t("tocTermsOfUse")} />
              <TocLink href="#changes" label={t("tocChanges")} />
              <TocLink href="#contact" label={t("tocContact")} />
            </ul>
          </div>
        </motion.nav>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 1 — INTRODUCTION */}
        {/* ═══════════════════════════════════════ */}
        <Section id="introduction" icon={FileText} title={t("sectionIntroduction")} delay={0.05}>
          <p>{t("introParagraph1")}</p>
          <p>{t("introParagraph2")}</p>
          <p>{t("introParagraph3")}</p>
          <div className="rounded-xl border border-psi-emerald/20 bg-psi-emerald/[0.03] p-5">
            <p className="text-sm text-white/70">
              <strong className="text-psi-emerald">{t("lgpdNotice")}</strong>{" "}
              {t("lgpdNoticeText")}
            </p>
          </div>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 2 — DATA COLLECTED */}
        {/* ═══════════════════════════════════════ */}
        <Section id="data-collected" icon={Database} title={t("sectionDataCollected")} delay={0.1}>
          <h3 className="text-base font-semibold text-white mt-6 mb-3">{t("authData")}</h3>
          <p>{t("authDataDesc")}</p>
          <ul>
            <li>{t("authDataName")}</li>
            <li>{t("authDataEmail")}</li>
            <li>{t("authDataAvatar")}</li>
          </ul>

          <h3 className="text-base font-semibold text-white mt-6 mb-3">{t("uploadedData")}</h3>
          <p>{t("uploadedDataDesc")}</p>
          <ul>
            <li>{t("uploadedPdfs")}</li>
            <li>{t("uploadedImages")}</li>
            <li>{t("uploadedReceipts")}</li>
            <li>{t("uploadedPayslips")}</li>
            <li>{t("uploadedReports")}</li>
          </ul>

          <h3 className="text-base font-semibold text-white mt-6 mb-3">{t("ocrData")}</h3>
          <p>{t("ocrDataDesc")}</p>
          <ul>
            <li>{t("ocrText")}</li>
            <li>{t("ocrMetadata")}</li>
            <li>{t("ocrFinancial")}</li>
          </ul>

          <h3 className="text-base font-semibold text-white mt-6 mb-3">{t("logData")}</h3>
          <p>{t("logDataDesc")}</p>
          <ul>
            <li>{t("logAccess")}</li>
            <li>{t("logActions")}</li>
            <li>{t("logSecurity")}</li>
          </ul>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 3 — PURPOSE */}
        {/* ═══════════════════════════════════════ */}
        <Section id="purpose" icon={ScanEye} title={t("sectionPurpose")} delay={0.15}>
          <p>{t("purposeIntro")}</p>
          <ul>
            <li><strong>{t("purposeAuth")}:</strong> {t("purposeAuthDesc")}</li>
            <li><strong>{t("purposeFraud")}:</strong> {t("purposeFraudDesc")}</li>
            <li><strong>{t("purposeAnalysis")}:</strong> {t("purposeAnalysisDesc")}</li>
            <li><strong>{t("purposeReports")}:</strong> {t("purposeReportsDesc")}</li>
            <li><strong>{t("purposeImprovement")}:</strong> {t("purposeImprovementDesc")}</li>
          </ul>
          <div className="rounded-xl border border-psi-electric/15 bg-psi-electric/[0.02] p-5">
            <p className="text-sm text-white/70">
              <strong className="text-psi-electric">{t("legalBasis")}:</strong>{" "}
              {t("legalBasisText")}
            </p>
          </div>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 4 — SHARING */}
        {/* ═══════════════════════════════════════ */}
        <Section id="sharing" icon={Server} title={t("sectionSharing")} delay={0.2}>
          <p>{t("sharingIntro")}</p>
          <ul>
            <li>
              <strong>{t("sharingAWS")}:</strong> {t("sharingAWSDesc")}
            </li>
            <li>
              <strong>{t("sharingGoogle")}:</strong> {t("sharingGoogleDesc")}
            </li>
            <li>
              <strong>{t("sharingOCR")}:</strong> {t("sharingOCRDesc")}
            </li>
            <li>
              <strong>{t("sharingMonitoring")}:</strong> {t("sharingMonitoringDesc")}
            </li>
          </ul>
          <p className="text-sm italic text-white/40">{t("sharingNoSell")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 5 — SECURITY */}
        {/* ═══════════════════════════════════════ */}
        <Section id="security" icon={Shield} title={t("sectionSecurity")} delay={0.25}>
          <p>{t("securityIntro")}</p>
          <ul>
            <li><strong>{t("securityEncryption")}:</strong> {t("securityEncryptionDesc")}</li>
            <li><strong>{t("securityHTTPS")}:</strong> {t("securityHTTPSDesc")}</li>
            <li><strong>{t("securityAuth")}:</strong> {t("securityAuthDesc")}</li>
            <li><strong>{t("securityAccess")}:</strong> {t("securityAccessDesc")}</li>
            <li><strong>{t("securityAudit")}:</strong> {t("securityAuditDesc")}</li>
            <li><strong>{t("securityMFA")}:</strong> {t("securityMFADesc")}</li>
          </ul>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 6 — RETENTION */}
        {/* ═══════════════════════════════════════ */}
        <Section id="retention" icon={Clock} title={t("sectionRetention")} delay={0.3}>
          <p>{t("retentionIntro")}</p>
          <ul>
            <li><strong>{t("retentionDocuments")}:</strong> {t("retentionDocumentsDesc")}</li>
            <li><strong>{t("retentionOCR")}:</strong> {t("retentionOCRDesc")}</li>
            <li><strong>{t("retentionLogs")}:</strong> {t("retentionLogsDesc")}</li>
            <li><strong>{t("retentionAccount")}:</strong> {t("retentionAccountDesc")}</li>
          </ul>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 7 — LGPD RIGHTS */}
        {/* ═══════════════════════════════════════ */}
        <Section id="rights" icon={UserCheck} title={t("sectionRights")} delay={0.35}>
          <p>{t("rightsIntro")}</p>
          <ul>
            <li>
              <strong>{t("rightAccess")}:</strong> {t("rightAccessDesc")}
            </li>
            <li>
              <strong>{t("rightCorrection")}:</strong> {t("rightCorrectionDesc")}
            </li>
            <li>
              <strong>{t("rightAnonymization")}:</strong> {t("rightAnonymizationDesc")}
            </li>
            <li>
              <strong>{t("rightPortability")}:</strong> {t("rightPortabilityDesc")}
            </li>
            <li>
              <strong>{t("rightDeletion")}:</strong> {t("rightDeletionDesc")}
            </li>
            <li>
              <strong>{t("rightRevocation")}:</strong> {t("rightRevocationDesc")}
            </li>
          </ul>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 8 — DATA DELETION */}
        {/* ═══════════════════════════════════════ */}
        <Section id="deletion" icon={Trash2} title={t("sectionDeletion")} delay={0.4}>
          <p>{t("deletionIntro")}</p>
          <ol className="list-decimal pl-5 space-y-1.5">
            <li>{t("deletionStep1")}</li>
            <li>{t("deletionStep2")}</li>
            <li>{t("deletionStep3")}</li>
            <li>{t("deletionStep4")}</li>
            <li>{t("deletionStep5")}</li>
          </ol>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 9 — DATA EXPORT */}
        {/* ═══════════════════════════════════════ */}
        <Section id="export" icon={Download} title={t("sectionExport")} delay={0.45}>
          <p>{t("exportIntro")}</p>
          <p>{t("exportFormat")}</p>
          <ul>
            <li>{t("exportProfile")}</li>
            <li>{t("exportConsent")}</li>
            <li>{t("exportDocuments")}</li>
            <li>{t("exportReports")}</li>
            <li>{t("exportActivity")}</li>
          </ul>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 10 — CONSENT */}
        {/* ═══════════════════════════════════════ */}
        <Section id="consent" icon={FileCheck} title={t("sectionConsent")} delay={0.5}>
          <p>{t("consentIntro")}</p>
          <p>{t("consentRecord")}</p>
          <ul>
            <li>{t("consentVersion")}</li>
            <li>{t("consentTimestamp")}</li>
            <li>{t("consentIP")}</li>
            <li>{t("consentMethod")}</li>
          </ul>
          <p>{t("consentWithdraw")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 11 — COOKIES */}
        {/* ═══════════════════════════════════════ */}
        <Section id="cookies" icon={Cookie} title={t("sectionCookies")} delay={0.55}>
          <p>{t("cookiesIntro")}</p>
          <ul>
            <li><strong>{t("cookiesEssential")}:</strong> {t("cookiesEssentialDesc")}</li>
            <li><strong>{t("cookiesPreferences")}:</strong> {t("cookiesPreferencesDesc")}</li>
            <li><strong>{t("cookiesAnalytics")}:</strong> {t("cookiesAnalyticsDesc")}</li>
          </ul>
          <p>{t("cookiesNoTracking")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 12 — MINORS */}
        {/* ═══════════════════════════════════════ */}
        <Section id="minors" icon={AlertTriangle} title={t("sectionMinors")} delay={0.6}>
          <p>{t("minorsIntro")}</p>
          <p>{t("minorsAction")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* ═══ TERMS OF USE ═══ */}
        {/* ═══════════════════════════════════════ */}
        <div className="my-16 border-t border-white/[0.06]" />

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ margin: "-40px" }}
          transition={{ duration: 0.5 }}
          className="mb-12 text-center"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.06] bg-white/[0.02] px-4 py-1.5 text-xs text-white/40 mb-4">
            <Gavel className="h-3 w-3" />
            <span>{t("termsBadge")}</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            {t("termsTitle")}
          </h2>
          <p className="mt-3 text-sm text-white/40">{t("termsSubtitle")}</p>
        </motion.div>

        {/* TERMS: Permitted Use */}
        <Section id="terms" icon={Gavel} title={t("termsSectionUse")} delay={0.1}>
          <p>{t("termsUseIntro")}</p>
          <ul>
            <li>{t("termsUse1")}</li>
            <li>{t("termsUse2")}</li>
            <li>{t("termsUse3")}</li>
            <li>{t("termsUse4")}</li>
          </ul>
        </Section>

        {/* TERMS: Responsibilities */}
        <Section id="terms-responsibilities" icon={ClipboardList} title={t("termsSectionResponsibilities")} delay={0.15}>
          <p>{t("termsRespIntro")}</p>
          <ul>
            <li>{t("termsResp1")}</li>
            <li>{t("termsResp2")}</li>
            <li>{t("termsResp3")}</li>
          </ul>
        </Section>

        {/* TERMS: Prohibitions */}
        <Section id="terms-prohibitions" icon={AlertTriangle} title={t("termsSectionProhibitions")} delay={0.2}>
          <p>{t("termsProhibIntro")}</p>
          <ul>
            <li><strong>{t("termsProhibFraud")}</strong> — {t("termsProhibFraudDesc")}</li>
            <li><strong>{t("termsProhibFake")}</strong> — {t("termsProhibFakeDesc")}</li>
            <li><strong>{t("termsProhibAbuse")}</strong> — {t("termsProhibAbuseDesc")}</li>
            <li><strong>{t("termsProhibReverse")}</strong> — {t("termsProhibReverseDesc")}</li>
            <li><strong>{t("termsProhibUnauthorized")}</strong> — {t("termsProhibUnauthorizedDesc")}</li>
          </ul>
        </Section>

        {/* TERMS: Limitation of Liability */}
        <Section id="terms-liability" icon={AlertTriangle} title={t("termsSectionLiability")} delay={0.25}>
          <p>{t("termsLiability1")}</p>
          <p>{t("termsLiability2")}</p>
          <p>{t("termsLiability3")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 13 — CHANGES */}
        {/* ═══════════════════════════════════════ */}
        <div className="my-16 border-t border-white/[0.06]" />
        <Section id="changes" icon={Bell} title={t("sectionChanges")} delay={0.3}>
          <p>{t("changesIntro")}</p>
          <p>{t("changesNotice")}</p>
        </Section>

        {/* ═══════════════════════════════════════ */}
        {/* SECTION 14 — CONTACT */}
        {/* ═══════════════════════════════════════ */}
        <Section id="contact" icon={Mail} title={t("sectionContact")} delay={0.35}>
          <p>{t("contactIntro")}</p>
          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 space-y-3">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-psi-electric" />
              <div>
                <p className="text-sm font-semibold text-white">{t("contactEmail")}</p>
                <a href="mailto:privacy@paysentineliq.com" className="text-sm text-psi-electric hover:underline">
                  privacy@paysentineliq.com
                </a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-psi-electric" />
              <div>
                <p className="text-sm font-semibold text-white">{t("contactResponse")}</p>
                <p className="text-sm text-white/50">{t("contactResponseTime")}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-psi-electric" />
              <div>
                <p className="text-sm font-semibold text-white">{t("contactDPO")}</p>
                <p className="text-sm text-white/50">{t("contactDPOName")}</p>
              </div>
            </div>
          </div>
        </Section>

        {/* ── Back to home or dashboard ── */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ margin: "-40px" }}
          className="mt-20 text-center"
        >
          <Link
            href={isAuthenticated ? "/dashboard" : "/"}
            className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm text-white/70 hover:text-white hover:border-white/[0.15] transition-all"
          >
            {isAuthenticated ? t("backToDashboard") : t("backToHome")}
            <ChevronRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </main>

      {/* Footer */}
      <LandingFooter />
    </div>
  );
}
