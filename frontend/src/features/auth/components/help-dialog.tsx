"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { HelpCircle, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";

type Props = {
  topic: "login" | "register";
};

const STEPS = [1, 2, 3, 4, 5, 6];

/** "Hilfe" button + modal for the login / register pages. The dialog is its
 * own state, so opening it never touches (or resets) the form underneath. */
export default function HelpDialog({ topic }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const key = topic === "login" ? "helpLogin" : "helpRegister";

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const trigger = triggerRef.current;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      trigger?.focus();
    };
  }, [open]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium text-accent-blue ring-1 ring-surface-border transition hover:bg-surface-hover focus-visible:outline-2 focus-visible:outline-accent-blue"
      >
        <HelpCircle size={15} aria-hidden="true" />
        {t("auth.helpButton")}
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onClick={(e) => e.stopPropagation()}
            className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-t-dialog bg-surface-card p-6 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:rounded-dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <h2 id={titleId} className="text-lg font-bold text-text-primary">
                {t(`auth.${key}Title`)}
              </h2>
              <button
                ref={closeRef}
                type="button"
                onClick={() => setOpen(false)}
                aria-label={t("auth.helpClose")}
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-text-secondary hover:bg-surface-hover"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>

            <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-6 text-text-secondary">
              {STEPS.map((n) => (
                <li key={n}>{t(`auth.${key}Step${n}`)}</li>
              ))}
            </ol>

            {topic === "login" && (
              <Link
                href="/forgot-password"
                className="mt-5 inline-block text-sm font-medium text-accent-blue hover:text-accent-blue-hover"
              >
                {t("auth.helpSupportLink")}
              </Link>
            )}
          </div>
        </div>
      )}
    </>
  );
}
