"use client";

import { useState, useMemo, useCallback, useEffect } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Bell, Settings2, CheckCheck, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { GlowCard } from "@/components/shared/GlowCard";
import { NotificationFilterPanel } from "@/components/notifications/NotificationFilterPanel";
import { NotificationCard } from "@/components/notifications/NotificationCard";
import { NotificationDeliveryCenter } from "@/components/notifications/NotificationDeliveryCenter";
import type { Notification } from "@/types";
import type { NotificationFilterType } from "@/components/notifications/types";
import {
  useNotifications,
  useUnreadNotificationCount,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useDismissNotification,
  useNotificationSettings,
  useUpdateNotificationSettings,
} from "@/hooks/useApi";
import { useRealtimeNotifications } from "@/hooks/useRealtimeNotifications";
import { useAlertStore } from "@/stores";

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const tCommon = useTranslations("common");

  // ── Filter State ──
  const [activeFilter, setActiveFilter] = useState<NotificationFilterType>("all");

  // ── API Data Fetching ──
  const {
    data: notificationsData,
    isLoading,
    isError,
    error,
  } = useNotifications();

  const { data: unreadCountData } = useUnreadNotificationCount();
  const { data: settingsData } = useNotificationSettings();

  // ── Mutations ──
  const markReadMutation = useMarkNotificationRead();
  const markAllReadMutation = useMarkAllNotificationsRead();
  const dismissMutation = useDismissNotification();
  const updateSettingsMutation = useUpdateNotificationSettings();

  // ── Realtime WebSocket ──
  useRealtimeNotifications(true);

  // ── Alert Store (realtime bridge) ──
  const storeNotifications = useAlertStore((s) => s.notifications);

  // ── Derived Data ──
  const apiNotifications: Notification[] = useMemo(
    () => notificationsData?.data ?? [],
    [notificationsData],
  );

  // Merge API notifications with realtime store notifications for instant UI
  // Deduplicate by ID, preferring store (newer) entries
  const allNotifications: Notification[] = useMemo(() => {
    const storeIds = new Set(storeNotifications.map((n) => n.id));
    const apiOnly = apiNotifications.filter((n) => !storeIds.has(n.id));
    return [...storeNotifications, ...apiOnly];
  }, [apiNotifications, storeNotifications]);

  const unreadCount =
    unreadCountData?.count ??
    allNotifications.filter((n) => !n.is_read).length;

  // ── Filter Logic ──
  const filteredNotifications = useMemo(() => {
    if (activeFilter === "all") return allNotifications;
    if (activeFilter === "critical")
      return allNotifications.filter((n) => n.severity === "critical");
    // Map filter types to notification types
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
    (id: string, isRead: boolean) => {
      if (isRead) {
        markReadMutation.mutate(id);
      }
    },
    [markReadMutation],
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

  const handleViewNotification = useCallback(
    (id: string, url: string) => {
      if (url && url !== "#") {
        window.location.href = url;
      }
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

  // ── Loading State ──
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px]">
        <Loader2 className="h-10 w-10 animate-spin text-psi-electric" />
        <p className="mt-4 text-psi-text-secondary">{tCommon("loading")}</p>
      </div>
    );
  }

  // ── Error State ──
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] text-center">
        <XCircle className="h-12 w-12 text-psi-fraud mb-4" />
        <h2 className="text-xl font-semibold text-psi-text-primary mb-2">
          {tCommon("error")}
        </h2>
        <p className="text-psi-text-secondary max-w-md">
          {(error as Error)?.message || "Unable to load notifications. Please try again."}
        </p>
      </div>
    );
  }

  // ── Main Content ──
  return (
    <div className="relative min-h-dvh-no-nav px-4 py-8 lg:px-8 space-y-8 animated-background">
      <div
        className="absolute inset-0 z-0 aura-glow-blue animate-pulse-subtle"
        aria-hidden="true"
      />
      <div className="relative z-10 space-y-8">
        {/* ── Header Section ── */}
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

            {/* Notification Preferences */}
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

        {/* ── Main Content Area ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Notification Filters and Feed */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Filter Panel */}
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

            {/* Notification Feed */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
              className="flex-1 space-y-4"
            >
              <AnimatePresence mode="wait">
                {filteredNotifications.length > 0 ? (
                  <motion.div
                    key="notifications-list"
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    variants={{
                      visible: { transition: { staggerChildren: 0.05 } },
                    }}
                    className="space-y-4"
                  >
                    {filteredNotifications.map((notification) => (
                      <NotificationCard
                        key={notification.id}
                        notification={notification}
                        onView={handleViewNotification}
                        onDismiss={handleDismissNotification}
                        onMarkReadToggle={handleMarkAsRead}
                      />
                    ))}
                  </motion.div>
                ) : (
                  <motion.div
                    key="empty-state"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="flex flex-col items-center justify-center p-12 text-center h-full min-h-[300px] rounded-xl glass-card"
                  >
                    <Bell className="h-12 w-12 text-psi-border mb-4" />
                    <h3 className="text-xl font-semibold text-psi-text-primary mb-2">
                      {t("empty.title")}
                    </h3>
                    <p className="text-psi-text-secondary max-w-sm mb-4">
                      {t("empty.description")}
                    </p>
                    {activeFilter !== "all" && (
                      <Button
                        variant="outline"
                        onClick={() => setActiveFilter("all")}
                      >
                        {t("empty.clearFilters")}
                      </Button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* ── Right Sidebar: Delivery Channels ── */}
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
