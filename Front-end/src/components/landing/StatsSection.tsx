// ============================================================
// PaySentinelIQ — Animated Statistics / Counters Section
// Four stat cards with count-up animations on scroll
// ============================================================

"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { ShieldCheck, Brain, Clock, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StatData {
  valueKey: string;
  labelKey: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  accent: string;
  accentGlow: string;
  type: "count" | "fadeIn";
  target?: number;
  suffix?: string;
}

const stats: StatData[] = [
  {
    valueKey: "stats.accuracy",
    labelKey: "stats.accuracyLabel",
    icon: ShieldCheck,
    accent: "text-[#00C48C]",
    accentGlow: "shadow-[#00C48C]/20",
    type: "count",
    target: 98,
    suffix: "%",
  },
  {
    valueKey: "stats.rules",
    labelKey: "stats.rulesLabel",
    icon: Brain,
    accent: "text-[#1E6FFF]",
    accentGlow: "shadow-[#1E6FFF]/20",
    type: "count",
    target: 50,
    suffix: "+",
  },
  {
    valueKey: "stats.monitoring",
    labelKey: "stats.monitoringLabel",
    icon: Clock,
    accent: "text-[#6A4DFF]",
    accentGlow: "shadow-[#6A4DFF]/20",
    type: "fadeIn",
  },
  {
    valueKey: "stats.realtime",
    labelKey: "stats.realtimeLabel",
    icon: Zap,
    accent: "text-[#00E5FF]",
    accentGlow: "shadow-[#00E5FF]/20",
    type: "fadeIn",
  },
];

// ---------------------------------------------------------------------------
// AnimatedCounter — count-up sub-component
// ---------------------------------------------------------------------------

function AnimatedCounter({
  target,
  suffix = "",
  inView,
}: {
  target: number;
  suffix?: string;
  inView: boolean;
}) {
  const [count, setCount] = useState(0);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!inView || startedRef.current) return;
    startedRef.current = true;

    const duration = 1500;
    const steps = 40;
    const increment = target / steps;
    const interval = duration / steps;

    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, interval);

    return () => clearInterval(timer);
  }, [inView, target]);

  return (
    <span className="relative inline-block">
      <span className="text-5xl font-bold tracking-tight md:text-6xl">
        {count}
      </span>
      <span className="text-5xl font-bold tracking-tight md:text-6xl">
        {suffix}
      </span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// AnimatedTypewriter — typewriter/fade-in sub-component
// ---------------------------------------------------------------------------

function AnimatedTypewriter({
  text,
  inView,
}: {
  text: string;
  inView: boolean;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!inView || visible) return;
    const timer = setTimeout(() => setVisible(true), 200);
    return () => clearTimeout(timer);
  }, [inView, visible]);

  return (
    <span
      className={cn(
        "text-4xl font-bold tracking-tight transition-all duration-700 md:text-5xl",
        visible ? "translate-y-0 opacity-100 blur-0" : "translate-y-2 opacity-0 blur-[2px]",
      )}
    >
      {text}
    </span>
  );
}

// ---------------------------------------------------------------------------
// StatCard
// ---------------------------------------------------------------------------

function StatCard({
  stat,
  index,
  inView,
}: {
  stat: StatData;
  index: number;
  inView: boolean;
}) {
  const t = useTranslations("landing");
  const Icon = stat.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, delay: index * 0.12, ease: "easeOut" }}
      className={cn(
        "group relative rounded-2xl p-6",
        "bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm",
        "transition-all duration-500",
        "hover:scale-[1.02]",
        stat.accentGlow,
        "hover:shadow-[0_8px_40px_rgba(30,111,255,0.08)]",
      )}
    >
      {/* Accent glow on hover */}
      <div
        className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{
          background: `radial-gradient(circle at 50% 0%, ${stat.accent.replace("text-", "")}0D, transparent 60%)`,
        }}
      />

      {/* Icon in top corner */}
      <div
        className={cn(
          "mb-4 inline-flex items-center justify-center rounded-xl p-2.5",
          "bg-white/[0.05]",
          stat.accent,
          "transition-colors duration-300 group-hover:bg-white/[0.08]",
        )}
      >
        <Icon className="h-5 w-5" strokeWidth={1.5} />
      </div>

      {/* Value */}
      <div className={cn("mb-2", stat.accent)}>
        {stat.type === "count" ? (
          <AnimatedCounter
            target={stat.target!}
            suffix={stat.suffix ?? ""}
            inView={inView}
          />
        ) : (
          <AnimatedTypewriter text={t(stat.valueKey)} inView={inView} />
        )}
      </div>

      {/* Label */}
      <p className="text-sm text-white/50">{t(stat.labelKey)}</p>

      {/* Bottom accent line */}
      <div
        className={cn(
          "absolute bottom-0 left-4 right-4 h-px",
          "bg-gradient-to-r from-transparent via-current/0 to-transparent",
          "transition-all duration-500",
          "group-hover:via-current/10",
        )}
      />
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function StatsSection() {
  const t = useTranslations("landing");
  const sectionRef = useRef<HTMLElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2, rootMargin: "-60px" },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="stats"
      className="relative w-full bg-gradient-to-b from-[#050816] via-[#0B1026] to-[#050816] py-20 lg:py-28"
    >
      {/* Decorative background */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute left-1/2 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-[#1E6FFF]/4 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-80 w-80 rounded-full bg-[#6A4DFF]/4 blur-[100px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section heading */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="mb-14 text-center lg:mb-16"
        >
          <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl lg:text-5xl">
            {t("stats.title")}
          </h2>
          <p className="mx-auto max-w-xl text-base text-white/50 md:text-lg">
            {t("stats.subtitle")}
          </p>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
          {stats.map((stat, i) => (
            <StatCard key={stat.valueKey} stat={stat} index={i} inView={inView} />
          ))}
        </div>
      </div>
    </section>
  );
}
