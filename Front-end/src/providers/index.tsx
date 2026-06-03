// ============================================================
// PaySentinelIQ — Global Providers
// TanStack Query + any future providers
// ============================================================

"use client";

import { QueryProvider } from "./QueryProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
