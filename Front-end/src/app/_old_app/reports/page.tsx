"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { FileBarChart } from "lucide-react";

export default function ReportsPage() {
  return (
    <PagePlaceholder
      title="Reports"
      description="Generate comprehensive payroll verification reports, fraud analysis summaries, and compliance documentation."
      icon={<FileBarChart className="h-8 w-8" />}
    />
  );
}
