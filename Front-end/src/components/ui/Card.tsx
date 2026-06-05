// ============================================================
// PaySentinelIQ — Card Component (Glassmorphism Edition)
// Premium glass cards with subtle aura glow and hover effects
// ============================================================

import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "interactive" | "alert";
  glow?: boolean;
  glass?: boolean; // Enhanced glassmorphism variant
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", glow, glass, children, ...props }, ref) => {
    const isInteractive = variant === "interactive";

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border p-6 transition-all duration-300",
          // Glassmorphism base — applies to all variants for a cohesive look
          "bg-psi-graphite/70 backdrop-blur-xl border-white/[0.06] shadow-lg shadow-black/20",
          {
            // Default: glass card with subtle backdrop blur
            "bg-psi-graphite/70": variant === "default",
            // Interactive: subtle lift on hover with glow border
            "bg-psi-graphite/70 cursor-pointer card-aura-hover border-white/[0.06]":
              isInteractive,
            // Alert: maintains glass but with fraud-colored border
            "bg-psi-graphite/70 border-psi-fraud/30": variant === "alert",
          },
          // Enhanced glassmorphism override
          glass && "glass-card-strong",
          // Glow prop adds initial subtle aura shadow
          glow && "aura-glow-blue",
          // Specific hover for interactive variant
          isInteractive && "hover:border-psi-electric/25 hover:shadow-lg hover:shadow-psi-electric/8",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

// ── Card sub-components ── //

function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 pb-4", className)}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-lg font-semibold text-psi-text-primary leading-tight", className)}
      {...props}
    />
  );
}

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-psi-text-secondary", className)}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("", className)} {...props} />;
}

function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center gap-3 pt-4 border-t border-psi-border mt-4", className)}
      {...props}
    />
  );
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
