"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, BarChart3, Bell, Download, ExternalLink, FileUp, Globe, Rocket, Smartphone, Trash2 } from "lucide-react";

import { AdminButton, AdminCard, AdminLabel, AdminPageHeader, AdminTextarea } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  archiveRelease,
  deleteDraftRelease,
  downloadReleaseFile,
  listReleases,
  publishRelease,
  updateReleaseNotes,
  uploadRelease,
  type AppReleaseAdmin,
} from "@/features/mobile-app/services/app-release-service";
import { formatBytes, groupChecksum } from "@/features/mobile-app/utils/platform";

const ERRORS: Record<string, string> = {
  APK_EXTENSION: "Nur .apk-Dateien sind erlaubt.",
  APK_MIME_TYPE: "Unerwarteter Dateityp — bitte die APK-Datei direkt hochladen.",
  APK_TOO_LARGE: "Die Datei ist zu groß (max. 150 MB).",
  APK_INVALID: "Keine gültige APK-Datei.",
  APK_INVALID_MANIFEST: "Das AndroidManifest der APK ist nicht lesbar.",
  APK_NOT_SIGNED: "Die APK ist nicht signiert. Bitte einen signierten Release-Build hochladen.",
  APK_DEBUG_SIGNED: "Debug-Build erkannt. Nur mit dem Release-Keystore signierte APKs sind erlaubt.",
  APK_WRONG_PACKAGE: "Falsche App: die Package-ID muss com.vizu.deutsch sein.",
  APK_SIGNER_MISMATCH: "Anderer Signaturschlüssel als bei früheren Releases — Updates würden bei allen Nutzern scheitern.",
  APK_VERSION_EXISTS: "Diese versionCode gibt es schon. Bitte versionCode im Build erhöhen.",
  VERSION_CODE_NOT_NEWER: "Die versionCode muss höher sein als die des aktuellen Releases.",
  APP_RELEASE_ARCHIVED: "Archivierte Releases können nicht erneut veröffentlicht werden.",
  APP_RELEASE_FILE_MISSING: "Die APK-Datei fehlt auf dem Server.",
  APP_RELEASE_DRAFT: "Entwürfe werden gelöscht, nicht archiviert.",
  APP_RELEASE_NOT_DRAFT: "Veröffentlichte Releases werden archiviert, nicht gelöscht.",
  "Super admin access required": "Nur Super Admins können App-Releases verwalten.",
};

function errorText(err: unknown): string {
  const raw = apiErrorMessage(err, "Aktion fehlgeschlagen.");
  return ERRORS[raw.split(":")[0]] ?? raw;
}

const STATUS: Record<AppReleaseAdmin["status"], { label: string; cls: string }> = {
  draft: { label: "Entwurf", cls: "bg-amber-500/15 text-amber-400" },
  published: { label: "Veröffentlicht", cls: "bg-emerald-500/15 text-emerald-400" },
  archived: { label: "Archiviert", cls: "bg-[var(--admin-hover)] text-[var(--admin-text-muted)]" },
};

const date = (v: string | null) => (v ? new Date(v).toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" }) : "—");

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <AdminCard className="p-4">
      <p className="text-xs font-medium text-[var(--admin-text-secondary)]">{label}</p>
      <p className="mt-1 text-xl font-bold text-[var(--admin-text-primary)]">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-[var(--admin-text-muted)]">{hint}</p>}
    </AdminCard>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: typeof Smartphone; children: React.ReactNode }) {
  return (
    <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-[var(--admin-text-primary)]">
      <Icon size={17} aria-hidden="true" /> {children}
    </h2>
  );
}

function ReleaseRow({ r, onError }: { r: AppReleaseAdmin; onError: (msg: string | null) => void }) {
  const qc = useQueryClient();
  const [notes, setNotes] = useState(r.release_notes);
  const [editing, setEditing] = useState(false);
  const done = () => {
    onError(null);
    qc.invalidateQueries({ queryKey: ["admin-app-releases"] });
  };
  const fail = (e: unknown) => onError(errorText(e));
  const publish = useMutation({ mutationFn: () => publishRelease(r.id), onSuccess: done, onError: fail });
  const archive = useMutation({ mutationFn: () => archiveRelease(r.id), onSuccess: done, onError: fail });
  const remove = useMutation({ mutationFn: () => deleteDraftRelease(r.id), onSuccess: done, onError: fail });
  const save = useMutation({ mutationFn: () => updateReleaseNotes(r.id, notes), onSuccess: () => { setEditing(false); done(); }, onError: fail });
  const busy = publish.isPending || archive.isPending || remove.isPending || save.isPending;

  return (
    <li className="rounded-xl p-4 ring-1 ring-[var(--admin-border)]" data-testid="app-release-row" data-status={r.status}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-base font-bold text-[var(--admin-text-primary)]">{r.version_name}</span>
        <span className="text-xs text-[var(--admin-text-muted)]">versionCode {r.version_code}</span>
        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS[r.status].cls}`}>{STATUS[r.status].label}</span>
        {r.is_latest && <span className="rounded-full bg-[var(--admin-primary)]/20 px-2 py-0.5 text-xs font-semibold text-[var(--admin-primary)]">Aktuell</span>}
      </div>
      <dl className="mt-2 grid gap-x-6 gap-y-1 text-xs text-[var(--admin-text-secondary)] sm:grid-cols-2 lg:grid-cols-4">
        <div><dt className="inline text-[var(--admin-text-muted)]">Größe: </dt><dd className="inline">{formatBytes(r.size_bytes)}</dd></div>
        <div><dt className="inline text-[var(--admin-text-muted)]">Mindestens: </dt><dd className="inline">Android {r.min_android_version}</dd></div>
        <div><dt className="inline text-[var(--admin-text-muted)]">Downloads: </dt><dd className="inline">{r.download_count}</dd></div>
        <div><dt className="inline text-[var(--admin-text-muted)]">Veröffentlicht: </dt><dd className="inline">{date(r.published_at)}</dd></div>
        <div className="sm:col-span-2 lg:col-span-4 break-all"><dt className="inline text-[var(--admin-text-muted)]">SHA-256: </dt><dd className="inline font-mono">{groupChecksum(r.sha256)}</dd></div>
        {r.signer_sha256 && <div className="sm:col-span-2 lg:col-span-4 break-all"><dt className="inline text-[var(--admin-text-muted)]">Signatur: </dt><dd className="inline font-mono">{groupChecksum(r.signer_sha256)}</dd></div>}
      </dl>

      {editing ? (
        <div className="mt-3 space-y-2">
          <AdminTextarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} maxLength={5000} aria-label="Release Notes" />
          <div className="flex gap-2">
            <AdminButton size="sm" onClick={() => save.mutate()} disabled={busy}>Speichern</AdminButton>
            <AdminButton size="sm" variant="ghost" onClick={() => { setNotes(r.release_notes); setEditing(false); }}>Abbrechen</AdminButton>
          </div>
        </div>
      ) : (
        <p className="mt-2 whitespace-pre-line text-sm text-[var(--admin-text-secondary)]">{r.release_notes || <em className="text-[var(--admin-text-muted)]">Keine Release Notes</em>}</p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {r.status !== "archived" && !r.is_latest && (
          <AdminButton size="sm" onClick={() => publish.mutate()} disabled={busy} data-testid="app-release-publish"><Rocket size={14} aria-hidden="true" /> Als aktuell veröffentlichen</AdminButton>
        )}
        {!editing && <AdminButton size="sm" variant="secondary" onClick={() => setEditing(true)} disabled={busy}>Release Notes bearbeiten</AdminButton>}
        <AdminButton size="sm" variant="secondary" onClick={() => downloadReleaseFile(r).catch(fail)} disabled={busy}><Download size={14} aria-hidden="true" /> APK</AdminButton>
        {r.status === "published" && (
          <AdminButton size="sm" variant="ghost" disabled={busy}
                       onClick={() => { if (window.confirm(r.is_latest ? "Aktuellen Release archivieren? Danach ist keine APK zum Download verfügbar, bis ein anderer veröffentlicht wird." : "Release archivieren?")) archive.mutate(); }}>
            <Archive size={14} aria-hidden="true" /> Archivieren
          </AdminButton>
        )}
        {r.status === "draft" && (
          <AdminButton size="sm" variant="danger" disabled={busy} onClick={() => { if (window.confirm("Entwurf und Datei löschen?")) remove.mutate(); }}>
            <Trash2 size={14} aria-hidden="true" /> Entwurf löschen
          </AdminButton>
        )}
      </div>
    </li>
  );
}

export default function AppManagementClient() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [progress, setProgress] = useState<number | null>(null);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["admin-app-releases"], queryFn: listReleases });

  const upload = useMutation({
    mutationFn: () => uploadRelease(file as File, notes, setProgress),
    onSuccess: (r) => {
      setMessage({ kind: "ok", text: `Version ${r.version_name} (versionCode ${r.version_code}) als Entwurf hochgeladen. Jetzt prüfen und veröffentlichen.` });
      setFile(null);
      setNotes("");
      setProgress(null);
      if (fileRef.current) fileRef.current.value = "";
      qc.invalidateQueries({ queryKey: ["admin-app-releases"] });
    },
    onError: (e) => {
      setProgress(null);
      setMessage({ kind: "error", text: errorText(e) });
    },
  });

  const overview = data?.overview;
  const latest = overview?.latest;

  return (
    <div className="space-y-6" data-testid="app-management">
      <AdminPageHeader title="App Management"
                       description="VIZU DEUTSCH für Android (APK) und iPhone (Web-App). Nur Super Admins können Releases hochladen und veröffentlichen." />

      {isError && <AdminCard><p className="text-sm text-[var(--admin-danger)]">{errorText(error)}</p></AdminCard>}

      {/* 1. App Overview + 6. Download Statistics */}
      <section aria-label="App Overview">
        <SectionTitle icon={Smartphone}>App Overview</SectionTitle>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Aktuelle Android-Version" value={isLoading ? "…" : latest ? latest.version_name : "—"} hint={latest ? `versionCode ${latest.version_code}` : "Noch kein Release veröffentlicht"} />
          <Stat label="Downloads gesamt" value={isLoading ? "…" : String(overview?.total_downloads ?? 0)} hint={latest ? `aktuell: ${latest.download_count}` : undefined} />
          <Stat label="Releases" value={isLoading ? "…" : String((overview?.published ?? 0) + (overview?.drafts ?? 0) + (overview?.archived ?? 0))}
                hint={overview ? `${overview.published} veröffentlicht · ${overview.drafts} Entwurf · ${overview.archived} archiviert` : undefined} />
          <Stat label="Package-ID" value={overview?.package ?? "com.vizu.deutsch"} hint="Nie ändern (sonst keine Updates)" />
        </div>
      </section>

      {/* 3. APK Upload */}
      <AdminCard>
        <SectionTitle icon={FileUp}>APK hochladen</SectionTitle>
        <p className="mb-3 text-sm text-[var(--admin-text-secondary)]">
          Version, versionCode, Mindest-Android und Signatur werden aus der APK gelesen. Erlaubt: signierter Release-Build von
          <span className="font-mono"> com.vizu.deutsch</span>, gleicher Signaturschlüssel wie bisher, max. 150 MB. Ein Upload ist zuerst ein Entwurf.
        </p>
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); if (file) { setMessage(null); upload.mutate(); } }}>
          <div>
            <AdminLabel htmlFor="apk-file">APK-Datei</AdminLabel>
            <input id="apk-file" ref={fileRef} type="file" accept=".apk,application/vnd.android.package-archive" data-testid="apk-file"
                   onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                   className="mt-1 block w-full text-sm text-[var(--admin-text-secondary)] file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--admin-hover)] file:px-3 file:py-2 file:font-semibold file:text-[var(--admin-text-primary)]" />
          </div>
          <div>
            {/* 5. Release Notes */}
            <AdminLabel htmlFor="apk-notes">Release Notes (wird Nutzern beim Update gezeigt)</AdminLabel>
            <AdminTextarea id="apk-notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} maxLength={5000} className="mt-1"
                           placeholder="z. B. Neue Battle-Arena, schnellere Lektionen …" />
          </div>
          {progress !== null && (
            <div className="h-2 overflow-hidden rounded-full bg-[var(--admin-hover)]" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-full bg-[var(--admin-primary)] transition-[width]" style={{ width: `${progress}%` }} />
            </div>
          )}
          <AdminButton type="submit" disabled={!file || upload.isPending} data-testid="apk-upload">
            <FileUp size={15} aria-hidden="true" /> {upload.isPending ? `Wird hochgeladen … ${progress ?? 0}%` : "Hochladen"}
          </AdminButton>
        </form>
      </AdminCard>

      {message && (
        <p role="status" className={`rounded-xl p-3 text-sm ${message.kind === "ok" ? "bg-emerald-500/10 text-emerald-400" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>
          {message.text}
        </p>
      )}

      {/* 2. Android Releases + 4. Version Management */}
      <AdminCard>
        <SectionTitle icon={Rocket}>Android Releases</SectionTitle>
        {isLoading ? (
          <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen …</p>
        ) : data && data.releases.length > 0 ? (
          <ul className="space-y-3">
            {data.releases.map((r) => <ReleaseRow key={r.id} r={r} onError={(text) => setMessage(text ? { kind: "error", text } : null)} />)}
          </ul>
        ) : (
          <p className="text-sm text-[var(--admin-text-muted)]">Noch keine APK hochgeladen. Die Download-Seite zeigt „Bald verfügbar“.</p>
        )}
      </AdminCard>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* 7. PWA Settings + 8. Installation Guide */}
        <AdminCard>
          <SectionTitle icon={Globe}>PWA (iPhone / iPad) & Installationsanleitung</SectionTitle>
          <dl className="space-y-1 text-sm text-[var(--admin-text-secondary)]">
            <div><dt className="inline text-[var(--admin-text-muted)]">Name: </dt><dd className="inline">VIZU DEUTSCH (Kurzname VIZU)</dd></div>
            <div><dt className="inline text-[var(--admin-text-muted)]">Anzeige: </dt><dd className="inline">standalone, Start /, Farbe #0e1834</dd></div>
            <div><dt className="inline text-[var(--admin-text-muted)]">Icons: </dt><dd className="inline">192, 512, maskable 512, apple-touch-icon 180</dd></div>
            <div><dt className="inline text-[var(--admin-text-muted)]">Offline: </dt><dd className="inline">Service Worker v3, Offline-Seite; Login, Zahlungen, Admin, Battle nie aus dem Cache</dd></div>
          </dl>
          <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Diese Werte stehen im Code (manifest.ts, sw.js); Änderungen gehen per Deploy.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link href="/download" target="_blank" className="inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-card-hover)]">
              <ExternalLink size={13} aria-hidden="true" /> Download-Seite /download
            </Link>
            <a href="/manifest.webmanifest" target="_blank" rel="noreferrer" className="inline-flex h-8 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-card-hover)]">
              <ExternalLink size={13} aria-hidden="true" /> Manifest
            </a>
          </div>
        </AdminCard>

        {/* 9. App Notifications + 10. Device Statistics */}
        <AdminCard>
          <SectionTitle icon={Bell}>App Notifications & Geräte</SectionTitle>
          <p className="text-sm text-[var(--admin-text-secondary)]">
            Push-Benachrichtigungen sind noch <strong>nicht eingerichtet</strong>: Android braucht ein Firebase-Projekt (FCM), iPhone (ab iOS 16.4,
            nur als Home-Bildschirm-App) Web-Push-Schlüssel. Bis dahin erscheinen alle Hinweise wie bisher in der App unter Benachrichtigungen
            (<Link href="/admin/notifications" className="underline">Notifications</Link>).
          </p>
          <p className="mt-3 flex items-start gap-2 text-sm text-[var(--admin-text-secondary)]">
            <BarChart3 size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
            Geräte-Statistik: gezählt werden nur APK-Downloads pro Release (siehe oben). Geräte- oder Nutzerdaten werden nicht gespeichert.
          </p>
        </AdminCard>
      </div>
    </div>
  );
}
