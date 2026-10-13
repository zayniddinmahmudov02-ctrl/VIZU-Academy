"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, CheckCircle2, ExternalLink, EyeOff, Save, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import { getLessonProgress, lmsAdminError, updateLmsLesson, type AdminLmsLesson } from "@/features/admin/services/lms-course-service";
import { COMPETENCY_META, lessonHref } from "@/features/lms/competencies";
import { getLmsLesson } from "@/features/lms/services/lms-service";
import type { CompetencyKind } from "@/features/lms/types";
import { cn } from "@/lib/utils";

import CompetencyPanel, { competencyIsEmpty } from "./competency-panel";
import { PublishBadge } from "./level-lessons";
import ResourceManager from "./resource-manager";
import { UNSAVED_MESSAGE, adminLmsKeys, useAdminLmsLesson, useAdminLmsLessonSync, useCanEditCourses, useUnsavedChangesWarning } from "./use-admin-lms";

type Tab = "lesson" | "competencies" | "preview" | "progress";
const TABS: { value: Tab; label: string }[] = [
  { value: "lesson", label: "Lektion" },
  { value: "competencies", label: "Kompetenzen" },
  { value: "preview", label: "Vorschau" },
  { value: "progress", label: "Fortschritt" },
];

function LessonForm({ data, canEdit, onDirtyChange }: { data: AdminLmsLesson; canEdit: boolean; onDirtyChange: (d: boolean) => void }) {
  const queryClient = useQueryClient();
  const l = data.lesson;
  const initial = useMemo(
    () => ({ title: l.title, description: l.description ?? "", duration: String(l.duration ?? 0), number: String(l.number), access: l.access_override ?? "" }),
    [l],
  );
  const [form, setForm] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const dirty = JSON.stringify(form) !== JSON.stringify(initial);
  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);

  async function save() {
    setBusy(true);
    setMessage(null);
    try {
      const patch: Parameters<typeof updateLmsLesson>[1] = {};
      if (form.title.trim() !== l.title) patch.title = form.title.trim();
      if ((form.description.trim() || null) !== l.description) patch.description = form.description.trim() || null;
      if (Number(form.duration) !== l.duration) patch.duration = Number(form.duration) || 0;
      if (Number(form.number) !== l.number) patch.number = Number(form.number);
      if ((form.access || null) !== l.access_override) patch.access_override = (form.access || null) as "OPEN" | "LOCKED" | null;
      const updated = await updateLmsLesson(l.id, patch);
      queryClient.setQueryData(adminLmsKeys.lesson(l.id), updated);
      await queryClient.invalidateQueries({ queryKey: ["admin-lms", "level"] });
      setMessage({ ok: true, text: "Gespeichert." });
    } catch (err) {
      setMessage({ ok: false, text: lmsAdminError(err, "Speichern fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  return (
    <AdminCard className="max-w-3xl space-y-4" >
      <div className="grid gap-4 sm:grid-cols-[1fr_8rem_8rem]">
        <div>
          <AdminLabel htmlFor="lms-title">Titel</AdminLabel>
          <AdminInput id="lms-title" value={form.title} disabled={!canEdit} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="admin-lesson-title" />
        </div>
        <div>
          <AdminLabel htmlFor="lms-number">Nummer</AdminLabel>
          <AdminInput id="lms-number" type="number" min={1} max={l.lessons_in_level ?? 30} value={form.number} disabled={!canEdit}
                      onChange={(e) => setForm({ ...form, number: e.target.value })} data-testid="admin-lesson-number" />
        </div>
        <div>
          <AdminLabel htmlFor="lms-duration">Dauer (Min.)</AdminLabel>
          <AdminInput id="lms-duration" type="number" min={0} value={form.duration} disabled={!canEdit} onChange={(e) => setForm({ ...form, duration: e.target.value })} />
        </div>
      </div>
      <div>
        <AdminLabel htmlFor="lms-desc">Kurzbeschreibung (Lektionskarte)</AdminLabel>
        <AdminTextarea id="lms-desc" rows={3} value={form.description} disabled={!canEdit} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </div>
      <div className="max-w-sm">
        <AdminLabel htmlFor="lms-access">Zugang (manuell)</AdminLabel>
        <AdminSelect id="lms-access" value={form.access} disabled={!canEdit} onChange={(e) => setForm({ ...form, access: e.target.value })} data-testid="admin-lesson-access">
          <option value="">Standard (Reihenfolge- und Premium-Regeln)</option>
          <option value="OPEN">Geöffnet — ohne Reihenfolge-Sperre</option>
          <option value="LOCKED">Gesperrt — für alle Schüler</option>
        </AdminSelect>
        <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Premium bleibt immer gültig: welche Lektionen kostenlos sind, regeln die Angebote (erste Lektion jedes Niveaus).</p>
      </div>
      {message && <p className={`text-sm ${message.ok ? "text-emerald-500" : "text-[var(--admin-danger)]"}`} role="status" data-testid="admin-lesson-message">{message.text}</p>}
      {canEdit && (
        <div className="flex items-center gap-3">
          <AdminButton disabled={busy || !dirty || !form.title.trim()} onClick={save} data-testid="admin-lesson-save"><Save size={15} /> Speichern</AdminButton>
          {dirty && <span className="text-xs text-amber-500" data-testid="admin-unsaved">Ungespeicherte Änderungen</span>}
        </div>
      )}
    </AdminCard>
  );
}

function Preview({ lessonId }: { lessonId: string }) {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["admin-lms", "preview", lessonId], queryFn: () => getLmsLesson(lessonId) });
  return (
    <AdminCard className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-[var(--admin-text-primary)]">So sehen Schüler diese Lektion</h3>
          <p className="text-sm text-[var(--admin-text-secondary)]">Verborgene Kompetenzen fehlen hier; leere erscheinen als „Nicht verfügbar“.</p>
        </div>
        <div className="flex gap-2">
          <AdminButton size="sm" variant="secondary" onClick={() => refetch()}>Aktualisieren</AdminButton>
          <a href={lessonHref(lessonId)} target="_blank" rel="noopener" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold text-[var(--admin-primary)] ring-1 ring-[var(--admin-border)]">
            Schülerseite öffnen <ExternalLink size={13} />
          </a>
        </div>
      </div>
      <p className="text-xs text-[var(--admin-text-muted)]">Super-Admins öffnen Schülerseiten nach dem Wechsel in das Schüler-Panel (Einstellungen → Panel); andere Admin-Rollen direkt.</p>
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {error ? <p className="text-sm text-[var(--admin-danger)]">Vorschau nicht verfügbar.</p> : null}
      {data && (
        <ol className="grid gap-2 sm:grid-cols-2" data-testid="admin-preview">
          {[...data.competencies].sort((a, b) => a.position - b.position).map((c) => (
            <li key={c.kind} className="flex items-center justify-between gap-2 rounded-xl bg-[var(--admin-hover)] px-3 py-2 text-sm" data-kind={c.kind} data-status={c.status}>
              <span><span className="mr-1 text-[var(--admin-text-muted)]">{c.position}.</span>{COMPETENCY_META[c.kind].name}</span>
              <span className={c.available ? "text-emerald-500" : "text-[var(--admin-text-muted)]"}>{c.available ? (c.tracked ? "mit Aufgaben" : "Text/Material") : "Nicht verfügbar"}</span>
            </li>
          ))}
        </ol>
      )}
    </AdminCard>
  );
}

function ProgressTab({ lessonId }: { lessonId: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useQuery({ queryKey: adminLmsKeys.progress(lessonId, page), queryFn: () => getLessonProgress(lessonId, page) });
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  return (
    <AdminCard className="space-y-3">
      <h3 className="font-semibold text-[var(--admin-text-primary)]">Schülerfortschritt {data ? `(${data.total})` : ""}</h3>
      {isLoading && <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {error ? <p className="text-sm text-[var(--admin-danger)]">{lmsAdminError(error)}</p> : null}
      {data && data.items.length === 0 && <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Schüler in dieser Lektion.</p>}
      {data && data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm" data-testid="admin-progress-table">
            <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="py-2">Schüler</th><th>Lektion</th><th>Kompetenzen</th><th>Letzte Aktivität</th></tr></thead>
            <tbody>
              {data.items.map((s) => {
                const comps = Object.values(s.competencies);
                return (
                  <tr key={s.user_id} className="border-t border-[var(--admin-border)]">
                    <td className="py-2 font-medium text-[var(--admin-text-primary)]">{s.name ?? s.user_id.slice(0, 8)}</td>
                    <td>{s.lesson_completed ? <span className="text-emerald-500">abgeschlossen</span> : "offen"}</td>
                    <td className="text-[var(--admin-text-secondary)]">{comps.filter((c) => c?.status === "completed").length} abgeschlossen · {comps.filter((c) => c?.status === "in_progress").length} in Bearbeitung</td>
                    <td className="text-[var(--admin-text-secondary)]">{s.last_activity_at ? new Date(s.last_activity_at).toLocaleString("de-DE") : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {pages > 1 && (
        <div className="flex items-center gap-2 text-sm">
          <AdminButton size="sm" variant="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton>
          <span>Seite {page} / {pages}</span>
          <AdminButton size="sm" variant="secondary" disabled={page === pages} onClick={() => setPage(page + 1)}>Weiter</AdminButton>
        </div>
      )}
    </AdminCard>
  );
}

/** VIZU LMS lesson editor: lesson data, the ten competencies (text, videos,
 * content, materials, publish state), student preview and progress. */
export default function LessonEditor({ lessonId }: { lessonId: string }) {
  const canEdit = useCanEditCourses();
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useAdminLmsLesson(lessonId);
  useAdminLmsLessonSync(lessonId);
  const [tab, setTab] = useState<Tab>("competencies");
  const [kind, setKind] = useState<CompetencyKind>("EINFUEHRUNG");
  const [dirtyForm, setDirtyForm] = useState(false);
  const [dirtyBody, setDirtyBody] = useState(false);
  const [confirm, setConfirm] = useState<"publish" | "unpublish" | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const dirty = dirtyForm || dirtyBody;
  useUnsavedChangesWarning(dirty);
  const onFormDirty = useCallback((d: boolean) => setDirtyForm(d), []);
  const onBodyDirty = useCallback((d: boolean) => setDirtyBody(d), []);

  function guard(action: () => void) {
    if (dirty && !window.confirm(UNSAVED_MESSAGE)) return;
    setDirtyForm(false);
    setDirtyBody(false);
    action();
  }

  if (isLoading) return <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>;
  if (error || !data) {
    return (
      <AdminCard>
        <p className="text-sm text-[var(--admin-danger)]">{lmsAdminError(error, "Lektion konnte nicht geladen werden.")}</p>
        <AdminButton variant="secondary" className="mt-3" onClick={() => refetch()}>Erneut versuchen</AdminButton>
      </AdminCard>
    );
  }

  const l = data.lesson;
  const competencies = [...data.competencies].sort((a, b) => a.position - b.position);
  const selected = competencies.find((c) => c.kind === kind) ?? competencies[0];
  const visibleWithContent = competencies.filter((c) => c.is_published && !competencyIsEmpty(c)).length;

  async function setPublished(published: boolean) {
    setBusy(true);
    setMessage(null);
    try {
      const updated = await updateLmsLesson(l.id, { is_published: published });
      queryClient.setQueryData(adminLmsKeys.lesson(l.id), updated);
      await queryClient.invalidateQueries({ queryKey: ["admin-lms", "level"] });
    } catch (err) {
      setMessage(lmsAdminError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5" data-testid="admin-lesson-editor">
      {l.level && (
        <Link href={`/admin/kurse/${l.level.toLowerCase()}`} className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--admin-text-secondary)] hover:text-[var(--admin-text-primary)]">
          <ArrowLeft size={15} /> {l.level} — Lektionen
        </Link>
      )}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">{l.level} · Lektion {l.number}{l.lessons_in_level ? ` von ${l.lessons_in_level}` : ""}</p>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--admin-text-primary)]" data-testid="admin-editor-title">{l.title}</h1>
          <p className="mt-1 text-sm text-[var(--admin-text-secondary)]">{visibleWithContent} von 10 Kompetenzen sichtbar mit Inhalt</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span data-testid="admin-lesson-state"><PublishBadge published={l.is_published} /></span>
          {canEdit && (
            <AdminButton variant={l.is_published ? "secondary" : "primary"} disabled={busy} onClick={() => setConfirm(l.is_published ? "unpublish" : "publish")} data-testid="admin-lesson-publish">
              {l.is_published ? <><EyeOff size={15} /> Zurückziehen</> : <><Upload size={15} /> Veröffentlichen</>}
            </AdminButton>
          )}
        </div>
      </div>
      {!canEdit && <p className="rounded-xl bg-amber-500/10 p-3 text-sm text-amber-600" data-testid="admin-readonly">Nur Lesezugriff — Inhalte ändern dürfen Super-Admin, Admin und Content-Manager.</p>}
      {message && <p className="text-sm text-[var(--admin-danger)]" role="alert">{message}</p>}

      <div className="flex flex-wrap gap-1 rounded-xl bg-[var(--admin-card)] p-1.5 ring-1 ring-[var(--admin-border)]" role="tablist">
        {TABS.map((t) => (
          <button key={t.value} type="button" role="tab" aria-selected={tab === t.value} data-testid={`admin-tab-${t.value}`}
                  onClick={() => t.value !== tab && guard(() => setTab(t.value))}
                  className={cn("rounded-lg px-3.5 py-2 text-sm font-medium transition-colors", tab === t.value ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)]")}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "lesson" && (
        <div className="space-y-5">
          <LessonForm key={JSON.stringify(l)} data={data} canEdit={canEdit} onDirtyChange={onFormDirty} />
          <AdminCard className="max-w-3xl">
            <ResourceManager lessonId={l.id} competency={null} resources={data.resources.filter((r) => r.competency === null)} canEdit={canEdit} />
          </AdminCard>
        </div>
      )}

      {tab === "competencies" && (
        <div className="lg:grid lg:grid-cols-[17rem_minmax(0,1fr)] lg:items-start lg:gap-5">
          <nav className="mb-5 lg:sticky lg:top-4 lg:mb-0" aria-label="Kompetenzen">
            <ol className="flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible" data-testid="admin-competency-list">
              {competencies.map((c) => {
                const empty = competencyIsEmpty(c);
                return (
                  <li key={c.kind} data-kind={c.kind}>
                    <button type="button" onClick={() => c.kind !== selected.kind && guard(() => setKind(c.kind))}
                            className={cn("flex w-full min-w-max items-center gap-2 rounded-xl px-3 py-2 text-left text-sm lg:min-w-0",
                              c.kind === selected.kind ? "bg-[var(--admin-primary)] text-white" : "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border)] hover:bg-[var(--admin-hover)]")}>
                      <span className="w-5 text-xs opacity-70">{c.position}.</span>
                      <span className="flex-1 truncate font-medium">{COMPETENCY_META[c.kind].name}</span>
                      {empty && <AlertTriangle size={13} className="shrink-0 text-amber-400" aria-label="kein Inhalt" />}
                      {c.is_published ? <CheckCircle2 size={14} className="shrink-0" aria-label="sichtbar" /> : <EyeOff size={14} className="shrink-0 opacity-60" aria-label="verborgen" />}
                    </button>
                  </li>
                );
              })}
            </ol>
          </nav>
          <CompetencyPanel key={selected.kind} data={data} competency={selected} canEdit={canEdit} onDirtyChange={onBodyDirty} />
        </div>
      )}

      {tab === "preview" && <Preview lessonId={l.id} />}
      {tab === "progress" && <ProgressTab lessonId={l.id} />}

      <ConfirmDialog
        open={confirm !== null}
        onOpenChange={(o) => !o && setConfirm(null)}
        title={confirm === "publish" ? "Lektion veröffentlichen" : "Lektion zurückziehen"}
        description={confirm === "publish"
          ? `„${l.title}“ wird für Schüler sichtbar. ${visibleWithContent === 0 ? "Achtung: noch keine sichtbare Kompetenz mit Inhalt." : `${visibleWithContent} Kompetenzen mit Inhalt sind sichtbar.`}`
          : "Die Lektion wird wieder zum Entwurf und verschwindet für Schüler (ihr Fortschritt bleibt erhalten)."}
        confirmLabel={confirm === "publish" ? "Veröffentlichen" : "Zurückziehen"}
        pendingLabel="Wird gespeichert..."
        variant={confirm === "publish" ? "primary" : "danger"}
        isPending={busy}
        onConfirm={() => { const p = confirm === "publish"; setConfirm(null); setPublished(p); }}
      />
    </div>
  );
}
