"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("errors");

  useEffect(() => {
    console.error("Route error:", error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6" role="alert">
      <div className="text-center max-w-md">
        <div className="mb-4 inline-flex rounded-2xl bg-psi-fraud/10 p-4">
          <AlertTriangle className="h-10 w-10 text-psi-fraud" />
        </div>
        <h2 className="text-xl font-bold mb-2">{t("app.title")}</h2>
        <p className="text-sm text-psi-text-secondary mb-1">
          {error.message || t("app.fallbackDescription")}
        </p>
        {error.digest && (
          <p className="text-xs font-mono text-psi-text-secondary/50 mb-6">
            ID: {error.digest}
          </p>
        )}
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white hover:bg-psi-electric/90 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          {t("tryAgain")}
        </button>
      </div>
    </div>
  );
}
