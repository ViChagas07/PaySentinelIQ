"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Bell } from "lucide-react";

export default function NotificationsPage() {
  return (
    <PagePlaceholder
      title="Notifications"
      description="Real-time alerts for fraud detection, verification results, compliance updates, and AI insights."
      icon={<Bell className="h-8 w-8" />}
      badge="5 Unread"
      badgeVariant="warning"
    />
  );
}
