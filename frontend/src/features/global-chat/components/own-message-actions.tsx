"use client";

import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";
import { Loader2, MoreHorizontal, Pencil, Trash2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { MAX_LENGTH, type ChatMessage } from "../global-chat-service";

const MENU_HEIGHT = 96;

/** "…" menu on the caller's own message: Edit / Delete. Opens upwards when
 *  there is no room below inside the chat list, and is anchored to the
 *  right edge of the (right-aligned) own bubble, so it stays on screen. */
export function OwnMessageMenu({ canEdit, canDelete, onEdit, onDelete, boundary, light }: {
  canEdit: boolean;
  canDelete: boolean;
  onEdit: () => void;
  onDelete: () => void;
  boundary: RefObject<HTMLElement | null>;
  light: boolean;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [up, setUp] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!open || !wrapRef.current) return;
    const own = wrapRef.current.getBoundingClientRect();
    const box = boundary.current?.getBoundingClientRect();
    const bottom = box ? box.bottom : window.innerHeight;
    setUp(bottom - own.bottom < MENU_HEIGHT && own.top - (box?.top ?? 0) > MENU_HEIGHT);
  }, [open, boundary]);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | TouchEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("touchstart", close);
    window.addEventListener("keydown", onKey, true);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("touchstart", close);
      window.removeEventListener("keydown", onKey, true);
    };
  }, [open]);

  if (!canEdit && !canDelete) return null;

  function pick(action: () => void) {
    setOpen(false);
    action();
  }

  return (
    <div ref={wrapRef} className="relative">
      <button type="button" onClick={() => setOpen((v) => !v)} aria-haspopup="menu" aria-expanded={open} aria-label={t("globalChat.messageMenu")}
              data-testid="global-chat-message-menu"
              className={cn("flex h-6 w-6 items-center justify-center rounded-md", light ? "text-white/80 hover:bg-white/15" : "text-text-muted hover:bg-surface-card")}>
        <MoreHorizontal size={14} />
      </button>
      {open && (
        <div role="menu" className={cn("absolute right-0 z-20 w-44 overflow-hidden rounded-xl bg-surface-card py-1 text-sm text-text-primary shadow-[var(--shadow-lg)] ring-1 ring-surface-border",
          up ? "bottom-full mb-1" : "top-full mt-1")}>
          {canEdit && (
            <button type="button" role="menuitem" onClick={() => pick(onEdit)} className="flex min-h-10 w-full items-center gap-2 px-3 text-left hover:bg-surface-hover">
              <Pencil size={14} /> {t("globalChat.edit")}
            </button>
          )}
          {canDelete && (
            <button type="button" role="menuitem" onClick={() => pick(onDelete)} className="flex min-h-10 w-full items-center gap-2 px-3 text-left text-danger hover:bg-surface-hover">
              <Trash2 size={14} /> {t("globalChat.delete")}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/** Inline editor in place of the bubble text: Enter saves, Shift+Enter is a
 *  new line, Escape cancels — the same keys as the message input. */
export function EditMessageForm({ message, onSave, onCancel }: {
  message: ChatMessage;
  onSave: (body: string) => Promise<void>;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState(message.body ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);

  const text = draft.trim();
  const tooLong = draft.length > MAX_LENGTH;

  async function save() {
    if (!text || tooLong || saving) return;
    if (text === (message.body ?? "").trim()) {
      onCancel();
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(text);
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : t("globalChat.err_generic"));
      setSaving(false);
    }
  }

  return (
    <form className="mt-1 space-y-1.5" data-testid="global-chat-edit-form" onSubmit={(e) => { e.preventDefault(); save(); }}>
      <textarea ref={ref} value={draft} rows={2} maxLength={MAX_LENGTH} aria-label={t("globalChat.edit")} data-testid="global-chat-edit-input"
                onChange={(e) => { setDraft(e.target.value); setError(null); }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                    e.preventDefault();
                    save();
                  } else if (e.key === "Escape") {
                    e.preventDefault();
                    e.stopPropagation();
                    onCancel();
                  }
                }}
                className="block max-h-40 min-h-16 w-full min-w-[220px] resize-none rounded-lg bg-surface-card px-2.5 py-2 text-sm text-text-primary ring-1 ring-surface-border outline-none [field-sizing:content] focus:ring-accent-blue" />
      <div className="flex items-center justify-between gap-2">
        <span className={cn("text-[10px]", tooLong ? "text-danger" : "text-text-muted")}>{draft.length}/{MAX_LENGTH}</span>
        <div className="flex gap-1.5">
          <button type="button" onClick={onCancel} disabled={saving}
                  className="min-h-9 rounded-lg bg-surface-card px-3 text-xs font-semibold text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover">
            {t("globalChat.cancel")}
          </button>
          <button type="submit" disabled={saving || !text || tooLong} data-testid="global-chat-edit-save"
                  className="inline-flex min-h-9 items-center gap-1 rounded-lg bg-accent-blue px-3 text-xs font-semibold text-white disabled:opacity-50">
            {saving && <Loader2 size={12} className="animate-spin" />}{t("globalChat.save")}
          </button>
        </div>
      </div>
      {!text && <p className="text-[11px] text-danger">{t("globalChat.err_empty")}</p>}
      {error && <p role="alert" className="text-[11px] text-danger">{error}</p>}
    </form>
  );
}

/** Confirmation before deleting one's own message. */
export function ConfirmDeleteDialog({ message, onConfirm, onCancel }: {
  message: ChatMessage;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onCancel();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onCancel]);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await onConfirm();
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : t("globalChat.err_generic"));
      setBusy(false);
    }
  }

  return (
    <div className="absolute inset-0 z-30 flex items-end justify-center bg-black/40 p-3 sm:items-center" onMouseDown={(e) => e.target === e.currentTarget && !busy && onCancel()}>
      <div role="alertdialog" aria-modal="true" aria-labelledby="gc-delete-title" aria-describedby="gc-delete-text" data-testid="global-chat-delete-dialog"
           className="w-full max-w-sm rounded-2xl bg-surface-card p-4 text-text-primary shadow-[var(--shadow-lg)] ring-1 ring-surface-border">
        <h3 id="gc-delete-title" className="text-sm font-bold">{t("globalChat.deleteTitle")}</h3>
        <p id="gc-delete-text" className="mt-1 text-xs text-text-secondary">{t("globalChat.deleteText")}</p>
        <p className="mt-2 line-clamp-3 whitespace-pre-wrap break-words rounded-lg bg-surface-hover p-2 text-xs">{message.body}</p>
        {error && <p role="alert" className="mt-2 text-xs text-danger">{error}</p>}
        <div className="mt-3 flex justify-end gap-2">
          <button ref={cancelRef} type="button" onClick={onCancel} disabled={busy}
                  className="min-h-10 rounded-xl px-4 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover">
            {t("globalChat.cancel")}
          </button>
          <button type="button" onClick={confirm} disabled={busy} data-testid="global-chat-delete-confirm"
                  className="inline-flex min-h-10 items-center gap-1.5 rounded-xl bg-danger px-4 text-sm font-semibold text-white disabled:opacity-60">
            {busy && <Loader2 size={14} className="animate-spin" />}{t("globalChat.delete")}
          </button>
        </div>
      </div>
    </div>
  );
}
