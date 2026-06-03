// ============================================================
// PaySentinelIQ — API Hooks (TanStack Query)
// Typed hooks for all domain endpoints with Zod validation
// ============================================================

import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from "@tanstack/react-query";
import { api, ApiClientError } from "@/lib/api";
import type {
  Payroll,
  FraudAlert,
  VerificationResult,
  ComplianceRecord,
  AIInsight,
  AuditLogEntry,
  Employee,
  Notification,
  PaginatedResponse,
} from "@/types";

// ============================================================
// Query Key Factory
// ============================================================

export const queryKeys = {
  payrolls: {
    all: ["payrolls"] as const,
    list: (params?: Record<string, unknown>) => ["payrolls", "list", params] as const,
    detail: (id: string) => ["payrolls", "detail", id] as const,
  },
  fraudAlerts: {
    all: ["fraud-alerts"] as const,
    list: (params?: Record<string, unknown>) => ["fraud-alerts", "list", params] as const,
    detail: (id: string) => ["fraud-alerts", "detail", id] as const,
    stats: ["fraud-alerts", "stats"] as const,
  },
  verifications: {
    all: ["verifications"] as const,
    detail: (id: string) => ["verifications", "detail", id] as const,
  },
  compliance: {
    all: ["compliance"] as const,
    list: (params?: Record<string, unknown>) => ["compliance", "list", params] as const,
    detail: (id: string) => ["compliance", "detail", id] as const,
  },
  aiInsights: {
    all: ["ai-insights"] as const,
    list: (params?: Record<string, unknown>) => ["ai-insights", "list", params] as const,
    feed: ["ai-insights", "feed"] as const,
  },
  auditLogs: {
    all: ["audit-logs"] as const,
    list: (params?: Record<string, unknown>) => ["audit-logs", "list", params] as const,
  },
  employees: {
    all: ["employees"] as const,
    list: (params?: Record<string, unknown>) => ["employees", "list", params] as const,
    detail: (id: string) => ["employees", "detail", id] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    list: ["notifications", "list"] as const,
    unreadCount: ["notifications", "unread-count"] as const,
  },
  dashboard: {
    kpis: ["dashboard", "kpis"] as const,
    trends: ["dashboard", "trends"] as const,
    heatmap: ["dashboard", "heatmap"] as const,
    riskDistribution: ["dashboard", "risk-distribution"] as const,
  },
};

// ============================================================
// Payroll Hooks
// ============================================================

export function usePayrolls(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.payrolls.list(params),
    queryFn: () => api.get<PaginatedResponse<Payroll>>("/payrolls", params as Record<string, string | number | boolean | undefined>),
  });
}

export function usePayroll(id: string) {
  return useQuery({
    queryKey: queryKeys.payrolls.detail(id),
    queryFn: () => api.get<Payroll>(`/payrolls/${id}`),
    enabled: !!id,
  });
}

export function useCreatePayroll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Payroll>) => api.post<Payroll>("/payrolls", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.payrolls.all });
    },
  });
}

export function useApprovePayroll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.patch<Payroll>(`/payrolls/${id}/approve`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.payrolls.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.payrolls.detail(id) });
    },
  });
}

// ============================================================
// Fraud Alert Hooks
// ============================================================

export function useFraudAlerts(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.fraudAlerts.list(params),
    queryFn: () => api.get<PaginatedResponse<FraudAlert>>("/fraud-alerts", params as Record<string, string | number | boolean | undefined>),
  });
}

export function useFraudAlert(id: string) {
  return useQuery({
    queryKey: queryKeys.fraudAlerts.detail(id),
    queryFn: () => api.get<FraudAlert>(`/fraud-alerts/${id}`),
    enabled: !!id,
  });
}

export function useFraudAlertStats() {
  return useQuery({
    queryKey: queryKeys.fraudAlerts.stats,
    queryFn: () => api.get<{
      total: number;
      new: number;
      under_review: number;
      escalated: number;
      confirmed: number;
      resolved: number;
    }>("/fraud-alerts/stats"),
    refetchInterval: 30_000, // Refetch every 30s for real-time feel
  });
}

export function useResolveFraudAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: string }) =>
      api.patch<FraudAlert>(`/fraud-alerts/${id}/resolve`, { resolution }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.fraudAlerts.all });
    },
  });
}

// ============================================================
// Verification Hooks
// ============================================================

export function useVerification(id: string) {
  return useQuery({
    queryKey: queryKeys.verifications.detail(id),
    queryFn: () => api.get<VerificationResult>(`/verifications/${id}`),
    enabled: !!id,
  });
}

export function useTriggerVerification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      api.post<VerificationResult>(`/verifications/trigger`, { document_id: documentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.verifications.all });
    },
  });
}

// ============================================================
// Compliance Hooks
// ============================================================

export function useComplianceRecords(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.compliance.list(params),
    queryFn: () => api.get<PaginatedResponse<ComplianceRecord>>("/compliance", params as Record<string, string | number | boolean | undefined>),
  });
}

export function useComplianceRecord(id: string) {
  return useQuery({
    queryKey: queryKeys.compliance.detail(id),
    queryFn: () => api.get<ComplianceRecord>(`/compliance/${id}`),
    enabled: !!id,
  });
}

// ============================================================
// AI Insights Hooks
// ============================================================

export function useAIInsights(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.aiInsights.list(params),
    queryFn: () => api.get<PaginatedResponse<AIInsight>>("/ai-insights", params as Record<string, string | number | boolean | undefined>),
    refetchInterval: 60_000,
  });
}

export function useAIInsightFeed() {
  return useQuery({
    queryKey: queryKeys.aiInsights.feed,
    queryFn: () => api.get<AIInsight[]>("/ai-insights/feed"),
    refetchInterval: 15_000, // Live feed every 15s
  });
}

// ============================================================
// Audit Log Hooks
// ============================================================

export function useAuditLogs(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.auditLogs.list(params),
    queryFn: () => api.get<PaginatedResponse<AuditLogEntry>>("/audit-logs", params as Record<string, string | number | boolean | undefined>),
  });
}

// ============================================================
// Employee Hooks
// ============================================================

export function useEmployees(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: queryKeys.employees.list(params),
    queryFn: () => api.get<PaginatedResponse<Employee>>("/employees", params as Record<string, string | number | boolean | undefined>),
  });
}

export function useEmployee(id: string) {
  return useQuery({
    queryKey: queryKeys.employees.detail(id),
    queryFn: () => api.get<Employee>(`/employees/${id}`),
    enabled: !!id,
  });
}

// ============================================================
// Notification Hooks
// ============================================================

export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.notifications.list,
    queryFn: () => api.get<PaginatedResponse<Notification>>("/notifications"),
    refetchInterval: 30_000,
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: queryKeys.notifications.unreadCount,
    queryFn: () => api.get<{ count: number }>("/notifications/unread-count"),
    refetchInterval: 15_000,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.patch(`/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

// ============================================================
// Dashboard Hooks
// ============================================================

export function useDashboardKpis() {
  return useQuery({
    queryKey: queryKeys.dashboard.kpis,
    queryFn: () =>
      api.get<{
        payrolls_processed: number;
        verification_rate: number;
        fraud_alerts: number;
        ai_confidence: number;
        high_risk_docs: number;
        compliance_incidents: number;
      }>("/dashboard/kpis"),
    refetchInterval: 30_000,
  });
}

export function useDashboardTrends() {
  return useQuery({
    queryKey: queryKeys.dashboard.trends,
    queryFn: () =>
      api.get<Array<{ month: string; volume: number; verified: number; flagged: number; passRate: number }>>(
        "/dashboard/trends"
      ),
    refetchInterval: 60_000,
  });
}

export function useDashboardHeatmap() {
  return useQuery({
    queryKey: queryKeys.dashboard.heatmap,
    queryFn: () =>
      api.get<
        Array<{
          name: string;
          payrolls: number;
          riskScore: number;
          flaggedCount: number;
          riskLevel: string;
        }>
      >("/dashboard/heatmap"),
    refetchInterval: 60_000,
  });
}

export function useDashboardRiskDistribution() {
  return useQuery({
    queryKey: queryKeys.dashboard.riskDistribution,
    queryFn: () =>
      api.get<
        Array<{
          range: string;
          count: number;
          color: string;
        }>
      >("/dashboard/risk-distribution"),
    refetchInterval: 120_000,
  });
}

// ============================================================
// Auth Hooks (placeholder — hook up to FastAPI auth)
// ============================================================

import { useAuthStore } from "@/stores";

export function useLogin() {
  const login = useAuthStore((s) => s.login);

  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      api.post<{ user: import("@/types").User; token: string }>("/auth/login", credentials),
    onSuccess: (data) => {
      login(data.user, data.token);
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);

  return useMutation({
    mutationFn: () => api.post("/auth/logout"),
    onSettled: () => {
      logout();
    },
  });
}
