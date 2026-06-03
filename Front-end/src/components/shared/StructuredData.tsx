// ============================================================
// Structured Data (JSON-LD) — must use plain <script> tags,
// NOT next/script, when rendered in Server Component <head>.
// next/script with strategy="beforeInteractive" is incompatible
// with Turbopack's client rendering path in Next.js 16.
// ============================================================

function getAppName(locale: string): string {
  return locale === "pt-BR" ? "SentinelaPay" : "PaySentinelIQ";
}

export function StructuredData({ locale }: { locale: string }) {
  const appName = getAppName(locale);

  const orgData = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: appName,
    url: "https://paysentineliq.com",
    logo: "https://paysentineliq.com/PSI_Logo2.png?v=3",
    description:
      "AI-powered payroll verification and fraud intelligence platform.",
    sameAs: ["https://github.com/paysentineliq"],
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: "support@paysentineliq.com",
    },
  };

  const webAppData = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: appName,
    url: "https://paysentineliq.com",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description:
      "Enterprise payroll verification and fraud risk intelligence platform.",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(orgData) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(webAppData) }}
      />
    </>
  );
}
