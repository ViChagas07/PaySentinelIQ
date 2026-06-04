// ============================================================
// PaySentinelIQ — Sidebar Navigation
// Enterprise RBAC-aware sidebar with nested sections
// ============================================================

"use client";

import { useState, useMemo } from "react";
import { Link, usePathname } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useUIStore, useAuthStore } from "@/stores";
import type { UserRole } from "@/types";
import { AppName } from "@/components/shared/AppName";
import Image from "next/image";
import {
  LayoutDashboard,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Scale,
  Brain,
  DollarSign,
  FileSearch,
  FileBarChart,
  Users,
  Building2,
  ScrollText,
  Bell,
  Settings,
  ChevronDown,
  ScanLine,
  Barcode,
  type LucideIcon,
} from "lucide-react";

// ── Navigation Item Types ── //

interface NavItem {
  /** Translation key from the "nav" namespace */
  labelKey: string;
  href: string;
  icon: LucideIcon;
  roles: UserRole[];
  badge?: string;
  badgeVariant?: "primary" | "success" | "warning" | "destructive";
  children?: NavItem[];
}

interface NavSection {
  /** Translation key from the "nav" namespace (e.g. "sections.core") */
  sectionKey: string;
  items: NavItem[];
}

// ── Navigation Configuration (keys reference "nav" namespace in translations) ── //

const navigationSections: NavSection[] = [
  {
    sectionKey: "sections.core",
    items: [
      {
        labelKey: "dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager", "payroll_specialist", "auditor", "viewer"],
      },
      {
        labelKey: "payroll",
        href: "/payroll",
        icon: DollarSign,
        roles: ["admin", "hr_manager", "payroll_specialist"],
      },
    ],
  },
  {
    sectionKey: "sections.intelligence",
    items: [
      {
        labelKey: "verification",
        href: "/verification-center",
        icon: ShieldCheck,
        roles: ["admin", "fraud_analyst", "compliance_officer"],
        badge: "AI",
        badgeVariant: "primary",
      },
      {
        labelKey: "fraudIntelligence",
        href: "/fraud-intelligence",
        icon: AlertTriangle,
        roles: ["admin", "fraud_analyst", "auditor"],
        badge: "3",
        badgeVariant: "destructive",
      },
      {
        labelKey: "compliance",
        href: "/compliance",
        icon: Scale,
        roles: ["admin", "compliance_officer", "auditor"],
      },
      {
        labelKey: "aiInsights",
        href: "/ai-insights",
        icon: Brain,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager"],
        badge: "New",
        badgeVariant: "success",
      },
    ],
  },
  {
    sectionKey: "sections.analysis",
    items: [
      {
        labelKey: "documentAnalysis",
        href: "/documents",
        icon: FileSearch,
        roles: ["admin", "fraud_analyst", "compliance_officer"],
      },
      {
        labelKey: "analyzePayroll",
        href: "/dashboard/analyze-payroll",
        icon: FileText,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager", "payroll_specialist", "auditor", "viewer"],
        badge: "AI",
        badgeVariant: "primary",
      },
      {
        labelKey: "analyzeBankSlip",
        href: "/dashboard/analyze-bank-slip",
        icon: Barcode,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager", "payroll_specialist", "auditor", "viewer"],
        badge: "AI",
        badgeVariant: "warning",
      },
      {
        labelKey: "reports",
        href: "/reports",
        icon: FileBarChart,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager", "auditor"],
      },
      {
        labelKey: "auditLogs",
        href: "/audit-logs",
        icon: ScrollText,
        roles: ["admin", "auditor", "compliance_officer"],
      },
    ],
  },
  {
    sectionKey: "sections.data",
    items: [
      {
        labelKey: "employees",
        href: "/employees",
        icon: Users,
        roles: ["admin", "hr_manager", "payroll_specialist"],
      },
      {
        labelKey: "companies",
        href: "/companies",
        icon: Building2,
        roles: ["admin", "auditor"],
      },
    ],
  },
  {
    sectionKey: "sections.system",
    items: [
      {
        labelKey: "notifications",
        href: "/notifications",
        icon: Bell,
        roles: ["admin", "fraud_analyst", "compliance_officer", "hr_manager", "payroll_specialist", "auditor", "viewer"],
        badge: "5",
        badgeVariant: "warning",
      },
      {
        labelKey: "settings",
        href: "/settings",
        icon: Settings,
        roles: ["admin"],
      },
    ],
  },
];

// ── Sidebar Component ── //

export function Sidebar() {
  const t = useTranslations("nav");
  const tc = useTranslations("common");
  const pathname = usePathname();
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const sidebarMobileOpen = useUIStore((s) => s.sidebarMobileOpen);
  const setSidebarMobileOpen = useUIStore((s) => s.setSidebarMobileOpen);
  const user = useAuthStore((s) => s.user);

  // Filter nav items based on user role — memoized
  // Guests (user=null) see viewer-level items only
  const filteredSections = useMemo(
    () =>
      navigationSections
        .map((section) => ({
          ...section,
          items: section.items.filter(
            (item) => user ? item.roles.includes(user.role) : item.roles.includes("viewer")
          ),
        }))
        .filter((section) => section.items.length > 0),
    [user?.role, user]
  );

  return (
    <>
      {/* Mobile overlay */}
      {sidebarMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-background transition-all duration-300 lg:relative",
          sidebarCollapsed ? "w-[72px]" : "w-64",
          sidebarMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        aria-label={t("sidebarLabel")}
      >
        {/* Logo — clickable, navigates to dashboard */}
        <Link
          href="/dashboard"
          onClick={() => setSidebarMobileOpen(false)}
          className={cn(
            "flex h-16 items-center border-b border-border transition-opacity hover:opacity-80",
            sidebarCollapsed ? "justify-center px-2" : "gap-3 px-4"
          )}
          aria-label={t("goToDashboard")}
        >
          <Image
            src="/PSI_Logo2.png"
            alt={tc("appName")}
            width={sidebarCollapsed ? 56 : 56}
            height={sidebarCollapsed ? 56 : 56}
            className={cn(
              "shrink-0 object-contain",
              sidebarCollapsed ? "h-14 w-14" : "h-14 w-auto"
            )}
            priority
          />
          {!sidebarCollapsed && (
            <div className="flex flex-col min-w-0">
              <AppName as="span" className="text-sm text-psi-text-primary truncate" />
              <span className="text-[10px] font-medium uppercase tracking-[0.2em] text-psi-text-secondary">
                {t("tagline")}
              </span>
            </div>
          )}
        </Link>

        {/* Nav items — flat list, no section headers */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          <ul className="space-y-0.5">
            {filteredSections.flatMap((section) => section.items).map((item) => (
              <SidebarItem
                key={item.href}
                item={item}
                label={t(item.labelKey as any)}
                isActive={pathname === item.href || pathname.startsWith(item.href + "/")}
                collapsed={sidebarCollapsed}
              />
            ))}
          </ul>
        </nav>


      </aside>
    </>
  );
}

// ── Sidebar Item ── //

function SidebarItem({
  item,
  label,
  isActive,
  collapsed,
}: {
  item: NavItem;
  label: string;
  isActive: boolean;
  collapsed: boolean;
}) {
  const t = useTranslations("nav");
  const [isOpen, setIsOpen] = useState(false);
  const hasChildren = item.children && item.children.length > 0;

  const Icon = item.icon;

  // Determine badge color class
  const badgeColorClass = {
    primary: "bg-psi-electric/15 text-psi-electric border-psi-electric/30",
    success: "bg-psi-emerald/15 text-psi-emerald border-psi-emerald/30",
    warning: "bg-psi-warning/15 text-psi-warning border-psi-warning/30",
    destructive: "bg-psi-fraud/15 text-psi-fraud border-psi-fraud/30",
  };

  if (hasChildren) {
    return (
      <li>
        <button
          onClick={() => collapsed || setIsOpen(!isOpen)}
          className={cn(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
            isActive
              ? "bg-psi-electric/10 text-psi-electric"
              : "text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary"
          )}
          aria-expanded={isOpen}
        >
          <Icon
            className={cn(
              "h-5 w-5 shrink-0",
              isActive ? "text-psi-electric" : "text-psi-text-secondary"
            )}
          />
          {!collapsed && (
            <>
              <span className="flex-1 text-left">{label}</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  isOpen && "rotate-180"
                )}
              />
            </>
          )}
        </button>
        {!collapsed && (
          <AnimatePresence>
            {isOpen && (
              <motion.ul
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="ml-9 mt-1 space-y-0.5 overflow-hidden"
              >
                {item.children!.map((child) => (
                  <li key={child.href}>
                    <Link
                      href={child.href}
                      className="block rounded-lg px-3 py-2 text-sm text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary transition-colors"
                    >
                      {t(child.labelKey)}
                    </Link>
                  </li>
                ))}
              </motion.ul>
            )}
          </AnimatePresence>
        )}
      </li>
    );
  }

  return (
    <li>
      <Link
        href={item.href}
        className={cn(
          "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
          isActive
            ? "bg-psi-electric/10 text-psi-electric"
            : "text-psi-text-secondary hover:bg-psi-border/30 hover:text-psi-text-primary"
        )}
        aria-current={isActive ? "page" : undefined}
        title={collapsed ? label : undefined}
      >
        {/* Active indicator bar */}
        {isActive && (
          <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-0.5 rounded-r-full bg-psi-electric" />
        )}

        <Icon
          className={cn(
            "h-5 w-5 shrink-0 transition-colors",
            isActive ? "text-psi-electric" : "text-psi-text-secondary group-hover:text-psi-text-primary"
          )}
        />

        {!collapsed && (
          <span className="flex-1 text-left">{label}</span>
        )}

        {!collapsed && item.badge && (
          <span
            className={cn(
              "rounded-md border px-1.5 py-0.5 text-[10px] font-bold leading-none",
              badgeColorClass[item.badgeVariant || "primary"]
            )}
          >
            {item.badge}
          </span>
        )}

        {/* Collapsed badge dot */}
        {collapsed && item.badge && item.badgeVariant === "destructive" && (
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-psi-fraud animate-pulse-alert" />
        )}
      </Link>
    </li>
  );
}
