"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { useAnalysisStore, type ExtraInfo } from "@/stores/analysis-store";
import { Lightbulb, MessageSquare, Building2, User, DollarSign, Briefcase, Calendar } from "lucide-react";

/* ═══════════════════════════════════════════════════
   Floating input field
   ═══════════════════════════════════════════════════ */

function FloatingInput({
  label, name, icon: Icon, value, onChange, placeholder, type = "text",
}: {
  label: string; name: keyof ExtraInfo; icon: React.ElementType;
  value: string; onChange: (name: keyof ExtraInfo, v: string) => void;
  placeholder?: string; type?: string;
}) {
  return (
    <div className="group relative">
      <label className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-psi-text-secondary mb-1.5">
        <Icon className="h-3 w-3" />
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        placeholder={placeholder}
        className={cn(
          "w-full rounded-lg border border-psi-border bg-psi-graphite/60 px-3 py-2.5 text-sm text-psi-text-primary",
          "placeholder:text-psi-text-secondary/40 outline-none transition-all duration-200",
          "focus:border-psi-electric focus:ring-1 focus:ring-psi-electric/30 focus:bg-psi-graphite",
          "group-hover:border-psi-border/80"
        )}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   Extra Info Form
   ═══════════════════════════════════════════════════ */

export function ExtraInfoForm({ documentType }: { documentType: "payroll" | "bank-slip" }) {
  const t = useTranslations("analysis");
  const extraInfo = useAnalysisStore((s) => s.extraInfo);
  const setExtraInfo = useAnalysisStore((s) => s.setExtraInfo);

  const set = (name: keyof ExtraInfo, value: string) => setExtraInfo({ [name]: value });

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Info banner */}
      <div className="flex items-start gap-2 rounded-lg bg-psi-electric/5 border border-psi-electric/10 px-3 py-2.5">
        <Lightbulb className="h-4 w-4 text-psi-electric mt-0.5 shrink-0" />
        <p className="text-xs text-psi-text-secondary leading-relaxed">
          {documentType === "payroll" ? t("payroll.extraHint") : t("bankSlip.extraHint")}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {documentType === "payroll" ? (
          <>
            <FloatingInput label={t("form.employeeName")} name="employeeName" icon={User} value={extraInfo.employeeName || ""} onChange={set} placeholder={t("form.placeholderEmployee")} />
            <FloatingInput label={t("form.companyName")} name="companyName" icon={Building2} value={extraInfo.companyName || ""} onChange={set} placeholder={t("form.placeholderCompany")} />
            <FloatingInput label={t("form.expectedSalary")} name="expectedSalary" icon={DollarSign} value={extraInfo.expectedSalary || ""} onChange={set} placeholder={t("form.placeholderSalary")} type="text" />
            <FloatingInput label={t("form.jobPosition")} name="jobPosition" icon={Briefcase} value={extraInfo.jobPosition || ""} onChange={set} placeholder={t("form.placeholderPosition")} />
            <FloatingInput label={t("form.employmentType")} name="employmentType" icon={Briefcase} value={extraInfo.employmentType || ""} onChange={set} placeholder={t("form.placeholderEmployment")} />
            <FloatingInput label={t("form.payrollPeriod")} name="payrollPeriod" icon={Calendar} value={extraInfo.payrollPeriod || ""} onChange={set} placeholder={t("form.placeholderPeriod")} />
          </>
        ) : (
          <>
            <FloatingInput label={t("form.companyName")} name="companyName" icon={Building2} value={extraInfo.companyName || ""} onChange={set} placeholder={t("form.placeholderCompany")} />
            <FloatingInput label={t("form.expectedAmount")} name="expectedSalary" icon={DollarSign} value={extraInfo.expectedSalary || ""} onChange={set} placeholder={t("form.placeholderAmount")} type="text" />
            <FloatingInput label={t("form.documentSource")} name="documentSource" icon={Building2} value={extraInfo.documentSource || ""} onChange={set} placeholder={t("form.placeholderSource")} />
            <FloatingInput label={t("form.employeeName")} name="employeeName" icon={User} value={extraInfo.employeeName || ""} onChange={set} placeholder={t("form.placeholderRecipient")} />
          </>
        )}
      </div>

      {/* Full-width fields */}
      <div className="grid grid-cols-1 gap-4">
        <div className="group relative">
          <label className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-psi-text-secondary mb-1.5">
            <MessageSquare className="h-3 w-3" />
            {t("form.suspiciousObservations")}
          </label>
          <textarea
            value={extraInfo.suspiciousObservations || ""}
            onChange={(e) => set("suspiciousObservations", e.target.value)}
            placeholder={documentType === "payroll" ? t("form.placeholderSuspiciousPayroll") : t("form.placeholderSuspiciousBankSlip")}
            rows={3}
            className="w-full rounded-lg border border-psi-border bg-psi-graphite/60 px-3 py-2.5 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/40 outline-none transition-all focus:border-psi-electric focus:ring-1 focus:ring-psi-electric/30 resize-none"
          />
        </div>
        <div className="group relative">
          <label className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-psi-text-secondary mb-1.5">
            <MessageSquare className="h-3 w-3" />
            {t("form.additionalNotes")}
          </label>
          <textarea
            value={extraInfo.notes || ""}
            onChange={(e) => set("notes", e.target.value)}
            placeholder={t("form.placeholderNotes")}
            rows={2}
            className="w-full rounded-lg border border-psi-border bg-psi-graphite/60 px-3 py-2.5 text-sm text-psi-text-primary placeholder:text-psi-text-secondary/40 outline-none transition-all focus:border-psi-electric focus:ring-1 focus:ring-psi-electric/30 resize-none"
          />
        </div>
      </div>
    </motion.div>
  );
}
