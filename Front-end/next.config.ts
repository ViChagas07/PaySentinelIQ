import { withSentryConfig } from "@sentry/nextjs";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin();

const nextConfig: NextConfig = {
  // ── Production Output ──
  output: "standalone",

  // ── Image Optimization ──
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [480, 640, 768, 1024, 1280, 1536, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 31536000, // 1 year for immutable assets
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },

  // ── Compression ──
  compress: true,

  // ── HTTP Headers (Security + Performance) ──
  async headers() {
    return [
      {
        // Security headers for PAGES only; static assets (_next/static, .css, .js)
        // are excluded so their original Content-Type is never overridden.
        source: "/:path((?!_next/static|.*\\.(?:css|js|woff2?|avif|webp|png|jpg|svg|ico)).*)",
        headers: [
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), interest-cohort=()" },
        ],
      },
      {
        source: "/:path*.{js,css,woff2,avif,webp,png,jpg,svg,ico}",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
    ];
  },

  // ── Experimental Optimizations ──
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "recharts",
      "framer-motion",
      "@radix-ui/react-avatar",
      "@radix-ui/react-dialog",
      "@radix-ui/react-dropdown-menu",
      "@radix-ui/react-popover",
      "@radix-ui/react-select",
      "@radix-ui/react-tabs",
      "@radix-ui/react-tooltip",
      "@tanstack/react-query",
    ],
    optimizeCss: true,
    scrollRestoration: true,
    webpackBuildWorker: true,
    parallelServerCompiles: true,
    parallelServerBuildTraces: true,
    // Partial Prerendering disabled (requires all client components to have Suspense wrappers)
    // cacheComponents: true,
  },

  // ── Logging ──
  logging: {
    fetches: {
      fullUrl: process.env.NODE_ENV === "development",
    },
  },

  // ── Production Source Maps (off for security + bundle size) ──
  productionBrowserSourceMaps: false,

  // ── React Strict Mode ──
  reactStrictMode: true,

  // ── Powered-By Header (off for security) ──
  poweredByHeader: false,
};

const sentryOrg = process.env.SENTRY_ORG ?? "paysentineliq";
const sentryProject = process.env.SENTRY_PROJECT ?? "paysentineliq-frontend";
const isSentryConfigured = Boolean(process.env.SENTRY_AUTH_TOKEN);

export default withSentryConfig(withNextIntl(nextConfig), {
  // For all available options, see:
  // https://www.npmjs.com/package/@sentry/webpack-plugin#options

  org: sentryOrg,
  project: sentryProject,

  // ══ Source map upload control ═══════════════════════════════════════
  // If SENTRY_AUTH_TOKEN is missing, disable source map upload so the
  // build doesn't fail when Sentry is not fully configured (e.g. local
  // dev or preview deployments without the secret).
  sourcemaps: {
    disable: !isSentryConfigured,
  },

  // Only print logs for uploading source maps in CI
  silent: isSentryConfigured && !process.env.CI,

  // For all available options, see:
  // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

  // Upload a larger set of source maps for prettier stack traces (increases build time)
  widenClientFileUpload: true,

  // Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
  // This can increase your server load as well as your hosting bill.
  // Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
  // side errors will fail.
  tunnelRoute: "/monitoring",

  webpack: {
    // Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
    // See the following for more information:
    // https://docs.sentry.io/product/crons/
    // https://vercel.com/docs/cron-jobs
    automaticVercelMonitors: true,

    // Tree-shaking options for reducing bundle size
    treeshake: {
      // Automatically tree-shake Sentry logger statements to reduce bundle size
      removeDebugLogging: true,
    },
  },
});
