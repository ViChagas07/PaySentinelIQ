"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { useTranslations } from "next-intl";

// ── Skeleton placeholders for each chart ──
function ChartSkeleton({ height = "h-64", labelKey = "loadingChart" }: { height?: string; labelKey?: string }) {
  const t = useTranslations("charts");
  const label = t(labelKey);
  return (
    <div
      className={`flex items-center justify-center ${height} rounded-lg bg-psi-navy/30 border border-psi-border/30`}
      role="status"
      aria-label={label}
    >
      <div className="flex flex-col items-center gap-2">
        <div className="h-8 w-8 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
        <span className="text-xs text-psi-text-secondary/50">{label}</span>
      </div>
    </div>
  );
}

// ── Lazy-loaded Chart Components ──

export const LazyPayrollTrendChart = dynamic(
  () => import("@/components/charts/PayrollTrendChart").then((mod) => ({ default: mod.PayrollTrendChart })),
  {
    loading: () => <ChartSkeleton height="h-72" labelKey="loadingTrend" />,
    ssr: false,
  }
);

export const LazyFraudHeatmap = dynamic(
  () => import("@/components/charts/FraudHeatmap").then((mod) => ({ default: mod.FraudHeatmap })),
  {
    loading: () => <ChartSkeleton height="h-64" labelKey="loadingHeatmap" />,
    ssr: false,
  }
);

export const LazyRiskDistributionChart = dynamic(
  () => import("@/components/charts/RiskDistributionChart").then((mod) => ({ default: mod.RiskDistributionChart })),
  {
    loading: () => <ChartSkeleton height="h-64" labelKey="loadingDistribution" />,
    ssr: false,
  }
);

export const LazyLiveAIInsightFeed = dynamic(
  () => import("@/components/dashboard/LiveAIInsightFeed").then((mod) => ({ default: mod.LiveAIInsightFeed })),
  {
    loading: () => (
      <div className="rounded-xl border border-psi-border bg-psi-graphite p-6 space-y-3">
        <div className="h-5 w-36 animate-pulse rounded bg-psi-border/50" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-16 w-full animate-pulse rounded-lg bg-psi-border/30" />
        ))}
      </div>
    ),
    ssr: false,
  }
);

// ── Wrapper component with Suspense boundary ──
export function ChartSuspense({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return <Suspense fallback={fallback || <ChartSkeleton />}>{children}</Suspense>;
}
