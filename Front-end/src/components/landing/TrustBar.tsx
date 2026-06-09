// ============================================================
// PaySentinelIQ — Landing Trust Bar
// Animated icon grid showcasing trust pillars
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import {
  Brain,
  ShieldCheck,
  BarChart3,
  DollarSign,
  FileCheck,
  SearchCheck,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TrustItem {
  icon: LucideIcon;
  labelKey: string;
}

const TRUST_ITEMS: TrustItem[] = [
  { icon: Brain, labelKey: "trust.ai" },
  { icon: ShieldCheck, labelKey: "trust.security" },
  { icon: BarChart3, labelKey: "trust.analytics" },
  { icon: DollarSign, labelKey: "trust.payments" },
  { icon: FileCheck, labelKey: "trust.compliance" },
  { icon: SearchCheck, labelKey: "trust.verification" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

export function TrustBar() {
  const t = useTranslations("landing");

  return (
    <section
      id="trust"
      className="relative w-full bg-[#050816] border-t border-b border-white/[0.06] py-16 lg:py-20"
    >
      {/* Section title */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 mb-12">
        <h2 className="text-center text-2xl md:text-3xl lg:text-4xl font-bold text-white">
          {t("trust.title")}
        </h2>
      </div>

      {/* Trust icon grid */}
      <motion.div
        className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 lg:gap-5"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-80px" }}
      >
        {TRUST_ITEMS.map((item, idx) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={idx}
              variants={itemVariants}
              className={cn(
                "flex flex-col items-center justify-center gap-3 rounded-xl",
                "bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm",
                "py-6 px-3 group cursor-default",
                "transition-colors duration-300"
              )}
            >
              <Icon
                className={cn(
                  "w-8 h-8 text-white/60 transition-colors duration-300",
                  "group-hover:text-psi-electric"
                )}
                strokeWidth={1.5}
              />
              <span className="text-xs md:text-sm text-white/50 text-center font-medium transition-colors duration-300 group-hover:text-white/80">
                {t(item.labelKey)}
              </span>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}
