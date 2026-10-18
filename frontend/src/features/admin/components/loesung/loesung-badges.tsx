import type { AudioState, KeyStatus } from "@/features/admin/services/loesung-service";

const base = "rounded-full px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap";
const tone = {
  ok: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]",
  warn: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  bad: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  info: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]",
  muted: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]",
};

export function KeyStatusBadge({ status }: { status: KeyStatus }) {
  const [label, cls] = status === "complete" ? ["Vollständig & geprüft", tone.ok] : status === "missing" ? ["Lösung fehlt", tone.bad] : ["Prüfung nötig", tone.warn];
  return <span className={`${base} ${cls}`} data-testid="badge-key">{label}</span>;
}

export function AudioBadge({ audio }: { audio: AudioState }) {
  const [label, cls] = audio === "ok" ? ["Audio vorhanden", tone.ok] : audio === "external" ? ["Externer Audio-Link", tone.info]
    : audio === "file_missing" ? ["Audiodatei fehlt", tone.bad] : ["Kein Audio", tone.bad];
  return <span className={`${base} ${cls}`} data-testid="badge-audio">{label}</span>;
}

export function PublishBadge({ published, ready }: { published: boolean; ready: boolean }) {
  const [label, cls] = published ? ["Veröffentlicht", tone.ok] : ready ? ["Bereit zur Veröffentlichung", tone.info] : ["Entwurf", tone.muted];
  return <span className={`${base} ${cls}`} data-testid="badge-publish">{label}</span>;
}
