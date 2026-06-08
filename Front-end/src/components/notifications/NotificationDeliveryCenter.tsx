"use client";

import { useTranslations } from "next-intl";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Mail, MessageSquareText, Send, Hash, Bell, Loader2, AlertTriangle } from "lucide-react";
import { GlowCard } from "@/components/shared/GlowCard";
import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/stores";
import type { NotificationDeliveryChannel } from "./types";

interface NotificationDeliveryCenterProps {
  initialChannelSettings?: Record<NotificationDeliveryChannel["id"], boolean>;
  onSave?: (settings: Record<NotificationDeliveryChannel["id"], boolean>) => Promise<void>;
}

const DEFAULT_CHANNEL_SETTINGS: Record<NotificationDeliveryChannel["id"], boolean> = {
  email: true,
  whatsapp: false,
  telegram: false,
  slack: false,
  inApp: true,
};

/**
 * Request browser Notification permission.
 * Returns the current permission state: "granted" | "denied" | "default".
 */
function getNotificationPermission(): NotificationPermission {
  if (typeof window === "undefined" || !("Notification" in window)) return "denied";
  return Notification.permission;
}

async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (typeof window === "undefined" || !("Notification" in window)) return "denied";
  try {
    const result = await Notification.requestPermission();
    return result;
  } catch {
    return "denied";
  }
}

export function NotificationDeliveryCenter({
  initialChannelSettings = DEFAULT_CHANNEL_SETTINGS,
  onSave,
}: NotificationDeliveryCenterProps) {
  const t = useTranslations("notifications.deliveryCenter");
  const user = useAuthStore((s) => s.user);

  const [settings, setSettings] = useState(initialChannelSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // ── Browser notification permission tracking ──
  const [notifPermission, setNotifPermission] = useState<NotificationPermission>("default");
  const [showPermissionWarning, setShowPermissionWarning] = useState(false);

  useEffect(() => {
    setNotifPermission(getNotificationPermission());
  }, []);

  // Sync state when external settings change
  useEffect(() => {
    setSettings(initialChannelSettings);
  }, [initialChannelSettings]);

  // ── Handle in-app toggle with browser permission flow ──
  const handleInAppToggle = useCallback(async (enabled: boolean) => {
    if (!enabled) {
      setSettings((prev) => ({ ...prev, inApp: false }));
      setShowPermissionWarning(false);
      return;
    }

    const perm = getNotificationPermission();
    if (perm === "granted") {
      setSettings((prev) => ({ ...prev, inApp: true }));
      setShowPermissionWarning(false);
      return;
    }

    if (perm === "denied") {
      setSettings((prev) => ({ ...prev, inApp: false }));
      setShowPermissionWarning(true);
      return;
    }

    // perm === "default" — request permission
    const result = await requestNotificationPermission();
    setNotifPermission(result);
    if (result === "granted") {
      setSettings((prev) => ({ ...prev, inApp: true }));
      setShowPermissionWarning(false);
    } else {
      setSettings((prev) => ({ ...prev, inApp: false }));
      setShowPermissionWarning(true);
    }
  }, []);

  const handleOpenBrowserSettings = useCallback(() => {
    window.open("chrome://settings/content/notifications", "_blank");
  }, []);

  // ── Validation helpers ──
  const getChannelWarning = useCallback(
    (channelId: NotificationDeliveryChannel["id"]): string | null => {
      if (!settings[channelId]) return null; // toggle is off — no warning needed
      switch (channelId) {
        case "telegram":
          // Check if user has telegram_username in their profile
          // For now, we rely on the profile data being passed or checked externally
          return null; // Profile data checking is done externally
        case "whatsapp":
          return null;
        case "slack":
          return null;
        default:
          return null;
      }
    },
    [settings],
  );

  const channels: NotificationDeliveryChannel[] = [
    {
      id: "email",
      labelKey: "channels.email.label",
      descriptionKey: "channels.email.description",
      icon: Mail,
      enabled: settings.email,
    },
    {
      id: "whatsapp",
      labelKey: "channels.whatsapp.label",
      descriptionKey: "channels.whatsapp.description",
      icon: MessageSquareText,
      enabled: settings.whatsapp,
    },
    {
      id: "telegram",
      labelKey: "channels.telegram.label",
      descriptionKey: "channels.telegram.description",
      icon: Send,
      enabled: settings.telegram,
    },
    {
      id: "slack",
      labelKey: "channels.slack.label",
      descriptionKey: "channels.slack.description",
      icon: Hash,
      enabled: settings.slack,
    },
    {
      id: "inApp",
      labelKey: "channels.inApp.label",
      descriptionKey: "channels.inApp.description",
      icon: Bell,
      enabled: settings.inApp,
    },
  ];

  const handleToggle = (channelId: NotificationDeliveryChannel["id"]) => {
    if (channelId === "inApp") {
      handleInAppToggle(!settings.inApp);
      return;
    }
    setSettings((prev) => ({
      ...prev,
      [channelId]: !prev[channelId],
    }));
    setSavedMessage(null);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSavedMessage(null);
    try {
      if (onSave) await onSave(settings);
      setSavedMessage(t("saved"));
    } catch {
      // Error delegated to parent
    } finally {
      setIsSaving(false);
      setTimeout(() => setSavedMessage(null), 3000);
    }
  };

  const hasChanges = Object.keys(settings).some(
    (key) =>
      settings[key as NotificationDeliveryChannel["id"]] !==
      initialChannelSettings[key as NotificationDeliveryChannel["id"]],
  );

  return (
    <GlowCard className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-psi-text-primary mb-1">
            {t("title")}
          </h2>
          <p className="text-sm text-psi-text-secondary">{t("description")}</p>
        </div>
      </div>

      <div className="space-y-4">
        {channels.map((channel) => {
          const Icon = channel.icon;
          const warning = getChannelWarning(channel.id);
          return (
            <div key={channel.id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-psi-border/50 text-psi-electric">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-psi-text-primary">
                      {t(channel.labelKey as any)}
                    </p>
                    <p className="text-xs text-psi-text-secondary">
                      {t(channel.descriptionKey as any)}
                    </p>
                  </div>
                </div>
                <Switch
                  checked={settings[channel.id]}
                  onCheckedChange={() => handleToggle(channel.id)}
                  id={`toggle-delivery-${channel.id}`}
                  aria-label={t(channel.labelKey as any)}
                />
              </div>
              {warning && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-1.5 mt-1 ml-12 text-[11px] text-psi-warning"
                >
                  <AlertTriangle className="h-3 w-3 shrink-0" />
                  {warning}
                </motion.p>
              )}
            </div>
          );
        })}

        {/* ── Browser notification permission warning ── */}
        {showPermissionWarning && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-2 ml-12 p-3 rounded-lg border border-psi-warning/20 bg-psi-warning/5"
          >
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-psi-warning mt-0.5 shrink-0" />
              <div>
                <p className="text-xs font-medium text-psi-warning">
                  Browser notifications were denied.
                </p>
                <p className="text-[10px] text-psi-text-secondary/70 mt-0.5">
                  Enable notifications in your browser settings to receive in-app alerts.
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenBrowserSettings}
              className="self-start text-[11px]"
            >
              Open browser notification settings
            </Button>
          </motion.div>
        )}
      </div>

      <div className="mt-6 flex items-center gap-3">
        <Button
          onClick={handleSave}
          disabled={isSaving || !hasChanges}
          className="min-w-[120px]"
        >
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-1" /> {t("saving")}
            </>
          ) : (
            t("saveSettings")
          )}
        </Button>
        {savedMessage && (
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-psi-emerald"
          >
            {savedMessage}
          </motion.p>
        )}
      </div>
    </GlowCard>
  );
}
