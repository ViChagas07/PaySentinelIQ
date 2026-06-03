"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { ScrollText } from "lucide-react";

export default function AuditLogsPage() {
  const t = useTranslations("auditLogs");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<ScrollText className="h-8 w-8" />}
      badge={t("pageBadge")}
    />
  );
}
