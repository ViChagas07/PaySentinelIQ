"use client";

import { Suspense } from "react";
import { useTranslations } from "next-intl";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { AIAssistantPanel } from "@/components/dashboard/AIAssistantPanel";
import { NotificationPanel } from "@/components/dashboard/NotificationPanel";

function ContentSkeleton() {
  const t = useTranslations("common");
  return (
    <div className="flex-1 p-6 lg:p-8 space-y-4" role="status" aria-label={t("loading")} aria-busy="true">
      <div className="h-8 w-56 animate-pulse rounded-lg bg-psi-border/50" />
      <div className="h-4 w-80 animate-pulse rounded-lg bg-psi-border/30" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl bg-psi-border/30" />
        ))}
      </div>
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-dvh overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Navbar />
        <div className="flex flex-1 overflow-hidden">
          <main id="main-content" className="flex-1 overflow-y-auto overflow-x-hidden" tabIndex={-1}>
            <ErrorBoundary>
              <Suspense fallback={<ContentSkeleton />}>
                <div className="p-3 sm:p-4 md:p-6 lg:p-8">
                  {children}
                </div>
              </Suspense>
            </ErrorBoundary>
          </main>
          <AIAssistantPanel />
          <NotificationPanel />
        </div>
      </div>
    </div>
  );
}
