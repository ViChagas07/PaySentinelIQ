"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Building2 } from "lucide-react";

export default function CompaniesPage() {
  return (
    <PagePlaceholder
      title="Companies"
      description="Multi-tenant company management with entity profiles, risk assessments, and compliance tracking."
      icon={<Building2 className="h-8 w-8" />}
    />
  );
}
