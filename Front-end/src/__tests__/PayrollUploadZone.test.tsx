// ============================================================
// PaySentinelIQ — Payroll upload zone/component tests
// ============================================================

import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  PayrollDocumentItem,
  PayrollUploadZone,
} from "@/components/payroll/PayrollUploadZone";
import type { PayrollUploadedDocument } from "@/lib/payroll-upload";

const t = (key: string) => key;

function apiClientError(status: number): Error {
  return Object.assign(
    new Error("raw backend detail: contracheque.pdf"),
    { name: "ApiClientError", status },
  );
}

function Harness({
  analyze,
}: {
  analyze: (formData: FormData) => Promise<unknown>;
}) {
  const [documents, setDocuments] = useState<PayrollUploadedDocument[]>([]);

  return (
    <>
      <PayrollUploadZone
        t={t}
        locale="pt-BR"
        extraInfo={{}}
        analyzeDocument={analyze}
        onDocumentChange={(document) =>
          setDocuments((prev) => {
            const index = prev.findIndex((item) => item.id === document.id);
            if (index === -1) return [...prev, document];
            const next = [...prev];
            next[index] = document;
            return next;
          })
        }
      />
      {documents.map((document) => (
        <PayrollDocumentItem
          key={document.id}
          document={document}
          t={t}
        />
      ))}
    </>
  );
}

function selectFiles(files: File[]) {
  fireEvent.change(screen.getByLabelText("upload.selectFile"), {
    target: { files },
  });
}

function makeFile(name = "contracheque.pdf"): File {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" });
}

describe("PayrollUploadZone", () => {
  it("moves a file to done and shows its risk summary on success", async () => {
    const analyze = vi.fn().mockResolvedValue({
      RISK_ASSESSMENT: {
        fraud_risk_score: 73,
        risk_classification: "HIGH",
        ai_confidence: 91,
      },
      AI_REASONING_SUMMARY: "Documento apresenta inconsistências.",
      persistence_status: "saved",
    });

    render(<Harness analyze={analyze} />);
    selectFiles([makeFile()]);

    await waitFor(() => expect(screen.getByText("73/100")).toBeInTheDocument());

    expect(screen.getByText("Documento apresenta inconsistências.")).toBeInTheDocument();
    expect(screen.getByText("contracheque.pdf")).toBeInTheDocument();
    expect(screen.queryByText("upload.persistenceWarning")).not.toBeInTheDocument();
    expect(analyze).toHaveBeenCalledTimes(1);

    const formData = analyze.mock.calls[0][0] as FormData;
    expect(formData.get("document_type")).toBe("contracheque");
  });

  it.each([422, 500])(
    "shows a readable error and no success entry for HTTP %i",
    async (status) => {
      const analyze = vi.fn().mockRejectedValue(apiClientError(status));

      render(<Harness analyze={analyze} />);
      selectFiles([makeFile()]);

      await waitFor(() =>
        expect(screen.getByRole("alert")).toHaveTextContent(
          status === 422 ? "upload.error.file" : "upload.error.server",
        ),
      );

      expect(screen.queryByText("73%")).not.toBeInTheDocument();
      expect(screen.queryByText("upload.persistenceWarning")).not.toBeInTheDocument();
      expect(screen.queryByText("upload.scanning")).not.toBeInTheDocument();
    },
  );

  it("keeps per-file outcomes independent when one upload fails", async () => {
    const analyze = vi.fn(async (formData: FormData) => {
      const file = formData.get("file") as File;
      if (file.name.includes("falha")) throw apiClientError(422);
      return {
        risk_score: 30,
        AI_REASONING_SUMMARY: "Sem anomalias.",
        persistence_status: "saved",
      };
    });

    render(<Harness analyze={analyze} />);
    selectFiles([makeFile("ok.pdf"), makeFile("falha.pdf")]);

    await waitFor(() => expect(screen.getByText("30/100")).toBeInTheDocument());

    expect(screen.getByRole("alert")).toHaveTextContent("upload.error.file");
    expect(screen.queryByText("upload.persistenceWarning")).not.toBeInTheDocument();
  });

  it("shows a non-fatal warning and no saved state when persistence fails", async () => {
    const analyze = vi.fn().mockResolvedValue({
      risk_score: 61,
      AI_REASONING_SUMMARY: "Análise concluída com ressalvas.",
      persistence_status: "failed",
    });

    render(<Harness analyze={analyze} />);
    selectFiles([makeFile()]);

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "upload.persistenceWarning",
      ),
    );

    expect(screen.getByText("61/100")).toBeInTheDocument();
    expect(screen.queryByText(/saved/i)).not.toBeInTheDocument();
  });
});
