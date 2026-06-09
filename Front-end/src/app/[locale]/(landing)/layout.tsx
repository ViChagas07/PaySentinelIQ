// ============================================================
// PaySentinelIQ — Landing Route Group Layout
// Minimal layout: no Sidebar, no AppLayout. Just a clean page.
// ============================================================

import { LandingNav } from "@/components/landing/LandingNav";

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen bg-[#050816] overflow-x-hidden">
      {/* Subtle animated background — lighter than dashboard */}
      <div className="fixed inset-0 pointer-events-none" aria-hidden="true">
        {/* Deep gradient orbs */}
        <div className="absolute top-0 -left-40 w-[600px] h-[600px] rounded-full bg-[#6A4DFF]/[0.04] blur-[120px]" />
        <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-[#00E5FF]/[0.03] blur-[100px]" />
        <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] rounded-full bg-[#1E6FFF]/[0.04] blur-[100px]" />
        {/* Subtle grid overlay */}
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
