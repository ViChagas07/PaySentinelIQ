"use client";

import { useLocale } from "next-intl";
import { cn } from "@/lib/utils";

interface AppNameProps {
  className?: string;
  /** Optional override for the container element tag, defaults to "span" */
  as?: "span" | "h1" | "div";
}

/**
 * Locale-aware application name.
 * - pt-BR: "Sentinela" + highlighted "Pay"   → SentinelaPay
 * - All other locales: "PaySentinel" + highlighted "IQ" → PaySentinelIQ
 */
export function AppName({ className, as: Tag = "span" }: AppNameProps) {
  const locale = useLocale();

  const isPortuguese = locale === "pt-BR";

  return (
    <Tag className={cn("font-bold tracking-tight", className)}>
      {isPortuguese ? (
        <>
          Sentinela
          <span className="text-psi-electric">Pay</span>
        </>
      ) : (
        <>
          PaySentinel
          <span className="text-psi-electric">IQ</span>
        </>
      )}
    </Tag>
  );
}
