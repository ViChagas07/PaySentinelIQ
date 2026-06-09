// ============================================================
// PaySentinelIQ — How It Works Timeline Section
// Vertical alternating timeline with 4 steps and animations
// ============================================================

"use client";

import { useRef } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { Upload, Cpu, ShieldCheck, BarChart3, ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Step data
// ---------------------------------------------------------------------------

interface StepData {
  step: number;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  titleKey: string;
  descKey: string;
  accent: string;
}

const steps: StepData[] = [
  {
    step: 1,
    icon: Upload,
    titleKey: "how.step1.title",
    descKey: "how.step1.desc",
    accent: "#1E6FFF",
  },
  {
    step: 2,
    icon: Cpu,
    titleKey: "how.step2.title",
    descKey: "how.step2.desc",
    accent: "#6A4DFF",
  },
  {
    step: 3,
    icon: ShieldCheck,
    titleKey: "how.step3.title",
    descKey: "how.step3.desc",
    accent: "#00C48C",
  },
  {
    step: 4,
    icon: BarChart3,
    titleKey: "how.step4.title",
    descKey: "how.step4.desc",
    accent: "#00E5FF",
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TimelineStep({
  step,
  icon: Icon,
  titleKey,
  descKey,
  accent,
  isLeft,
  isLast,
}: StepData & { isLeft: boolean; isLast: boolean }) {
  const t = useTranslations("landing");

  return (
    <motion.div
      initial={{ opacity: 0, x: isLeft ? -40 : 40 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, delay: step * 0.15, ease: "easeOut" }}
      className={cn(
        "relative w-full",
        "lg:w-1/2",
        isLeft ? "lg:pr-16 lg:self-start lg:text-right" : "lg:pl-16 lg:self-end",
      )}
    >
      {/* Step number badge — overlaps card edge */}
      <div
        className={cn(
          "absolute top-4 z-20",
          isLeft ? "-right-4 lg:-right-5" : "-left-4 lg:-left-5",
        )}
      >
        <div
          className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold text-white"
          style={{ backgroundColor: accent }}
        >
          {step}
        </div>
      </div>

      {/* Card */}
      <div
        className={cn(
          "group relative rounded-2xl p-6",
          "bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm",
          "transition-all duration-500",
          "hover:border-white/[0.12]",
          "hover:shadow-[0_8px_40px_rgba(30,111,255,0.06)]",
        )}
      >
        {/* Hover glow border */}
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100"
          style={{
            background: `linear-gradient(135deg, ${accent}14 0%, transparent 50%, ${accent}14 100%)`,
          }}
        />

        {/* Icon in gradient circle */}
        <div
          className={cn(
            "mb-4 inline-flex items-center justify-center rounded-full p-3",
            "bg-gradient-to-br from-[#1E6FFF]/20 to-[#6A4DFF]/20",
          )}
        >
          <Icon className="h-6 w-6 text-white/80" strokeWidth={1.5} />
        </div>

        {/* Title */}
        <h3 className="mb-2 text-lg font-semibold text-white">
          {t(titleKey)}
        </h3>

        {/* Description */}
        <p className="text-sm leading-relaxed text-white/50">
          {t(descKey)}
        </p>

        {/* Bottom edge glow on hover */}
        <div
          className={cn(
            "absolute bottom-0 left-4 right-4 h-px",
            "bg-gradient-to-r from-transparent via-white/0 to-transparent",
            "transition-all duration-500",
            "group-hover:via-white/10",
          )}
        />
      </div>

      {/* Mobile connector arrow (desktop uses central line) */}
      {!isLast && (
        <div
          className={cn(
            "flex justify-center py-2",
            isLeft ? "lg:hidden" : "lg:hidden",
          )}
        >
          <ArrowDown className="h-5 w-5 text-white/15" />
        </div>
      )}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function HowItWorks() {
  const t = useTranslations("landing");
  const timelineRef = useRef<HTMLDivElement>(null);

  return (
    <section
      id="how-it-works"
      className="relative w-full overflow-hidden bg-[#050816] py-20 lg:py-28"
    >
      {/* Decorative background */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        {/* Subtle dots pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        {/* Ambient glows */}
        <div className="absolute -top-32 left-1/4 h-80 w-80 rounded-full bg-[#1E6FFF]/5 blur-[100px]" />
        <div className="absolute right-1/4 top-1/2 h-96 w-96 rounded-full bg-[#6A4DFF]/4 blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-[#00E5FF]/4 blur-[80px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="mb-16 text-center lg:mb-20"
        >
          <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl lg:text-5xl">
            {t("how.title")}
          </h2>
          <p className="mx-auto max-w-xl text-base text-white/50 md:text-lg">
            {t("how.subtitle")}
          </p>
        </motion.div>

        {/* Timeline */}
        <div ref={timelineRef} className="relative">
          {/* Central connector line (desktop only) */}
          <div
            className="pointer-events-none absolute left-4 top-0 hidden h-full w-px lg:left-1/2 lg:block"
            aria-hidden="true"
          >
            {/* Animated gradient line */}
            <div className="h-full w-full animate-pulse bg-gradient-to-b from-[#1E6FFF]/30 via-[#6A4DFF]/30 to-[#00E5FF]/30 opacity-60" />
            {/* Glow overlay */}
            <div className="absolute inset-0 h-full w-px bg-gradient-to-b from-transparent via-white/20 to-transparent" />
          </div>

          {/* Steps */}
          <div className="flex flex-col gap-8 lg:gap-12">
            {steps.map((s, i) => (
              <TimelineStep
                key={s.step}
                {...s}
                isLeft={i % 2 === 0}
                isLast={i === steps.length - 1}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
