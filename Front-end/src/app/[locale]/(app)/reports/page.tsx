"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { FileBarChart } from "lucide-react";

export default function ReportsPage() {
  const t = useTranslations("reports");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<FileBarChart className="h-8 w-8" />}
    />
  );
}
