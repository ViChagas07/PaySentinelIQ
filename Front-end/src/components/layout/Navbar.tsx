// ============================================================
// PaySentinelIQ — Top Navbar
// Enterprise navbar with global search, AI actions, alerts, tenant selector
// ============================================================

"use client";

import { useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { Link as IntlLink, useRouter } from "@/i18n/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useUIStore, useAuthStore, useAlertStore } from "@/stores";
import {
  Search, Menu, Bell, ChevronDown, Globe, User, LogOut, Settings, LogIn,
} from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";

// ── Available locales for the language switcher ── //
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

// ── Animated AI Robot Icon ── //
function AnimatedBotIcon({ isHovered }: { isHovered: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      {/* Antenna */}
      <path d="M12 3v2" />
      <circle cx="12" cy="2.5" r="1" fill="currentColor" stroke="none" />

      {/* Head housing */}
      <rect x="3" y="6" width="18" height="12" rx="3.5" />

      {/* Left eye — blinks by scaling Y to near-zero */}
      <motion.g
        animate={isHovered ? { scaleY: [1, 0.1, 1] } : { scaleY: 1 }}
        transition={{ duration: 0.35, times: [0, 0.5, 1], ease: "easeInOut" }}
        style={{ originX: "8.5px", originY: "11px" }}
      >
        <circle cx="8.5" cy="11" r="1.4" fill="currentColor" stroke="none" />
      </motion.g>

      {/* Right eye */}
      <motion.g
        animate={isHovered ? { scaleY: [1, 0.1, 1] } : { scaleY: 1 }}
        transition={{ duration: 0.35, times: [0, 0.5, 1], ease: "easeInOut" }}
        style={{ originX: "15.5px", originY: "11px" }}
      >
        <circle cx="15.5" cy="11" r="1.4" fill="currentColor" stroke="none" />
      </motion.g>

      {/* Subtle smile */}
      <path d="M8.5 15.2a3.2 3.2 0 0 0 7 0" strokeWidth="1.2" />
    </svg>
  );
}

// ── Animated Notification Bell Icon ── //
function AnimatedBellIcon({ isHovered }: { isHovered: boolean }) {
  return (
    <motion.span
      className="inline-flex"
      style={{ display: "inline-flex", transformOrigin: "50% 2px" }}
      animate={isHovered ? {
        rotate: [0, -10, 10, -7, 7, -4, 4, 0],
      } : {
        rotate: 0,
      }}
      transition={{ duration: 0.55, ease: "easeInOut" }}
    >
      <Bell className="h-5 w-5" />
    </motion.span>
  );
}

// ── Reusable hover button with icon animation + levitation ── //
function HoverButton({
  icon,
  isOpen,
  activeClass,
  inactiveClass,
  onClick,
  label,
  children,
}: {
  icon: (isHovered: boolean) => React.ReactNode;
  isOpen: boolean;
  activeClass: string;
  inactiveClass: string;
  onClick: () => void;
  label: string;
  children?: React.ReactNode;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        "relative rounded-lg p-2 transition-colors",
        isOpen ? activeClass : inactiveClass
      )}
      aria-label={label}
      aria-expanded={isOpen}
    >
      <motion.span
        className="flex items-center justify-center"
        animate={hovered ? { y: -2 } : { y: 0 }}
        transition={{ type: "spring", stiffness: 400, damping: 25, mass: 0.4 }}
      >
        {icon(hovered)}
      </motion.span>
      {children}
    </button>
  );
}

export function Navbar() {
  const t = useTranslations("nav");
  const tc = useTranslations("common");
  const ta = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const setSidebarMobileOpen = useUIStore((s) => s.setSidebarMobileOpen);
  const aiPanelOpen = useUIStore((s) => s.aiPanelOpen);
  const toggleAiPanel = useUIStore((s) => s.toggleAiPanel);
  const notificationsPanelOpen = useUIStore((s) => s.notificationsPanelOpen);
  const toggleNotificationsPanel = useUIStore((s) => s.toggleNotificationsPanel);
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);
  const unreadCount = useAlertStore((s) => s.unreadCount);

  const [searchFocused, setSearchFocused] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const [globeHovered, setGlobeHovered] = useState(false);

  const userInitials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() || "U";

  // Upgrade Google profile picture to high resolution (256×256)
  const highResAvatarUrl = user?.avatar_url?.replace(/=s96-c$/, "=s256-c");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/95 backdrop-blur-md px-4 lg:px-6">
      {/* Mobile menu toggle */}
      <button
        onClick={() => setSidebarMobileOpen(true)}
        className="lg:hidden rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary transition-colors"
        aria-label={t("openMenu")}
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Desktop sidebar toggle */}
      <button
        onClick={toggleSidebar}
        className="hidden lg:flex rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary transition-colors"
        aria-label={t("toggleSidebar")}
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Global Search */}
      <div
        className={cn(
          "relative flex-1 max-w-xl transition-all duration-200",
          searchFocused && "scale-[1.02]"
        )}
      >
        <div
          className={cn(
              "flex items-center gap-2 rounded-lg border bg-card/60 px-3 py-2 transition-all",
            searchFocused
              ? "border-psi-electric shadow-lg shadow-psi-electric/10"
              : "border-border"
          )}
        >
          <Search className="h-4 w-4 shrink-0 text-psi-text-secondary" />
          <input
            type="search"
            placeholder={t("searchPlaceholder")}
            className="flex-1 bg-transparent text-sm text-psi-text-primary placeholder:text-psi-text-secondary/50 outline-none"
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            aria-label={t("globalSearch")}
          />
          <kbd className="hidden sm:inline-flex h-5 items-center gap-0.5 rounded border border-border px-1.5 text-[10px] font-medium text-psi-text-secondary">
            <span className="text-xs">⌘</span>K
          </kbd>
        </div>
      </div>

      {/* Right actions — ml-auto keeps icons tracking the right wall on zoom out */}
      <div className="flex items-center gap-1 ml-auto pr-3">
        {/* AI Assistant quick toggle */}
        <HoverButton
          icon={(hovered) => <AnimatedBotIcon isHovered={hovered} />}
          isOpen={aiPanelOpen}
          activeClass="text-psi-electric bg-psi-electric/10"
          inactiveClass="text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-electric"
          onClick={toggleAiPanel}
          label={t("aiAssistant")}
        >
          <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-psi-emerald opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-psi-emerald" />
          </span>
        </HoverButton>

        {/* Notifications */}
        <HoverButton
          icon={(hovered) => <AnimatedBellIcon isHovered={hovered} />}
          isOpen={notificationsPanelOpen}
          activeClass="text-psi-text-primary bg-psi-border/50"
          inactiveClass="text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary"
          onClick={toggleNotificationsPanel}
          label={t("notificationsAria", { count: unreadCount })}
        >
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 min-w-5 px-1 text-[10px] leading-none"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
        </HoverButton>

        {/* Language switcher globe */}
        <div className="relative">
          <button
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
            onMouseEnter={() => setGlobeHovered(true)}
            onMouseLeave={() => setGlobeHovered(false)}
            className="rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary transition-colors"
            aria-expanded={showLanguageMenu}
            aria-label={tc("language")}
            aria-haspopup="true"
          >
            <motion.span
              className="inline-flex"
              style={{ display: "inline-flex", perspective: "40px" }}
              animate={globeHovered ? {
                rotate: [0, -8, -18, -30, -22, -10, 0],
              } : {
                rotate: 0,
              }}
              transition={{ duration: 0.7, ease: "easeInOut" }}
            >
              <Globe className="h-5 w-5" />
            </motion.span>
          </button>

          <AnimatePresence>
            {showLanguageMenu && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-border bg-card shadow-2xl shadow-black/30 overflow-hidden z-50"
              >
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-psi-text-secondary/60">
                    {tc("language")}
                  </p>
                </div>
                {LOCALES.map(({ code, label }) => (
                  <IntlLink
                    key={code}
                    href="/"
                    locale={code}
                    onClick={() => setShowLanguageMenu(false)}
                    className={cn(
                      "flex w-full items-center gap-3 px-3 py-2.5 text-sm transition-colors",
                      locale === code
                        ? "bg-psi-electric/10 text-psi-electric"
                        : "text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary"
                    )}
                  >
                    <span className="flex-1 text-left">{label}</span>
                    {locale === code && (
                      <span className="h-1.5 w-1.5 rounded-full bg-psi-electric" />
                    )}
                  </IntlLink>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-psi-border/50 transition-colors"
            aria-expanded={showUserMenu}
            aria-haspopup="true"
            aria-label={t("userMenu")}
          >
            <Avatar className="h-8 w-8 border-2 border-border">
              {isAuthenticated && highResAvatarUrl && (
                <AvatarImage
                  src={highResAvatarUrl}
                  alt={user?.full_name || ""}
                  className="object-cover"
                  referrerPolicy="no-referrer"
                />
              )}
              <AvatarFallback className={cn(
                "text-xs font-bold",
                isAuthenticated
                  ? "bg-psi-electric/20 text-psi-electric"
                  : "bg-psi-border/50 text-psi-text-secondary"
              )}>
                {isAuthenticated ? userInitials : "?"}
              </AvatarFallback>
            </Avatar>
            <div className="hidden md:block text-left">
              <p className="text-xs font-medium text-psi-text-primary leading-tight">
                {isAuthenticated ? (user?.full_name || t("unknownUser")) : ta("guest")}
              </p>
              <p className="text-[10px] text-psi-text-secondary leading-tight capitalize">
                {isAuthenticated ? (user?.role?.replace("_", " ") || ta("guest")) : ta("loginToAccount")}
              </p>
            </div>
            <ChevronDown
              className={cn(
                "hidden md:block h-3.5 w-3.5 text-psi-text-secondary transition-transform",
                showUserMenu && "rotate-180"
              )}
            />
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-border bg-card shadow-2xl shadow-black/30 overflow-hidden z-50"
              >
                {isAuthenticated ? (
                  <>
                    <div className="px-4 py-3 border-b border-border">
                      <p className="text-sm font-semibold text-psi-text-primary">
                        {user?.full_name}
                      </p>
                      <p className="text-xs text-psi-text-secondary">{user?.email}</p>
                    </div>
                    <div className="py-1">
                      <IntlLink
                        href="/profile"
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <User className="h-4 w-4" />
                        {t("profile")}
                      </IntlLink>
                      <IntlLink
                        href="/settings"
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <Settings className="h-4 w-4" />
                        {t("settings")}
                      </IntlLink>
                    </div>
                    <div className="border-t border-border py-1">
                      <button
                        onClick={() => {
                          setShowUserMenu(false);
                          logout();
                        }}
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-psi-fraud hover:bg-psi-fraud/10 transition-colors"
                      >
                        <LogOut className="h-4 w-4" />
                        {ta("signOutLabel")}
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="px-4 py-3 border-b border-border">
                      <p className="text-sm font-semibold text-psi-text-primary">
                        {ta("guest")}
                      </p>
                      <p className="text-xs text-psi-text-secondary">
                        {tc("tagline")}
                      </p>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setShowUserMenu(false);
                          router.push("/auth/login");
                        }}
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-psi-electric hover:bg-psi-electric/10 transition-colors"
                      >
                        <LogIn className="h-4 w-4" />
                        {ta("loginToAccount")}
                      </button>
                      <IntlLink
                        href="/settings"
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <Settings className="h-4 w-4" />
                        {t("settings")}
                      </IntlLink>
                    </div>
                  </>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
