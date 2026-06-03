// ============================================================
// PaySentinelIQ — Fraud Risk Table
// Sortable, filterable table with real fraud alerts from the API.
// No hardcoded/mock data.
// ============================================================

"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  ArrowUpDown,
  Search,
  Eye,
  MoreHorizontal,
  Clock,
} from "lucide-react";
import { useFraudAlerts } from "@/hooks/useApi";

// ── Types ── /

interface FraudRecord {
  id: string;
  document: string;
  employee: string;
  department: string;
  riskLevel: "low" | "medium" | "high" | "critical";
  aiConfidence: number;
  anomalyCategory: string;
  riskScore: number;
  status: "new" | "under_review" | "escalated" | "confirmed_fraud" | "false_positive" | "resolved";
  date: string;
}

type SortField = keyof FraudRecord;
type SortDir = "asc" | "desc";

const riskLevelConfig: Record<string, string> = {
  low: "text-psi-emerald",
  medium: "text-psi-warning",
  high: "text-psi-fraud",
  critical: "text-psi-fraud font-bold",
};

function getCategoryKey(category: string): string {
  const map: Record<string, string> = {
    salary_discrepancy: "salaryAnomaly",
    ghost_employee: "ghostEmployee",
    tax_evasion: "taxAnomaly",
    document_forgery: "documentForgery",
    timesheet_fraud: "timesheetFraud",
    compliance_violation: "compliance",
    duplicate_payment: "duplicatePayment",
    identity_mismatch: "identityMismatch",
    unauthorized_deduction: "unauthorizedDeduction",
  };
  return map[category] || "compliance";
}

// ── Main Table ── //

export function FraudRiskTable() {
  const t = useTranslations("fraud");
  const tc = useTranslations("common");

  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const statusConfig: Record<FraudRecord["status"], { label: string; variant: "success" | "warning" | "destructive" | "default" | "primary" }> = {
    new: { label: t("statusNew"), variant: "destructive" },
    under_review: { label: t("statusInReview"), variant: "warning" },
    escalated: { label: t("statusEscalated"), variant: "destructive" },
    confirmed_fraud: { label: t("statusConfirmedFraud"), variant: "destructive" },
    false_positive: { label: t("statusFalsePositive"), variant: "success" },
    resolved: { label: t("statusResolved"), variant: "success" },
  };

  const riskLabels: Record<string, string> = {
    low: t("riskLevelLow"),
    medium: t("riskLevelMedium"),
    high: t("riskLevelHigh"),
    critical: t("riskLevelCritical"),
  };

  // ── Fetch real fraud alerts from the API ──
  const { data: alertsResponse, isLoading } = useFraudAlerts({
    ...(riskFilter !== "all" ? { risk_level: riskFilter } : {}),
    ...(statusFilter !== "all" ? { status: statusFilter } : {}),
  });
  const apiRecords: FraudRecord[] = useMemo(() => {
    if (!alertsResponse?.data) return [];
    return alertsResponse.data.map((alert: any) => ({
      id: alert.id,
      document: alert.document_id || "",
      employee: "",
      department: "",
      riskLevel: alert.risk_level || "low",
      aiConfidence: Math.round((alert.ai_confidence || 0) * 100),
      anomalyCategory: alert.anomaly_category || "other",
      riskScore: Math.round(alert.risk_score || 0),
      status: alert.status || "new",
      date: alert.created_at ? alert.created_at.slice(0, 10) : "",
    }));
  }, [alertsResponse]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const filteredRecords = useMemo(() => {
    let filtered = [...apiRecords];

    if (search) {
      const s = search.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.document.toLowerCase().includes(s) ||
          r.employee.toLowerCase().includes(s) ||
          r.department.toLowerCase().includes(s) ||
          r.anomalyCategory.toLowerCase().includes(s)
      );
    }

    if (riskFilter !== "all") {
      filtered = filtered.filter((r) => r.riskLevel === riskFilter);
    }

    if (statusFilter !== "all") {
      filtered = filtered.filter((r) => r.status === statusFilter);
    }

    filtered.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      const dir = sortDir === "asc" ? 1 : -1;

      if (typeof aVal === "number" && typeof bVal === "number") {
        return (aVal - bVal) * dir;
      }
      return String(aVal).localeCompare(String(bVal)) * dir;
    });

    return filtered;
  }, [search, riskFilter, statusFilter, sortField, sortDir, apiRecords]);

  return (
    <div>
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-psi-text-secondary" />
          <input
            type="search"
            placeholder={t("searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-psi-border bg-psi-navy/50 pl-10 pr-4 py-2 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/40 outline-none focus:border-psi-electric transition-colors"
          />
        </div>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-lg border border-psi-border bg-psi-navy/50 px-3 py-2 text-sm text-psi-text-primary outline-none focus:border-psi-electric transition-colors"
          aria-label={t("filterByRisk")}
        >
          <option value="all">{t("allRiskLevels")}</option>
          <option value="low">{t("riskLevelLow")}</option>
          <option value="medium">{t("riskLevelMedium")}</option>
          <option value="high">{t("riskLevelHigh")}</option>
          <option value="critical">{t("riskLevelCritical")}</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-psi-border bg-psi-navy/50 px-3 py-2 text-sm text-psi-text-primary outline-none focus:border-psi-electric transition-colors"
          aria-label={t("filterByStatus")}
        >
          <option value="all">{t("allStatuses")}</option>
          <option value="new">{t("statusNew")}</option>
          <option value="under_review">{t("statusInReview")}</option>
          <option value="escalated">{t("statusEscalated")}</option>
          <option value="confirmed_fraud">{t("statusConfirmedFraud")}</option>
          <option value="false_positive">{t("statusFalsePositive")}</option>
          <option value="resolved">{t("statusResolved")}</option>
        </select>
      </div>

      {/* Results count */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="h-6 w-6 rounded-full border-2 border-psi-electric/30 border-t-psi-electric animate-spin" />
        </div>
      ) : (
      <>
      <p className="text-xs text-psi-text-secondary mb-3">
        {t.rich("showingRecords", {
          count: filteredRecords.length,
          total: apiRecords.length,
          strong: (chunks) => <span className="font-semibold text-psi-text-primary">{chunks}</span>,
        })}
      </p>

      {/* Table — sempre visível, mesmo com 0 registros */}
      <div className="rounded-xl border border-psi-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-psi-border bg-psi-navy/40">
                {[
                  { field: "document" as SortField, label: t("columnDocument") },
                  { field: "employee" as SortField, label: t("columnEmployee") },
                  { field: "department" as SortField, label: t("columnDepartment") },
                  { field: "riskLevel" as SortField, label: t("columnRiskLevel") },
                  { field: "aiConfidence" as SortField, label: t("columnAIConfidence") },
                  { field: "anomalyCategory" as SortField, label: t("columnAnomaly") },
                  { field: "riskScore" as SortField, label: t("columnScore") },
                  { field: "status" as SortField, label: t("columnStatus") },
                ].map((col) => (
                  <th
                    key={col.field}
                    role="columnheader"
                    tabIndex={0}
                    aria-sort={
                      sortField === col.field
                        ? sortDir === "asc" ? "ascending" : "descending"
                        : "none"
                    }
                    onClick={() => handleSort(col.field)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleSort(col.field);
                      }
                    }}
                    className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-psi-text-secondary cursor-pointer hover:text-psi-text-primary transition-colors select-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-psi-electric"
                  >
                    <div className="flex items-center gap-1.5">
                      {col.label}
                      <ArrowUpDown className="h-3 w-3" aria-hidden="true" />
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-psi-text-secondary">
                  {tc("actions")}
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filteredRecords.map((record, i) => (
                  <motion.tr
                    key={record.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-psi-border/50 hover:bg-psi-electric/[0.03] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-psi-electric shrink-0" />
                        <span className="text-sm text-psi-text-primary font-medium truncate max-w-[160px]">
                          {record.document}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-psi-text-primary">{record.employee}</td>
                    <td className="px-4 py-3 text-sm text-psi-text-secondary">{record.department}</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={record.riskLevel === "critical" ? "destructive" : record.riskLevel === "high" ? "destructive" : record.riskLevel === "medium" ? "warning" : "success"}
                        dot
                        className={cn(
                          "text-[10px]",
                          record.riskLevel === "critical" && "animate-pulse-alert"
                        )}
                      >
                        {riskLabels[record.riskLevel]}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 flex-1 rounded-full bg-psi-border overflow-hidden max-w-[60px]">
                          <div
                            className="h-full rounded-full bg-psi-electric"
                            style={{ width: `${record.aiConfidence}%` }}
                          />
                        </div>
                        <span className="text-xs text-psi-text-secondary tabular-nums">
                          {record.aiConfidence}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-psi-text-secondary">{t(`categories.${getCategoryKey(record.anomalyCategory)}`)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("text-sm font-bold tabular-nums", riskLevelConfig[record.riskLevel])}>
                        {record.riskScore}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusConfig[record.status].variant} className="text-[10px]">
                        {statusConfig[record.status].label}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" aria-label={tc("viewDetails")}>
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="sm" aria-label={tc("moreOptions")}>
                          <MoreHorizontal className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {/* Empty — mostra apenas uma linha sutil quando não há registros */}
        {filteredRecords.length === 0 && (
          <div className="py-8 text-center">
            <p className="text-xs text-psi-text-secondary/50">{t("noRecords")}</p>
          </div>
        )}
      </div>
      </>
      )}
    </div>
  );
}
