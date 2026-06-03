"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { AppName } from "@/components/shared/AppName";

export default function GlobalLoading() {
  const t = useTranslations("common");

  return (
    <div className="flex items-center justify-center min-h-screen bg-psi-navy" role="status" aria-label={t("loading")}>
      <div className="flex flex-col items-center gap-4">
        {/* Logo pulse */}
        <div className="relative">
          <div className="absolute -inset-2 rounded-xl bg-psi-electric/20 animate-ping" />
          <Image
            src="/PSI_Logo2.png"
            alt={t("appName")}
            width={112}
            height={112}
            className="relative h-28 w-auto object-contain animate-pulse"
            priority
          />
        </div>
        {/* Skeleton bars */}
        <div className="space-y-3 w-48">
          <div className="h-3 rounded-full bg-psi-border animate-pulse" style={{ width: "100%" }} />
          <div className="h-3 rounded-full bg-psi-border animate-pulse" style={{ width: "75%" }} />
          <div className="h-3 rounded-full bg-psi-border animate-pulse" style={{ width: "50%" }} />
        </div>
        <p className="text-xs text-psi-text-secondary animate-pulse">
          {t("loading")}{" "}
          <AppName as="span" className="font-bold tracking-tight" />
        </p>
      </div>
    </div>
  );
}
