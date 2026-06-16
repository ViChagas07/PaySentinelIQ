// ============================================================
// PaySentinelIQ — Landing Trust Bar
// Logo + app name header, animated icon grid with levitation on hover
// ============================================================

"use client";

import { useState } from "react";
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
import { AppName } from "@/components/shared/AppName";
import Image from "next/image";

// ── Trust items data ── //

interface TrustItem {
  icon: LucideIcon;
  labelKey: string;
  accentColor: string;
  accentGlow: string;
}

const TRUST_ITEMS: TrustItem[] = [
  { icon: Brain, labelKey: "trust.ai", accentColor: "#1E6FFF", accentGlow: "rgba(30,111,255,0.25)" },
  { icon: ShieldCheck, labelKey: "trust.security", accentColor: "#00C48C", accentGlow: "rgba(0,196,140,0.25)" },
  { icon: BarChart3, labelKey: "trust.analytics", accentColor: "#6A4DFF", accentGlow: "rgba(106,77,255,0.25)" },
  { icon: DollarSign, labelKey: "trust.payments", accentColor: "#00E5FF", accentGlow: "rgba(0,229,255,0.25)" },
  { icon: FileCheck, labelKey: "trust.compliance", accentColor: "#1E6FFF", accentGlow: "rgba(30,111,255,0.25)" },
  { icon: SearchCheck, labelKey: "trust.verification", accentColor: "#00C48C", accentGlow: "rgba(0,196,140,0.25)" },
];

// ── Animation variants ── //

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
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

// ── Levitating icon card sub-component ── //

function TrustCard({ item }: { item: TrustItem }) {
  const t = useTranslations("landing");
  const [hovered, setHovered] = useState(false);
  const Icon = item.icon;

  return (
    <motion.div
      variants={itemVariants}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        "relative flex flex-col items-center justify-center gap-3 rounded-xl",
        "bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm",
        "py-6 px-3 cursor-default",
        "transition-all duration-500",
        hovered && "border-white/[0.15]"
      )}
      style={{
        boxShadow: hovered
          ? `0 8px 32px ${item.accentGlow}, inset 0 1px 0 ${item.accentGlow}`
          : "0 2px 8px rgba(0,0,0,0.15)",
      }}
    >
      {/* Levitating icon */}
      <motion.div
        animate={{ y: hovered ? -6 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20, mass: 0.6 }}
        className="relative"
      >
        {/* Glow ring behind icon */}
        <motion.div
          className="absolute inset-0 rounded-full blur-md"
          animate={{
            opacity: hovered ? 1 : 0,
            scale: hovered ? 1.6 : 0.8,
          }}
          transition={{ duration: 0.4 }}
          style={{ backgroundColor: item.accentGlow }}
        />
        <Icon
          className={cn(
            "relative w-8 h-8 transition-colors duration-300",
            hovered ? "text-white" : "text-white/60"
          )}
          strokeWidth={1.5}
        />
      </motion.div>

      {/* Label */}
      <motion.span
        animate={{ y: hovered ? 2 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20, mass: 0.6 }}
        className={cn(
          "text-xs md:text-sm text-center font-medium transition-colors duration-300",
          hovered ? "text-white" : "text-white/50"
        )}
      >
        {t(item.labelKey)}
      </motion.span>
    </motion.div>
  );
}

// ── Main component ── //

export function TrustBar() {
  const t = useTranslations("landing");

  return (
    <section
      id="trust"
      className="relative w-full bg-[#050816] border-t border-b border-white/[0.06] py-16 lg:py-20"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* ── Logo + App name header ── */}
        <motion.div
          className="flex flex-col items-center justify-center mb-10"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        >
          <div className="relative mb-4">
            {/* Glow behind logo */}
            <div className="absolute inset-0 rounded-full bg-[#1E6FFF]/20 blur-3xl scale-150" />
            <Image
              src="/PSI_Logo2.png"
              alt="PaySentinelIQ"
              width={180}
              height={180}
              className="relative h-40 w-auto object-contain"
              priority
            />
          </div>
          <AppName
            as="span"
            className="text-3xl md:text-4xl font-bold tracking-tight text-white"
          />
        </motion.div>

        {/* ── Trust title ── */}
        <motion.h2
          className="text-center text-2xl md:text-3xl lg:text-4xl font-bold text-white mb-12"
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
        >
          {t("trust.title")}
        </motion.h2>

        {/* ── Trust icon grid ── */}
        <motion.div
          className="mx-auto max-w-5xl grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 lg:gap-5"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
        >
          {TRUST_ITEMS.map((item, idx) => (
            <TrustCard key={idx} item={item} />
          ))}
        </motion.div>
      </div>
    </section>
  );
}
