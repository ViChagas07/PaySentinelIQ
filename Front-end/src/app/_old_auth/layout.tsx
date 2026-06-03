// ============================================================
// PaySentinelIQ — Auth Layout
// Clean, centered layout for authentication pages
// ============================================================

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-psi-navy p-4">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  );
}
