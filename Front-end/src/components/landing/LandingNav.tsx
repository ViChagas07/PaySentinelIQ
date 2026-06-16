// ============================================================
// PaySentinelIQ — Landing Page Navigation
// Minimal, transparent top bar for the public landing experience
// ============================================================

"use client";

import { useState, useEffect, useMemo } from "react";
import { useTranslations, useLocale } from "next-intl";
import { Link, useRouter } from "@/i18n/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores";
import { Button } from "@/components/ui/Button";
import { AppName } from "@/components/shared/AppName";
import Image from "next/image";
import { Menu, X, Globe, ChevronDown, LogIn, LayoutDashboard } from "lucide-react";

const LOCALES = [
  { code: "en", label: "English" },
  { code: "pt-BR", label: "Português (Brasil)" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
  { code: "ja", label: "日本語" },
  { code: "zh", label: "中文" },
  { code: "ru", label: "Русский" },
  { code: "ar", label: "العربية" },
];

export function LandingNav() {
  const t = useTranslations("landing");
  const tc = useTranslations("common");
  const locale = useLocale();
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  // ── User avatar helpers ──
  const userInitials = useMemo(
    () =>
      user?.full_name
        ?.split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase() || "?",
    [user?.full_name]
  );

  const highResAvatarUrl = useMemo(
    () => user?.avatar_url?.replace(/=s96-c$/, "=s256-c"),
    [user?.avatar_url]
  );

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const currentLocale = LOCALES.find((l) => l.code === locale);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-[#050816]/80 backdrop-blur-xl border-b border-white/[0.06] shadow-lg shadow-black/10"
          : "bg-transparent"
      )}
    >
      <div className="mx-auto max-w-7xl flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-3 shrink-0 group"
          aria-label={tc("appName")}
        >
          <Image
            src="/PSI_Logo2.png"
            alt={tc("appName")}
            width={40}
            height={40}
            className="h-9 w-auto object-contain"
            priority
          />
          <span className="hidden sm:block">
            <AppName as="span" className="text-base font-bold text-white" />
          </span>
        </Link>

        {/* Desktop nav links */}
        <nav className="hidden lg:flex items-center gap-1">
          <a
            href="#features"
            className="px-3 py-2 text-sm text-white/60 hover:text-white transition-colors rounded-lg hover:bg-white/[0.05]"
          >
            {t("nav.features")}
          </a>
          <a
            href="#how-it-works"
            className="px-3 py-2 text-sm text-white/60 hover:text-white transition-colors rounded-lg hover:bg-white/[0.05]"
          >
            {t("nav.howItWorks")}
          </a>
          <a
            href="#preview"
            className="px-3 py-2 text-sm text-white/60 hover:text-white transition-colors rounded-lg hover:bg-white/[0.05]"
          >
            {t("nav.preview")}
          </a>
          <a
            href="#stats"
            className="px-3 py-2 text-sm text-white/60 hover:text-white transition-colors rounded-lg hover:bg-white/[0.05]"
          >
            {t("nav.stats")}
          </a>
        </nav>

        {/* Right actions */}
        <div className="flex items-center gap-2">
          {/* Language switcher */}
          <div className="relative hidden sm:block">
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-sm text-white/60 hover:text-white hover:bg-white/[0.05] transition-colors"
              aria-expanded={langOpen}
              aria-label={tc("language")}
            >
              <Globe className="h-4 w-4" />
              <span className="hidden md:inline">{currentLocale?.label || locale}</span>
              <ChevronDown className={cn("h-3 w-3 transition-transform", langOpen && "rotate-180")} />
            </button>
            <AnimatePresence>
              {langOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.96 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-44 rounded-xl border border-white/[0.08] bg-[#0B1026]/95 backdrop-blur-xl shadow-2xl overflow-hidden z-50"
                >
                  {LOCALES.map(({ code, label }) => (
                    <Link
                      key={code}
                      href="/"
                      locale={code}
                      onClick={() => setLangOpen(false)}
                      className={cn(
                        "flex w-full items-center gap-3 px-3 py-2.5 text-sm transition-colors",
                        locale === code
                          ? "bg-[#1E6FFF]/10 text-[#1E6FFF]"
                          : "text-white/60 hover:bg-white/[0.05] hover:text-white"
                      )}
                    >
                      <span className="flex-1 text-left">{label}</span>
                      {locale === code && (
                        <span className="h-1.5 w-1.5 rounded-full bg-[#1E6FFF]" />
                      )}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* CTA or Dashboard + Avatar */}
          {isAuthenticated ? (
            <div className="hidden sm:flex items-center gap-2">
              {/* Avatar circle */}
              <div className="relative h-8 w-8 shrink-0 rounded-full border-2 border-[#1E6FFF]/40 overflow-hidden bg-[#1E6FFF]/15">
                {user?.avatar_url ? (
                  <img
                    src={highResAvatarUrl ?? user.avatar_url}
                    alt={user?.full_name || ""}
                    className="absolute inset-0 h-full w-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[#1E6FFF]">
                    {userInitials}
                  </span>
                )}
              </div>
              <Button
                onClick={() => router.push("/dashboard")}
                variant="ghost"
                size="sm"
                className="gap-2 text-white/70 hover:text-white"
              >
                <LayoutDashboard className="h-4 w-4" />
                <span className="hidden md:inline">{t("nav.dashboard")}</span>
              </Button>
            </div>
          ) : (
            <Button
              onClick={() => router.push("/auth/login")}
              size="sm"
              className="gap-2 bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] hover:from-[#1E6FFF]/90 hover:to-[#6A4DFF]/90 text-white shadow-lg shadow-[#1E6FFF]/20"
            >
              <LogIn className="h-4 w-4" />
              <span>{t("nav.signIn")}</span>
            </Button>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden rounded-lg p-2 text-white/60 hover:text-white hover:bg-white/[0.05] transition-colors"
            aria-label={mobileOpen ? tc("close") : tc("openMenu")}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="lg:hidden border-t border-white/[0.06] bg-[#050816]/95 backdrop-blur-xl overflow-hidden"
          >
            <nav className="flex flex-col px-4 py-3 space-y-1">
              <a
                href="#features"
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 text-sm text-white/60 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors"
              >
                {t("nav.features")}
              </a>
              <a
                href="#how-it-works"
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 text-sm text-white/60 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors"
              >
                {t("nav.howItWorks")}
              </a>
              <a
                href="#preview"
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 text-sm text-white/60 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors"
              >
                {t("nav.preview")}
              </a>
              <a
                href="#stats"
                onClick={() => setMobileOpen(false)}
                className="px-3 py-2.5 text-sm text-white/60 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors"
              >
                {t("nav.stats")}
              </a>
              <div className="pt-2 border-t border-white/[0.06]">
                {isAuthenticated ? (
                  <div className="space-y-2">
                    {/* User identity row */}
                    <div className="flex items-center gap-3 px-3 py-2">
                      <div className="relative h-9 w-9 shrink-0 rounded-full border-2 border-[#1E6FFF]/40 overflow-hidden bg-[#1E6FFF]/15">
                        {user?.avatar_url ? (
                          <img
                            src={highResAvatarUrl ?? user.avatar_url}
                            alt={user?.full_name || ""}
                            className="absolute inset-0 h-full w-full object-cover"
                            referrerPolicy="no-referrer"
                          />
                        ) : (
                          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[#1E6FFF]">
                            {userInitials}
                          </span>
                        )}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="text-sm font-medium text-white truncate">
                          {user?.full_name || t("nav.unknownUser")}
                        </span>
                        <span className="text-[10px] text-white/40">
                          {user?.email || ""}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setMobileOpen(false);
                        router.push("/dashboard");
                      }}
                      className="flex w-full items-center gap-2 px-3 py-2.5 text-sm text-[#1E6FFF] hover:bg-[#1E6FFF]/5 rounded-lg transition-colors"
                    >
                      <LayoutDashboard className="h-4 w-4" />
                      {t("nav.dashboard")}
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setMobileOpen(false);
                      router.push("/auth/login");
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2.5 text-sm font-medium bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] text-white rounded-lg"
                  >
                    <LogIn className="h-4 w-4" />
                    {t("nav.signIn")}
                  </button>
                )}
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
