"use client";

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
    label: "LGPD Compliant",
    tooltip:
      "Este produto cumpre os requisitos da Lei Geral de Proteção de Dados (LGPD).",
  },
  encrypted: {
    icon: Lock,
    label: "Encrypted",
    tooltip:
      "Dados protegidos com criptografia ponta a ponta. Segurança em todos os níveis.",
  },
  consent: {
    icon: FileCheck,
    label: "Consent Managed",
    tooltip:
      "Coleta e tratamento de dados somente mediante consentimento explícito do titular.",
  },
  audit: {
    icon: ClipboardList,
    label: "Audit Trail",
    tooltip:
      "Trilha de auditoria completa. Todas as operações são registradas e rastreáveis.",
  },
  "no-tracking": {
    icon: EyeOff,
    label: "No Tracking",
    tooltip:
      "Nenhum rastreador ou cookie de terceiros. Privacidade total do usuário.",
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
  const config = variantConfig[variant ?? "lgpd"];
  const Icon = config.icon;

  return (
    <span
      title={config.tooltip}
      aria-label={config.tooltip}
      className={cn(badgeVariants({ variant, size }), className)}
    >
      <Icon className="h-3 w-3 shrink-0" strokeWidth={2.5} />
      <span className="font-semibold uppercase tracking-wider">
        {config.label}
      </span>
    </span>
  );
}
