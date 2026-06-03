// ============================================================
// PaySentinelIQ — Skeleton Loader
// ============================================================

import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-psi-border/60",
        className
      )}
      role="status"
      aria-label="Loading"
      {...props}
    />
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-xl border border-psi-border bg-psi-graphite p-6">
      <Skeleton className="mb-3 h-4 w-24" />
      <Skeleton className="mb-2 h-8 w-32" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}

export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex items-center gap-4 px-6 py-4 border-b border-psi-border">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-4", i === 0 ? "w-48" : "w-24")}
        />
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-psi-border bg-psi-graphite p-6">
      <Skeleton className="mb-4 h-5 w-40" />
      <div className="flex items-end gap-3 h-48">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t-md"
            style={{ height: `${30 + Math.random() * 70}%` }}
          />
        ))}
      </div>
    </div>
  );
}
