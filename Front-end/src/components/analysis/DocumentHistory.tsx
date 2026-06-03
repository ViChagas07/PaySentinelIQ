"use client";

import { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { HistoryEntry } from "@/stores/analysis-store";
import { StatusPill } from "@/components/shared/GlowCard";
import {
  Search, Clock, Trash2, FileText, ChevronDown,
  Download, RotateCcw,
} from "lucide-react";

export function DocumentHistory({
  entries,
  onRemove,
  onReopen,
}: {
  entries: HistoryEntry[];
  onRemove?: (id: string) => void;
  onReopen?: (entry: HistoryEntry) => void;
}) {
  const t = useTranslations("analysis");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"date" | "risk" | "duration">("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const filtered = useMemo(() => {
    let list = [...entries];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((e) => e.fileName.toLowerCase().includes(q) || e.aiSummary.toLowerCase().includes(q));
    }
    if (statusFilter !== "all") list = list.filter((e) => e.status === statusFilter);
    list.sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (sortBy === "date") return dir * (new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime());
      if (sortBy === "risk") return dir * (b.riskScore - a.riskScore);
      return dir * (b.processingDuration - a.processingDuration);
    });
    return list;
  }, [entries, search, statusFilter, sortBy, sortDir]);

  const toggleSort = (field: "date" | "risk" | "duration") => {
    if (sortBy === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortBy(field); setSortDir("desc"); }
  };

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-psi-border/20 mb-3">
          <Clock className="h-6 w-6 text-psi-text-secondary" />
        </div>
        <p className="text-sm font-medium text-psi-text-secondary">{t("history.noHistory")}</p>
        <p className="text-xs text-psi-text-secondary/60 mt-1">{t("history.noHistoryHint")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-psi-text-secondary" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder={t("history.searchPlaceholder")}
            className="w-full rounded-lg border border-psi-border bg-psi-graphite/60 pl-9 pr-3 py-2 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/50 outline-none focus:border-psi-electric transition-colors"
          />
        </div>
        <select
          value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-psi-border bg-psi-graphite/60 px-3 py-2 text-sm text-psi-text-primary outline-none focus:border-psi-electric transition-colors"
        >
          <option value="all">{t("history.allStatus")}</option>
          <option value="completed">{t("history.completed")}</option>
          <option value="flagged">{t("history.flagged")}</option>
          <option value="failed">{t("history.failed")}</option>
        </select>
      </div>

      <div className="rounded-xl border border-psi-border/50 overflow-hidden">
        <div className="hidden sm:grid grid-cols-12 gap-2 px-4 py-2.5 bg-psi-border/10 text-[10px] uppercase tracking-wider text-psi-text-secondary font-semibold">
          <div className="col-span-4">{t("history.columnDocument")}</div>
          <button onClick={() => toggleSort("date")} className="col-span-2 flex items-center gap-1 hover:text-psi-text-primary">
            {t("history.columnDate")} {sortBy === "date" && <ChevronDown className={cn("h-3 w-3", sortDir === "asc" && "rotate-180")} />}
          </button>
          <div className="col-span-1">{t("history.columnStatus")}</div>
          <button onClick={() => toggleSort("risk")} className="col-span-1 flex items-center gap-1 hover:text-psi-text-primary">
            {t("history.columnRisk")} {sortBy === "risk" && <ChevronDown className={cn("h-3 w-3", sortDir === "asc" && "rotate-180")} />}
          </button>
          <button onClick={() => toggleSort("duration")} className="col-span-1 flex items-center gap-1 hover:text-psi-text-primary">
            {t("history.columnTime")} {sortBy === "duration" && <ChevronDown className={cn("h-3 w-3", sortDir === "asc" && "rotate-180")} />}
          </button>
          <div className="col-span-2">{t("history.columnSummary")}</div>
          <div className="col-span-1 text-right">{t("history.columnActions")}</div>
        </div>

        <AnimatePresence>
          {filtered.map((entry) => (
            <motion.div
              key={entry.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, height: 0 }}
              className="grid grid-cols-1 sm:grid-cols-12 gap-2 px-4 py-3 border-t border-psi-border/30 hover:bg-psi-border/10 transition-colors items-center"
            >
              <div className="sm:col-span-4 flex items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0 text-psi-text-secondary" />
                <span className="text-sm text-psi-text-primary truncate">{entry.fileName}</span>
              </div>
              <div className="sm:col-span-2 text-xs text-psi-text-secondary">{entry.uploadDate}</div>
              <div className="sm:col-span-1">
                <StatusPill label={entry.status} variant={entry.status === "completed" ? "success" : entry.status === "flagged" ? "warning" : "destructive"} />
              </div>
              <div className="sm:col-span-1">
                <span className={cn("text-sm font-bold", entry.riskScore >= 80 ? "text-psi-fraud" : entry.riskScore >= 60 ? "text-psi-warning" : "text-psi-emerald")}>{entry.riskScore}</span>
              </div>
              <div className="sm:col-span-1 text-xs text-psi-text-secondary">{entry.processingDuration}s</div>
              <div className="sm:col-span-2 text-xs text-psi-text-secondary truncate">{entry.aiSummary.slice(0, 60)}...</div>
              <div className="sm:col-span-1 flex items-center justify-end gap-1">
                {onReopen && (
                  <button onClick={() => onReopen(entry)} className="rounded p-1.5 text-psi-text-secondary hover:text-psi-electric hover:bg-psi-electric/10 transition-colors" title={t("history.reopen")}>
                    <RotateCcw className="h-3.5 w-3.5" />
                  </button>
                )}
                <button className="rounded p-1.5 text-psi-text-secondary hover:text-psi-text-primary hover:bg-psi-border/20 transition-colors" title={t("history.download")}>
                  <Download className="h-3.5 w-3.5" />
                </button>
                {onRemove && (
                  <button onClick={() => onRemove(entry.id)} className="rounded p-1.5 text-psi-text-secondary hover:text-psi-fraud hover:bg-psi-fraud/10 transition-colors" title={t("history.delete")}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <p className="text-[11px] text-psi-text-secondary text-right">
        {t("history.showing", { shown: filtered.length, total: entries.length })}
      </p>
    </div>
  );
}
