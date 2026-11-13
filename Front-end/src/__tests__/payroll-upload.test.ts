// ============================================================
// PaySentinelIQ — Payroll upload helper tests
// ============================================================

import { afterEach, describe, expect, it, vi } from "vitest";
import {
  analyzePayrollFile,
  buildPayrollAnalysisFormData,
  getPayrollUploadErrorCode,
  PAYROLL_DOCUMENT_TYPE,
} from "@/lib/payroll-upload";

function makeFile(name = "contracheque.pdf"): File {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" });
}

function apiClientError(status: number): Error {
  return Object.assign(
    new Error("raw backend detail: contracheque.pdf"),
    { name: "ApiClientError", status },
  );
}

const baseParams = {
  file: makeFile(),
  extraInfo: {},
  locale: "pt-BR",
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("buildPayrollAnalysisFormData", () => {
  it("uses the canonical payroll document type and reuses extra info", () => {
    const formData = buildPayrollAnalysisFormData(makeFile("folha.pdf"), {
      expectedSalary: "8500.00",
      companyName: "ACME LTDA",
      jobPosition: "Analista Financeiro",
    });

    expect(formData.get("document_type")).toBe(PAYROLL_DOCUMENT_TYPE);
    expect(formData.get("document_type")).toBe("contracheque");
    expect(formData.get("salario_bruto")).toBe("8500.00");
    expect(formData.get("razao_social")).toBe("ACME LTDA");
    expect(formData.get("cargo")).toBe("Analista Financeiro");

    const file = formData.get("file");
    expect(file).toBeInstanceOf(File);
    expect((file as File).name).toBe("folha.pdf");
  });

  it("omits empty optional extra info fields", () => {
    const formData = buildPayrollAnalysisFormData(makeFile());

    expect(formData.get("document_type")).toBe("contracheque");
    expect(formData.has("salario_bruto")).toBe(false);
    expect(formData.has("razao_social")).toBe(false);
    expect(formData.has("cargo")).toBe(false);
  });
});

describe("getPayrollUploadErrorCode", () => {
  it.each([
    [401, "auth"],
    [403, "auth"],
    [400, "file"],
    [413, "file"],
    [415, "file"],
    [422, "file"],
    [404, "server"],
    [429, "server"],
    [500, "server"],
    [502, "server"],
    [503, "server"],
    [408, "timeout"],
  ])("maps HTTP %i to %s", (status, expected) => {
    expect(getPayrollUploadErrorCode(apiClientError(status))).toBe(expected);
  });

  it("maps network, timeout and unknown failures without exposing raw errors", () => {
    expect(getPayrollUploadErrorCode(new TypeError("Failed to fetch"))).toBe("network");
    expect(
      getPayrollUploadErrorCode(new DOMException("timed out", "TimeoutError")),
    ).toBe("timeout");
    expect(
      getPayrollUploadErrorCode(new DOMException("aborted", "AbortError")),
    ).toBe("timeout");
    expect(getPayrollUploadErrorCode({ name: "WeirdError" })).toBe("unknown");
  });
});

describe("analyzePayrollFile", () => {
  it("maps a successful analysis to a done result", async () => {
    const analyze = vi.fn().mockResolvedValue({
      RISK_ASSESSMENT: {
        fraud_risk_score: 82,
        risk_classification: "HIGH",
        ai_confidence: 94,
      },
      ANOMALY_LIST: [],
      persistence_status: "saved",
    });

    const outcome = await analyzePayrollFile({ ...baseParams, analyze });

    expect(outcome.status).toBe("done");
    if (outcome.status !== "done") throw new Error("expected a successful outcome");
    expect(outcome.result.riskScore).toBe(82);
    expect(outcome.result.confidenceScore).toBe(94);
    expect(outcome.result.documentType).toBe("payroll");
    expect(outcome.persistenceFailed).toBe(false);
    expect(outcome.result.persistenceStatus).toBe("saved");
  });

  it("returns an error outcome for 4xx/5xx and never a result", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const consoleWarn = vi.spyOn(console, "warn").mockImplementation(() => {});

    for (const [status, errorCode] of [
      [422, "file"],
      [401, "auth"],
      [500, "server"],
      [502, "server"],
    ] as const) {
      const outcome = await analyzePayrollFile({
        ...baseParams,
        analyze: vi.fn().mockRejectedValue(apiClientError(status)),
      });

      expect(outcome).toEqual({ status: "error", errorCode });
      expect("result" in outcome).toBe(false);
    }

    expect(consoleError).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
  });

  it("returns error outcomes for network and timeout failures", async () => {
    const network = await analyzePayrollFile({
      ...baseParams,
      analyze: vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    });
    const timeout = await analyzePayrollFile({
      ...baseParams,
      analyze: vi.fn().mockRejectedValue(
        new DOMException("The operation timed out.", "TimeoutError"),
      ),
    });

    expect(network).toEqual({ status: "error", errorCode: "network" });
    expect(timeout).toEqual({ status: "error", errorCode: "timeout" });
  });

  it("marks a failed persistence as a warning without claiming it was saved", async () => {
    const outcome = await analyzePayrollFile({
      ...baseParams,
      analyze: vi.fn().mockResolvedValue({
        risk_score: 61,
        AI_REASONING_SUMMARY: "Anomalias encontradas no documento.",
        persistence_status: "failed",
      }),
    });

    expect(outcome.status).toBe("done");
    if (outcome.status !== "done") throw new Error("expected a completed analysis");
    expect(outcome.persistenceFailed).toBe(true);
    expect(outcome.result.persistenceStatus).toBe("failed");
    expect(outcome.result.persistenceStatus).not.toBe("saved");
  });

  it("rejects non-object and empty responses without marking them as done", async () => {
    const nullOutcome = await analyzePayrollFile({
      ...baseParams,
      analyze: vi.fn().mockResolvedValue(null),
    });
    const emptyOutcome = await analyzePayrollFile({
      ...baseParams,
      analyze: vi.fn().mockResolvedValue({}),
    });

    expect(nullOutcome).toEqual({ status: "error", errorCode: "unknown" });
    expect(emptyOutcome).toEqual({ status: "error", errorCode: "unknown" });
  });
});
