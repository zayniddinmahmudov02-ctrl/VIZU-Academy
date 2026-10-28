"use client";

import { useEffect, useState } from "react";

const EVENT = "wb-status";

/** Short status line ("Saved", "Removed") for actions anywhere in the Wörterbuch. */
export function announce(message: string, error = false) {
  window.dispatchEvent(new CustomEvent(EVENT, { detail: { message, error } }));
}

export default function StatusToast() {
  const [status, setStatus] = useState<{ message: string; error: boolean } | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const show = (e: Event) => {
      setStatus((e as CustomEvent<{ message: string; error: boolean }>).detail);
      clearTimeout(timer);
      timer = setTimeout(() => setStatus(null), 2500);
    };
    window.addEventListener(EVENT, show);
    return () => {
      window.removeEventListener(EVENT, show);
      clearTimeout(timer);
    };
  }, []);

  return (
    <div aria-live="polite" role="status" className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      {status && (
        <p className={`rounded-xl px-4 py-2.5 text-sm font-semibold shadow-[var(--shadow-md)] ${
          status.error ? "bg-danger text-white" : "bg-brand-900 text-white"}`}>
          {status.message}
        </p>
      )}
    </div>
  );
}
