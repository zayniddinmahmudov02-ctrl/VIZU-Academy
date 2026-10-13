"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CheckCircle2, Layers, RefreshCw, Wand2 } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import { ensureStructure, getStorageHealth, lmsAdminError, updateLevel, type AdminLevelSummary } from "@/features/admin/services/lms-course-service";

import { adminLmsKeys, useAdminLevels, useCanEditCourses } from "./use-admin-lms";

function LevelCard({ level, canEdit }: { level: AdminLevelSummary; canEdit: boolean }) {
  const queryClient = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const complete = level.lessons_existing === level.lessons_target && level.numbers_missing.length === 0;

  async function run(action: () => Promise<string>) {
    setBusy(true);
    setMessage(null);
    try {
      setMessage({ ok: true, text: await action() });
      await queryClient.invalidateQueries({ queryKey: ["admin-lms"] });
    } catch (err) {
      setMessage({ ok: false, text: lmsAdminError(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminCard className="flex flex-col gap-4" >
      <div className="flex items-start justify-between gap-3" data-testid="admin-lms-level" data-level={level.level}>
        <div>
          <p className="text-3xl font-bold text-[var(--admin-text-primary)]">{level.level}</p>
          <p className="text-sm text-[var(--admin-text-secondary)]">{level.title ?? "Noch nicht angelegt"}</p>
        </div>
        {complete ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-500"><CheckCircle2 size={13} /> Vollständig</span>
        ) : (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-500"><AlertTriangle size={13} /> Unvollständig</span>
        )}
      </div>

      <dl className="grid grid-cols-3 gap-2 text-center text-sm">
        <div className="rounded-xl bg-[var(--admin-hover)] p-2"><dt className="text-[11px] text-[var(--admin-text-muted)]">Soll</dt><dd className="text-lg font-bold" data-testid="admin-level-target">{level.lessons_target}</dd></div>
        <div className="rounded-xl bg-[var(--admin-hover)] p-2"><dt className="text-[11px] text-[var(--admin-text-muted)]">Angelegt</dt><dd className="text-lg font-bold" data-testid="admin-level-existing">{level.lessons_existing}</dd></div>
        <div className="rounded-xl bg-[var(--admin-hover)] p-2"><dt className="text-[11px] text-[var(--admin-text-muted)]">Veröffentlicht</dt><dd className="text-lg font-bold">{level.lessons_published}</dd></div>
      </dl>

      {level.numbers_missing.length > 0 && (
        <p className="text-xs text-[var(--admin-text-secondary)]">Fehlende Lektionsnummern: {level.numbers_missing.join(", ")}</p>
      )}
      {level.numbers_outside_range.length > 0 && (
        <p className="text-xs text-amber-500">Lektionen außerhalb 1–{level.lessons_target}: {level.numbers_outside_range.join(", ")}</p>
      )}

      <label className="flex cursor-pointer items-center gap-2.5 text-sm text-[var(--admin-text-secondary)]">
        <AdminCheckbox
          checked={level.sequential_unlock}
          disabled={!canEdit || busy || !level.course_id}
          onCheckedChange={(checked) => run(async () => {
            await updateLevel(level.level, checked);
            return checked ? "Lektionen öffnen sich jetzt nacheinander." : "Alle Lektionen sind wieder frei zugänglich (Premium-Regeln bleiben).";
          })}
        />
        Lektionen nacheinander freischalten
      </label>

      {message && <p className={`text-sm ${message.ok ? "text-emerald-500" : "text-[var(--admin-danger)]"}`} role="status">{message.text}</p>}

      <div className="mt-auto flex flex-wrap gap-2">
        <Link href={`/admin/kurse/${level.level.toLowerCase()}`} className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-[var(--admin-primary)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--admin-primary-hover)]">
          Lektionen <ArrowRight size={14} />
        </Link>
        {canEdit && !complete && (
          <AdminButton variant="secondary" disabled={busy} onClick={() => setConfirm(true)} data-testid="admin-ensure-structure">
            <Wand2 size={14} /> Struktur anlegen
          </AdminButton>
        )}
      </div>

      <ConfirmDialog
        open={confirm}
        onOpenChange={setConfirm}
        title={`${level.level}: fehlende Lektionen anlegen`}
        description={`Legt die fehlenden Lektionen ${level.numbers_missing.length ? level.numbers_missing.join(", ") : ""} als Entwurf an (nicht sichtbar für Schüler). Vorhandene Lektionen werden weder gelöscht noch umnummeriert.`}
        confirmLabel="Anlegen"
        pendingLabel="Wird angelegt..."
        variant="primary"
        isPending={busy}
        onConfirm={() => {
          setConfirm(false);
          run(async () => {
            const r = await ensureStructure(level.level);
            return r.created.lessons.length ? `${r.created.lessons.length} Entwürfe angelegt.` : "Nichts zu tun — alles vorhanden.";
          });
        }}
      />
    </AdminCard>
  );
}

function StorageHealthCard() {
  const [enabled, setEnabled] = useState(false);
  const { data, isFetching, error, refetch } = useQuery({ queryKey: adminLmsKeys.health("all"), queryFn: () => getStorageHealth(), enabled });
  return (
    <AdminCard className="space-y-3" >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-[var(--admin-text-primary)]">Dateien prüfen</h2>
          <p className="text-sm text-[var(--admin-text-secondary)]">Videos, Untertitel, Materialien und Hören-Audios: liegt jede Datei auf dem Server?</p>
        </div>
        <AdminButton variant="secondary" disabled={isFetching} onClick={() => (enabled ? refetch() : setEnabled(true))} data-testid="admin-storage-check">
          <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} /> {isFetching ? "Wird geprüft..." : "Jetzt prüfen"}
        </AdminButton>
      </div>
      {error ? <p className="text-sm text-[var(--admin-danger)]">{lmsAdminError(error)}</p> : null}
      {data && (
        <div className="space-y-2 text-sm" data-testid="admin-storage-result">
          <p className={data.totals.missing ? "text-amber-500" : "text-emerald-500"}>
            {data.totals.checked} Dateien geprüft · {data.totals.missing} fehlen
          </p>
          {data.lessons.map((l) => (
            <div key={l.lesson_id} className="rounded-xl bg-[var(--admin-hover)] p-3">
              <Link href={`/admin/kurse/lektion/${l.lesson_id}`} className="font-semibold text-[var(--admin-text-primary)] hover:underline">
                {l.level} · Lektion {l.number}: {l.title}
              </Link>
              <ul className="mt-1 space-y-0.5 text-[var(--admin-text-secondary)]">
                {l.problems.map((p) => (
                  <li key={`${p.kind}-${p.id}`}>{p.kind}: „{p.title}“ — {p.status === "missing" ? "Datei fehlt" : "keine Datei"}{p.published ? " (veröffentlicht!)" : ""}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </AdminCard>
  );
}

export default function LevelsOverview() {
  const canEdit = useCanEditCourses();
  const { data, isLoading, error, refetch } = useAdminLevels();
  return (
    <div className="space-y-6">
      <AdminPageHeader
        title="Kurse A1–C1"
        description={data ? `${data.total_lessons_target} Lektionen in fünf Niveaus — Struktur, Lektionen, Kompetenzen und Materialien.` : "Struktur, Lektionen, Kompetenzen und Materialien."}
        action={<Layers size={22} className="text-[var(--admin-text-muted)]" />}
      />
      {!canEdit && <p className="rounded-xl bg-amber-500/10 p-3 text-sm text-amber-600">Nur Lesezugriff — Inhalte ändern dürfen Super-Admin, Admin und Content-Manager.</p>}
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {error ? (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">{lmsAdminError(error, "Niveaus konnten nicht geladen werden.")}</p>
          <AdminButton variant="secondary" className="mt-3" onClick={() => refetch()}>Erneut versuchen</AdminButton>
        </AdminCard>
      ) : null}
      {data && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.levels.map((level) => <LevelCard key={level.level} level={level} canEdit={canEdit} />)}
        </div>
      )}
      <StorageHealthCard />
    </div>
  );
}
