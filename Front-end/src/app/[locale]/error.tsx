"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("errors");

  useEffect(() => {
    console.error("Unhandled application error:", error);
  }, [error]);

  return (
    <html>
      <body className="bg-psi-navy text-psi-text-primary">
        <main className="flex min-h-screen items-center justify-center p-4" id="main-content" role="main">
          <div className="text-center max-w-md animate-slide-in-up">
            <div className="mb-6 inline-flex rounded-2xl bg-psi-fraud/10 p-5">
              <AlertTriangle className="h-12 w-12 text-psi-fraud" />
            </div>
            <h1 className="text-2xl font-bold mb-3">{t("global.title")}</h1>
            <p className="text-sm text-psi-text-secondary mb-2">
              {t("global.description")}
            </p>
            {error.digest && (
              <p className="text-xs font-mono text-psi-text-secondary/50 mb-6">
                Error ID: {error.digest}
              </p>
            )}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={reset}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-psi-electric px-5 py-2.5 text-sm font-medium text-white hover:bg-psi-electric/90 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                {t("tryAgain")}
              </button>
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-psi-border px-5 py-2.5 text-sm font-medium text-psi-text-secondary hover:bg-white/5 transition-colors"
              >
                <Home className="h-4 w-4" />
                {t("goHome")}
              </Link>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
