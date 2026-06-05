// ============================================================
// PaySentinelIQ — Button Component
// ============================================================

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-psi-electric focus-visible:ring-offset-2 focus-visible:ring-offset-psi-navy disabled:pointer-events-none disabled:opacity-50 btn-aura",
  {
    variants: {
      variant: {
        primary:
          "bg-psi-electric text-white shadow-lg shadow-psi-electric/20 hover:bg-psi-electric/90 hover:shadow-xl hover:shadow-psi-electric/30 active:scale-[0.97] hover:scale-[1.02]",
        secondary:
          "bg-psi-border text-psi-text-primary hover:bg-psi-border/80 active:scale-[0.97] hover:scale-[1.02]",
        destructive:
          "bg-psi-fraud text-white shadow-lg shadow-psi-fraud/20 hover:bg-psi-fraud/90 active:scale-[0.97] hover:scale-[1.02]",
        success:
          "bg-psi-emerald text-white shadow-lg shadow-psi-emerald/20 hover:bg-psi-emerald/90 active:scale-[0.97] hover:scale-[1.02]",
        outline:
          "border border-psi-border/50 bg-transparent text-psi-text-primary hover:bg-white/[0.04] hover:border-psi-electric/30 active:scale-[0.97] hover:scale-[1.02]",
        ghost:
          "bg-transparent text-psi-text-secondary hover:bg-white/[0.04] hover:text-psi-text-primary",
        link: "bg-transparent text-psi-electric underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-lg",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, disabled, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
