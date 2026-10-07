"use client";

import { useEffect, useRef } from "react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

const LENGTH = 6;

interface Props {
  value: string;
  onChange: (value: string) => void;
  onComplete?: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
  autoFocus?: boolean;
}

/** 6-digit code input: one box per digit, digits only, paste of a whole
 * code, backspace/arrow navigation, numeric keyboard on phones and
 * one-time-code autofill. The value lives only in the parent's state. */
export default function OtpInput({ value, onChange, onComplete, disabled, error, autoFocus = true }: Props) {
  const { t } = useTranslation();
  const refs = useRef<(HTMLInputElement | null)[]>([]);
  const digits = Array.from({ length: LENGTH }, (_, i) => value[i] ?? "");

  useEffect(() => {
    if (autoFocus) refs.current[0]?.focus();
  }, [autoFocus]);

  function update(next: string, focusIndex: number) {
    const clean = next.replace(/\D/g, "").slice(0, LENGTH);
    onChange(clean);
    refs.current[Math.min(focusIndex, LENGTH - 1)]?.focus();
    if (clean.length === LENGTH) onComplete?.(clean);
  }

  function handleInput(index: number, raw: string) {
    const typed = raw.replace(/\D/g, "");
    if (!typed) return;
    if (typed.length > 1) {
      // autofill / paste into one box
      update(value.slice(0, index) + typed, index + typed.length);
      return;
    }
    const chars = digits.slice();
    chars[index] = typed;
    update(chars.join("").slice(0, LENGTH), index + 1);
  }

  function handleKeyDown(index: number, event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Backspace") {
      event.preventDefault();
      const chars = digits.slice();
      if (chars[index]) {
        chars[index] = "";
        onChange(chars.join("").replace(/\s/g, ""));
        return;
      }
      if (index > 0) {
        chars[index - 1] = "";
        onChange(chars.join("").replace(/\s/g, ""));
        refs.current[index - 1]?.focus();
      }
    } else if (event.key === "ArrowLeft" && index > 0) {
      refs.current[index - 1]?.focus();
    } else if (event.key === "ArrowRight" && index < LENGTH - 1) {
      refs.current[index + 1]?.focus();
    }
  }

  function handlePaste(event: React.ClipboardEvent<HTMLInputElement>) {
    const pasted = event.clipboardData.getData("text").replace(/\D/g, "");
    if (!pasted) return;
    event.preventDefault();
    update(pasted, pasted.length);
  }

  return (
    <div className="flex justify-center gap-2 sm:gap-2.5" role="group" aria-label={t("auth.codeLabel")}>
      {digits.map((digit, i) => (
        <input
          key={i}
          ref={(el) => {
            refs.current[i] = el;
          }}
          value={digit}
          onChange={(e) => handleInput(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onPaste={handlePaste}
          onFocus={(e) => e.target.select()}
          disabled={disabled}
          inputMode="numeric"
          pattern="[0-9]*"
          autoComplete={i === 0 ? "one-time-code" : "off"}
          maxLength={LENGTH}
          aria-label={t("auth.codeDigitAria", { n: i + 1 })}
          data-testid={`otp-${i}`}
          className={cn(
            "h-12 w-11 rounded-xl border bg-surface-card text-center text-xl font-bold tabular-nums text-text-primary outline-none transition-colors sm:h-14 sm:w-12",
            "focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 disabled:opacity-60",
            error ? "border-danger" : "border-surface-border",
          )}
        />
      ))}
    </div>
  );
}
