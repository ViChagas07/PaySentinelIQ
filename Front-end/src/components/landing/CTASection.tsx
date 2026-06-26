// ============================================================
// PaySentinelIQ — CTA Section
// Immersive call-to-action with glowing gradient orb
// Adapts buttons based on authentication state
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { ArrowRight, LogIn, LayoutDashboard } from "lucide-react";
import { useAuthStore } from "@/stores";

export function CTASection() {
  const t = useTranslations("landing");
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <section
      id="cta"
      className="relative w-full overflow-hidden bg-[#050816] py-24 lg:py-32"
    >
      {/* Large glowing orb background */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center" aria-hidden="true">
        <div
          className="h-[500px] w-[500px] rounded-full blur-[120px] sm:h-[700px] sm:w-[700px]"
          style={{
            background:
              "radial-gradient(circle at center, rgba(106,77,255,0.25) 0%, rgba(30,111,255,0.18) 40%, transparent 70%)",
          }}
        />
      </div>

      {/* Dark overlay to ensure text contrast */}
      <div className="pointer-events-none absolute inset-0 bg-[#050816]/30" aria-hidden="true" />

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 32, scale: 0.97 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ margin: "-80px" }}
          transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          <h2 className="text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl">
            {t("cta.title")}
          </h2>

          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-white/50 sm:text-lg">
            {t("cta.subtitle")}
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            {isAuthenticated ? (
              <Button
                asChild
                size="lg"
                className={cn(
                  "gap-2 rounded-xl bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] px-8 py-3",
                  "text-white shadow-lg shadow-[#1E6FFF]/20",
                  "hover:from-[#1E6FFF]/90 hover:to-[#6A4DFF]/90"
                )}
              >
                <Link href="/dashboard">
                  <span className="inline-flex items-center gap-2">
                    <LayoutDashboard className="h-4 w-4" />
                    {t("cta.goToDashboard")}
                    <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
              </Button>
            ) : (
              <>
                <Button
                  asChild
                  size="lg"
                  className={cn(
                    "gap-2 rounded-xl bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] px-8 py-3",
                    "text-white shadow-lg shadow-[#1E6FFF]/20",
                    "hover:from-[#1E6FFF]/90 hover:to-[#6A4DFF]/90"
                  )}
                >
                  <Link href="/auth/login">
                    <span className="inline-flex items-center gap-2">
                      {t("cta.startFree")}
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  </Link>
                </Button>

                <Button
                  variant="outline"
                  asChild
                  size="lg"
                  className={cn(
                    "gap-2 rounded-xl border-white/20 px-8 py-3",
                    "text-white/70 hover:bg-white/[0.05] hover:text-white"
                  )}
                >
                  <Link href="/auth/login">
                    <span className="inline-flex items-center gap-2">
                      <LogIn className="h-4 w-4" />
                      {t("cta.login")}
                    </span>
                  </Link>
                </Button>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
