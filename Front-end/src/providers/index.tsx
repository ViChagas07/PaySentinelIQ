// ============================================================
// PaySentinelIQ — Global Providers
// TanStack Query, Sonner Toaster, and notification listener
// ============================================================

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { QueryProvider } from "./QueryProvider";
import { Toaster } from "sonner";

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  // ── Deep linking listener for burst summary "View All" action ──
  useEffect(() => {
    function handleNavigate(e: CustomEvent<{ path: string }>) {
      router.push(e.detail.path);
    }

    window.addEventListener("psi:navigate", handleNavigate as EventListener);
    return () => {
      window.removeEventListener("psi:navigate", handleNavigate as EventListener);
    };
  }, [router]);

  return (
    <QueryProvider>
      {children}
      <Toaster
        position="top-right"
        richColors
        closeButton
        expand
        visibleToasts={6}
        gap={12}
        offset={72} /* below navbar (56px + 16px) */
        toastOptions={{
          duration: 5000,
          style: {
            fontFamily: "var(--font-sans)",
          },
        }}
      />
    </QueryProvider>
  );
}
