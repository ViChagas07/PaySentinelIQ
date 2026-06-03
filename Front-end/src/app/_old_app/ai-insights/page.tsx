"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Brain } from "lucide-react";

export default function AIInsightsPage() {
  return (
    <PagePlaceholder
      title="PSI Insight Dashboard"
      description="AI reasoning center with risk score visualizations, animated reasoning breakdown, anomaly summaries, and verification recommendations."
      icon={<Brain className="h-8 w-8" />}
      badge="AI Reasoning"
      badgeVariant="primary"
    />
  );
}
