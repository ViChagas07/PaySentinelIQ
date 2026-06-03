// ============================================================
// PaySentinelIQ — Zustand Global State Stores
// ============================================================

import { create } from "zustand";
import type { User, Tenant, FraudAlert, Notification } from "@/types";

// ── Auth Store ── //

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  login: (user, token) =>
    set({ user, token, isAuthenticated: true, isLoading: false }),
  logout: () =>
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    }),
  setLoading: (isLoading) => set({ isLoading }),
}));

// ── Tenant Store ── //

interface TenantStore {
  currentTenant: Tenant | null;
  availableTenants: Tenant[];
  setCurrentTenant: (tenant: Tenant) => void;
  setAvailableTenants: (tenants: Tenant[]) => void;
}

export const useTenantStore = create<TenantStore>((set) => ({
  currentTenant: null,
  availableTenants: [],
  setCurrentTenant: (currentTenant) => set({ currentTenant }),
  setAvailableTenants: (availableTenants) => set({ availableTenants }),
}));

// ── Alert / Notification Store ── //

interface AlertStore {
  alerts: FraudAlert[];
  unreadCount: number;
  notifications: Notification[];
  setAlerts: (alerts: FraudAlert[]) => void;
  addAlert: (alert: FraudAlert) => void;
  markAlertRead: (id: string) => void;
  setNotifications: (notifications: Notification[]) => void;
  addNotification: (notification: Notification) => void;
  markNotificationRead: (id: string) => void;
  dismissAlert: (id: string) => void;
}

export const useAlertStore = create<AlertStore>((set, get) => ({
  alerts: [],
  unreadCount: 0,
  notifications: [],
  setAlerts: (alerts) => set({ alerts, unreadCount: alerts.filter((a) => a.status === "new").length }),
  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts],
      unreadCount: state.unreadCount + 1,
    })),
  markAlertRead: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, status: "under_review" as const } : a
      ),
    })),
  setNotifications: (notifications) => set({ notifications }),
  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications],
    })),
  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n
      ),
    })),
  dismissAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.filter((a) => a.id !== id),
      unreadCount: state.alerts.filter((a) => a.id !== id && a.status === "new").length,
    })),
}));

// ── UI State Store ── //

interface UIStore {
  sidebarCollapsed: boolean;
  sidebarMobileOpen: boolean;
  aiPanelOpen: boolean;
  notificationsPanelOpen: boolean;
  toggleSidebar: () => void;
  setSidebarMobileOpen: (open: boolean) => void;
  toggleAiPanel: () => void;
  toggleNotificationsPanel: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  sidebarMobileOpen: false,
  aiPanelOpen: false,
  notificationsPanelOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarMobileOpen: (open) => set({ sidebarMobileOpen: open }),
  toggleAiPanel: () => set((s) => ({ aiPanelOpen: !s.aiPanelOpen })),
  toggleNotificationsPanel: () => set((s) => ({ notificationsPanelOpen: !s.notificationsPanelOpen })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
}));
