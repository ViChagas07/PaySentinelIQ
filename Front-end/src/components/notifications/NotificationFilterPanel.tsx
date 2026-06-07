"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Bell,
  Wallet,
  Landmark,
  FileText,
  Lightbulb,
  Scale,
  Settings,
  AlertTriangle,
} from "lucide-react";
import type { NotificationFilter, NotificationFilterType } from "./types";
import { Badge } from "@/components/ui/Badge";

interface NotificationFilterPanelProps {
  activeFilter: NotificationFilterType;
  onFilterChange: (filter: NotificationFilterType) => void;
  filterCounts: Record<NotificationFilterType, number>;
}

const filterIconMap = {
  all: Bell,
  payments: Wallet,
  fraud_detection: AlertTriangle,
  documents: FileText,
  ai_insights: Lightbulb,
  compliance: Scale,
  system: Settings,
  critical: AlertTriangle, // Re-using for critical, might need a more specific icon later
};

export function NotificationFilterPanel({
  activeFilter,
  onFilterChange,
  filterCounts,
}: NotificationFilterPanelProps) {
  const t = useTranslations("notifications.filters");

  const filters: NotificationFilter[] = [
    { id: "all", labelKey: "all", icon: filterIconMap.all, count: filterCounts.all },
    { id: "payments", labelKey: "payments", icon: filterIconMap.payments, count: filterCounts.payments },
    { id: "fraud_detection", labelKey: "fraudDetection", icon: filterIconMap.fraud_detection, count: filterCounts.fraud_detection },
    { id: "documents", labelKey: "documents", icon: filterIconMap.documents, count: filterCounts.documents },
    { id: "ai_insights", labelKey: "aiInsights", icon: filterIconMap.ai_insights, count: filterCounts.ai_insights },
    { id: "compliance", labelKey: "compliance", icon: filterIconMap.compliance, count: filterCounts.compliance },
    { id: "system", labelKey: "system", icon: filterIconMap.system, count: filterCounts.system },
    { id: "critical", labelKey: "critical", icon: filterIconMap.critical, count: filterCounts.critical },
  ];

  return (
    <nav
      className="relative z-10 flex flex-wrap gap-2 rounded-xl bg-psi-graphite p-2 shadow-lg glass-card"
      aria-label={useTranslations("notifications.feed")("filterAriaLabel")}
    >
      {filters.map((filter) => {
        const isActive = activeFilter === filter.id;
        const Icon = filter.icon;
        return (
          <motion.button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={cn(
              "relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200",
              "text-psi-text-secondary hover:bg-psi-border/40 hover:text-psi-text-primary",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-psi-electric focus-visible:ring-offset-2 focus-visible:ring-offset-psi-navy",
              isActive && "text-psi-electric"
            )}
            aria-current={isActive ? "page" : undefined}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isActive && (
              <motion.div
                layoutId="active-filter-indicator"
                className="absolute inset-0 -z-10 rounded-lg bg-psi-electric/10 shadow-inner shadow-psi-electric/20"
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
            <Icon className={cn("h-4 w-4", isActive ? "text-psi-electric" : "text-psi-text-secondary")} />
            <span>{t(filter.labelKey)}</span>
            {filter.count > 0 && (
              <Badge
                variant={filter.id === "critical" ? "destructive" : isActive ? "primary" : "outline"}
                className={cn(
                  "ml-1 min-w-[20px] justify-center px-1.5 py-0.5 text-xs font-semibold",
                  isActive && "bg-psi-electric text-white",
                  filter.id === "critical" && isActive && "bg-psi-fraud text-white"
                )}
              >
                {filter.count}
              </Badge>
            )}
          </motion.button>
        );
      })}
    </nav>
  );
}