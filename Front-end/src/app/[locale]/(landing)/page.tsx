// ============================================================
// PaySentinelIQ — Public Landing Page
// The front door of the app. Visible to everyone.
// Each section is wrapped in its own error boundary for resilience.
// ============================================================

"use client";

import { Component, type ReactNode } from "react";
import { useAuthStore } from "@/stores";
import { LandingHero } from "@/components/landing/LandingHero";
import { TrustBar } from "@/components/landing/TrustBar";
import { FeaturesGrid } from "@/components/landing/FeaturesGrid";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ProductPreview } from "@/components/landing/ProductPreview";
import { StatsSection } from "@/components/landing/StatsSection";
import { CTASection } from "@/components/landing/CTASection";
import { LandingFooter } from "@/components/landing/LandingFooter";

// ── Per-section error boundary: if one section breaks, the rest still render ──

class SectionErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error("Landing section error:", error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? null;
    }
    return this.props.children;
  }
}

// ── Loading state while auth hydrates ──

function AuthLoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#050816]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#1E6FFF] border-t-transparent" />
    </div>
  );
}

// ── Main component ──

export default function LandingPage() {
  const isLoading = useAuthStore((s) => s.isLoading);

  if (isLoading) {
    return <AuthLoadingSpinner />;
  }

  return (
    <>
      <SectionErrorBoundary>
        <LandingHero />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <TrustBar />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <FeaturesGrid />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <HowItWorks />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <ProductPreview />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <StatsSection />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <CTASection />
      </SectionErrorBoundary>

      <SectionErrorBoundary>
        <LandingFooter />
      </SectionErrorBoundary>
    </>
  );
}
