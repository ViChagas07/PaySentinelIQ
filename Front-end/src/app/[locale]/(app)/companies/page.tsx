"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Building2 } from "lucide-react";

export default function CompaniesPage() {
  const t = useTranslations("companies");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<Building2 className="h-8 w-8" />}
    />
  );
}
