import { forwardRef, InputHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  error?: boolean;
};

const Input = forwardRef<HTMLInputElement, Props>(
  ({ className, error, ...props }, ref) => {
    return (
      <input
        ref={ref}
        {...props}
        className={cn(
          "h-11 w-full rounded-input bg-surface-card px-4 text-sm text-text-primary shadow-sm ring-1 ring-surface-border outline-none transition-all duration-200 placeholder:text-text-muted",
          "focus:ring-2 focus:ring-accent-blue/50",
          error && "ring-2 ring-danger/60",
          className,
        )}
      />
    );
  },
);

Input.displayName = "Input";

export default Input;

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  error?: boolean;
};

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        {...props}
        className={cn(
          "w-full resize-none rounded-input bg-surface-card px-4 py-3 text-sm text-text-primary shadow-sm ring-1 ring-surface-border outline-none transition-all duration-200 placeholder:text-text-muted",
          "focus:ring-2 focus:ring-accent-blue/50",
          error && "ring-2 ring-danger/60",
          className,
        )}
      />
    );
  },
);

Textarea.displayName = "Textarea";
