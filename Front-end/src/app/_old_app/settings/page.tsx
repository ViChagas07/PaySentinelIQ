"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <PagePlaceholder
      title="Settings"
      description="Platform configuration, user management, RBAC roles, API keys, and integration settings."
      icon={<Settings className="h-8 w-8" />}
    />
  );
}
