
import type { LucideIcon } from "lucide-react";
import { type Notification } from "@/types";

export type NotificationFilterType = 
  | "all"
  | "payments"
  | "fraud_detection"
  | "documents"
  | "ai_insights"
  | "compliance"
  | "system"
  | "critical";

export type NotificationSeverity = 
  | "critical"
  | "warning"
  | "normal"
  | "success"
  | "ai";

export interface NotificationFilter {
  id: NotificationFilterType;
  labelKey: string; // i18n key for the label
  icon: LucideIcon;
  count: number;
}

export interface NotificationCardProps {
  notification: Notification;
  onView: (id: string, url: string) => void;
  onDismiss: (id: string) => void;
  onMarkReadToggle: (id: string, isRead: boolean) => void;
}

export interface NotificationDeliveryChannel {
  id: "email" | "whatsapp" | "telegram" | "slack" | "inApp";
  labelKey: string;
  descriptionKey: string;
  icon: LucideIcon;
  enabled: boolean;
}
