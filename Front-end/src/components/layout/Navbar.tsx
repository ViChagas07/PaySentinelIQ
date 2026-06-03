// ============================================================
// PaySentinelIQ — Top Navbar
// Enterprise navbar with global search, AI actions, alerts, tenant selector
// ============================================================

"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link as IntlLink, useRouter } from "@/i18n/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useUIStore, useAuthStore, useTenantStore, useAlertStore } from "@/stores";
import {
  Search, Menu, Bell, Bot, ChevronDown, Building2, User, LogOut, Settings, LogIn,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";

export function Navbar() {
  const t = useTranslations("nav");
  const tc = useTranslations("common");
  const ta = useTranslations("auth");
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
  const currentTenant = useTenantStore((s) => s.currentTenant);
  const availableTenants = useTenantStore((s) => s.availableTenants);
  const setCurrentTenant = useTenantStore((s) => s.setCurrentTenant);
  const unreadCount = useAlertStore((s) => s.unreadCount);

  const [searchFocused, setSearchFocused] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showTenantMenu, setShowTenantMenu] = useState(false);

  const userInitials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() || "U";

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

      {/* Right actions */}
      <div className="flex items-center gap-1">
        {/* AI Assistant quick toggle */}
        <button
          onClick={toggleAiPanel}
          className={cn(
            "relative rounded-lg p-2 transition-colors",
            aiPanelOpen
              ? "text-psi-electric bg-psi-electric/10"
              : "text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-electric"
          )}
          aria-label={t("aiAssistant")}
          aria-expanded={aiPanelOpen}
        >
          <Bot className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-psi-emerald opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-psi-emerald" />
          </span>
        </button>

        {/* Notifications */}
        <button
          onClick={toggleNotificationsPanel}
          className={cn(
            "relative rounded-lg p-2 transition-colors",
            notificationsPanelOpen
              ? "text-psi-text-primary bg-psi-border/50"
              : "text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary"
          )}
          aria-label={t("notificationsAria", { count: unreadCount })}
          aria-expanded={notificationsPanelOpen}
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 min-w-5 px-1 text-[10px] leading-none"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
        </button>

        {/* Tenant selector */}
        <div className="relative">
          <button
            onClick={() => setShowTenantMenu(!showTenantMenu)}
            className="hidden sm:flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-psi-text-secondary hover:bg-psi-border/50 hover:text-psi-text-primary transition-colors"
            aria-expanded={showTenantMenu}
            aria-haspopup="true"
          >
            <Building2 className="h-4 w-4 text-psi-electric" />
            <span className="max-w-[120px] truncate">
              {currentTenant?.name || t("selectCompany")}
            </span>
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 transition-transform",
                showTenantMenu && "rotate-180"
              )}
            />
          </button>

          <AnimatePresence>
            {showTenantMenu && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-border bg-card shadow-2xl shadow-black/30 overflow-hidden z-50"
              >
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-psi-text-secondary/60">
                    {t("switchCompany")}
                  </p>
                </div>
                {availableTenants.map((tenant) => (
                  <button
                    key={tenant.id}
                    onClick={() => {
                      setCurrentTenant(tenant);
                      setShowTenantMenu(false);
                    }}
                    className={cn(
                      "flex w-full items-center gap-3 px-3 py-2.5 text-sm transition-colors",
                      tenant.id === currentTenant?.id
                        ? "bg-psi-electric/10 text-psi-electric"
                        : "text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary"
                    )}
                  >
                    <Building2 className="h-4 w-4" />
                    <span className="flex-1 text-left">{tenant.name}</span>
                    {tenant.id === currentTenant?.id && (
                      <span className="h-1.5 w-1.5 rounded-full bg-psi-electric" />
                    )}
                  </button>
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
                      <button
                        className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors"
                        onClick={() => setShowUserMenu(false)}
                      >
                        <User className="h-4 w-4" />
                        {t("profile")}
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
