"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import {
  Shield,
  Lock,
  FileCheck,
  ClipboardList,
  EyeOff,
} from "lucide-react";

const variantConfig = {
  lgpd: {
    icon: Shield,
    labelKey: "privacyBadge.lgpd",
    tooltipKey: "privacyBadge.lgpdTooltip",
  },
  encrypted: {
    icon: Lock,
    labelKey: "privacyBadge.encrypted",
    tooltipKey: "privacyBadge.encryptedTooltip",
  },
  consent: {
    icon: FileCheck,
    labelKey: "privacyBadge.consent",
    tooltipKey: "privacyBadge.consentTooltip",
  },
  audit: {
    icon: ClipboardList,
    labelKey: "privacyBadge.audit",
    tooltipKey: "privacyBadge.auditTooltip",
  },
  "no-tracking": {
    icon: EyeOff,
    labelKey: "privacyBadge.noTracking",
    tooltipKey: "privacyBadge.noTrackingTooltip",
  },
} as const;

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border backdrop-blur-sm transition-colors",
  {
    variants: {
      variant: {
        lgpd: "border-psi-electric/20 bg-psi-electric/10 text-psi-electric hover:border-psi-electric/30",
        encrypted:
          "border-psi-emerald/20 bg-psi-emerald/10 text-psi-emerald hover:border-psi-emerald/30",
        consent:
          "border-psi-electric/20 bg-psi-electric/10 text-psi-electric hover:border-psi-electric/30",
        audit:
          "border-psi-warning/20 bg-psi-warning/10 text-psi-warning hover:border-psi-warning/30",
        "no-tracking":
          "border-psi-emerald/20 bg-psi-emerald/10 text-psi-emerald hover:border-psi-emerald/30",
      },
      size: {
        sm: "px-2 py-0.5 text-[10px]",
        md: "px-2.5 py-1 text-xs",
      },
    },
    defaultVariants: {
      variant: "lgpd",
      size: "sm",
    },
  }
);

export interface PrivacyBadgeProps
  extends VariantProps<typeof badgeVariants> {
  className?: string;
}

export function PrivacyBadge({
  variant = "lgpd",
  size = "sm",
  className,
}: PrivacyBadgeProps) {
  const t = useTranslations("common");
  const config = variantConfig[variant ?? "lgpd"];
  const Icon = config.icon;
  const label = t(config.labelKey);
  const tooltip = t(config.tooltipKey);

  return (
    <span
      title={tooltip}
      aria-label={tooltip}
      className={cn(badgeVariants({ variant, size }), className)}
    >
      <Icon className="h-3 w-3 shrink-0" strokeWidth={2.5} />
      <span className="font-semibold uppercase tracking-wider">
        {label}
      </span>
    </span>
  );
}
