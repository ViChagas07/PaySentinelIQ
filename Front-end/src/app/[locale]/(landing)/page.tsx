// ============================================================
// PaySentinelIQ — Public Landing Page
// The front door of the app. Visible to everyone.
// Authenticated users see a "Go to Dashboard" option in the nav.
// ============================================================

"use client";

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
  const isLoading = useAuthStore((s) => s.isLoading);

  // Brief loading spinner while auth state hydrates from localStorage
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#050816] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#1E6FFF] border-t-transparent" />
      </div>
    );
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
