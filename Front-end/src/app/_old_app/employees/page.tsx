"use client";

import PagePlaceholder from "@/components/shared/PagePlaceholder";
import { Users } from "lucide-react";

export default function EmployeesPage() {
  return (
    <PagePlaceholder
      title="Employees"
      description="Employee directory with risk scores, payroll history, verification status, and AI-powered anomaly detection."
      icon={<Users className="h-8 w-8" />}
    />
  );
}
