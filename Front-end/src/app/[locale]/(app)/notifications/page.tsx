"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Bell } from "lucide-react";

export default function NotificationsPage() {
  const t = useTranslations("notifications");

  return (
    <PagePlaceholder
      title={t("panelTitle")}
      description={t("pageDescription")}
      icon={<Bell className="h-8 w-8" />}
      badge={t("unreadCount", { count: 5 })}
      badgeVariant="warning"
    />
  );
}
