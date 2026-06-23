// ============================================================
// PaySentinelIQ — RealtimeNotificationToast Component Tests
// ============================================================

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RealtimeNotificationToast } from "@/components/notifications/RealtimeNotificationToast";
import type { Notification } from "@/types";

// ── Mock next/navigation ──

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

// ── Helpers ──

function makeNotification(
  overrides: Partial<Notification> = {},
): Notification {
  return {
    id: "test-notif-1",
    user_id: "user-1",
    tenant_id: "tenant-1",
    type: "system",
    title: "Test Title",
    message: "This is a test notification message with enough detail.",
    severity: "normal",
    is_read: false,
    action_url: null,
    metadata: {},
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Suite ──

describe("RealtimeNotificationToast", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Rendering ──

  it("should render the notification title and message", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification()} />,
    );

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This is a test notification message with enough detail.",
      ),
    ).toBeInTheDocument();
  });

  it("should render the type label (System) for system notifications", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "system" })} />,
    );

    expect(screen.getByText("System")).toBeInTheDocument();
  });

  it("should render the type label (Fraud Alert) for fraud_alert notifications", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "fraud_alert" })} />,
    );

    expect(screen.getByText("Fraud Alert")).toBeInTheDocument();
  });

  it("should render the type label (Payment) for payment notifications", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "payment" })} />,
    );

    expect(screen.getByText("Payment")).toBeInTheDocument();
  });

  it("should render the type label (Verification) for verification_complete", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "verification_complete" })} />,
    );

    expect(screen.getByText("Verification")).toBeInTheDocument();
  });

  it("should render the type label (Compliance) for compliance_alert", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "compliance_alert" })} />,
    );

    expect(screen.getByText("Compliance")).toBeInTheDocument();
  });

  it("should render the type label (Document) for document_event", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "document_event" })} />,
    );

    expect(screen.getByText("Document")).toBeInTheDocument();
  });

  it("should render the type label (AI Insight) for ai_insight", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "ai_insight" })} />,
    );

    expect(screen.getByText("AI Insight")).toBeInTheDocument();
  });

  it("should render the type label (Critical Alert) for critical", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "critical" })} />,
    );

    expect(screen.getByText("Critical Alert")).toBeInTheDocument();
  });

  it('should render "View details" action hint', () => {
    render(
      <RealtimeNotificationToast notification={makeNotification()} />,
    );

    expect(screen.getByText("View details")).toBeInTheDocument();
  });

  // ── Deep linking ──

  it("should navigate to action_url when clicked", async () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          action_url: "/fraud-alerts/details-123",
        })}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));

    expect(mockPush).toHaveBeenCalledWith("/fraud-alerts/details-123");
  });

  it("should navigate to default route when no action_url is provided", async () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          type: "payment",
          action_url: null,
        })}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));

    expect(mockPush).toHaveBeenCalledWith("/payments");
  });

  it("should navigate to /fraud-alerts for fraud_alert type", async () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          type: "fraud_alert",
          action_url: null,
        })}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));

    expect(mockPush).toHaveBeenCalledWith("/fraud-alerts");
  });

  it("should navigate to /notifications for unknown types", async () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          type: "unknown" as Notification["type"],
          action_url: null,
        })}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button"));

    expect(mockPush).toHaveBeenCalledWith("/notifications");
  });

  it("should navigate on Enter key press", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "critical" })} />,
    );

    const toast = screen.getByRole("button");
    fireEvent.keyDown(toast, { key: "Enter" });

    expect(mockPush).toHaveBeenCalledWith("/fraud-alerts");
  });

  it("should navigate on Space key press", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification({ type: "critical" })} />,
    );

    const toast = screen.getByRole("button");
    fireEvent.keyDown(toast, { key: " " });

    expect(mockPush).toHaveBeenCalledWith("/fraud-alerts");
  });

  // ── Dismiss button ──

  it("should call onDismiss when close button is clicked", async () => {
    const onDismiss = vi.fn();

    render(
      <RealtimeNotificationToast
        notification={makeNotification()}
        onDismiss={onDismiss}
      />,
    );

    const user = userEvent.setup();
    const dismissButton = screen.getByLabelText("Dismiss notification");
    await user.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("should not render dismiss button when onDismiss is not provided", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification()} />,
    );

    expect(screen.queryByLabelText("Dismiss notification")).toBeNull();
  });

  // ── Accessibility ──

  it("should have a correct ARIA label", () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          type: "fraud_alert",
          title: "Suspicious Transaction",
        })}
      />,
    );

    const toast = screen.getByRole("button");
    expect(toast).toHaveAttribute(
      "aria-label",
      "Fraud Alert: Suspicious Transaction. Click to view details.",
    );
  });

  it("should be focusable", () => {
    render(
      <RealtimeNotificationToast notification={makeNotification()} />,
    );

    const toast = screen.getByRole("button");
    toast.focus();
    expect(toast).toHaveFocus();
  });

  // ── Long content ──

  it("should truncate long titles with line-clamp", () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          title: "A very long title that should be truncated after one line because it really goes on and on",
        })}
      />,
    );

    const title = screen.getByText(
      "A very long title that should be truncated after one line because it really goes on and on",
    );
    expect(title).toBeInTheDocument();
    expect(title.className).toContain("line-clamp-1");
  });

  it("should truncate long messages with line-clamp-2", () => {
    render(
      <RealtimeNotificationToast
        notification={makeNotification({
          message:
            "This is a very long message that should be clamped to two lines maximum. It goes on and on with many more details that would be too long to fit in the toast preview space.",
        })}
      />,
    );

    const msg = screen.getByText(
      "This is a very long message that should be clamped to two lines maximum. It goes on and on with many more details that would be too long to fit in the toast preview space.",
    );
    expect(msg.className).toContain("line-clamp-2");
  });
});
