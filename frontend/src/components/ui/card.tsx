import { HTMLAttributes, forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const cardVariants = cva("rounded-card transition-shadow duration-200", {
  variants: {
    variant: {
      default: "bg-surface-card shadow-[var(--shadow-md)] ring-1 ring-surface-border",
      elevated: "bg-surface-card shadow-[var(--shadow-lg)] ring-1 ring-surface-border",
      outline: "bg-transparent ring-1 ring-surface-border",
      gradient:
        "bg-gradient-to-br from-accent-blue to-purple-600 text-white shadow-[var(--shadow-lg)] shadow-accent-blue/20",
    },
    padding: {
      none: "",
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    },
  },
  defaultVariants: {
    variant: "default",
    padding: "lg",
  },
});

type Props = HTMLAttributes<HTMLDivElement> & VariantProps<typeof cardVariants>;

const Card = forwardRef<HTMLDivElement, Props>(
  ({ className, variant, padding, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(cardVariants({ variant, padding }), className)}
        {...props}
      />
    );
  },
);

Card.displayName = "Card";

export default Card;
