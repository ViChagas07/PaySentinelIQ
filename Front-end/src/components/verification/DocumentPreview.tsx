// ============================================================
// PaySentinelIQ — Document Preview Panel
// Simulated PDF view with OCR overlay and highlighted sections
// ============================================================

"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";
import { FileText, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useState } from "react";

interface Highlight {
  id: string;
  label: string;
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
  severity: "low" | "medium" | "high" | "critical";
}

export function DocumentPreview({
  highlights = [],
  totalPages = 1,
}: {
  highlights?: Highlight[];
  totalPages?: number;
}) {
  const t = useTranslations("verification");
  const tc = useTranslations("common");
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [activeHighlight, setActiveHighlight] = useState<string | null>(null);

  const currentHighlights = highlights.filter((h) => h.page === currentPage);

  const severityColors: Record<string, string> = {
    low: "border-psi-emerald bg-psi-emerald/10",
    medium: "border-psi-warning bg-psi-warning/10",
    high: "border-psi-fraud bg-psi-fraud/10",
    critical: "border-psi-fraud bg-psi-fraud/20 shadow-lg shadow-psi-fraud/20",
  };

  const severityDots: Record<string, string> = {
    low: "bg-psi-emerald",
    medium: "bg-psi-warning",
    high: "bg-psi-fraud",
    critical: "bg-psi-fraud animate-pulse-alert",
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-psi-border bg-psi-graphite/50">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-psi-electric" />
          <span className="text-sm font-medium text-psi-text-primary">
            Q1_2025_Payroll_Report.pdf
          </span>
          <Badge variant="destructive" dot className="text-[10px]">
            {t("flagsCount", { count: 5 })}
          </Badge>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" onClick={() => setZoom(Math.max(0.5, zoom - 0.25))} aria-label={tc("zoomOut")}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-xs text-psi-text-secondary tabular-nums w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button variant="ghost" size="sm" onClick={() => setZoom(Math.min(2, zoom + 0.25))} aria-label={tc("zoomIn")}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <div className="w-px h-5 bg-psi-border mx-1" />
          <Button variant="ghost" size="sm" aria-label={tc("download")}>
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Page content */}
      <div className="flex-1 overflow-auto p-6 bg-psi-navy/80">
        <motion.div
          key={`page-${currentPage}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.25 }}
          className="relative mx-auto bg-white/[0.03] rounded-lg border border-psi-border"
          style={{
            width: `${595 * zoom}px`,
            minHeight: `${842 * zoom}px`,
            maxWidth: "100%",
          }}
        >
          {/* Simulated document content */}
          <div className="p-8 space-y-6" style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
            {/* Header */}
            <div className="border-b border-white/10 pb-4">
              <h3 className="text-lg font-bold text-white/80">{t("documentHeader")}</h3>
              <p className="text-sm text-white/40 mt-1">{t("documentPeriod", { start: "January 1", end: "March 31, 2025" })}</p>
              <p className="text-sm text-white/40">{t("documentCompany", { company: "Acme Corporation", department: "All" })}</p>
            </div>

            {/* Summary section */}
            <div>
              <h4 className="text-base font-semibold text-white/70 mb-3">1. Executive Summary</h4>
              <p className="text-sm text-white/50 leading-relaxed">
                This report summarizes payroll expenses for Q1 2025 across all departments.
                Total gross payroll amounts to{' '}
                <span className="px-1 border-b-2 border-psi-fraud/60 bg-psi-fraud/10 rounded">
                  $847,230.00
                </span>{' '}
                with total deductions of $124,560.00. Net payable amount is $722,670.00.
                A total of 1,247 employees were processed across 12 pay periods.
              </p>
            </div>

            {/* Table section */}
            <div>
              <h4 className="text-base font-semibold text-white/70 mb-3">2. Department Breakdown</h4>
              <table className="w-full text-sm text-white/60">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-2 text-white/50 font-medium">{t("tableDept")}</th>
                    <th className="text-right py-2 text-white/50 font-medium">{t("tableEmployees")}</th>
                    <th className="text-right py-2 text-white/50 font-medium">{t("tableGrossPay")}</th>
                    <th className="text-right py-2 text-white/50 font-medium">{t("tableAvgSalary")}</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { dept: "Engineering", emp: 340, gross: "$245,000", avg: "$72,058" },
                    { dept: "Sales", emp: 280, gross: "$198,500", avg: "$70,892" },
                    { dept: "Marketing", emp: 190, gross: "$126,300", avg: "$66,473" },
                    { dept: "Operations", emp: 250, gross: "$167,800", avg: "$67,120" },
                    { dept: "Customer Support", emp: 300, gross: "$150,000", avg: "$50,000" },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-2 text-white/70">{row.dept}</td>
                      <td className="py-2 text-right tabular-nums">{row.emp}</td>
                      <td className={`py-2 text-right tabular-nums ${row.dept === "Customer Support" ? "text-psi-fraud font-semibold" : ""}`}>
                        {row.gross}
                      </td>
                      <td className="py-2 text-right tabular-nums">{row.avg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Tax section */}
            <div>
              <h4 className="text-base font-semibold text-white/70 mb-3">3. Tax Withholdings</h4>
              <p className="text-sm text-white/50 leading-relaxed">
                Federal tax withheld: $187,450.00 · State tax: $42,300.00 · FICA: $64,800.00
                <span className="ml-1 px-1 border-b-2 border-psi-warning/60 bg-psi-warning/10 rounded">
                  Anomaly: $12,400 unaccounted in Engineering department
                </span>
              </p>
            </div>
          </div>

          {/* OCR Overlay Highlights */}
          {currentHighlights.map((h) => (
            <motion.div
              key={h.id}
              role="button"
              tabIndex={0}
              aria-label={`Highlighted field: ${h.label}`}
              aria-pressed={activeHighlight === h.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.02 }}
              onClick={() => setActiveHighlight(activeHighlight === h.id ? null : h.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setActiveHighlight(activeHighlight === h.id ? null : h.id);
                }
              }}
              className={cn(
                "absolute cursor-pointer rounded border-2 transition-all duration-200",
                severityColors[h.severity],
                activeHighlight === h.id && "ring-2 ring-psi-electric border-psi-electric"
              )}
              style={{
                left: `${h.x}%`,
                top: `${h.y}%`,
                width: `${h.width}%`,
                height: `${h.height}%`,
                transform: "translate(-2px, -2px)",
              }}
            >
              {activeHighlight === h.id && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="absolute -top-8 left-0 bg-psi-graphite border border-psi-border rounded-md px-2 py-1 text-[10px] text-psi-text-primary whitespace-nowrap shadow-xl z-10"
                >
                  {h.label}
                  <span
                    className={cn(
                      "ml-1.5 inline-block h-1.5 w-1.5 rounded-full",
                      severityDots[h.severity]
                    )}
                  />
                </motion.div>
              )}
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Page navigation */}
      <div className="flex items-center justify-center gap-4 px-4 py-2 border-t border-psi-border bg-psi-graphite/50">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage === 1}
          onClick={() => setCurrentPage(currentPage - 1)}
          aria-label={tc("previousPage")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-xs text-psi-text-secondary tabular-nums">
          {tc("pageOf", { current: currentPage, total: totalPages })}
        </span>
        <Button
          variant="ghost"
          size="sm"
          disabled={currentPage === totalPages}
          onClick={() => setCurrentPage(currentPage + 1)}
          aria-label={tc("nextPage")}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
