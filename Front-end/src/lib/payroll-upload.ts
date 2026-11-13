// ============================================================
// PaySentinelIQ — Payroll document upload/analyze helper
// Keeps the payroll payment center wired to the canonical
// POST /documents/analyze contract without duplicating UI logic.
// ============================================================

import { mapPSIReportToAnalysisResult } from "@/lib/analysis-mapper";
import type { AnalysisResult, ExtraInfo } from "@/stores/analysis-store";

/** Canonical document type used by the payroll analysis route. */
export const PAYROLL_DOCUMENT_TYPE = "contracheque" as const;

export type PayrollUploadStatus = "idle" | "scanning" | "done" | "error";

export type PayrollUploadErrorCode =
  | "auth"
  | "file"
  | "server"
  | "network"
  | "timeout"
  | "unknown";

export interface PayrollUploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  status: PayrollUploadStatus;
  result?: AnalysisResult;
  errorCode?: PayrollUploadErrorCode;
}

export interface PayrollUploadSuccess {
  status: "done";
  result: AnalysisResult;
  /** True when the canonical endpoint analyzed the file but could not persist it. */
  persistenceFailed: boolean;
}

export interface PayrollUploadFailure {
  status: "error";
  errorCode: PayrollUploadErrorCode;
}

export type PayrollUploadOutcome = PayrollUploadSuccess | PayrollUploadFailure;

export interface AnalyzePayrollFileParams {
  file: File;
  extraInfo?: ExtraInfo;
  locale: string;
  analyze: (formData: FormData) => Promise<unknown>;
}

/**
 * Build the multipart payload expected by POST /documents/analyze.
 *
 * The extra-info field names mirror the canonical payroll analysis page
 * (`/dashboard/analyze-payroll`) so both entry points stay consistent.
 */
export function buildPayrollAnalysisFormData(
  file: File,
  extraInfo: ExtraInfo = {},
): FormData {
  const formData = new FormData();
  formData.append("file", file, file.name);
  formData.append("document_type", PAYROLL_DOCUMENT_TYPE);

  if (extraInfo.expectedSalary) {
    formData.append("salario_bruto", extraInfo.expectedSalary);
  }
  if (extraInfo.companyName) {
    formData.append("razao_social", extraInfo.companyName);
  }
  if (extraInfo.jobPosition) {
    formData.append("cargo", extraInfo.jobPosition);
  }

  return formData;
}

function readHttpStatus(error: unknown): number | undefined {
  if (
    typeof error === "object" &&
    error !== null &&
    typeof (error as { status?: unknown }).status === "number"
  ) {
    return (error as { status: number }).status;
  }
  return undefined;
}

function readErrorName(error: unknown): string | undefined {
  if (
    typeof error === "object" &&
    error !== null &&
    typeof (error as { name?: unknown }).name === "string"
  ) {
    return (error as { name: string }).name;
  }
  return undefined;
}

/**
 * Map an API/fetch failure to a stable, user-facing error code.
 * The raw backend message and the file name are intentionally discarded.
 */
export function getPayrollUploadErrorCode(error: unknown): PayrollUploadErrorCode {
  const status = readHttpStatus(error);
  if (status !== undefined) {
    if (status === 401 || status === 403) return "auth";
    if (status === 408) return "timeout";
    if (status === 413 || status === 415 || status === 422) return "file";
    if (status === 429 || status >= 500 || status === 404) return "server";
    if (status === 400) return "file";
    return "unknown";
  }

  const name = readErrorName(error);
  if (name === "TimeoutError" || name === "AbortError") return "timeout";
  if (error instanceof TypeError) return "network";

  return "unknown";
}

/**
 * Analyze one payroll file through the canonical endpoint and map the
 * response into the UI shape. Never throws: failures are returned as an
 * explicit error outcome so callers cannot mark them as successful.
 */
export async function analyzePayrollFile({
  file,
  extraInfo,
  locale,
  analyze,
}: AnalyzePayrollFileParams): Promise<PayrollUploadOutcome> {
  let report: unknown;
  try {
    const formData = buildPayrollAnalysisFormData(file, extraInfo);
    report = await analyze(formData);
  } catch (error) {
    return { status: "error", errorCode: getPayrollUploadErrorCode(error) };
  }

  if (typeof report !== "object" || report === null || Array.isArray(report)) {
    return { status: "error", errorCode: "unknown" };
  }
  if (Object.keys(report).length === 0) {
    return { status: "error", errorCode: "unknown" };
  }

  try {
    const result = mapPSIReportToAnalysisResult(
      report as Parameters<typeof mapPSIReportToAnalysisResult>[0],
      file.name,
      "payroll",
      locale,
    );

    return {
      status: "done",
      result,
      persistenceFailed: result.persistenceStatus === "failed",
    };
  } catch {
    return { status: "error", errorCode: "unknown" };
  }
}
