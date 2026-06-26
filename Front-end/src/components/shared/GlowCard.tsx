"use client";

import { cn } from "@/lib/utils";

/* ═══════════════════════════════════════════════════
   Glow Card — premium card with animated border glow
   ═══════════════════════════════════════════════════ */

export function GlowCard({
  children,
  className,
  glowColor = "psi-electric",
  glowIntensity = "medium",
  noPadding = false,
}: {
  children: React.ReactNode;
  className?: string;
  glowColor?: "psi-electric" | "psi-emerald" | "psi-warning" | "psi-fraud" | "purple";
  glowIntensity?: "low" | "medium" | "high";
  noPadding?: boolean;
}) {
  const glowMap = {
    "psi-electric": "from-psi-electric/20 via-psi-electric/5 to-transparent",
    "psi-emerald": "from-psi-emerald/20 via-psi-emerald/5 to-transparent",
    "psi-warning": "from-psi-warning/20 via-psi-warning/5 to-transparent",
    "psi-fraud": "from-psi-fraud/20 via-psi-fraud/5 to-transparent",
    purple: "from-purple-500/20 via-purple-500/5 to-transparent",
  };

  const intensityMap = {
    low: "opacity-60",
    medium: "opacity-80",
    high: "opacity-100",
  };

  return (
    <div className={cn("relative group", className)}>
      {/* Animated glow ring */}
      <div
        className={cn(
          "absolute -inset-[1px] rounded-xl bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm",
          glowMap[glowColor],
          intensityMap[glowIntensity]
        )}
      />
      {/* Content — glass surface with backdrop blur */}
      <div className={cn("relative rounded-xl border border-white/[0.06] bg-psi-graphite/60 backdrop-blur-xl shadow-xl", !noPadding && "px-6 py-5 md:px-8 md:py-6")}>
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Glass Card — premium glassmorphism with aura glow
   ═══════════════════════════════════════════════════ */

export function GlassCard({
  children,
  className,
  hover = false,
  glowColor = "blue",
}: {
  children: React.ReactNode;
  className?: string;
  /** Enable subtle hover lift + border glow */
  hover?: boolean;
  /** Glow accent color */
  glowColor?: "blue" | "cyan" | "violet" | "emerald" | "none";
}) {
  const glowClasses: Record<string, string> = {
    blue: "hover:shadow-psi-electric/10",
    cyan: "hover:shadow-cyan-500/10",
    violet: "hover:shadow-violet-500/10",
    emerald: "hover:shadow-emerald-500/10",
    none: "",
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-2xl shadow-2xl transition-all duration-300",
        hover && "card-aura-hover cursor-pointer",
        glowColor !== "none" && glowClasses[glowColor],
        className
      )}
    >
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Status Pill
   ═══════════════════════════════════════════════════ */

export function StatusPill({
  label,
  variant = "default",
}: {
  label: string;
  variant?: "default" | "success" | "warning" | "destructive" | "info";
}) {
  const variants = {
    default: "bg-psi-border/40 text-psi-text-secondary border-psi-border",
    success: "bg-psi-emerald/10 text-psi-emerald border-psi-emerald/30",
    warning: "bg-psi-warning/10 text-psi-warning border-psi-warning/30",
    destructive: "bg-psi-fraud/10 text-psi-fraud border-psi-fraud/30",
    info: "bg-psi-electric/10 text-psi-electric border-psi-electric/30",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        variants[variant]
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", {
        "bg-psi-text-secondary": variant === "default",
        "bg-psi-emerald": variant === "success",
        "bg-psi-warning": variant === "warning",
        "bg-psi-fraud": variant === "destructive",
        "bg-psi-electric": variant === "info",
      })} />
      {label}
    </span>
  );
}

/* ═══════════════════════════════════════════════════
   Animated Progress Bar
   ═══════════════════════════════════════════════════ */

export function AnimatedProgress({
  value,
  max = 100,
  color = "psi-electric",
  height = "h-2",
  showLabel = true,
  animated = true,
}: {
  value: number;
  max?: number;
  color?: "psi-electric" | "psi-emerald" | "psi-warning" | "psi-fraud";
  height?: string;
  showLabel?: boolean;
  animated?: boolean;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const colors = {
    "psi-electric": "bg-psi-electric",
    "psi-emerald": "bg-psi-emerald",
    "psi-warning": "bg-psi-warning",
    "psi-fraud": "bg-psi-fraud",
  };

  return (
    <div className="w-full">
      <div className={cn("w-full rounded-full bg-psi-border/50 overflow-hidden", height)}>
        <div
          className={cn(
            "h-full rounded-full transition-all duration-1000 ease-out",
            colors[color],
            animated && "animate-pulse"
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <p className="mt-1 text-xs text-psi-text-secondary text-right">{Math.round(pct)}%</p>
      )}
    </div>
  );
}
