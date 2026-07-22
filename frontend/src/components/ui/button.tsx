import { ButtonHTMLAttributes, forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-button text-sm font-semibold transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40",
  {
    variants: {
      variant: {
        primary:
          "bg-gradient-to-b from-accent-blue-hover to-accent-blue text-white shadow-md shadow-accent-blue/25 hover:shadow-lg hover:shadow-accent-blue/30 hover:-translate-y-px active:translate-y-0",
        secondary:
          "bg-surface-card text-text-primary shadow-sm ring-1 ring-surface-border hover:bg-surface-hover",
        ghost:
          "bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text-primary",
        danger:
          "bg-danger text-white shadow-sm shadow-danger/30 hover:brightness-110",
      },
      size: {
        sm: "h-9 px-3.5 text-xs",
        md: "h-11 px-5",
        lg: "h-13 px-7 text-base",
      },
      fullWidth: {
        true: "w-full",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

type Props = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant, size, fullWidth, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, fullWidth }), className)}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";

export default Button;
