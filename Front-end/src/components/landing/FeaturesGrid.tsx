// ============================================================
// PaySentinelIQ — Landing Features Grid
// Six feature cards showcasing the platform's capabilities
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Brain,
  Sparkles,
  FileSearch,
  Receipt,
  Lightbulb,
  ShieldCheck,
  ScrollText,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FeatureCard {
  icon: LucideIcon;
  accentIcon?: LucideIcon;
  titleKey: string;
  descKey: string;
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    icon: Brain,
    accentIcon: Sparkles,
    titleKey: "features.fraud.title",
    descKey: "features.fraud.desc",
  },
  {
    icon: FileSearch,
    titleKey: "features.payroll.title",
    descKey: "features.payroll.desc",
  },
  {
    icon: Receipt,
    titleKey: "features.invoice.title",
    descKey: "features.invoice.desc",
  },
  {
    icon: Lightbulb,
    titleKey: "features.insights.title",
    descKey: "features.insights.desc",
  },
  {
    icon: ShieldCheck,
    titleKey: "features.compliance.title",
    descKey: "features.compliance.desc",
  },
  {
    icon: ScrollText,
    titleKey: "features.audit.title",
    descKey: "features.audit.desc",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

export function FeaturesGrid() {
  const t = useTranslations("landing");

  return (
    <section
      id="features"
      className="relative w-full bg-[#050816] py-20 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section heading */}
        <div className="text-center mb-14 lg:mb-16">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4">
            {t("features.title")}
          </h2>
          <p className="text-base md:text-lg text-white/50 max-w-2xl mx-auto">
            {t("features.subtitle")}
          </p>
        </div>

        {/* Feature cards grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 lg:gap-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ margin: "-60px" }}
        >
          {FEATURE_CARDS.map((card, idx) => {
            const Icon = card.icon;
            const AccentIcon = card.accentIcon;
            return (
              <motion.div
                key={idx}
                variants={cardVariants}
                className={cn(
                  "group relative rounded-2xl p-6",
                  "bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm",
                  "transition-all duration-300",
                  "hover:-translate-y-1",
                  "hover:border-psi-electric/30",
                  "hover:shadow-[0_8px_40px_rgba(30,111,255,0.08)]"
                )}
              >
                {/* Icon container */}
                <div
                  className={cn(
                    "inline-flex items-center justify-center rounded-lg p-2.5 mb-5",
                    "bg-gradient-to-br from-psi-electric/20 to-[#6A4DFF]/20",
                    "transition-colors duration-300",
                    "group-hover:from-psi-electric/25 group-hover:to-[#6A4DFF]/25"
                  )}
                >
                  <Icon
                    className={cn(
                      "w-6 h-6 text-white/80 transition-colors duration-300",
                      "group-hover:text-psi-electric"
                    )}
                    strokeWidth={1.5}
                  />
                  {AccentIcon && (
                    <AccentIcon
                      className={cn(
                        "w-3.5 h-3.5 text-white/60 transition-colors duration-300 -ml-1 -mb-1",
                        "group-hover:text-psi-electric"
                      )}
                      strokeWidth={1.5}
                    />
                  )}
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold text-white mb-2">
                  {t(card.titleKey)}
                </h3>

                {/* Description */}
                <p className="text-sm text-white/50 leading-relaxed">
                  {t(card.descKey)}
                </p>

                {/* Subtle bottom highlight line on hover */}
                <div
                  className={cn(
                    "absolute bottom-0 left-4 right-4 h-px",
                    "bg-gradient-to-r from-transparent via-psi-electric/0 to-transparent",
                    "transition-all duration-300",
                    "group-hover:via-psi-electric/20"
                  )}
                />
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
