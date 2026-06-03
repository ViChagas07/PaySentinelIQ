"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Brain } from "lucide-react";

export default function AIInsightsPage() {
  const t = useTranslations("aiInsights");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<Brain className="h-8 w-8" />}
      badge={t("pageBadge")}
      badgeVariant="primary"
    />
  );
}
