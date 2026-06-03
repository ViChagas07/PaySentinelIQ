"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Scale } from "lucide-react";

export default function CompliancePage() {
  return (
    <PagePlaceholder
      title="Compliance Intelligence"
      description="Entity profiles with verification status, compliance indicators, AI-generated public record summaries, and sanctions screening."
      icon={<Scale className="h-8 w-8" />}
      badge="Compliance"
    />
  );
}
