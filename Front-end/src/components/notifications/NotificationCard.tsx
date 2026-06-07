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
  CheckCheck,
  Eye,
  Trash2,
  XCircle,
  CheckCircle2,
  CircleDotDashed,
  MessageSquare,
} from "lucide-react";
import type { NotificationCardProps, NotificationSeverity } from "./types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

// ── Type-to-icon/color configuration ──
const notificationTypeConfig = {
  payment: { icon: Wallet, color: "text-psi-electric", bg: "bg-psi-electric/10" },
  fraud_alert: { icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10" },
  document_event: { icon: FileText, color: "text-psi-text-secondary", bg: "bg-psi-border/50" },
  ai_insight: { icon: Lightbulb, color: "text-psi-electric", bg: "bg-psi-electric/10" },
  compliance_alert: { icon: Scale, color: "text-psi-warning", bg: "bg-psi-warning/10" },
  system: { icon: Settings, color: "text-psi-text-secondary", bg: "bg-psi-border/50" },
  critical: { icon: AlertTriangle, color: "text-psi-fraud", bg: "bg-psi-fraud/10" },
  verification_complete: { icon: CheckCheck, color: "text-psi-emerald", bg: "bg-psi-emerald/10" },
};

// ── Type label mapping (i18n key suffix) ──
const typeLabelKeys: Record<string, string> = {
  payment: "fraud_alert", // payment uses same pattern key (not "payment" — fallback to generic)
  fraud_alert: "fraud_alert",
  document_event: "verification_complete", // document events show as verification-related
  ai_insight: "ai_insight",
  compliance_alert: "compliance_alert",
  system: "system",
  critical: "fraud_alert",
  verification_complete: "verification_complete",
};

const severityColors: Record<NotificationSeverity, string> = {
  critical: "border-psi-fraud shadow-red-500/20",
  warning: "border-psi-warning shadow-orange-500/20",
  normal: "border-psi-electric shadow-blue-500/20",
  success: "border-psi-emerald shadow-green-500/20",
  ai: "border-purple-500 shadow-purple-500/20",
};

// ── Human-readable type labels (fallback when i18n key missing) ──
const typeFallbackLabels: Record<string, string> = {
  payment: "Payment",
  fraud_alert: "Fraud Alert",
  document_event: "Document",
  ai_insight: "AI Insight",
  compliance_alert: "Compliance",
  system: "System",
  critical: "Critical",
  verification_complete: "Verification",
};

function timeAgo(
  dateStr: string,
  t: ReturnType<typeof useTranslations<"notifications">>,
): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return t("justNow");
  if (minutes < 60) return t("minutesAgo", { count: minutes });
  if (hours < 24) return t("hoursAgo", { count: hours });
  return t("daysAgo", { count: days });
}

export function NotificationCard({
  notification,
  onView,
  onDismiss,
  onMarkReadToggle,
}: NotificationCardProps) {
  const t = useTranslations("notifications");
  const tActions = useTranslations("notifications.actions");
  const tBadges = useTranslations("notifications.badges");

  const config =
    notificationTypeConfig[notification.type as keyof typeof notificationTypeConfig] ||
    notificationTypeConfig.system;
  const Icon = config.icon;
  const ago = timeAgo(notification.created_at, t);

  const isAI = notification.type === "ai_insight";
  const isUnread = !notification.is_read;

  // Resolve type label: try i18n key, fall back to hardcoded
  const typeLabelKey = typeLabelKeys[notification.type];
  const typeLabel = typeLabelKey ? (t(typeLabelKey as any) as string) : null;
  const displayType =
    typeLabel && typeLabel !== typeLabelKey
      ? typeLabel
      : typeFallbackLabels[notification.type] || notification.type;

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
    exit: { opacity: 0, y: -20, transition: { duration: 0.2 } },
  };

  const handleView = () => {
    onView(notification.id, notification.action_url || "#");
  };

  const handleDismiss = () => {
    onDismiss(notification.id);
  };

  const handleToggleRead = () => {
    onMarkReadToggle(notification.id, !notification.is_read);
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      layout
      className={cn(
        "relative group flex flex-col gap-3 p-4 rounded-xl border transition-all duration-300 ease-out",
        "bg-psi-graphite/60 backdrop-blur-md shadow-lg",
        notification.is_read
          ? "border-psi-border"
          : `border-psi-electric/30 ${severityColors[notification.severity as NotificationSeverity]}`,
        "hover:border-psi-electric/60 hover:shadow-xl hover:shadow-psi-electric/10",
      )}
      role="article"
      aria-label={`${displayType}: ${notification.title}`}
    >
      {/* ── Severity Indicator Aura (hover only) ── */}
      <div
        className={cn(
          "absolute -inset-0.5 rounded-xl opacity-0 transition-opacity duration-300",
          "group-hover:opacity-100",
          notification.severity === "critical" &&
            "bg-gradient-to-br from-psi-fraud to-transparent",
          notification.severity === "warning" &&
            "bg-gradient-to-br from-psi-warning to-transparent",
          notification.severity === "normal" &&
            "bg-gradient-to-br from-psi-electric to-transparent",
          notification.severity === "success" &&
            "bg-gradient-to-br from-psi-emerald to-transparent",
          notification.severity === "ai" &&
            "bg-gradient-to-br from-purple-500 to-transparent",
        )}
        aria-hidden="true"
        style={{ filter: "blur(8px)" }}
      />

      {/* ── Inner border ── */}
      <div
        className={cn(
          "absolute inset-0.5 rounded-xl border transition-colors duration-300",
          notification.is_read ? "border-psi-border" : "border-psi-electric/40",
        )}
      />

      <div className="relative z-10 flex items-start gap-3">
        {/* ── Left: Icon ── */}
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
            config.bg,
            notification.is_read ? "opacity-70" : "",
          )}
          aria-hidden="true"
        >
          <Icon className={cn("h-5 w-5", config.color)} />
        </div>

        {/* ── Center: Title, Description, Timestamp, Metadata ── */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5 flex-wrap">
            {/* Type category */}
            <span
              className={cn(
                "text-xs font-semibold uppercase tracking-wider",
                notification.is_read ? "text-psi-text-secondary" : config.color,
              )}
            >
              {displayType}
            </span>

            {/* Unread marker: show "New" badge only for unread notifications */}
            {isUnread && (
              <Badge
                variant="primary"
                className="px-1.5 py-0.5 text-[10px] font-medium bg-psi-electric/20 text-psi-electric"
              >
                {tBadges("new")}
              </Badge>
            )}

            {/* AI label */}
            {isAI && (
              <Badge className="bg-purple-500/20 text-purple-300 px-1.5 py-0.5 text-[10px] font-medium">
                {tBadges("aiGenerated")}
              </Badge>
            )}
          </div>

          {/* Title */}
          <h3 className="text-sm font-medium text-psi-text-primary leading-snug mb-1">
            {notification.title}
          </h3>

          {/* Message */}
          <p className="text-xs text-psi-text-secondary leading-relaxed">
            {notification.message}
          </p>

          {/* Metadata key-value pairs */}
          {notification.metadata && Object.keys(notification.metadata).length > 0 && (
            <div className="mt-2 text-xs text-psi-text-secondary/80 flex flex-wrap gap-x-3 gap-y-1">
              {Object.entries(notification.metadata).map(([key, value]) => (
                <span key={key} className="flex items-center gap-1">
                  <CircleDotDashed className="h-3 w-3 text-psi-border" aria-hidden="true" />
                  <strong className="font-medium capitalize">{key}:</strong> {String(value)}
                </span>
              ))}
            </div>
          )}

          {/* Timestamp */}
          <p className="mt-2 text-[10px] text-psi-text-secondary/70">{ago}</p>
        </div>

        {/* ── Right: Action Buttons (visible on hover) ── */}
        <div className="flex flex-col items-end gap-2 ml-auto md:opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          {/* View / Open action */}
          {notification.action_url && (
            <Button
              onClick={handleView}
              variant="ghost"
              size="sm"
              aria-label={tActions("view")}
            >
              <Eye className="h-4 w-4" /> {tActions("view")}
            </Button>
          )}

          {/* Document event: "Open Document" */}
          {notification.type === "document_event" && (
            <Button
              onClick={handleView}
              variant="ghost"
              size="sm"
              aria-label={tActions("openDocument")}
            >
              <FileText className="h-4 w-4" /> {tActions("openDocument")}
            </Button>
          )}

          {/* Payment: "Open Payment" */}
          {notification.type === "payment" && (
            <Button
              onClick={handleView}
              variant="ghost"
              size="sm"
              aria-label={tActions("openPayment")}
            >
              <Wallet className="h-4 w-4" /> {tActions("openPayment")}
            </Button>
          )}

          {/* Fraud alert (not resolved): "Resolve" */}
          {notification.type === "fraud_alert" &&
            notification.severity !== "success" && (
              <Button
                onClick={handleView}
                variant="destructive"
                size="sm"
                aria-label={tActions("resolve")}
              >
                <XCircle className="h-4 w-4" /> {tActions("resolve")}
              </Button>
            )}

          {/* Fraud alert (resolved): "View" */}
          {notification.type === "fraud_alert" &&
            notification.severity === "success" && (
              <Button
                onClick={handleView}
                variant="success"
                size="sm"
                aria-label={tActions("view")}
              >
                <CheckCircle2 className="h-4 w-4" /> {tActions("view")}
              </Button>
            )}

          {/* Dismiss */}
          <Button
            onClick={handleDismiss}
            variant="ghost"
            size="sm"
            aria-label={tActions("dismiss")}
          >
            <Trash2 className="h-4 w-4" /> {tActions("dismiss")}
          </Button>

          {/* Mark Read / Unread toggle */}
          <Button
            onClick={handleToggleRead}
            variant="ghost"
            size="sm"
            aria-label={
              notification.is_read ? tActions("markAsUnread") : tActions("markAsRead")
            }
          >
            {notification.is_read ? (
              <MessageSquare className="h-4 w-4" />
            ) : (
              <CheckCheck className="h-4 w-4" />
            )}
            {notification.is_read ? tActions("markAsUnread") : tActions("markAsRead")}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
