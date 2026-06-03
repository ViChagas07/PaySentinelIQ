// ============================================================
// PaySentinelIQ — Badge Component
// ============================================================

import { forwardRef, type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "border-psi-border bg-psi-border/50 text-psi-text-secondary",
        primary:
          "border-psi-electric/30 bg-psi-electric/10 text-psi-electric",
        success:
          "border-psi-emerald/30 bg-psi-emerald/10 text-psi-emerald",
        warning:
          "border-psi-warning/30 bg-psi-warning/10 text-psi-warning",
        destructive:
          "border-psi-fraud/30 bg-psi-fraud/10 text-psi-fraud animate-pulse-alert",
        outline:
          "border-psi-border bg-transparent text-psi-text-secondary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, dot, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(badgeVariants({ variant }), className)}
        {...props}
      >
        {dot && (
          <span
            className={cn("h-1.5 w-1.5 rounded-full", {
              "bg-psi-electric": variant === "primary",
              "bg-psi-emerald": variant === "success",
              "bg-psi-warning": variant === "warning",
              "bg-psi-fraud": variant === "destructive",
              "bg-psi-text-secondary": variant === "default" || variant === "outline",
            })}
          />
        )}
        {children}
      </div>
    );
  }
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
