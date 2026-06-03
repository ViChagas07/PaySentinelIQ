// ============================================================
// PaySentinelIQ — Fraud Intelligence Center
// Risk table, investigation timeline, fraud heatmap summary
// ============================================================

"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { FraudRiskTable } from "@/components/fraud/FraudRiskTable";
import { InvestigationTimeline } from "@/components/fraud/InvestigationTimeline";
import { Button } from "@/components/ui/Button";
import {
  AlertTriangle,
  TrendingUp,
  Clock,
  Download,
  BarChart3,
  ShieldCheck,
} from "lucide-react";

// ── Summary stats ── //

const summaryStats = [
  { label: "Active Alerts", value: "12", sub: "+3 this week", color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/30" },
  { label: "Under Review", value: "8", sub: "4 analysts assigned", color: "text-psi-warning", bg: "bg-psi-warning/10", border: "border-psi-warning/30" },
  { label: "Confirmed Fraud", value: "3", sub: "92% conviction rate", color: "text-psi-fraud", bg: "bg-psi-fraud/10", border: "border-psi-fraud/30" },
  { label: "Avg. Response", value: "14m", sub: "Down from 22m last month", color: "text-psi-emerald", bg: "bg-psi-emerald/10", border: "border-psi-emerald/30" },
];

export default function FraudIntelligencePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-psi-text-primary tracking-tight">
            Fraud Intelligence Center
          </h1>
          <p className="text-sm text-psi-text-secondary mt-1">
            Real-time fraud detection, investigation workflow, and risk analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="destructive" dot>
            5 Critical Alerts
          </Badge>
          <Button variant="outline" size="sm">
            <Download className="h-3.5 w-3.5 mr-1" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryStats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-psi-text-secondary uppercase tracking-wider">
                    {stat.label}
                  </span>
                  {stat.label === "Active Alerts" && (
                    <AlertTriangle className="h-4 w-4 text-psi-fraud animate-pulse-alert" />
                  )}
                </div>
                <p className={cn("text-2xl font-bold tabular-nums", stat.color)}>{stat.value}</p>
                <p className="text-[11px] text-psi-text-secondary mt-0.5">{stat.sub}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Fraud Risk Table — 2 cols */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Fraud Risk Table</CardTitle>
                <p className="text-xs text-psi-text-secondary mt-1">
                  AI-detected anomalies requiring analyst review
                </p>
              </div>
              <Button variant="outline" size="sm">
                <BarChart3 className="h-3.5 w-3.5 mr-1" />
                View Analytics
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <FraudRiskTable />
          </CardContent>
        </Card>

        {/* Investigation Timeline — 1 col */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Investigation Timeline</CardTitle>
            <p className="text-xs text-psi-text-secondary mt-1">
              FR-001: Salary Discrepancy — John D. Smith
            </p>
          </CardHeader>
          <CardContent>
            <InvestigationTimeline />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ── cn helper ── //
import { cn } from "@/lib/utils";
