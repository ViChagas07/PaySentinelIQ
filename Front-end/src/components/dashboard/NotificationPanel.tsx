// ============================================================
// PaySentinelIQ — Notification Slide-Out Panel
// Real-time alerts for fraud, verification, compliance, and AI
// ============================================================

"use client";

import { useRef, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useUIStore, useAlertStore } from "@/stores";
import { Bell, X, CheckCheck, AlertTriangle, ShieldCheck, FileSearch, Cpu, Info, ChevronRight, Eye, Trash2, Wallet, FileText } from "lucide-react";
import type { Notification } from "@/types";
import type { NotificationSeverity } from "../notifications/types"; // Import NotificationSeverity

// ── Real notifications come from the useNotifications API hook ──
// Notifications are synced via useAlertStore which connects to the API.

// ── Icon and color per notification type/severity ── //

const typeConfig: Record<Notification["type"], { icon: typeof Bell; color: string; bg: string; defaultSeverity: NotificationSeverity }> = {
  fraud_alert: { icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", defaultSeverity: "critical" },
  verification_complete: { icon: ShieldCheck, color: "text-psi-emerald", bg: "bg-psi-emerald/10", defaultSeverity: "success" },
  compliance_alert: { icon: FileSearch, color: "text-psi-warning", bg: "bg-psi-warning/10", defaultSeverity: "warning" },
  ai_insight: { icon: Cpu, color: "text-psi-electric", bg: "bg-psi-electric/10", defaultSeverity: "ai" },
  system: { icon: Info, color: "text-psi-text-secondary", bg: "bg-psi-border/50", defaultSeverity: "normal" },
  payment: { icon: Wallet, color: "text-psi-electric", bg: "bg-psi-electric/10", defaultSeverity: "normal" },
  document_event: { icon: FileText, color: "text-psi-text-secondary", bg: "bg-psi-border/50", defaultSeverity: "normal" },
  critical: { icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10", defaultSeverity: "critical" }, // For general critical notifications
};

// ── Relative time formatter ── //

function timeAgo(dateStr: string, t: ReturnType<typeof useTranslations<"notifications">>): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (mins < 1) return t("justNow");
  if (mins < 60) return t("minutesAgo", { count: mins });
  if (hours < 24) return t("hoursAgo", { count: hours });
  return t("daysAgo", { count: days });
}

// ── Panel ── //

export function NotificationPanel() {
  const t = useTranslations("notifications");
  const notificationsPanelOpen = useUIStore((s) => s.notificationsPanelOpen);
  const toggleNotificationsPanel = useUIStore((s) => s.toggleNotificationsPanel);
  const notifications = useAlertStore((s) => s.notifications);
  const markNotificationRead = useAlertStore((s) => s.markNotificationRead);
  const dismissAlert = useAlertStore((s) => s.dismissAlert);

  const panelRef = useRef<HTMLDivElement>(null);

  // Real notifications from the store (synced via API)
  const displayNotifications = notifications;
  const unread = displayNotifications.filter((n) => !n.is_read);

  // ── Keyboard: Escape to close ── //
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && notificationsPanelOpen) {
        toggleNotificationsPanel();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [notificationsPanelOpen, toggleNotificationsPanel]);

  // ── Focus trap ── //
  const handlePanelKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        toggleNotificationsPanel();
      }
    },
    [toggleNotificationsPanel]
  );

  // ── Mark all as read ── //
  const markAllRead = () => {
    displayNotifications.forEach((n) => {
      if (!n.is_read) markNotificationRead(n.id);
    });
  };

  return (
    <AnimatePresence>
      {notificationsPanelOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
            onClick={toggleNotificationsPanel}
            aria-hidden="true"
          />

          {/* Panel */}
          <motion.aside
            ref={panelRef}
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 26, stiffness: 300 }}
            onKeyDown={handlePanelKeyDown}
            role="complementary"
            aria-label={t("panelTitle")}
            className={cn(
              "fixed right-0 top-0 z-50 flex h-dvh w-full flex-col border-l border-psi-border bg-psi-graphite shadow-2xl",
              "sm:w-[420px] lg:relative lg:z-0 lg:h-auto lg:w-[380px] lg:border-l"
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-psi-border px-4 py-3 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-psi-border/50">
                  <Bell className="h-4.5 w-4.5 text-psi-text-primary" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-psi-text-primary">
                    {t("panelTitle")}
                  </h2>
                  {unread.length > 0 && (
                    <p className="text-[10px] text-psi-text-secondary">
                      {t("unreadCount", { count: unread.length })}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                {unread.length > 0 && (
                  <button
                    onClick={markAllRead}
                    className="rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/40 hover:text-psi-text-primary transition-colors"
                    aria-label={t("markAllRead")}
                    title={t("markAllRead")}
                  >
                    <CheckCheck className="h-4 w-4" />
                  </button>
                )}
                <button
                  onClick={toggleNotificationsPanel}
                  className="rounded-lg p-2 text-psi-text-secondary hover:bg-psi-border/40 hover:text-psi-text-primary transition-colors"
                  aria-label={t("panelClose")}
                >
                  <X className="h-4.5 w-4.5" />
                </button>
              </div>
            </div>

            {/* Notification list */}
            <div className="flex-1 overflow-y-auto">
              {displayNotifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center">
                  <Bell className="h-10 w-10 text-psi-border mb-3" />
                  <p className="text-sm text-psi-text-secondary">{t("panelEmpty")}</p>
                </div>
              ) : (
                <div className="divide-y divide-psi-border/50">
                  {displayNotifications.map((notification) => {
                    const config = typeConfig[notification.type] || typeConfig.system;
                    const Icon = config.icon;
                    const ago = timeAgo(notification.created_at, t);

                    return (
                      <motion.div
                        key={notification.id}
                        initial={!notification.is_read ? { backgroundColor: "rgba(56,189,248,0.05)" } : {}}
                        animate={{ backgroundColor: "transparent" }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className={cn(
                          "relative px-4 py-3.5 hover:bg-psi-border/20 transition-colors group",
                          !notification.is_read && "bg-psi-electric/[0.04]"
                        )}
                      >
                        {/* Unread dot */}
                        {!notification.is_read && (
                          <span className="absolute left-1.5 top-4 h-2 w-2 rounded-full bg-psi-electric" />
                        )}

                        <div className="flex gap-3">
                          {/* Type icon */}
                          <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg", config.bg)}>
                            <Icon className={cn("h-4 w-4", config.color)} />
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={cn("text-[10px] font-semibold uppercase tracking-wider", config.color)}>
                                {t(notification.type)}
                              </span>
                              <span className="text-[10px] text-psi-text-secondary/60">{ago}</span>
                            </div>
                            <p className="text-sm font-medium text-psi-text-primary mt-0.5 leading-snug">
                              {t(notification.title as any)}
                            </p>
                            <p className="text-xs text-psi-text-secondary mt-1 line-clamp-2 leading-relaxed">
                              {t(notification.message as any)}
                            </p>

                            {/* Actions */}
                            <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              {notification.action_url && (
                                <button
                                  onClick={() => {
                                    if (!notification.is_read) markNotificationRead(notification.id);
                                  }}
                                  className="inline-flex items-center gap-1 text-[11px] font-medium text-psi-electric hover:text-psi-electric/80 transition-colors"
                                >
                                  <Eye className="h-3 w-3" />
                                  {t("viewDetails")}
                                  <ChevronRight className="h-3 w-3" />
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  if (!notification.is_read) markNotificationRead(notification.id);
                                }}
                                className="inline-flex items-center gap-1 text-[11px] text-psi-text-secondary hover:text-psi-fraud transition-colors"
                                aria-label={t("dismiss")}
                              >
                                <Trash2 className="h-3 w-3" />
                                {t("dismiss")}
                              </button>
                            </div>

                            {/* Mobile always-visible actions */}
                            <div className="flex items-center gap-2 mt-2 lg:hidden">
                              {notification.action_url && (
                                <button className="inline-flex items-center gap-1 text-[11px] font-medium text-psi-electric">
                                  <Eye className="h-3 w-3" />
                                  {t("viewDetails")}
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
