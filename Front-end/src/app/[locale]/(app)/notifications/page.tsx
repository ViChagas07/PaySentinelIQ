"use client";

import { useState, useMemo, useCallback, useEffect, useSyncExternalStore, useRef } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Bell, Settings2, CheckCheck, XCircle, Loader2, WifiOff, Clock, Trash2, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { NotificationFilterPanel } from "@/components/notifications/NotificationFilterPanel";
import { NotificationCard } from "@/components/notifications/NotificationCard";
import { NotificationDeliveryCenter } from "@/components/notifications/NotificationDeliveryCenter";
import type { Notification } from "@/types";
import type { NotificationFilterType } from "@/components/notifications/types";
import {
  useNotifications,
  useUnreadNotificationCount,
  useMarkNotificationRead,
  useMarkNotificationUnread,
  useMarkAllNotificationsRead,
  useDismissNotification,
  useDeleteNotificationsByAge,
  useNotificationSettings,
  useUpdateNotificationSettings,
} from "@/hooks/useApi";
import { useRealtimeNotifications } from "@/hooks/useRealtimeNotifications";
import { useOsNotifications } from "@/hooks/useOsNotifications";
import { useAlertStore } from "@/stores";
import { ApiClientError } from "@/lib/api";

// ── Browser online/offline subscription ──
function subscribeToOnlineStatus(callback: () => void) {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getOnlineSnapshot() {
  return typeof navigator !== "undefined" && navigator.onLine;
}

// ── Explicit page states ──
type PageState = "loading" | "ready" | "empty" | "error" | "offline" | "timeout";

function derivePageState(
  isLoading: boolean,
  isError: boolean,
  isSuccess: boolean,
  error: Error | null,
  notificationCount: number,
  isOnline: boolean,
  hasCachedData: boolean,
  minLoadingElapsed: boolean,
): PageState {
  // Offline — check before anything else
  if (!isOnline) {
    // If we have cached data, treat as ready (with warning banner)
    if (hasCachedData) return "ready";
    return "offline";
  }

  // Still loading — enforce minimum 600ms display to prevent flicker
  if ((isLoading || !minLoadingElapsed) && !hasCachedData) {
    return "loading";
  }

  // Error occurred
  if (isError) {
    const msg = error?.message?.toLowerCase() ?? "";

    // Timeout / abort — network hiccup, not a server crash
    if (msg.includes("timeout") || msg.includes("abort")) {
      // If we have cached data, show ready with warning
      if (hasCachedData) return "ready";
      // No cached data: treat as empty — the user likely has no notifications.
      // A timeout means the server may be slow, not down.
      return "empty";
    }

    // If we have cached data, treat as ready with stale data + warning banner
    if (hasCachedData) return "ready";

    // No cached data — check if this is a genuine server crash (5xx)
    // or a benign error (404 not found, network issue, etc.)
    if (error instanceof ApiClientError && error.status >= 500) {
      // Genuine server error — show error state
      return "error";
    }

    // Non-critical error (404, network, etc.) — treat as empty.
    // The user likely has no notifications; showing "Server unavailable"
    // is scarier and less accurate than showing "No notifications yet."
    return "empty";
  }

  // Success but no notifications
  if (isSuccess && notificationCount === 0) {
    return "empty";
  }

  // Success with data
  return "ready";
}

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const tCommon = useTranslations("common");

  // ── Reactive online status ──
  const isOnline = useSyncExternalStore(subscribeToOnlineStatus, getOnlineSnapshot, () => true);

  // ── Minimum loading display (600ms) to prevent flicker ──
  const [minLoadingElapsed, setMinLoadingElapsed] = useState(false);
  const loadingStartRef = useRef(Date.now());

  useEffect(() => {
    const elapsed = Date.now() - loadingStartRef.current;
    const remaining = Math.max(0, 600 - elapsed);
    if (remaining === 0) {
      setMinLoadingElapsed(true);
      return;
    }
    const timer = setTimeout(() => setMinLoadingElapsed(true), remaining);
    return () => clearTimeout(timer);
  }, []);

  // ── Filter State ──
  const [activeFilter, setActiveFilter] = useState<NotificationFilterType>("all");

  // ── API Data Fetching ──
  const {
    data: notificationsData,
    isLoading,
    isError,
    isSuccess,
    error,
    refetch,
  } = useNotifications();

  const { data: unreadCountData } = useUnreadNotificationCount();
  const { data: settingsData } = useNotificationSettings();

  // ── Mutations ──
  const markReadMutation = useMarkNotificationRead();
  const markUnreadMutation = useMarkNotificationUnread();
  const markAllReadMutation = useMarkAllNotificationsRead();
  const dismissMutation = useDismissNotification();
  const deleteByAgeMutation = useDeleteNotificationsByAge();
  const updateSettingsMutation = useUpdateNotificationSettings();

  // ── Delete dropdown state ──
  const [deleteMenuOpen, setDeleteMenuOpen] = useState(false);

  // ── Realtime WebSocket (ALWAYS active — even during empty/error states) ──
  useRealtimeNotifications(true);

  // ── Alert Store (realtime bridge) ──
  const storeNotifications = useAlertStore((s) => s.notifications);

  // ── OS Notifications (native browser push when in-app is enabled) ──
  const inAppEnabled = settingsData?.in_app_alerts ?? false;
  useOsNotifications(inAppEnabled, storeNotifications);

  // ── Derived Data ──
  const apiNotifications: Notification[] = useMemo(
    () => notificationsData?.data ?? [],
    [notificationsData],
  );

  // Merge API notifications with realtime store notifications
  const allNotifications: Notification[] = useMemo(() => {
    const storeIds = new Set(storeNotifications.map((n) => n.id));
    const apiOnly = apiNotifications.filter((n) => !storeIds.has(n.id));
    return [...storeNotifications, ...apiOnly];
  }, [apiNotifications, storeNotifications]);

  const unreadCount =
    unreadCountData?.count ??
    allNotifications.filter((n) => !n.is_read).length;

  // ── Explicit page state ──
  // hasCachedData: true if we've ever received a response (even empty data)
  // This prevents polling failures from showing error when we have valid empty cached data
  const hasCachedData = notificationsData !== undefined;

  const pageState = derivePageState(
    isLoading,
    isError,
    isSuccess,
    error as Error | null,
    allNotifications.length,
    isOnline,
    hasCachedData,
    minLoadingElapsed,
  );

  // ── Filter Logic ──
  const filteredNotifications = useMemo(() => {
    if (activeFilter === "all") return allNotifications;
    if (activeFilter === "critical")
      return allNotifications.filter((n) => n.severity === "critical");
    const typeMap: Record<string, string> = {
      payments: "payment",
      fraud_detection: "fraud_alert",
      documents: "document_event",
      ai_insights: "ai_insight",
      compliance: "compliance_alert",
      system: "system",
    };
    const targetType = typeMap[activeFilter];
    if (targetType) return allNotifications.filter((n) => n.type === targetType);
    return allNotifications;
  }, [allNotifications, activeFilter]);

  const filterCounts = useMemo(() => {
    const counts: Record<NotificationFilterType, number> = {
      all: allNotifications.length,
      payments: allNotifications.filter((n) => n.type === "payment").length,
      fraud_detection: allNotifications.filter((n) => n.type === "fraud_alert").length,
      documents: allNotifications.filter((n) => n.type === "document_event").length,
      ai_insights: allNotifications.filter((n) => n.type === "ai_insight").length,
      compliance: allNotifications.filter((n) => n.type === "compliance_alert").length,
      system: allNotifications.filter((n) => n.type === "system").length,
      critical: allNotifications.filter((n) => n.severity === "critical").length,
    };
    return counts;
  }, [allNotifications]);

  // ── Handlers ──
  const handleMarkAsRead = useCallback(
    (id: string, targetIsRead: boolean) => {
      if (targetIsRead) {
        markReadMutation.mutate(id);
      } else {
        markUnreadMutation.mutate(id);
      }
    },
    [markReadMutation, markUnreadMutation],
  );

  const handleDismissNotification = useCallback(
    (id: string) => {
      dismissMutation.mutate(id);
    },
    [dismissMutation],
  );

  const handleMarkAllRead = useCallback(() => {
    markAllReadMutation.mutate();
  }, [markAllReadMutation]);

  // ── Delete options ──
  const DELETE_OPTIONS = useMemo(
    () => [
      { key: "1d", labelKey: "header.deleteYesterday" as const, olderThan: "1d" },
      { key: "3d", labelKey: "header.delete3Days" as const, olderThan: "3d" },
      { key: "7d", labelKey: "header.delete7Days" as const, olderThan: "7d" },
      { key: "30d", labelKey: "header.delete30Days" as const, olderThan: "30d" },
      { key: "all", labelKey: "header.deleteAll" as const, olderThan: "0d" },
    ],
    [],
  );

  const handleDeleteByAge = useCallback(
    (olderThan: string) => {
      setDeleteMenuOpen(false);
      deleteByAgeMutation.mutate(olderThan);
    },
    [deleteByAgeMutation],
  );

  const handleViewNotification = useCallback(
    (id: string, url: string) => {
      if (url && url !== "#") window.location.href = url;
      handleMarkAsRead(id, true);
    },
    [handleMarkAsRead],
  );

  const handleSaveDeliverySettings = useCallback(
    async (settings: Record<string, boolean>) => {
      await updateSettingsMutation.mutateAsync(settings);
    },
    [updateSettingsMutation],
  );

  // ── Feed content based on state ──
  const renderFeedContent = () => {
    switch (pageState) {
      case "loading":
        return (
          <motion.div
            key="feed-loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center p-12 min-h-[300px] rounded-xl glass-card"
          >
            <Loader2 className="h-10 w-10 animate-spin text-psi-electric mb-4" />
            <p className="text-psi-text-secondary">{tCommon("loading")}</p>
          </motion.div>
        );

      case "error":
        return (
          <motion.div
            key="feed-error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center p-12 text-center min-h-[300px] rounded-xl glass-card"
          >
            <XCircle className="h-12 w-12 text-psi-fraud mb-4" />
            <h3 className="text-lg font-semibold text-psi-text-primary mb-2">
              Unable to load notifications
            </h3>
            <p className="text-psi-text-secondary max-w-sm mb-4">
              Server temporarily unavailable. Please try again.
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              {tCommon("retry")}
            </Button>
          </motion.div>
        );

      case "offline":
        return (
          <motion.div
            key="feed-offline"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center p-12 text-center min-h-[300px] rounded-xl glass-card"
          >
            <WifiOff className="h-12 w-12 text-psi-warning mb-4" />
            <h3 className="text-lg font-semibold text-psi-text-primary mb-2">
              You are offline
            </h3>
            <p className="text-psi-text-secondary max-w-sm">
              Reconnect to receive updates. Notifications will appear automatically when your connection returns.
            </p>
          </motion.div>
        );

      case "timeout":
        return (
          <motion.div
            key="feed-timeout"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center p-12 text-center min-h-[300px] rounded-xl glass-card"
          >
            <Clock className="h-12 w-12 text-psi-warning mb-4" />
            <h3 className="text-lg font-semibold text-psi-text-primary mb-2">
              Connection timeout
            </h3>
            <p className="text-psi-text-secondary max-w-sm mb-4">
              The server took too long to respond. Retrying automatically...
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              {tCommon("retry")}
            </Button>
          </motion.div>
        );

      case "empty":
        return (
          <motion.div
            key="feed-empty"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center justify-center p-12 text-center min-h-[300px] rounded-xl glass-card"
          >
            <motion.div
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <Bell className="h-14 w-14 text-psi-electric/40 mb-4" />
            </motion.div>
            <h3 className="text-xl font-semibold text-psi-text-primary mb-2">
              {t("empty.noNotificationsTitle")}
            </h3>
            <p className="text-psi-text-secondary max-w-md">
              {t("empty.noNotificationsDescription")}
            </p>
            {activeFilter !== "all" && (
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setActiveFilter("all")}
              >
                {t("empty.clearFilters")}
              </Button>
            )}
          </motion.div>
        );

      case "ready":
      default:
        if (filteredNotifications.length === 0) {
          // Active filter produced no results
          return (
            <motion.div
              key="feed-filtered-empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center p-12 text-center min-h-[300px] rounded-xl glass-card"
            >
              <Bell className="h-12 w-12 text-psi-border mb-4" />
              <h3 className="text-xl font-semibold text-psi-text-primary mb-2">
                {t("empty.title")}
              </h3>
              <p className="text-psi-text-secondary max-w-sm mb-4">
                {t("empty.description")}
              </p>
              <Button variant="outline" onClick={() => setActiveFilter("all")}>
                {t("empty.clearFilters")}
              </Button>
            </motion.div>
          );
        }

        return (
          <motion.div
            key="notifications-list"
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
            className="space-y-4"
          >
            <AnimatePresence mode="popLayout">
              {filteredNotifications.map((notification) => (
                <NotificationCard
                  key={notification.id}
                  notification={notification}
                  onView={handleViewNotification}
                  onDismiss={handleDismissNotification}
                  onMarkReadToggle={handleMarkAsRead}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        );
    }
  };

  // ═══════════════════════════════════════════════════════
  // RENDER — page structure ALWAYS visible
  // ═══════════════════════════════════════════════════════
  return (
    <div className="relative px-4 py-8 lg:px-8 space-y-8 min-h-[calc(100dvh-4rem)]">
      {/* Aura glow */}
      <div
        className="absolute inset-0 z-0 aura-glow-blue"
        aria-hidden="true"
        style={{ animation: "pulse-alert 4s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}
      />

      <div className="relative z-10 space-y-8">
        {/* ── Header (ALWAYS visible) ── */}
        <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-3xl font-bold text-psi-text-primary mb-2"
            >
              {t("header.title")}
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-psi-text-secondary max-w-2xl"
            >
              {t("header.subtitle")}
            </motion.p>
          </div>

          <div className="flex items-center gap-3">
            {/* Unread counter */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              {unreadCount > 0 && (
                <Badge
                  variant="primary"
                  className="bg-psi-electric/20 text-psi-electric animate-pulse-alert px-3 py-1 text-sm"
                  aria-live="polite"
                >
                  {unreadCount} {t("header.unreadLabel")}
                </Badge>
              )}
            </motion.div>

            {/* Mark All Read */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Button
                onClick={handleMarkAllRead}
                variant="secondary"
                size="sm"
                disabled={unreadCount === 0 || markAllReadMutation.isPending}
                aria-label={t("header.markAllRead")}
              >
                {markAllReadMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCheck className="h-4 w-4" />
                )}{" "}
                {t("header.markAllRead")}
              </Button>
            </motion.div>

            {/* Delete (Trash) with time dropdown */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.45 }}
              className="relative"
            >
              <Button
                onClick={() => setDeleteMenuOpen(!deleteMenuOpen)}
                variant="secondary"
                size="sm"
                disabled={allNotifications.length === 0 || deleteByAgeMutation.isPending}
                aria-label={t("header.delete")}
              >
                {deleteByAgeMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}{" "}
                {t("header.delete")}
                <ChevronDown className={cn("h-3 w-3 ml-1 transition-transform", deleteMenuOpen && "rotate-180")} />
              </Button>

              <AnimatePresence>
                {deleteMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-2 w-44 rounded-xl border border-border bg-card shadow-2xl shadow-black/30 overflow-hidden z-50"
                  >
                    <div className="px-3 py-2 border-b border-border">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-psi-text-secondary/60">
                        {t("header.deleteOlderThan")}
                      </p>
                    </div>
                    {DELETE_OPTIONS.map((opt) => (
                      <button
                        key={opt.key}
                        onClick={() => handleDeleteByAge(opt.olderThan)}
                        className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-psi-text-secondary hover:bg-psi-fraud/10 hover:text-psi-fraud transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        {t(opt.labelKey)}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Settings */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              <Button
                onClick={() => {
                  const el = document.getElementById("delivery-center");
                  el?.scrollIntoView({ behavior: "smooth" });
                }}
                variant="secondary"
                size="sm"
                aria-label={t("header.settings")}
              >
                <Settings2 className="h-4 w-4" /> {t("header.settings")}
              </Button>
            </motion.div>
          </div>
        </header>

        {/* ── Status banner (error/offline/timeout while data exists) ── */}
        {hasCachedData && (isError || !isOnline) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 px-4 py-3 rounded-xl border border-psi-warning/30 bg-psi-warning/10 text-psi-warning text-sm"
            role="alert"
          >
            {!isOnline ? (
              <WifiOff className="h-4 w-4 shrink-0" />
            ) : pageState === "timeout" ? (
              <Clock className="h-4 w-4 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0" />
            )}
            <span>
              {!isOnline
                ? "You are offline. Showing last known notifications."
                : pageState === "timeout"
                  ? "Connection timeout. Showing cached notifications."
                  : "Unable to refresh. Showing last known data."}
            </span>
          </motion.div>
        )}

        {/* ── Main Content Area (ALWAYS visible) ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Filters + Feed */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Filter Panel (ALWAYS visible) */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              <NotificationFilterPanel
                activeFilter={activeFilter}
                onFilterChange={setActiveFilter}
                filterCounts={filterCounts}
              />
            </motion.div>

            {/* Feed — content swaps based on state */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
              className="flex-1"
            >
              {renderFeedContent()}
            </motion.div>
          </div>

          {/* Delivery Center (ALWAYS visible) */}
          <aside className="lg:col-span-1" id="delivery-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <NotificationDeliveryCenter
                initialChannelSettings={
                  settingsData
                    ? {
                        email: settingsData.email_alerts,
                        whatsapp: settingsData.whatsapp_alerts,
                        telegram: settingsData.telegram_alerts,
                        slack: settingsData.slack_alerts,
                        inApp: settingsData.in_app_alerts,
                      }
                    : undefined
                }
                onSave={handleSaveDeliverySettings}
              />
            </motion.div>
          </aside>
        </div>
      </div>
    </div>
  );
}
