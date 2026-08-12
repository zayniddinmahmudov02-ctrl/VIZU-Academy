"use client";

import {
  ButtonHTMLAttributes,
  forwardRef,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import { Checkbox as BaseCheckbox } from "@base-ui/react/checkbox";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

// Standalone admin-only UI primitives, styled entirely against the
// `--admin-*` tokens in globals.css (`.admin-shell`). Deliberately does
// NOT import anything from components/ui/* — the Student Dashboard's
// primitives are themed for light/dark mode, not this fixed dark-premium
// palette, and the two surfaces must stay import-independent.

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--admin-primary)] text-white shadow-[0_1px_1px_rgba(0,0,0,0.15),0_8px_16px_-8px_rgba(91,91,248,0.5)] hover:bg-[var(--admin-primary-hover)]",
  secondary:
    "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-card-hover)]",
  ghost:
    "bg-transparent text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)] hover:text-[var(--admin-text-primary)]",
  danger:
    "bg-[var(--admin-danger)] text-white hover:brightness-110",
};

type AdminButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: "sm" | "md";
};

export const AdminButton = forwardRef<HTMLButtonElement, AdminButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50",
        size === "md" ? "h-10 px-4" : "h-8 px-3 text-xs",
        BUTTON_VARIANTS[variant],
        className,
      )}
      {...props}
    />
  ),
);
AdminButton.displayName = "AdminButton";

export const AdminInput = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-10 w-full rounded-lg bg-[var(--admin-card)] px-3.5 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)] transition placeholder:text-[var(--admin-text-muted)]",
      "focus:ring-2 focus:ring-[var(--admin-primary)]",
      className,
    )}
    {...props}
  />
));
AdminInput.displayName = "AdminInput";

export const AdminTextarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full resize-none rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)] transition placeholder:text-[var(--admin-text-muted)]",
      "focus:ring-2 focus:ring-[var(--admin-primary)]",
      className,
    )}
    {...props}
  />
));
AdminTextarea.displayName = "AdminTextarea";

type AdminSelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  children: ReactNode;
};

export const AdminSelect = forwardRef<HTMLSelectElement, AdminSelectProps>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          "h-10 w-full appearance-none rounded-lg bg-[var(--admin-card)] px-3.5 pr-9 text-sm text-[var(--admin-text-primary)] outline-none ring-1 ring-[var(--admin-border-strong)] transition",
          "focus:ring-2 focus:ring-[var(--admin-primary)]",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        size={15}
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]"
      />
    </div>
  ),
);
AdminSelect.displayName = "AdminSelect";

export function AdminLabel({
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn(
        "mb-1.5 block text-sm font-medium text-[var(--admin-text-primary)]",
        className,
      )}
      {...props}
    />
  );
}

interface AdminCheckboxProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  "aria-label"?: string;
}

export function AdminCheckbox({ checked, onCheckedChange, ...props }: AdminCheckboxProps) {
  return (
    <BaseCheckbox.Root
      checked={checked}
      onCheckedChange={onCheckedChange}
      {...props}
      className={cn(
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-[var(--admin-card)] ring-1 ring-[var(--admin-border-strong)] transition-all duration-150",
        "data-[checked]:bg-[var(--admin-primary)] data-[checked]:ring-[var(--admin-primary)]",
      )}
    >
      <BaseCheckbox.Indicator className="flex items-center justify-center text-white data-[unchecked]:hidden">
        <Check size={13} strokeWidth={3} />
      </BaseCheckbox.Indicator>
    </BaseCheckbox.Root>
  );
}

export function AdminCard({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function AdminPageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--admin-text-primary)]">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
