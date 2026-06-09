// ============================================================
// PaySentinelIQ — Landing Page Hero
// Full-width hero with animated cards, trust indicators, and CTA
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import {
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Play,
  Sparkles,
  FileCheck,
  Brain,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Animation presets
// ---------------------------------------------------------------------------

const fadeUpStagger = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const },
  }),
};

const containerStagger = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12, delayChildren: 0.1 },
  },
};

const fadeInStagger = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: "easeOut" as const },
  },
};

// ---------------------------------------------------------------------------
// Floating card data
// ---------------------------------------------------------------------------

type FloatingCardData = {
  icon: typeof ShieldCheck;
  iconColor: string;
  glowColor: string;
  titleKey: string;
  metricKey: string;
  positionClasses: string;
  floatDelay: number;
};

const cards: FloatingCardData[] = [
  {
    icon: ShieldCheck,
    iconColor: "text-[#00C48C]",
    glowColor: "shadow-[#00C48C]/15",
    titleKey: "hero.card1.title",
    metricKey: "hero.card1.risk",
    positionClasses: "lg:ml-4 lg:mt-0",
    floatDelay: 0,
  },
  {
    icon: FileCheck,
    iconColor: "text-[#1E6FFF]",
    glowColor: "shadow-[#1E6FFF]/15",
    titleKey: "hero.card2.title",
    metricKey: "hero.card2.authenticity",
    positionClasses: "lg:ml-16 lg:-mt-4",
    floatDelay: 0.6,
  },
  {
    icon: Brain,
    iconColor: "text-[#6A4DFF]",
    glowColor: "shadow-[#6A4DFF]/15",
    titleKey: "hero.card3.title",
    metricKey: "hero.card3.confidence",
    positionClasses: "lg:ml-8 lg:-mt-4",
    floatDelay: 1.2,
  },
];

const trustItems = [
  { key: "hero.trust.ai" },
  { key: "hero.trust.realtime" },
  { key: "hero.trust.security" },
  { key: "hero.trust.compliance" },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FloatingAnalysisCard({
  icon: Icon,
  iconColor,
  glowColor,
  titleKey,
  metricKey,
  floatDelay,
}: FloatingCardData) {
  const t = useTranslations("landing");

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ delay: floatDelay + 0.3, duration: 0.5 }}
      className={cn(
        "relative w-full max-w-xs",
        glowColor,
      )}
    >
      <motion.div
        animate={{
          y: [0, -10, 0],
          rotate: [0, 0.8, 0, -0.6, 0],
        }}
        transition={{
          y: { repeat: Infinity, duration: 3.6, ease: "easeInOut", delay: floatDelay },
          rotate: { repeat: Infinity, duration: 5, ease: "easeInOut", delay: floatDelay },
        }}
        className={cn(
          "relative w-full rounded-2xl border border-white/[0.06]",
          "bg-white/[0.03] backdrop-blur-xl p-5",
          "shadow-lg hover:shadow-xl transition-shadow duration-500",
          "group cursor-default",
        )}
      >
      {/* Card inner glow */}
      <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div
          className="absolute inset-0 rounded-2xl opacity-20 blur-md"
          style={{
            background: `radial-gradient(ellipse at 30% 20%, ${iconColor.replace("text-", "")}, transparent 70%)`,
          }}
        />
      </div>

      {/* Pulse ring */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 rounded-2xl border opacity-0 group-hover:opacity-100 transition-opacity duration-700",
          iconColor.replace("text-", "border-").replace("border-[", "border-[") + "/20"
        )}
      />

      <div className="relative z-10 flex items-start justify-between">
        <p className="text-sm font-medium text-white/90">{t(titleKey)}</p>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04]", iconColor)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="relative z-10 mt-4">
        <span className={cn("text-2xl font-bold tracking-tight", iconColor)}>
          {t(metricKey)}
        </span>
      </div>

      {/* Mini progress bar decoration */}
      <div className="relative z-10 mt-3 h-1 w-full overflow-hidden rounded-full bg-white/[0.05]">
        <motion.div
          className={cn("h-full rounded-full", iconColor.replace("text-", "bg-"))}
          initial={{ width: "0%" }}
          whileInView={{ width: "85%" }}
          viewport={{ once: true }}
          transition={{ delay: floatDelay + 0.6, duration: 0.8, ease: "easeOut" }}
        />
      </div>
      </motion.div>
    </motion.div>
  );
}

function TrustIndicator({ textKey, index }: { textKey: string; index: number }) {
  const t = useTranslations("landing");

  return (
    <motion.div
      custom={index}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      variants={fadeUpStagger}
      className="flex items-center gap-2"
    >
      <CheckCircle2 className="h-4 w-4 shrink-0 text-[#00C48C]" />
      <span className="text-sm text-white/50">{t(textKey)}</span>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function LandingHero() {
  const t = useTranslations("landing");

  return (
    <section className="relative min-h-screen overflow-hidden bg-[#050816] pt-28 lg:pt-44">
      {/* Decorative background elements */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        {/* Top-right glow */}
        <div className="absolute -top-48 right-0 h-[600px] w-[600px] rounded-full bg-[#1E6FFF]/5 blur-[120px]" />
        {/* Bottom-left glow */}
        <div className="absolute -bottom-48 -left-32 h-[500px] w-[500px] rounded-full bg-[#6A4DFF]/5 blur-[120px]" />
        {/* Center accent */}
        <div className="absolute left-1/2 top-1/3 h-[400px] w-[400px] -translate-x-1/2 rounded-full bg-[#00E5FF]/3 blur-[100px]" />
        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-16 xl:gap-24">
          {/* ============================================================
              LEFT SIDE — Text content
              ============================================================ */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerStagger}
            className="flex flex-col items-start text-left"
          >
            {/* Badge */}
            <motion.div
              variants={fadeInStagger}
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#1E6FFF]/20 bg-[#1E6FFF]/5 px-4 py-1.5 shadow-[0_0_24px_rgba(30,111,255,0.15)]"
            >
              <Sparkles className="h-3.5 w-3.5 text-[#1E6FFF]" />
              <span className="bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] bg-clip-text text-xs font-semibold tracking-wide text-transparent">
                {t("hero.badge")}
              </span>
            </motion.div>

            {/* Heading */}
            <motion.h1
              variants={fadeInStagger}
              className="max-w-xl text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl lg:text-[3.4rem] lg:leading-[1.1]"
            >
              {t("hero.title")}
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              variants={fadeInStagger}
              className="mt-5 max-w-lg text-base leading-relaxed text-white/50 sm:text-lg"
            >
              {t("hero.subtitle")}
            </motion.p>

            {/* Buttons */}
            <motion.div variants={fadeInStagger} className="mt-8 flex flex-wrap items-center gap-3">
              <Button
                asChild
                size="lg"
                className="gap-2 rounded-xl bg-gradient-to-r from-[#1E6FFF] to-[#6A4DFF] px-6 py-3 text-white shadow-lg shadow-[#1E6FFF]/20 hover:from-[#1E6FFF]/90 hover:to-[#6A4DFF]/90"
              >
                <Link href="/auth/login">
                  {t("hero.cta")}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>

              <Button
                variant="ghost"
                size="lg"
                className="gap-2 rounded-xl border border-white/[0.06] px-6 py-3 text-white/70 hover:bg-white/[0.05] hover:text-white"
              >
                <Play className="h-4 w-4 fill-white/70" />
                {t("hero.demo")}
              </Button>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              variants={fadeInStagger}
              className="mt-10 grid w-full max-w-lg grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4"
            >
              {trustItems.map((item, i) => (
                <TrustIndicator key={item.key} textKey={item.key} index={i} />
              ))}
            </motion.div>
          </motion.div>

          {/* ============================================================
              RIGHT SIDE — Animated cards
              ============================================================ */}
          <div className="relative flex items-center justify-center lg:justify-end">
            {/* Backdrop orbs */}
            <div className="pointer-events-none absolute inset-0" aria-hidden="true">
              <div className="absolute left-1/4 top-0 h-64 w-64 rounded-full bg-[#1E6FFF]/10 blur-[80px]" />
              <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-[#6A4DFF]/10 blur-[80px]" />
              <div className="absolute left-0 top-1/2 h-48 w-48 -translate-y-1/2 rounded-full bg-[#00E5FF]/8 blur-[80px]" />
            </div>

            {/* Glowing vertical connector line */}
            <div className="pointer-events-none absolute left-1/2 top-[5%] hidden h-[85%] w-px lg:block" aria-hidden="true">
              <div className="h-full w-full bg-gradient-to-b from-transparent via-[#1E6FFF]/20 to-transparent" />
            </div>

            {/* Cards stack */}
            <div className="relative flex w-full flex-col items-center gap-5 py-8 lg:items-end lg:py-4">
              {cards.map((card) => (
                <div key={card.titleKey} className={cn("w-full max-w-xs", card.positionClasses)}>
                  <FloatingAnalysisCard {...card} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom fade-out so content below blends smoothly */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#050816] to-transparent" />
    </section>
  );
}
