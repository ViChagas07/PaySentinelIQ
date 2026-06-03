// ============================================================
// PaySentinelIQ — Investigation Timeline
// Shows real timeline events passed from the parent component.
// No hardcoded/mock data.
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import {
  AlertTriangle,
  Brain,
  User,
  FileText,
  ShieldCheck,
  Clock,
  MessageSquare,
  ArrowUpRight,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface TimelineEvent {
  id: string;
  type: "ai_detection" | "analyst_review" | "document_upload" | "status_change" | "comment" | "escalation";
  title: string;
  description: string;
  user: string;
  timestamp: string;
  riskLevel?: "low" | "medium" | "high" | "critical";
}

// ── Event icon configuration ── //

const eventConfig: Record<TimelineEvent["type"], { icon: LucideIcon; color: string; bg: string }> = {
  ai_detection: { icon: Brain, color: "text-psi-electric", bg: "bg-psi-electric/10 border-psi-electric/30" },
  analyst_review: { icon: User, color: "text-psi-text-primary", bg: "bg-psi-border/50 border-psi-border" },
  document_upload: { icon: FileText, color: "text-psi-text-secondary", bg: "bg-psi-border/30 border-psi-border" },
  status_change: { icon: ShieldCheck, color: "text-psi-emerald", bg: "bg-psi-emerald/10 border-psi-emerald/30" },
  comment: { icon: MessageSquare, color: "text-psi-text-secondary", bg: "bg-psi-border/30 border-psi-border" },
  escalation: { icon: ArrowUpRight, color: "text-psi-fraud", bg: "bg-psi-fraud/10 border-psi-fraud/30" },
};

// ── Component ── //

export function InvestigationTimeline({ events = [] }: { events?: TimelineEvent[] }) {
  const t = useTranslations("fraud");
  return (
    <div className="relative">
      {/* Vertical line — sempre visível */}
      <div className="absolute left-[25px] top-0 bottom-0 w-px bg-psi-border" aria-hidden="true" />

      <div className="space-y-1">
        {events.length === 0 ? (
          <div className="pl-14 py-6 text-center">
            <p className="text-xs text-psi-text-secondary/50">{t("noActivity")}</p>
          </div>
        ) : (
          events.map((event, i) => {
            const config = eventConfig[event.type];
            const Icon = config.icon;

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08, duration: 0.3 }}
                className="relative pl-14 pb-6 last:pb-0"
              >
                {/* Icon circle */}
                <div
                  className={cn(
                    "absolute left-[13px] top-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-psi-navy",
                    config.bg
                  )}
                >
                  <Icon className={cn("h-3 w-3", config.color)} />
                </div>

                {/* Content */}
                <div className="rounded-lg border border-psi-border bg-psi-graphite/60 p-3.5 hover:bg-psi-graphite/80 transition-colors">
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-psi-text-primary">{event.title}</h4>
                      {event.riskLevel && (
                        <Badge
                          variant={event.riskLevel === "high" ? "destructive" : "warning"}
                          className="text-[10px] py-0 px-1.5"
                        >
                          {t(`riskLevel${event.riskLevel.charAt(0).toUpperCase() + event.riskLevel.slice(1)}`)}
                        </Badge>
                      )}
                    </div>
                    <span className="text-[10px] text-psi-text-secondary whitespace-nowrap">
                      {event.timestamp}
                    </span>
                  </div>
                  <p className="text-xs text-psi-text-secondary leading-relaxed">
                    {event.description}
                  </p>
                  <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-psi-border">
                    <Clock className="h-3 w-3 text-psi-text-secondary/60" />
                    <span className="text-[10px] text-psi-text-secondary/60">{event.user}</span>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
