"use client";

import { useTranslations } from "next-intl";

function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-psi-border/50 ${className}`} />;
}

export default function DashboardLoading() {
  const t = useTranslations("dashboard");

  return (
    <div className="space-y-6 p-4 md:p-6 lg:p-8" role="status" aria-label={t("loading")}>
      {/* Header skeleton */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <SkeletonBlock className="h-8 w-56" />
          <SkeletonBlock className="h-4 w-80" />
        </div>
        <div className="flex items-center gap-3">
          <SkeletonBlock className="h-6 w-36 rounded-full" />
          <SkeletonBlock className="h-4 w-28" />
        </div>
      </div>

      {/* KPI grid skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-psi-border bg-psi-graphite p-4 space-y-2">
            <SkeletonBlock className="h-3 w-24" />
            <SkeletonBlock className="h-8 w-28" />
            <SkeletonBlock className="h-3 w-32" />
          </div>
        ))}
      </div>

      {/* Chart + AI feed skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-psi-border bg-psi-graphite p-6 space-y-4">
          <SkeletonBlock className="h-5 w-48" />
          <SkeletonBlock className="h-4 w-72" />
          <SkeletonBlock className="h-64 w-full" />
        </div>
        <div className="rounded-xl border border-psi-border bg-psi-graphite p-6 space-y-3">
          <SkeletonBlock className="h-5 w-36" />
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonBlock key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>

      {/* Bottom row skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-psi-border bg-psi-graphite p-6 space-y-4">
          <SkeletonBlock className="h-5 w-40" />
          <SkeletonBlock className="h-4 w-64" />
          <SkeletonBlock className="h-64 w-full" />
        </div>
        <div className="rounded-xl border border-psi-border bg-psi-graphite p-6 space-y-4">
          <SkeletonBlock className="h-5 w-44" />
          <SkeletonBlock className="h-4 w-56" />
          <SkeletonBlock className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}
