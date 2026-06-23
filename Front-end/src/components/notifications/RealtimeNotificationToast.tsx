// ============================================================
// PaySentinelIQ — Realtime Notification Toast Component
// Premium toast content rendered inside Sonner toasts.
// Aligned 100% with the PaySentinelIQ design system.
// ============================================================

"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  CheckCircle2,
  Wallet,
  FileText,
  Lightbulb,
  Scale,
  Bell,
  ArrowRight,
  XCircle,
  MessageSquareWarning,
  Eye,
} from "lucide-react";
import type { Notification } from "@/types";

// ── Icon + Color configuration per notification type ──

interface ToastVariantConfig {
  icon: typeof AlertTriangle;
  color: string;
  bg: string;
  border: string;
  glow: string;
  sonnerType: "success" | "error" | "warning" | "info";
}

const toastTypeConfig: Record<string, ToastVariantConfig> = {
  payment: {
    icon: Wallet,
    color: "text-psi-emerald",
    bg: "bg-psi-emerald/10",
    border: "border-psi-emerald/30",
    glow: "shadow-psi-emerald/20",
    sonnerType: "success",
  },
  fraud_alert: {
    icon: AlertTriangle,
    color: "text-psi-fraud",
    bg: "bg-psi-fraud/10",
    border: "border-psi-fraud/30",
    glow: "shadow-psi-fraud/20",
    sonnerType: "error",
  },
  verification_complete: {
    icon: CheckCircle2,
    color: "text-psi-emerald",
    bg: "bg-psi-emerald/10",
    border: "border-psi-emerald/30",
    glow: "shadow-psi-emerald/20",
    sonnerType: "success",
  },
  compliance_alert: {
    icon: Scale,
    color: "text-psi-warning",
    bg: "bg-psi-warning/10",
    border: "border-psi-warning/30",
    glow: "shadow-psi-warning/20",
    sonnerType: "warning",
  },
  document_event: {
    icon: FileText,
    color: "text-psi-electric",
    bg: "bg-psi-electric/10",
    border: "border-psi-electric/30",
    glow: "shadow-psi-electric/20",
    sonnerType: "info",
  },
  system: {
    icon: Bell,
    color: "text-psi-text-secondary",
    bg: "bg-psi-border/50",
    border: "border-psi-border",
    glow: "shadow-psi-border/20",
    sonnerType: "info",
  },
  ai_insight: {
    icon: Lightbulb,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    glow: "shadow-purple-500/20",
    sonnerType: "info",
  },
  critical: {
    icon: MessageSquareWarning,
    color: "text-psi-fraud",
    bg: "bg-psi-fraud/10",
    border: "border-psi-fraud/30",
    glow: "shadow-psi-fraud/20",
    sonnerType: "error",
  },
};

// ── Route mapping for deep linking ──

const typeRouteMap: Record<string, string> = {
  payment: "/payments",
  fraud_alert: "/fraud-alerts",
  verification_complete: "/verifications",
  compliance_alert: "/compliance",
  document_event: "/documents",
  ai_insight: "/ai-insights",
  critical: "/fraud-alerts",
};

// ── Label mapping ──

const typeLabels: Record<string, string> = {
  payment: "Payment",
  fraud_alert: "Fraud Alert",
  verification_complete: "Verification",
  compliance_alert: "Compliance",
  document_event: "Document",
  system: "System",
  ai_insight: "AI Insight",
  critical: "Critical Alert",
};

// ── Toast ID prefix (for deduplication) ──

export const TOAST_ID_PREFIX = "psi-toast-";

// ── Props ──

interface RealtimeNotificationToastProps {
  notification: Notification;
  onDismiss?: () => void;
}

// ── Component ──

export function RealtimeNotificationToast({
  notification,
  onDismiss,
}: RealtimeNotificationToastProps) {
  const router = useRouter();

  const type = notification.type as keyof typeof toastTypeConfig;
  const config = toastTypeConfig[type] || toastTypeConfig.system;

  const Icon = config.icon;
  const label = typeLabels[type] || "Notification";

  const handleClick = useCallback(() => {
    // Deep linking: navigate to the relevant section
    const baseRoute = typeRouteMap[type] || "/notifications";
    const targetUrl = notification.action_url || baseRoute;
    router.push(targetUrl);
  }, [router, notification.action_url, type]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick],
  );

  return (
    <motion.div
      initial={{ opacity: 0, x: 20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.95 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "relative flex items-start gap-3 w-full max-w-[380px] cursor-pointer select-none",
        "rounded-xl p-3 transition-colors duration-200",
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`${label}: ${notification.title}. Click to view details.`}
    >
      {/* ── Ambient glow aura ── */}
      <div
        className={cn(
          "absolute -inset-1 rounded-xl opacity-60 transition-opacity",
          "bg-gradient-to-br",
          config.glow,
        )}
        style={{ filter: "blur(12px)" }}
        aria-hidden="true"
      />

      {/* ── Icon ── */}
      <div
        className={cn(
          "relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          config.bg,
        )}
        aria-hidden="true"
      >
        <Icon className={cn("h-5 w-5", config.color)} />
      </div>

      {/* ── Content ── */}
      <div className="relative z-10 flex-1 min-w-0">
        {/* Header: type badge + time */}
        <div className="flex items-center gap-2 mb-0.5">
          <span
            className={cn(
              "text-[10px] font-bold uppercase tracking-[0.08em]",
              config.color,
            )}
          >
            {label}
          </span>
          <span className="text-[10px] text-psi-text-secondary/50 ml-auto">
            just now
          </span>
        </div>

        {/* Title */}
        <p className="text-sm font-semibold text-psi-text-primary leading-snug mb-0.5 line-clamp-1">
          {notification.title}
        </p>

        {/* Message */}
        <p className="text-xs text-psi-text-secondary/90 leading-relaxed line-clamp-2">
          {notification.message}
        </p>

        {/* Action hint */}
        <span
          className={cn(
            "inline-flex items-center gap-1 mt-1.5 text-[11px] font-medium",
            config.color,
          )}
        >
          <Eye className="h-3 w-3" />
          View details
          <ArrowRight className="h-3 w-3" />
        </span>
      </div>

      {/* ── Close / Dismiss ── */}
      {onDismiss && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
          className="relative z-10 flex h-5 w-5 items-center justify-center rounded-full opacity-40 hover:opacity-100 transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-psi-electric"
          aria-label="Dismiss notification"
        >
          <XCircle className="h-4 w-4 text-psi-text-secondary" />
        </button>
      )}
    </motion.div>
  );
}

// ── Factory: build toast content for sonner.toast.custom() ──

export function buildNotificationToastContent(
  notification: Notification,
  onDismiss?: () => void,
) {
  return (
    <RealtimeNotificationToast
      notification={notification}
      onDismiss={onDismiss}
    />
  );
}
