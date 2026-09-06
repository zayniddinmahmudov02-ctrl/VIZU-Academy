"use client";

import { useEffect, useRef, useState } from "react";
import { Download, Share, SquarePlus, X } from "lucide-react";

import { useInstallPrompt } from "@/features/pwa/hooks/use-install-prompt";

/** "App installieren" — only rendered when the platform can actually do
 * something useful: a real one-tap install on Chrome/Edge/Android, or
 * the Share -> Add to Home Screen instructions on iOS Safari (which has
 * no install-prompt API at all). Renders nothing everywhere else
 * (already installed, or a browser/OS combination with no install path
 * — no dead button shown). */
export default function InstallAppButton() {
  const { canInstall, showIOSInstructions, promptInstall } = useInstallPrompt();
  const [iosDialogOpen, setIosDialogOpen] = useState(false);
  const openButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Escape closes the dialog; focus moves into it on open and back to
  // the trigger button on close, so keyboard users never lose their
  // place — same expectations as any other modal in this app.
  useEffect(() => {
    if (!iosDialogOpen) return;

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setIosDialogOpen(false);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      openButtonRef.current?.focus();
    };
  }, [iosDialogOpen]);

  const buttonClass =
    "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-card text-text-secondary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-all duration-200 hover:-translate-y-px hover:text-accent-blue active:translate-y-0";

  if (canInstall) {
    return (
      <button type="button" onClick={promptInstall} aria-label="App installieren" title="App installieren" className={buttonClass}>
        <Download size={16} />
      </button>
    );
  }

  if (showIOSInstructions) {
    return (
      <>
        <button
          ref={openButtonRef}
          type="button"
          onClick={() => setIosDialogOpen(true)}
          aria-label="App installieren"
          title="App installieren"
          className={buttonClass}
        >
          <Download size={16} />
        </button>

        {iosDialogOpen && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="install-ios-dialog-title"
            // safe-bottom: this sits flush against the bottom edge on
            // mobile (items-end) — needs clearance from the home
            // indicator, same reasoning as drawer.tsx/admin-mobile-nav.tsx.
            className="safe-bottom fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
            onClick={() => setIosDialogOpen(false)}
          >
            <div
              className="w-full max-w-sm rounded-card bg-surface-card p-5 shadow-[var(--shadow-card)] ring-1 ring-surface-border"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between">
                <h3 id="install-ios-dialog-title" className="text-sm font-bold text-text-primary">
                  VIZU App installieren
                </h3>
                <button
                  ref={closeButtonRef}
                  type="button"
                  onClick={() => setIosDialogOpen(false)}
                  aria-label="Schließen"
                  className="rounded text-text-muted hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue/50"
                >
                  <X size={16} />
                </button>
              </div>
              <ol className="mt-4 space-y-3 text-sm text-text-secondary">
                <li className="flex items-center gap-2.5">
                  <Share size={16} className="shrink-0 text-accent-blue" />
                  Tippe unten in Safari auf <strong className="text-text-primary">Teilen</strong>
                </li>
                <li className="flex items-center gap-2.5">
                  <SquarePlus size={16} className="shrink-0 text-accent-blue" />
                  Wähle <strong className="text-text-primary">Zum Home-Bildschirm</strong>
                </li>
              </ol>
            </div>
          </div>
        )}
      </>
    );
  }

  return null;
}
