"use client";

import { Checkbox as BaseCheckbox } from "@base-ui/react/checkbox";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

interface Props {
  checked?: boolean;
  defaultChecked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  id?: string;
  name?: string;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
}

export default function Checkbox({ className, ...props }: Props) {
  return (
    <BaseCheckbox.Root
      {...props}
      className={cn(
        "flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-surface-card ring-1 ring-surface-border transition-all duration-150",
        "data-[checked]:bg-gradient-to-b data-[checked]:from-accent-blue-hover data-[checked]:to-accent-blue data-[checked]:ring-accent-blue",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    >
      <BaseCheckbox.Indicator className="flex items-center justify-center text-white data-[unchecked]:hidden">
        <Check size={13} strokeWidth={3} />
      </BaseCheckbox.Indicator>
    </BaseCheckbox.Root>
  );
}
