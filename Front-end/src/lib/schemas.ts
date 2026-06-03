// ============================================================
// PaySentinelIQ — Zod Validation Schemas
// Form validation schemas for all domain entities
// ============================================================

import { z } from "zod";

// ── Auth Schemas ── //

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  remember: z.boolean().optional(),
});

export type LoginForm = z.infer<typeof loginSchema>;

export const mfaSchema = z.object({
  code: z.string().length(6, "MFA code must be 6 digits").regex(/^\d+$/, "MFA code must be numeric"),
});

export type MfaForm = z.infer<typeof mfaSchema>;

// ── Payroll Schemas ── //

export const payrollSchema = z.object({
  employee_id: z.string().min(1, "Employee is required"),
  period_start: z.string().min(1, "Start date is required"),
  period_end: z.string().min(1, "End date is required"),
  gross_pay: z.number().positive("Gross pay must be positive"),
  tax_withheld: z.number().min(0, "Tax cannot be negative"),
  deductions: z
    .array(
      z.object({
        type: z.string().min(1, "Deduction type is required"),
        amount: z.number().min(0, "Amount cannot be negative"),
        description: z.string().optional(),
      })
    )
    .optional(),
  notes: z.string().max(500, "Notes must be under 500 characters").optional(),
});

export type PayrollForm = z.infer<typeof payrollSchema>;

// ── Employee Schemas ── //

export const employeeSchema = z.object({
  full_name: z.string().min(2, "Name is required").max(100),
  email: z.string().email("Valid email is required"),
  department: z.string().min(1, "Department is required"),
  position: z.string().min(1, "Position is required"),
  salary: z.number().positive("Salary must be positive"),
  hire_date: z.string().min(1, "Hire date is required"),
  status: z.enum(["active", "terminated", "on_leave"]),
});

export type EmployeeForm = z.infer<typeof employeeSchema>;

// ── Fraud Alert Review Schemas ── //

export const fraudReviewSchema = z.object({
  resolution: z.enum(["confirmed_fraud", "false_positive", "escalated"]),
  notes: z.string().min(10, "Please provide detailed review notes (min 10 characters)").max(1000),
  evidence_references: z.array(z.string()).optional(),
});

export type FraudReviewForm = z.infer<typeof fraudReviewSchema>;

// ── Document Upload Schema ── //

export const documentUploadSchema = z.object({
  document_type: z.enum([
    "payroll_report",
    "tax_form",
    "timesheet",
    "employment_contract",
    "bank_statement",
    "identity_document",
    "compliance_report",
  ]),
  employee_id: z.string().optional(),
  description: z.string().max(300).optional(),
});

export type DocumentUploadForm = z.infer<typeof documentUploadSchema>;

// ── Compliance Check Schema ── //

export const complianceCheckSchema = z.object({
  entity_id: z.string().min(1, "Entity is required"),
  entity_type: z.enum(["company", "employee", "vendor"]),
  check_types: z.array(z.enum(["sanctions", "pep", "adverse_media", "public_records"])).min(1),
});

export type ComplianceCheckForm = z.infer<typeof complianceCheckSchema>;

// ── Settings Schemas ── //

export const settingsSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  notification_email: z.string().email("Valid email required"),
  fraud_alert_threshold: z.number().min(0).max(100),
  auto_verify_threshold: z.number().min(0).max(100),
  two_factor_required: z.boolean(),
});

export type SettingsForm = z.infer<typeof settingsSchema>;
