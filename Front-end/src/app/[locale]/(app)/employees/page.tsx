"use client";

import { useTranslations } from "next-intl";
import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Users } from "lucide-react";

export default function EmployeesPage() {
  const t = useTranslations("employees");

  return (
    <PagePlaceholder
      title={t("pageTitle")}
      description={t("pageDescription")}
      icon={<Users className="h-8 w-8" />}
    />
  );
}
