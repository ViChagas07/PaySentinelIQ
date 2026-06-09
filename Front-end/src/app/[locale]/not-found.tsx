"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { FileQuestion, Home } from "lucide-react";

export default function NotFound() {
  const t = useTranslations("errors");

  return (
    <main className="flex min-h-screen items-center justify-center p-4 bg-psi-navy" id="main-content" role="main">
      <div className="text-center max-w-md animate-slide-in-up">
        <div className="mb-6 inline-flex rounded-2xl bg-psi-electric/10 p-5">
          <FileQuestion className="h-12 w-12 text-psi-electric" />
        </div>
        <h1 className="text-2xl font-bold text-psi-text-primary mb-2">{t("notFound.title")}</h1>
        <p className="text-sm text-psi-text-secondary mb-1">{t("notFound.description")}</p>
        <p className="text-xs text-psi-text-secondary/50 mb-8">{t("notFound.httpStatus")}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white hover:bg-psi-electric/90 transition-colors"
        >
          <Home className="h-4 w-4" />
          {t("notFound.backToDashboard")}
        </Link>
      </div>
    </main>
  );
}
