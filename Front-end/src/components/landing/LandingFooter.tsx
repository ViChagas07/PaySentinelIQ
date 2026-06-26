// ============================================================
// PaySentinelIQ — Landing Footer
// Enterprise multi-column footer with brand, product, company, legal
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { AppName } from "@/components/shared/AppName";
import Image from "next/image";
import { Globe, Mail, ExternalLink, Link2 } from "lucide-react";

const SOCIAL_LINKS = [
  { href: "https://github.com", icon: ExternalLink, label: "GitHub" },
  { href: "https://linkedin.com", icon: Link2, label: "LinkedIn" },
  { href: "mailto:contact@paysentinel.com", icon: Mail, label: "Email" },
];

const PRODUCT_LINKS = [
  { href: "#", key: "footer.features" },
  { href: "#", key: "footer.pricing" },
  { href: "#", key: "footer.security" },
];

const COMPANY_LINKS = [
  { href: "#", key: "footer.about" },
  { href: "#", key: "footer.docs" },
  { href: "#", key: "footer.support" },
];

const LEGAL_LINKS = [
  { href: "/privacy-policy", key: "footer.privacy" },
  { href: "/privacy-policy", key: "footer.terms" },
];

const LOCALES = [
  { code: "en", label: "English" },
  { code: "pt-BR", label: "Português" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "ja", label: "日本語" },
  { code: "zh", label: "中文" },
  { code: "ru", label: "Русский" },
  { code: "ar", label: "العربية" },
];

const footerVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4, ease: "easeOut" as const },
  }),
};

export function LandingFooter() {
  const t = useTranslations("landing");
  const tc = useTranslations("common");

  return (
    <footer className="w-full border-t border-white/[0.06] bg-[#050816]">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {/* Column 1 — Brand */}
          <motion.div
            custom={0}
            initial="hidden"
            whileInView="visible"
            viewport={{ margin: "-40px" }}
            variants={footerVariants}
          >
            <Link href="/" className="inline-flex items-center gap-2">
              <span className="inline-flex items-center gap-2">
                <Image
                  src="/PSI_Logo2.png"
                  alt={tc("appName")}
                  width={32}
                  height={32}
                  className="h-8 w-auto object-contain"
                />
                <AppName as="span" className="text-sm text-white/60" />
              </span>
            </Link>

            <p className="mt-3 text-sm leading-relaxed text-white/40">
              {t("footer.tagline")}
            </p>

            {/* Social links */}
            <div className="mt-5 flex items-center gap-2">
              {SOCIAL_LINKS.map((item) => {
                const Icon = item.icon;
                return (
                  <a
                    key={item.label}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={item.label}
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-lg",
                      "text-white/30 hover:bg-white/[0.06] hover:text-white",
                      "transition-colors duration-200"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </a>
                );
              })}
            </div>
          </motion.div>

          {/* Column 2 — Product */}
          <motion.div
            custom={1}
            initial="hidden"
            whileInView="visible"
            viewport={{ margin: "-40px" }}
            variants={footerVariants}
          >
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-white/50">
              {t("footer.product")}
            </h3>
            <ul className="space-y-2.5">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.key}>
                  <a
                    href={link.href}
                    className="text-sm text-white/40 transition-colors hover:text-white"
                  >
                    {t(link.key)}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Column 3 — Company */}
          <motion.div
            custom={2}
            initial="hidden"
            whileInView="visible"
            viewport={{ margin: "-40px" }}
            variants={footerVariants}
          >
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-white/50">
              {t("footer.company")}
            </h3>
            <ul className="space-y-2.5">
              {COMPANY_LINKS.map((link) => (
                <li key={link.key}>
                  <a
                    href={link.href}
                    className="text-sm text-white/40 transition-colors hover:text-white"
                  >
                    {t(link.key)}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Column 4 — Legal */}
          <motion.div
            custom={3}
            initial="hidden"
            whileInView="visible"
            viewport={{ margin: "-40px" }}
            variants={footerVariants}
          >
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-white/50">
              {t("footer.legal")}
            </h3>
            <ul className="space-y-2.5">
              {LEGAL_LINKS.map((link) => (
                <li key={link.key}>
                  <Link
                    href={link.href}
                    className="text-sm text-white/40 transition-colors hover:text-white"
                  >
                    {t(link.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/[0.06] pt-6 sm:flex-row">
          <p className="text-xs text-white/30">{t("footer.copyright")}</p>

          {/* Locale display */}
          <div className="flex items-center gap-1.5 text-xs text-white/30">
            <Globe className="h-3 w-3" />
            <span>{tc("language")}</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
