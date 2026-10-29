"use client";

import { useEffect, useMemo, useState } from "react";
import { Ban, Loader2, VolumeX, X } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  addYears,
  createRestriction,
  errorCode,
  fmtDateTime,
  type BanDuration,
  type MuteDuration,
  type Restriction,
  type RestrictionKind,
} from "../global-chat-service";

// Moderator tool (SUPER_ADMIN / ADMIN), German like the rest of the admin
// panel. Themed with the shared surface tokens so it works both inside the
// chat window (any dashboard) and on /admin/global-chat. The server checks
// every rule again; this only explains them.

const MUTE_OPTIONS: { value: MuteDuration; label: string; ms?: number }[] = [
  { value: "10m", label: "10 Minuten", ms: 10 * 60_000 },
  { value: "1h", label: "1 Stunde", ms: 3_600_000 },
  { value: "24h", label: "24 Stunden", ms: 86_400_000 },
  { value: "3d", label: "3 Tage", ms: 3 * 86_400_000 },
  { value: "7d", label: "7 Tage", ms: 7 * 86_400_000 },
  { value: "30d", label: "30 Tage", ms: 30 * 86_400_000 },
  { value: "custom", label: "Eigene Dauer" },
];
const BAN_OPTIONS: { value: BanDuration; label: string; years?: number }[] = [
  { value: "1y", label: "1 Jahr", years: 1 },
  { value: "2y", label: "2 Jahre", years: 2 },
  { value: "3y", label: "3 Jahre", years: 3 },
  { value: "5y", label: "5 Jahre", years: 5 },
  { value: "permanent", label: "Dauerhaft" },
];

const ERRORS: Record<string, string> = {
  cannot_restrict_moderator: "Admins können im Chat nicht stummgeschaltet oder gesperrt werden.",
  cannot_restrict_self: "Du kannst dich nicht selbst sperren.",
  permanent_ban_super_admin_only: "Eine dauerhafte Sperre darf nur ein Super Admin vergeben.",
  mute_too_long: "Eine Stummschaltung darf höchstens 1 Jahr dauern – dafür gibt es die Sperre.",
  ends_at_in_past: "Das Ende muss in der Zukunft liegen.",
  ends_at_required: "Bitte ein Ende wählen.",
  reason_required: "Bitte einen Grund angeben.",
  restriction_conflict: "Gleichzeitig wurde schon eine Sperre angelegt. Bitte neu laden.",
};

export function restrictionErrorText(err: unknown): string {
  const code = errorCode(err);
  return (code && ERRORS[code]) || "Aktion fehlgeschlagen. Bitte erneut versuchen.";
}

/** "2026-10-29T14:05" for <input type="datetime-local"> in local time. */
export function toLocalInput(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export const fieldClass =
  "w-full rounded-xl bg-surface-hover px-3 py-2.5 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue";

export default function RestrictDialog({
  target,
  messageId,
  initialKind = "mute",
  canBanPermanently,
  onClose,
  onDone,
}: {
  target: { id: string; name: string };
  messageId?: string;
  initialKind?: RestrictionKind;
  canBanPermanently: boolean;
  onClose: () => void;
  onDone: (r: Restriction) => void;
}) {
  const [kind, setKind] = useState<RestrictionKind>(initialKind);
  const [duration, setDuration] = useState<string>(initialKind === "ban" ? "1y" : "1h");
  const [customEnd, setCustomEnd] = useState(() => toLocalInput(new Date(Date.now() + 2 * 86_400_000)));
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function switchKind(next: RestrictionKind) {
    setKind(next);
    setDuration(next === "ban" ? "1y" : "1h");
    setError(null);
  }

  const start = useMemo(() => new Date(), []);
  const end: Date | null = useMemo(() => {
    if (kind === "mute") {
      if (duration === "custom") return customEnd ? new Date(customEnd) : null;
      return new Date(start.getTime() + (MUTE_OPTIONS.find((o) => o.value === duration)?.ms ?? 0));
    }
    const years = BAN_OPTIONS.find((o) => o.value === duration)?.years;
    return years ? addYears(start, years) : null;
  }, [kind, duration, customEnd, start]);

  async function submit() {
    if (reason.trim().length < 3) {
      setError("Bitte einen Grund angeben (mind. 3 Zeichen).");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const r = await createRestriction({
        user_id: target.id,
        kind,
        duration: duration as MuteDuration | BanDuration,
        ends_at: kind === "mute" && duration === "custom" && end ? end.toISOString() : undefined,
        reason: reason.trim(),
        public_note: note.trim() || undefined,
        message_id: messageId,
      });
      onDone(r);
    } catch (err) {
      setError(restrictionErrorText(err));
    } finally {
      setSaving(false);
    }
  }

  const options = kind === "mute" ? MUTE_OPTIONS : BAN_OPTIONS;

  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div role="dialog" aria-modal="true" aria-labelledby="gc-restrict-title" data-testid="gc-restrict-dialog"
           className="max-h-[100dvh] w-full overflow-y-auto rounded-t-2xl bg-surface-card p-5 text-text-primary shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:max-w-md sm:rounded-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 id="gc-restrict-title" className="text-base font-bold">Global Chat: {kind === "mute" ? "Stummschalten" : "Sperren"}</h2>
            <p className="mt-0.5 text-sm text-text-secondary">Benutzer: <b className="text-text-primary">{target.name}</b></p>
          </div>
          <button type="button" onClick={onClose} aria-label="Schließen" className="rounded-full p-1.5 text-text-muted hover:bg-surface-hover"><X size={18} /></button>
        </div>

        <div role="radiogroup" aria-label="Art" className="mb-4 grid grid-cols-2 gap-2">
          {(["mute", "ban"] as const).map((k) => (
            <button key={k} type="button" role="radio" aria-checked={kind === k} onClick={() => switchKind(k)}
                    className={cn("flex min-h-11 items-center justify-center gap-2 rounded-xl text-sm font-semibold ring-1",
                      kind === k ? (k === "ban" ? "bg-danger text-white ring-danger" : "bg-accent-blue text-white ring-accent-blue") : "bg-surface-hover text-text-secondary ring-surface-border")}>
              {k === "mute" ? <VolumeX size={16} /> : <Ban size={16} />} {k === "mute" ? "Stummschalten" : "Sperren"}
            </button>
          ))}
        </div>

        <fieldset className="mb-4">
          <legend className="mb-1.5 text-sm font-medium">Dauer</legend>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {options.map((o) => {
              const locked = o.value === "permanent" && !canBanPermanently;
              return (
                <label key={o.value} className={cn("flex min-h-10 cursor-pointer items-center gap-2 rounded-lg px-3 text-sm ring-1",
                  duration === o.value ? "bg-accent-blue/10 ring-accent-blue" : "ring-surface-border", locked && "cursor-not-allowed opacity-50")}
                       title={locked ? "Nur Super Admin" : undefined}>
                  <input type="radio" name="gc-duration" value={o.value} checked={duration === o.value} disabled={locked}
                         onChange={() => setDuration(o.value)} className="accent-[var(--accent-blue)]" />
                  {o.label}
                </label>
              );
            })}
          </div>
          {kind === "mute" && duration === "custom" && (
            <label className="mt-2 block text-sm">
              <span className="mb-1 block text-text-secondary">Ende</span>
              <input type="datetime-local" value={customEnd} min={toLocalInput(new Date())} onChange={(e) => setCustomEnd(e.target.value)} className={fieldClass} />
            </label>
          )}
          {kind === "ban" && <p className="mt-2 text-xs text-text-muted">Sperren gelten mindestens 1 Jahr (Kalenderjahre). Für kürzere Pausen: Stummschalten.</p>}
        </fieldset>

        <dl className="mb-4 grid grid-cols-2 gap-2 rounded-xl bg-surface-hover p-3 text-xs ring-1 ring-surface-border">
          <div><dt className="text-text-muted">Beginn</dt><dd className="font-semibold">{fmtDateTime(start.toISOString())}</dd></div>
          <div><dt className="text-text-muted">Ende</dt><dd className="font-semibold" data-testid="gc-restrict-end">{end ? fmtDateTime(end.toISOString()) : duration === "permanent" ? "dauerhaft" : "—"}</dd></div>
        </dl>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block font-medium">Grund (intern, nur für Admins) *</span>
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} maxLength={2000} rows={2} className={fieldClass}
                    placeholder="z. B. wiederholte Beleidigungen trotz Verwarnung" />
        </label>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block font-medium">Hinweis für den Benutzer (optional)</span>
          <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} className={fieldClass} placeholder="z. B. Bitte respektvoll bleiben." />
        </label>

        <p className="mb-4 text-xs text-text-muted">Betrifft nur das Schreiben im Global Chat. Mitlesen, Kurse, Zahlungen und Gruppen-Chats bleiben unverändert.</p>

        {error && <p role="alert" className="mb-3 rounded-lg bg-danger/10 p-2.5 text-sm text-danger">{error}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="min-h-11 rounded-xl px-4 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:bg-surface-hover">Abbrechen</button>
          <button type="button" onClick={submit} disabled={saving || (kind === "mute" && duration === "custom" && !customEnd)}
                  className={cn("inline-flex min-h-11 items-center gap-2 rounded-xl px-4 text-sm font-semibold text-white disabled:opacity-60", kind === "ban" ? "bg-danger" : "bg-accent-blue")}>
            {saving && <Loader2 size={16} className="animate-spin" />}
            {kind === "mute" ? "Stummschalten" : "Sperre bestätigen"}
          </button>
        </div>
      </div>
    </div>
  );
}
