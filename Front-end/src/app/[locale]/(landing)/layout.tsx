// ============================================================
// PaySentinelIQ — Landing Route Group Layout
// Client component to ensure React context propagation for
// next-intl and other providers reach LandingNav correctly.
// ============================================================

"use client";

import { LandingNav } from "@/components/landing/LandingNav";

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#050816]">
      {/* Subtle background — decorative only, no interaction */}
      <div className="pointer-events-none fixed inset-0" aria-hidden="true">
        <div className="absolute -left-40 top-0 h-[600px] w-[600px] rounded-full bg-[#6A4DFF] opacity-[0.04] blur-[120px]" />
        <div className="absolute -right-40 top-1/3 h-[500px] w-[500px] rounded-full bg-[#00E5FF] opacity-[0.03] blur-[100px]" />
        <div className="absolute bottom-0 left-1/4 h-[400px] w-[400px] rounded-full bg-[#1E6FFF] opacity-[0.04] blur-[100px]" />
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />
      </div>

      <LandingNav />
      <main>{children}</main>
    </div>
  );
}
