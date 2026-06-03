// ============================================================
// PaySentinelIQ — Risk Score Gauge
// Animated circular gauge for verification/fraud risk scores
// ============================================================

"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";

interface RiskGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function RiskGauge({ score, size = 140, strokeWidth = 10, label }: RiskGaugeProps) {
  const t = useTranslations("charts");
  const tv = useTranslations("verification");
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const center = size / 2;

  // Determine color based on score
  const getColor = (s: number) => {
    if (s <= 30) return "#00C48C"; // Emerald
    if (s <= 60) return "#FF8C00"; // Warning
    return "#D63B3B"; // Fraud Red
  };

  const color = getColor(score);
  const riskLabel =
    score <= 30
      ? t("riskLowLabel")
      : score <= 60
      ? t("riskMediumLabel")
      : score <= 85
      ? t("riskHighLabel")
      : t("riskCriticalLabel");

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedScore(score), 300);
    return () => clearTimeout(timer);
  }, [score]);

  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      {label && (
        <p className="text-xs font-medium uppercase tracking-wider text-psi-text-secondary">
          {label}
        </p>
      )}
      <div className="relative" style={{ width: size, height: size }} role="img" aria-label={`Risk score: ${score} out of 100 — ${riskLabel}`}>
        {/* Background circle */}
        <svg width={size} height={size} className="transform -rotate-90" aria-hidden="true">
          <title>{`Risk Score: ${score}% — ${riskLabel}`}</title>
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#1E2D45"
            strokeWidth={strokeWidth}
          />
          {/* Animated progress */}
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 8px ${color}40)` }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-3xl font-bold tabular-nums"
            style={{ color }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            {animatedScore}
          </motion.span>
          <span className="text-xs text-psi-text-secondary">{tv("outOf100")}</span>
          <span
            className="mt-1 rounded-full px-2 py-0.5 text-[10px] font-semibold"
            style={{
              backgroundColor: `${color}15`,
              color,
              border: `1px solid ${color}30`,
            }}
          >
            {riskLabel}
          </span>
        </div>
      </div>
    </div>
  );
}
