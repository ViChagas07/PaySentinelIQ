// ============================================================
// PaySentinelIQ — Error Boundary
// Graceful error handling for data-fetching components
// ============================================================

"use client";

import { Component, type ReactNode } from "react";
import { useTranslations } from "next-intl";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

// ── Translation map type (for class component compatibility) ──

interface ErrorBoundaryTranslations {
  boundary: {
    title: string;
    description: string;
    help: string;
    refreshPage: string;
    tryAgain: string;
    loadDataTitle: string;
    loadDataDescription: string;
    loadDataHelp: string;
  };
  tryAgain: string;
}
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onRetry?: () => void;
  /** Translations injected by the wrapper */
  t?: ErrorBoundaryTranslations;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryClass extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry?.();
  };

  private errorRef: HTMLDivElement | null = null;

  componentDidUpdate(_prevProps: ErrorBoundaryProps, prevState: ErrorBoundaryState) {
    if (!prevState.hasError && this.state.hasError && this.errorRef) {
      this.errorRef.focus();
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      const tb = this.props.t?.boundary;

      return (
        <div ref={(el) => { this.errorRef = el; }} tabIndex={-1} className="focus:outline-none">
        <Card variant="alert" role="alert" aria-live="assertive">
          <CardContent className="flex flex-col items-center py-12 text-center">
            <div className="mb-4 rounded-2xl bg-psi-fraud/10 p-4">
              <AlertTriangle className="h-8 w-8 text-psi-fraud" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-semibold text-psi-text-primary mb-2" id="error-title">
              {tb?.title ?? "Something went wrong"}
            </h3>
            <p className="text-sm text-psi-text-secondary max-w-md mb-1">
              {this.state.error?.message || tb?.description || "An unexpected error occurred."}
            </p>
            <p className="text-xs text-psi-text-secondary/60 mb-6">
              {tb?.help ?? "The error has been logged. Try refreshing the page or contact support."}
            </p>
            <div className="flex gap-3">
              <Button variant="outline" size="sm" onClick={() => window.location.reload()} aria-label={tb?.refreshPage}>
                <RefreshCw className="h-4 w-4 mr-1" aria-hidden="true" />
                {tb?.refreshPage ?? "Refresh Page"}
              </Button>
              <Button variant="primary" size="sm" onClick={this.handleRetry} aria-label={tb?.tryAgain}>
                {tb?.tryAgain ?? "Try Again"}
              </Button>
            </div>
          </CardContent>
        </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// ── Wrapper that injects translations ──

export function ErrorBoundary(props: Omit<ErrorBoundaryProps, "t">) {
  const t = useTranslations("errors");
  const translations: ErrorBoundaryTranslations = {
    boundary: {
      title: t("boundary.title"),
      description: t("boundary.description"),
      help: t("boundary.help"),
      refreshPage: t("boundary.refreshPage"),
      tryAgain: t("boundary.tryAgain"),
      loadDataTitle: t("boundary.loadDataTitle"),
      loadDataDescription: t("boundary.loadDataDescription"),
      loadDataHelp: t("boundary.loadDataHelp"),
    },
    tryAgain: t("tryAgain"),
  };
  return <ErrorBoundaryClass {...props} t={translations} />;
}

// ── Functional fallback (translated) ──

interface ErrorFallbackProps {
  error: Error | null;
  onRetry?: () => void;
}

export function ErrorFallback({ error, onRetry }: ErrorFallbackProps) {
  const t = useTranslations("errors");

  return (
    <Card variant="alert" role="alert" aria-live="assertive">
      <CardContent className="flex flex-col items-center py-12 text-center">
        <div className="mb-4 rounded-2xl bg-psi-fraud/10 p-4">
          <AlertTriangle className="h-8 w-8 text-psi-fraud" aria-hidden="true" />
        </div>
        <h3 className="text-lg font-semibold text-psi-text-primary mb-2">
          {t("boundary.loadDataTitle")}
        </h3>
        <p className="text-sm text-psi-text-secondary max-w-md mb-1">
          {error?.message || t("boundary.loadDataDescription")}
        </p>
        <p className="text-xs text-psi-text-secondary/60 mb-6">
          {t("boundary.loadDataHelp")}
        </p>
        {onRetry && (
          <Button variant="primary" size="sm" onClick={onRetry}>
            <RefreshCw className="h-4 w-4 mr-1" />
            {t("tryAgain")}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
