"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { DollarSign } from "lucide-react";

export default function PayrollPage() {
  return (
    <PagePlaceholder
      title="Payroll Generation Center"
      description="Financial workspace for payroll creation, tax calculations, salary simulation, PDF generation, and digital signatures."
      icon={<DollarSign className="h-8 w-8" />}
      badge="Finance"
      badgeVariant="success"
    />
  );
}
