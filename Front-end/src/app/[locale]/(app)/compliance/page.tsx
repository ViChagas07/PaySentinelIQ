"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Scale } from "lucide-react";

export default function CompliancePage() {
  const t = useTranslations("compliance");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<Scale className="h-8 w-8" />}
      badge={t("pageBadge")}
    />
  );
}
