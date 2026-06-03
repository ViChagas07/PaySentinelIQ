"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { FileSearch } from "lucide-react";

export default function DocumentsPage() {
  const t = useTranslations("documents");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<FileSearch className="h-8 w-8" />}
      badge={t("pageBadge")}
      badgeVariant="primary"
    />
  );
}
