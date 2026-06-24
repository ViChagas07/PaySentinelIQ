// ============================================================
// PaySentinelIQ — App Footer (Authenticated Layout)
// Minimal, premium footer — Stripe/Vercel/Linear inspired
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Shield, FileText, Gavel, Mail } from "lucide-react";

export function AppFooter() {
  const t = useTranslations("privacy");
  const tc = useTranslations("common");

  return (
    <footer className="flex-shrink-0 border-t border-white/[0.06] bg-psi-navy/50 backdrop-blur-sm">
      <div className="mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
        {/* Copyright */}
        <p className="text-[11px] text-white/25 order-2 sm:order-1">
          &copy; {new Date().getFullYear()} {tc("appName")}
        </p>

        {/* Legal links */}
        <nav className="flex items-center gap-4 order-1 sm:order-2" aria-label={tc("legalLinks")}>
          <Link
            href="/privacy-policy"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white/70 transition-colors"
          >
            <FileText className="h-3 w-3 opacity-60" />
            <span>{t("privacyPolicyLink")}</span>
          </Link>

          <div className="w-px h-3 bg-white/[0.08]" aria-hidden="true" />

          <Link
            href="/privacy-policy"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white/70 transition-colors"
          >
            <Gavel className="h-3 w-3 opacity-60" />
            <span>{t("termsLink")}</span>
          </Link>

          <div className="w-px h-3 bg-white/[0.08]" aria-hidden="true" />

          <Link
            href="/privacy-policy#security"
            className="inline-flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white/70 transition-colors"
          >
            <Shield className="h-3 w-3 opacity-60" />
            <span>{t("securityLink")}</span>
          </Link>

          <div className="w-px h-3 bg-white/[0.08]" aria-hidden="true" />

          <a
            href="mailto:privacy@paysentineliq.com"
            className="inline-flex items-center gap-1.5 text-[11px] text-white/35 hover:text-white/70 transition-colors"
          >
            <Mail className="h-3 w-3 opacity-60" />
            <span>{t("contactLink")}</span>
          </a>
        </nav>
      </div>
    </footer>
  );
}
