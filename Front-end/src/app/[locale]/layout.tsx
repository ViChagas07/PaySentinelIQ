import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import "../globals.css";
import { Providers } from "@/providers";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { routing } from "@/i18n/routing";
import { SettingsProvider } from "@/components/settings/SettingsProvider";
import { StructuredData } from "@/components/shared/StructuredData";
import { SkipToContent } from "@/components/shared/SkipToContent";
import GlobalLoading from "./loading";

// ── Optimized Fonts (self-hosted, no external requests) ──
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
  preload: true,
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
  adjustFontFallback: true,
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
  preload: true,
  fallback: ["ui-monospace", "monospace"],
  adjustFontFallback: true,
});

// ── App name per locale ──
const APP_NAMES: Record<string, string> = {
  "pt-BR": "SentinelaPay",
};

function getAppName(locale: string): string {
  return APP_NAMES[locale] || "PaySentinelIQ";
}

// ── Dynamic Metadata per Locale ──
const LOCALE_METADATA: Record<string, { locale: string; title: string; description: string }> = {
  en: { locale: "en_US", title: "PaySentinelIQ | AI-Powered Payroll Verification & Fraud Intelligence", description: "Enterprise-grade payroll verification and fraud risk intelligence platform." },
  "pt-BR": { locale: "pt_BR", title: "SentinelaPay | Verificação de Pagamentos com IA", description: "Plataforma enterprise de verificação de folha de pagamento e inteligência antifraude." },
  es: { locale: "es_ES", title: "PaySentinelIQ | Verificación de Nóminas con IA", description: "Plataforma empresarial de verificación de nóminas e inteligencia antifraude." },
  fr: { locale: "fr_FR", title: "PaySentinelIQ | Vérification de Paie par IA", description: "Plateforme de vérification de paie et intelligence anti-fraude." },
  de: { locale: "de_DE", title: "PaySentinelIQ | KI-gestützte Gehaltsprüfung", description: "Enterprise-Plattform für Gehaltsabrechnungsprüfung und Betrugserkennung." },
  ja: { locale: "ja_JP", title: "PaySentinelIQ | AI給与検証", description: "AI搭載の給与検証と不正検知インテリジェンスプラットフォーム。" },
  zh: { locale: "zh_CN", title: "PaySentinelIQ | AI薪资验证", description: "企业级薪资验证与欺诈情报平台。" },
  ru: { locale: "ru_RU", title: "PaySentinelIQ | Проверка зарплат с ИИ", description: "Корпоративная платформа проверки зарплат и выявления мошенничества." },
  ar: { locale: "ar_SA", title: "PaySentinelIQ | التحقق من الرواتب بالذكاء الاصطناعي", description: "منصة مؤسسية للتحقق من الرواتب واستخبارات الاحتيال." },
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = LOCALE_METADATA[locale] || LOCALE_METADATA.en;
  const appName = getAppName(locale);

  return {
    title: { default: meta.title, template: `%s | ${appName}` },
    description: meta.description,
    keywords: ["payroll verification", "fraud detection", "risk intelligence", "AI compliance"],
    authors: [{ name: appName, url: "https://paysentineliq.com" }],
    creator: appName,
    publisher: appName,
    metadataBase: new URL("https://paysentineliq.com"),
    alternates: { canonical: "/", languages: Object.fromEntries(routing.locales.map((l) => [l, `/${l}`])) },
    openGraph: {
      type: "website",
      locale: meta.locale,
      url: "https://paysentineliq.com",
      siteName: appName,
      title: meta.title,
      description: meta.description,
      images: [{ url: "/og-image.png", width: 1200, height: 630, alt: `${appName} Dashboard` }],
    },
    twitter: {
      card: "summary_large_image",
      title: meta.title,
      description: meta.description,
      images: ["/og-image.png"],
      creator: "@paysentineliq",
    },
    robots: { index: true, follow: true, googleBot: { index: true, follow: true, "max-video-preview": -1, "max-image-preview": "large", "max-snippet": -1 } },
    category: "technology",
  };
}

// ── Root Layout ──
export default async function LocaleLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const messages = await getMessages();
  const t = await getTranslations();
  const skipToContentLabel = t("accessibility.skipToContent");
  const isRTL = locale === "ar";

  return (
    <html
      lang={locale}
      dir={isRTL ? "rtl" : "ltr"}
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        {/* DNS Prefetch + Preconnect for API */}
        <link rel="dns-prefetch" href={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"} />
        <link rel="preconnect" href={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"} crossOrigin="anonymous" />
        {/* Preconnect to CDN for font assets (self-hosted by Next.js, but icon fonts if any) */}
        <link rel="preload" href="/favicon.png" as="image" type="image/png" />
        <link rel="icon" href="/favicon.png" sizes="any" type="image/png" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="theme-color" content="#0A1628" />
        <meta name="color-scheme" content="dark light" />
        {/* Structured Data */}
        <StructuredData locale={locale} />
        {/* Preload critical CSS */}
        <link rel="preload" href="/_next/static/css/app/layout.css" as="style" />
      </head>
      <body className="min-h-full bg-background text-psi-text-primary">
        <SkipToContent label={skipToContentLabel} />
        <div id="a11y-announcer" aria-live="polite" aria-atomic="true" />
        <NextIntlClientProvider messages={messages}>
          <SettingsProvider>
            <Providers>
              <Suspense fallback={<GlobalLoading />}>
                {children}
              </Suspense>
            </Providers>
          </SettingsProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
