"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { ScrollText } from "lucide-react";

export default function AuditLogsPage() {
  return (
    <PagePlaceholder
      title="Audit & Compliance Logs"
      description="Immutable activity timeline tracking user actions, AI decisions, analyst reviews, and system events."
      icon={<ScrollText className="h-8 w-8" />}
      badge="Immutable"
    />
  );
}
