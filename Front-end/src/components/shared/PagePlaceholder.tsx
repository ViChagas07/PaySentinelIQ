// ============================================================
// PaySentinelIQ — Placeholder Page Helper
// ============================================================

"use client";

import { useTranslations } from "next-intl";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface PagePlaceholderProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  badge?: string;
  badgeVariant?: "primary" | "success" | "warning" | "destructive";
}

export default function PagePlaceholder({
  title,
  description,
  icon,
  badge,
  badgeVariant = "primary",
}: PagePlaceholderProps) {
  const t = useTranslations("common");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">{title}</h1>
          <p className="text-sm text-psi-text-secondary mt-1">{description}</p>
        </div>
        {badge && <Badge variant={badgeVariant}>{badge}</Badge>}
      </div>

      <Card>
        <CardContent className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-4 rounded-2xl bg-psi-electric/10 p-4 text-psi-electric">
            {icon}
          </div>
          <CardTitle className="mb-2">{title}</CardTitle>
          <CardDescription className="max-w-md">
            {t("underDevelopment")}
          </CardDescription>
        </CardContent>
      </Card>
    </div>
  );
}
