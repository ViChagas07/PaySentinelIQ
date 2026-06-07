"use client";

import { useTranslations } from "next-intl";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Mail, MessageSquareText, Send, Hash, Bell, Loader2 } from "lucide-react";
import { GlowCard } from "@/components/shared/GlowCard";
import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";
import type { NotificationDeliveryChannel } from "./types";

interface NotificationDeliveryCenterProps {
  /** Channel settings fetched from API. Falls back to sensible defaults. */
  initialChannelSettings?: Record<NotificationDeliveryChannel["id"], boolean>;
  /** Called when user saves settings. Should persist to API. */
  onSave?: (settings: Record<NotificationDeliveryChannel["id"], boolean>) => Promise<void>;
}

const DEFAULT_CHANNEL_SETTINGS: Record<NotificationDeliveryChannel["id"], boolean> = {
  email: true,
  whatsapp: false,
  telegram: false,
  slack: false,
  inApp: true,
};

export function NotificationDeliveryCenter({
  initialChannelSettings = DEFAULT_CHANNEL_SETTINGS,
  onSave,
}: NotificationDeliveryCenterProps) {
  const t = useTranslations("notifications.deliveryCenter");
  const [settings, setSettings] = useState(initialChannelSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Sync state when external settings change
  useEffect(() => {
    setSettings(initialChannelSettings);
  }, [initialChannelSettings]);

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
      if (onSave) {
        await onSave(settings);
      }
      setSavedMessage(t("saved"));
    } catch {
      // Error handling delegated to parent via onSave
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
          return (
            <div key={channel.id} className="flex items-center justify-between">
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
          );
        })}
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
