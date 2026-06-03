"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { DollarSign } from "lucide-react";

export default function PayrollPage() {
  const t = useTranslations("payroll");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<DollarSign className="h-8 w-8" />}
      badge={t("pageBadge")}
      badgeVariant="success"
    />
  );
}
