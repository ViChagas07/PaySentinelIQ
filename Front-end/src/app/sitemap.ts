import type { MetadataRoute } from "next";
import { routing } from "@/i18n/routing";

const BASE_URL = "https://paysentineliq.com";

const PAGES = [
  { path: "", priority: 1.0, changeFreq: "hourly" as const },
  { path: "/fraud-intelligence", priority: 0.9, changeFreq: "hourly" as const },
  { path: "/verification-center", priority: 0.9, changeFreq: "hourly" as const },
  { path: "/compliance", priority: 0.8, changeFreq: "daily" as const },
  { path: "/payroll", priority: 0.8, changeFreq: "daily" as const },
  { path: "/employees", priority: 0.7, changeFreq: "weekly" as const },
  { path: "/companies", priority: 0.7, changeFreq: "weekly" as const },
  { path: "/reports", priority: 0.6, changeFreq: "weekly" as const },
  { path: "/documents", priority: 0.6, changeFreq: "weekly" as const },
  { path: "/audit-logs", priority: 0.5, changeFreq: "monthly" as const },
  { path: "/settings", priority: 0.4, changeFreq: "monthly" as const },
  { path: "/notifications", priority: 0.4, changeFreq: "monthly" as const },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const entries: MetadataRoute.Sitemap = [];

  for (const locale of routing.locales) {
    const localePrefix = locale === routing.defaultLocale ? "" : `/${locale}`;

    for (const page of PAGES) {
      entries.push({
        url: `${BASE_URL}${localePrefix}${page.path}`,
        lastModified: new Date(),
        changeFrequency: page.changeFreq,
        priority: page.priority,
        alternates: {
          languages: Object.fromEntries(
            routing.locales.map((l) => [
              l,
              `${BASE_URL}${l === routing.defaultLocale ? "" : `/${l}`}${page.path}`,
            ])
          ),
        },
      });
    }
  }

  return entries;
}
