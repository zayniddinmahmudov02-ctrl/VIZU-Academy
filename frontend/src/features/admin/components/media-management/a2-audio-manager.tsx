"use client";

import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, CircleDashed, FileAudio2, Link2, Link2Off, LoaderCircle, Pencil, Play, RefreshCw, Trash2, Upload, XCircle } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  confirmA2ReadinessCheck,
  deleteA2Asset,
  getA2AssetBlobUrl,
  getA2Assets,
  getA2Manifest,
  getA2Readiness,
  getA2Targets,
  linkA2Asset,
  unlinkA2Asset,
  updateA2Asset,
  uploadA2Asset,
  verifyA2Asset,
  type A2Asset,
  type A2AudioKind,
  type A2Readiness,
  type A2Target,
} from "@/features/admin/services/media-management-service";
import { A2_ACCEPT, classify, precheck, summarize, type ImportResult } from "./a2-audio-import";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";
const input = "min-h-9 rounded-lg bg-[var(--admin-card)] px-2 text-sm text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)]";
const KINDS: { value: A2AudioKind; label: string }[] = [
  { value: "HOEREN", label: "Hören" }, { value: "TEXT", label: "Text" }, { value: "UNTERRICHT", label: "Unterricht" }, { value: "OTHER", label: "Sonstiges" },
];
const LESSONS = Array.from({ length: 14 }, (_, i) => i + 1);
const STATUS_TEXT: Record<A2Readiness["status"], string> = {
  READY: "READY — bereit für den Verkauf",
  NEEDS_CONTENT: "NEEDS_CONTENT — Inhalte fehlen",
  NEEDS_CONFIGURATION: "NEEDS_CONFIGURATION — Einrichtung fehlt",
  NEEDS_TESTING: "NEEDS_TESTING — Prüfungen offen",
};

function bytes(n: number | null) {
  if (!n) return "—";
  return n >= 1024 * 1024 ? `${(n / 1024 / 1024).toFixed(2)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`;
}

function seconds(n: number | null) {
  return n ? `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}` : "—";
}

/** Duration from the file's metadata in the browser (optional — null if it cannot be read). */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    let settled = false;
    const done = (value: number | null) => {
      if (settled) return;
      settled = true;
      URL.revokeObjectURL(url);
      resolve(value);
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => done(Number.isFinite(audio.duration) && audio.duration > 0 ? Math.round(audio.duration) : null);
    audio.onerror = () => done(null);
    setTimeout(() => done(null), 5000);
    audio.src = url;
  });
}

// ---------------------------------------------------------------- readiness

function ReadinessCard({ data, onChanged }: { data: A2Readiness; onChanged: (r: A2Readiness) => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ready = data.status === "READY";

  async function toggle(key: string, done: boolean) {
    const note = done ? window.prompt("Notiz (optional), z. B. wie / wo geprüft:") : null;
    if (done && note === null) return;
    setBusy(key);
    setError(null);
    try {
      onChanged(await confirmA2ReadinessCheck(key, done, note ?? undefined));
    } catch (cause) {
      setError(apiErrorMessage(cause, "Konnte nicht gespeichert werden (nur Super Admin)."));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className={card} data-testid="a2-readiness" data-status={data.status}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-[var(--admin-text-primary)]">A2 · Verkaufsbereitschaft</h2>
          <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
            Aus den echten Daten berechnet. Der Verkauf wird hier nicht eingeschaltet (Admin → Angebote → Verkauf). Verkauf aktuell: <strong>{data.sales_enabled ? "an" : "aus"}</strong>.
          </p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${ready ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]"}`}>
          {STATUS_TEXT[data.status]}
        </span>
      </div>
      <ul className="mt-4 space-y-2">
        {data.checks.map((c) => (
          <li key={c.key} className="rounded-xl border border-[var(--admin-border)] p-3 text-sm" data-testid={`a2-check-${c.key}`} data-ok={c.ok}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <p className="flex items-start gap-2 text-[var(--admin-text-primary)]">
                {c.ok ? <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--admin-success)]" /> : <XCircle size={16} className="mt-0.5 shrink-0 text-[var(--admin-danger)]" />}
                <span>{c.label}{c.detail && <span className="block text-xs text-[var(--admin-text-muted)]">{c.detail}</span>}</span>
              </p>
              {c.manual && (
                <AdminButton size="sm" variant="secondary" disabled={busy === c.key} onClick={() => void toggle(c.key, !c.ok)}>
                  {busy === c.key && <LoaderCircle size={14} className="animate-spin" />}{c.ok ? "Zurücksetzen" : "Bestätigen"}
                </AdminButton>
              )}
            </div>
            {c.items.length > 0 && (
              <details className="mt-2 text-xs text-[var(--admin-text-secondary)]">
                <summary className="cursor-pointer">{c.items.length} Eintrag/Einträge</summary>
                <ul className="mt-1 list-disc space-y-0.5 pl-5">{c.items.map((item) => <li key={item} className="break-words">{item}</li>)}</ul>
              </details>
            )}
          </li>
        ))}
      </ul>
      {data.content_gaps.length > 0 && (
        <details className="mt-3 rounded-xl border border-[var(--admin-border)] p-3 text-sm" data-testid="a2-content-gaps">
          <summary className="cursor-pointer font-medium text-[var(--admin-text-primary)]">Noch auszufüllen: {data.content_gaps.length}</summary>
          <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-[var(--admin-text-secondary)]">{data.content_gaps.map((g) => <li key={g}>{g}</li>)}</ul>
        </details>
      )}
      {error && <p role="alert" className="mt-2 text-sm text-[var(--admin-danger)]">{error}</p>}
    </section>
  );
}

// ---------------------------------------------------------------- import

interface QueueItem { file: File; progress: number | null; result: ImportResult | null }

function ImportCard({ onDone }: { onDone: () => Promise<void> }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [running, setRunning] = useState(false);
  const [dragging, setDragging] = useState(false);

  async function run(files: File[]) {
    if (!files.length || running) return;
    const items: QueueItem[] = files.map((file) => ({ file, progress: null, result: null }));
    setQueue(items);
    setRunning(true);
    const set = (i: number, patch: Partial<QueueItem>) => setQueue((cur) => cur.map((it, j) => (j === i ? { ...it, ...patch } : it)));
    for (let i = 0; i < items.length; i++) {
      const file = items[i].file;
      const problem = precheck(file.name, file.size);
      if (problem) {
        set(i, { result: { name: file.name, outcome: "error", assetId: null, message: problem, unlinked: false } });
        continue;
      }
      set(i, { progress: 0 });
      try {
        const asset = await uploadA2Asset(file, await readDuration(file), (p) => set(i, { progress: p }));
        set(i, { progress: null, result: classify(file.name, { asset }) });
      } catch (error) {
        set(i, { progress: null, result: classify(file.name, { error }) });
      }
    }
    setRunning(false);
    await onDone();
  }

  const done = queue.map((q) => q.result).filter((r): r is ImportResult => r !== null);
  const s = summarize(done);

  return (
    <section className={card} data-testid="a2-import">
      <h2 className="text-base font-bold text-[var(--admin-text-primary)]">A2 Audio Manager · Hochladen</h2>
      <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">
        Eine oder mehrere MP3-/M4A-Dateien (max. 100 MB). Unterricht, Art und Teil werden aus dem Dateinamen gelesen und können danach korrigiert werden.
        Hochladen verknüpft nichts mit einer Lektion — das bestätigst du unten selbst.
      </p>
      <input ref={inputRef} type="file" multiple accept={A2_ACCEPT} className="hidden" aria-label="A2-Audiodateien auswählen" data-testid="a2-import-input"
             onChange={(e) => { const files = Array.from(e.target.files ?? []); e.target.value = ""; void run(files); }} />
      <div role="button" tabIndex={0} aria-disabled={running}
           onClick={() => !running && inputRef.current?.click()}
           onKeyDown={(e) => { if ((e.key === "Enter" || e.key === " ") && !running) { e.preventDefault(); inputRef.current?.click(); } }}
           onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)}
           onDrop={(e) => { e.preventDefault(); setDragging(false); void run(Array.from(e.dataTransfer.files)); }}
           className={`mt-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-6 text-center text-sm ${dragging ? "border-[var(--admin-primary)] bg-[var(--admin-primary)]/5" : "border-[var(--admin-border)]"}`}>
        {running ? <LoaderCircle size={22} className="animate-spin text-[var(--admin-primary)]" /> : <Upload size={22} className="text-[var(--admin-primary)]" />}
        <span className="font-medium text-[var(--admin-text-primary)]">{running ? "Upload läuft …" : "Dateien hierher ziehen oder klicken"}</span>
      </div>
      {queue.length > 0 && (
        <>
          <p className="mt-4 text-sm text-[var(--admin-text-primary)]" role="status" data-testid="a2-import-summary">
            {done.length}/{queue.length} verarbeitet · <span className="text-[var(--admin-success)]">{s.success} erfolgreich</span> · {s.duplicate} Duplikat(e) ·{" "}
            <span className="text-[var(--admin-danger)]">{s.error} Fehler</span> · {s.unlinked} noch nicht verknüpft
          </p>
          <ul className="mt-2 space-y-1.5 text-xs">
            {queue.map((q, i) => (
              <li key={`${q.file.name}-${i}`} className="rounded-lg border border-[var(--admin-border)] px-3 py-2" data-testid="a2-import-row" data-outcome={q.result?.outcome ?? "waiting"}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="break-all font-medium text-[var(--admin-text-primary)]">{q.file.name}</span>
                  <span className={q.result?.outcome === "success" ? "text-[var(--admin-success)]" : q.result?.outcome === "error" ? "text-[var(--admin-danger)]" : "text-[var(--admin-text-muted)]"}>
                    {q.result ? { success: "erfolgreich", duplicate: "Duplikat", error: "Fehler" }[q.result.outcome] : q.progress !== null ? `${q.progress}%` : "wartet"}
                  </span>
                </div>
                {q.progress !== null && (
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-[var(--admin-border)]"><div className="h-full bg-[var(--admin-primary)]" style={{ width: `${q.progress}%` }} /></div>
                )}
                {q.result?.message && <p className="mt-1 text-[var(--admin-text-secondary)]">{q.result.message}</p>}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- library

function AssetRow({ asset, targets, onChanged }: { asset: A2Asset; targets: A2Target[]; onChanged: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [linking, setLinking] = useState(false);
  const [allTargets, setAllTargets] = useState(false);
  const [target, setTarget] = useState(asset.suggestion?.listening_id ?? "");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteFile, setDeleteFile] = useState(false);
  const [form, setForm] = useState({ unterricht: asset.unterricht, audio_kind: asset.audio_kind, part: asset.part, title: asset.title, sort_order: asset.sort_order });

  async function act(fn: () => Promise<unknown>, fallback: string) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await onChanged();
      return true;
    } catch (cause) {
      setError(apiErrorMessage(cause, fallback));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function togglePreview() {
    if (preview) {
      URL.revokeObjectURL(preview);
      return setPreview(null);
    }
    setBusy(true);
    try {
      setPreview(await getA2AssetBlobUrl(asset.id));
    } catch (cause) {
      setError(apiErrorMessage(cause, "Audio konnte nicht geladen werden."));
    } finally {
      setBusy(false);
    }
  }

  const choices = targets.filter((t) => allTargets || t.lesson_number === asset.unterricht);
  const verified = asset.verification === "verified";

  return (
    <article className="space-y-2 rounded-xl border border-[var(--admin-border)] p-3" data-testid="a2-asset" data-asset-id={asset.id}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]"><FileAudio2 size={15} className="shrink-0 text-[var(--admin-primary)]" /><span className="break-words">{asset.title}</span></h4>
          <p className="mt-0.5 break-all text-xs text-[var(--admin-text-muted)]">
            Original: {asset.original_filename} · {asset.audio_format} · {bytes(asset.size_bytes)} · {seconds(asset.duration_seconds)}
            {" · "}{KINDS.find((k) => k.value === asset.audio_kind)?.label ?? "Art offen"}{asset.part ? ` · Teil ${asset.part}` : ""} · Reihenfolge {asset.sort_order}
          </p>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${verified ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : asset.verification === "problem" ? "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]" : "bg-[var(--admin-warning)]/10 text-[var(--admin-warning)]"}`}>
          {verified ? <CheckCircle2 size={12} /> : asset.verification === "problem" ? <AlertTriangle size={12} /> : <CircleDashed size={12} />}
          {verified ? "geprüft" : asset.verification === "problem" ? "Problem" : "nicht geprüft"}
        </span>
      </div>
      {asset.file_status !== "ok" && <p role="status" className="text-xs font-medium text-[var(--admin-danger)]">Datei fehlt im Speicher.</p>}
      {asset.verification_note && <p className="text-xs text-[var(--admin-text-secondary)]">Notiz: {asset.verification_note}</p>}
      <p className="text-xs text-[var(--admin-text-secondary)]">
        {asset.linked ? (
          <>Verknüpft mit <strong>{asset.linked.lesson_number}. Unterricht · {asset.linked.title}</strong>{asset.linked.is_published ? " (veröffentlicht)" : " (Entwurf — nach dem Prüfen veröffentlichen)"}
            {!asset.linked.in_sync && <span className="text-[var(--admin-danger)]"> · die Aufgabe spielt inzwischen eine andere Datei</span>}
            {asset.link_mismatch && <span className="text-[var(--admin-danger)]"> · Unterricht {asset.unterricht} passt nicht zur Lektion</span>}</>
        ) : asset.suggestion ? (
          <>Vorschlag ({asset.suggestion.reason}): <strong>{asset.suggestion.lesson_number}. Unterricht · {asset.suggestion.title}</strong> — wird erst nach deiner Bestätigung verknüpft.</>
        ) : "Nicht verknüpft."}
      </p>
      {preview && <audio controls src={preview} className="w-full" aria-label={`${asset.title} anhören`} />}

      {editing && (
        <form className="grid gap-2 rounded-lg bg-[var(--admin-border)]/20 p-2 sm:grid-cols-5" onSubmit={(e) => { e.preventDefault(); void act(() => updateA2Asset(asset.id, form), "Konnte nicht gespeichert werden.").then((ok) => ok && setEditing(false)); }}>
          <label className="text-xs">Unterricht
            <select className={`${input} mt-0.5 w-full`} value={form.unterricht ?? ""} onChange={(e) => setForm({ ...form, unterricht: e.target.value ? Number(e.target.value) : null })}>
              <option value="">—</option>{LESSONS.map((n) => <option key={n} value={n}>{n}</option>)}
            </select></label>
          <label className="text-xs">Art
            <select className={`${input} mt-0.5 w-full`} value={form.audio_kind ?? ""} onChange={(e) => setForm({ ...form, audio_kind: (e.target.value || null) as A2AudioKind | null })}>
              <option value="">—</option>{KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
            </select></label>
          <label className="text-xs">Teil
            <input className={`${input} mt-0.5 w-full`} type="number" min={1} max={99} value={form.part ?? ""} onChange={(e) => setForm({ ...form, part: e.target.value ? Number(e.target.value) : null })} /></label>
          <label className="text-xs">Reihenfolge
            <input className={`${input} mt-0.5 w-full`} type="number" min={0} max={10000} value={form.sort_order} onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) || 0 })} /></label>
          <label className="text-xs sm:col-span-5">Name
            <input className={`${input} mt-0.5 w-full`} value={form.title} maxLength={255} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <div className="flex gap-2 sm:col-span-5">
            <AdminButton size="sm" type="submit" disabled={busy || !form.title.trim()}>Speichern</AdminButton>
            <AdminButton size="sm" variant="secondary" type="button" onClick={() => setEditing(false)}>Abbrechen</AdminButton>
          </div>
        </form>
      )}

      {linking && (
        <div className="space-y-2 rounded-lg bg-[var(--admin-border)]/20 p-2 text-xs">
          <label className="block">Hören-Aufgabe
            <select className={`${input} mt-0.5 w-full`} value={target} onChange={(e) => setTarget(e.target.value)} data-testid="a2-link-target">
              <option value="">— auswählen —</option>
              {choices.map((t) => (
                <option key={t.listening_id} value={t.listening_id}>
                  {t.lesson_number}. Unterricht · {t.title}{t.asset_id && t.asset_id !== asset.id ? " (hat schon eine Datei — wird ersetzt)" : t.has_audio ? " (hat Audio — wird archiviert)" : ""}
                </option>
              ))}
            </select></label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={allTargets} onChange={(e) => setAllTargets(e.target.checked)} /> Aufgaben aller A2-Lektionen zeigen</label>
          <p className="text-[var(--admin-text-muted)]">Die Aufgabe wird danach Entwurf, bis du Audio und Fragen geprüft und sie veröffentlicht hast. Ihr bisheriges Audio wird archiviert, nicht gelöscht.</p>
          <div className="flex gap-2">
            <AdminButton size="sm" disabled={busy || !target} onClick={() => void act(() => linkA2Asset(asset.id, target), "Verknüpfen fehlgeschlagen.").then((ok) => ok && setLinking(false))}>
              <Link2 size={14} /> Verknüpfung bestätigen
            </AdminButton>
            <AdminButton size="sm" variant="secondary" onClick={() => setLinking(false)}>Abbrechen</AdminButton>
          </div>
        </div>
      )}

      {confirmDelete && (
        <div role="alertdialog" aria-label="Löschen bestätigen" className="space-y-2 rounded-lg border border-[var(--admin-danger)] p-2 text-xs">
          <p>„{asset.original_filename}“ aus der A2-Bibliothek entfernen?</p>
          <label className="flex items-center gap-2"><input type="checkbox" checked={deleteFile} onChange={(e) => setDeleteFile(e.target.checked)} /> auch die Datei endgültig löschen (nur wenn nichts anderes sie verwendet)</label>
          <div className="flex gap-2">
            <AdminButton size="sm" disabled={busy} onClick={() => void act(() => deleteA2Asset(asset.id, deleteFile), "Löschen fehlgeschlagen. Es wurde nichts geändert.")}>
              <Trash2 size={14} /> Ja, entfernen
            </AdminButton>
            <AdminButton size="sm" variant="secondary" onClick={() => setConfirmDelete(false)}>Abbrechen</AdminButton>
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <AdminButton size="sm" variant="secondary" disabled={busy || asset.file_status !== "ok"} onClick={() => void togglePreview()}>
          {busy ? <LoaderCircle size={14} className="animate-spin" /> : <Play size={14} />}{preview ? "Player schließen" : "Anhören"}
        </AdminButton>
        {!verified && <AdminButton size="sm" variant="secondary" disabled={busy || asset.file_status !== "ok"} onClick={() => void act(() => verifyA2Asset(asset.id, "verified"), "Konnte nicht gespeichert werden.")}><CheckCircle2 size={14} /> Geprüft</AdminButton>}
        <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => { const note = window.prompt("Was stimmt nicht?"); if (note?.trim()) void act(() => verifyA2Asset(asset.id, "problem", note), "Konnte nicht gespeichert werden."); }}>
          <AlertTriangle size={14} /> Problem
        </AdminButton>
        <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => setEditing((v) => !v)}><Pencil size={14} /> Korrigieren</AdminButton>
        {asset.linked
          ? <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => void act(() => unlinkA2Asset(asset.id), "Lösen fehlgeschlagen.")}><Link2Off size={14} /> Verknüpfung lösen</AdminButton>
          : <AdminButton size="sm" disabled={busy || asset.verification === "problem"} onClick={() => setLinking((v) => !v)} data-testid="a2-link"><Link2 size={14} /> Mit Lektion verknüpfen</AdminButton>}
        {!asset.linked && <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => setConfirmDelete(true)}><Trash2 size={14} /> Entfernen</AdminButton>}
      </div>
      {error && <p role="alert" className="text-sm text-[var(--admin-danger)]">{error}</p>}
    </article>
  );
}

export default function A2AudioManager() {
  const queryClient = useQueryClient();
  const assets = useQuery({ queryKey: ["media-mgmt", "a2-assets"], queryFn: getA2Assets });
  const targets = useQuery({ queryKey: ["media-mgmt", "a2-targets"], queryFn: getA2Targets });
  const manifest = useQuery({ queryKey: ["media-mgmt", "a2-manifest"], queryFn: getA2Manifest });
  const readiness = useQuery({ queryKey: ["media-mgmt", "a2-readiness"], queryFn: getA2Readiness });

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["media-mgmt"] });
  }

  const list = assets.data ?? [];
  const groups = [...LESSONS.map((n) => ({ key: String(n), label: `${n}. Unterricht`, items: list.filter((a) => a.unterricht === n) })),
    { key: "none", label: "Ohne Unterricht", items: list.filter((a) => a.unterricht === null) }].filter((g) => g.items.length);
  const c = manifest.data?.counts;

  return (
    <section className="space-y-5" data-testid="a2-audio-manager">
      {readiness.data && <ReadinessCard data={readiness.data} onChanged={(r) => queryClient.setQueryData(["media-mgmt", "a2-readiness"], r)} />}
      {readiness.isError && <p role="alert" className="text-sm text-[var(--admin-danger)]">Verkaufsbereitschaft konnte nicht geladen werden.</p>}
      <ImportCard onDone={refresh} />
      <section className={card} data-testid="a2-library">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[var(--admin-text-primary)]">A2-Audio-Bibliothek · Manifest</h2>
            {c && (
              <p className="mt-1 text-sm text-[var(--admin-text-secondary)]" data-testid="a2-manifest-counts">
                {c.files} Datei(en) · {c.verified} geprüft · {c.linked} verknüpft · {c.unlinked} offen · Hören-Aufgaben mit Audio: {c.tasks_with_audio}/{c.tasks}
              </p>
            )}
          </div>
          <AdminButton variant="secondary" size="sm" disabled={assets.isFetching} onClick={() => void refresh()}>
            {assets.isFetching ? <LoaderCircle size={15} className="animate-spin" /> : <RefreshCw size={15} />} Aktualisieren
          </AdminButton>
        </div>
        {manifest.data && manifest.data.missing_audio.length > 0 && (
          <details className="mt-3 rounded-xl border border-[var(--admin-warning)]/40 p-3 text-sm" data-testid="a2-missing-audio" open>
            <summary className="cursor-pointer font-medium text-[var(--admin-warning)]">Audio hali yuklanmagan / fehlt: {manifest.data.missing_audio.length} Hören-Aufgabe(n)</summary>
            <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-[var(--admin-text-secondary)]">
              {manifest.data.missing_audio.map((t) => <li key={t.listening_id}>{t.lesson_number}. Unterricht · {t.title}</li>)}
            </ul>
          </details>
        )}
        {assets.isPending ? <p role="status" className="mt-4 text-sm text-[var(--admin-text-muted)]">Wird geladen …</p>
          : assets.isError ? <p role="alert" className="mt-4 text-sm text-[var(--admin-danger)]">Bibliothek konnte nicht geladen werden.</p>
          : list.length === 0 ? <p className="mt-4 text-sm text-[var(--admin-text-muted)]">Noch keine A2-Audiodatei hochgeladen.</p>
          : groups.map((g) => (
            <div key={g.key} className="mt-4 space-y-2" data-testid={`a2-group-${g.key}`}>
              <h3 className="text-sm font-bold text-[var(--admin-text-primary)]">{g.label} · {g.items.length}</h3>
              {g.items.map((a) => <AssetRow key={`${a.id}-${a.verification}-${a.linked?.listening_id ?? ""}`} asset={a} targets={targets.data ?? []} onChanged={refresh} />)}
            </div>
          ))}
      </section>
    </section>
  );
}
