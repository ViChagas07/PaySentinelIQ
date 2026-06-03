// ============================================================
// PaySentinelIQ — App Route Group Layout
// Wraps all authenticated pages with Sidebar + Navbar
// ============================================================

import AppLayout from "@/components/layout/AppLayout";

export default function AppGroupLayout({ children }: { children: React.ReactNode }) {
  return <AppLayout>{children}</AppLayout>;
}
