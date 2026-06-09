// ============================================================
// PaySentinelIQ — Public Landing Page
// The FIRST page unauthenticated users see.
// Authenticated users are redirected to /dashboard.
// ============================================================

"use client";

import { useEffect } from "react";
import { useRouter } from "@/i18n/navigation";
import { useAuthStore } from "@/stores";
import { LandingHero } from "@/components/landing/LandingHero";
import { TrustBar } from "@/components/landing/TrustBar";
import { FeaturesGrid } from "@/components/landing/FeaturesGrid";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ProductPreview } from "@/components/landing/ProductPreview";
import { StatsSection } from "@/components/landing/StatsSection";
import { CTASection } from "@/components/landing/CTASection";
import { LandingFooter } from "@/components/landing/LandingFooter";

export default function LandingPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  // Show nothing while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#050816] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#1E6FFF] border-t-transparent" />
      </div>
    );
  }

  // Don't render landing for authenticated users (they'll be redirected)
  if (isAuthenticated) {
    return null;
  }

  return (
    <>
      <LandingHero />
      <TrustBar />
      <FeaturesGrid />
      <HowItWorks />
      <ProductPreview />
      <StatsSection />
      <CTASection />
      <LandingFooter />
    </>
  );
}
