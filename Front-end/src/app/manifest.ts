import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "PaySentinelIQ",
    short_name: "PSI",
    description: "AI-Powered Payroll Verification & Fraud Intelligence",
    start_url: "/",
    display: "standalone",
    background_color: "#0A1628",
    theme_color: "#1E6FFF",
    orientation: "any",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icon-192-maskable.png", sizes: "192x192", type: "image/png", purpose: "maskable" },
      { src: "/icon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    categories: ["business", "finance", "productivity"],
    screenshots: [
      { src: "/screenshot-dashboard.png", sizes: "1280x720", type: "image/png", form_factor: "wide" },
      { src: "/screenshot-mobile.png", sizes: "390x844", type: "image/png", form_factor: "narrow" },
    ],
  };
}
