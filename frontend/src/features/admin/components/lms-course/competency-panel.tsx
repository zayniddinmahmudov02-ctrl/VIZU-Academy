"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Captions, Eye, EyeOff, Save, Trash2, Upload } from "lucide-react";

import { AdminButton, AdminCard, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import RichTextEditor from "@/components/admin/rich-text-editor";
import ExerciseManager from "@/features/admin/components/lesson-skills/exercise-manager";
import GrammarManager from "@/features/admin/components/lesson-skills/grammar-manager";
import HoerenManager from "@/features/admin/components/lesson-skills/hoeren-manager";
import LesenManager from "@/features/admin/components/lesson-skills/lesen-manager";
import WordManager from "@/features/admin/components/lesson-skills/word-manager";
import SpeakingManager from "@/features/admin/components/managers/speaking-manager";
import VideoManager from "@/features/admin/components/managers/video-manager";
import WritingManager from "@/features/admin/components/managers/writing-manager";
import {
  deleteSubtitles,
  lmsAdminError,
  setVideoCompetency,
  setVideoPublished,
  updateCompetency,
  uploadSubtitles,
  type AdminCompetency,
  type AdminLmsLesson,
  type AdminLmsVideo,
} from "@/features/admin/services/lms-course-service";
import { COMPETENCY_META } from "@/features/lms/competencies";
import type { CompetencyKind } from "@/features/lms/types";

import ResourceManager from "./resource-manager";
import { adminLmsKeys } from "./use-admin-lms";

const KINDS = Object.keys(COMPETENCY_META) as CompetencyKind[];

/** Nothing a student could see in this competency (text, videos, resources,
 * tasks / words / rules / exercises) — shown as a clear warning. */
export function competencyIsEmpty(c: AdminCompetency): boolean {
  const n = c.content;
  const counts = [n.videos, n.resources, n.words, n.rules, n.readings, n.listenings, n.frage?.total, n.exercises?.total, n.tasks?.total];
  return !(c.body ?? "").replace(/<[^>]+>/g, "").trim() && counts.every((x) => !x);
}

function contentSummary(c: AdminCompetency): string {
  const n = c.content;
  const parts = [
    n.words ? `${n.words} Wörter` : null,
    n.rules ? `${n.rules} Regeln` : null,
    n.readings ? `${n.readings} Lesetexte` : null,
    n.listenings ? `${n.listenings} Hörtexte` : null,
    n.frage?.total ? `${n.frage.published}/${n.frage.total} Frage` : null,
    n.tasks?.total ? `${n.tasks.published}/${n.tasks.total} Aufgaben` : null,
    n.exercises?.total ? `${n.exercises.published}/${n.exercises.total} Übungssets` : null,
    n.videos ? `${n.videos} Videos` : null,
    n.resources ? `${n.resources} Materialien` : null,
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "kein Inhalt";
}

function ContentManager({ lessonId, kind }: { lessonId: string; kind: CompetencyKind }) {
  switch (kind) {
    case "EINFUEHRUNG":
      return (
        <div className="space-y-6">
          <section>
            <h4 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Videos hochladen und verwalten (alle Videos der Lektion)</h4>
            <VideoManager lessonId={lessonId} />
          </section>
          <section>
            <h4 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Frage des Themas</h4>
            <SpeakingManager lessonId={lessonId} kind="FRAGE" />
          </section>
        </div>
      );
    case "WORTSCHATZ":
      return <WordManager lessonId={lessonId} />;
    case "GRAMMATIK":
      return <GrammarManager lessonId={lessonId} />;
    case "LESEN":
      return <LesenManager lessonId={lessonId} />;
    case "HOEREN":
      return <HoerenManager lessonId={lessonId} />;
    case "SPRECHEN":
      return <SpeakingManager lessonId={lessonId} />;
    case "SCHREIBEN":
      return <WritingManager lessonId={lessonId} />;
    case "UEBUNGEN":
      return <ExerciseManager lessonId={lessonId} skill="UEBUNGEN" label="Übungen" />;
    case "ABSCHLUSSTEST":
      return <ExerciseManager lessonId={lessonId} skill="YAKUNIY" label="Abschlusstest" />;
    case "ZUSAMMENFASSUNG":
      return <p className="text-sm text-[var(--admin-text-secondary)]">Die Zusammenfassung zeigt dem Schüler automatisch seine Ergebnisse der Lektion; oben kann ein eigener Text ergänzt werden.</p>;
  }
}

function VideoRow({ video, canEdit, onDone }: { video: AdminLmsVideo; canEdit: boolean; onDone: (error?: string) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [confirmPublish, setConfirmPublish] = useState(false);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      onDone();
    } catch (err) {
      onDone(lmsAdminError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="flex flex-wrap items-center gap-3 rounded-xl bg-[var(--admin-hover)] p-3" data-testid="admin-competency-video" data-video-id={video.id}>
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-[var(--admin-text-primary)]">{video.title}</p>
        <p className="text-xs text-[var(--admin-text-muted)]">
          {video.file_status === "ok" ? "Datei vorhanden" : video.file_status === "missing" ? "Datei fehlt!" : "keine Datei"} ·{" "}
          {video.has_subtitles ? (video.subtitle_status === "ok" ? "Untertitel ✓" : "Untertitel-Datei fehlt") : "keine Untertitel"}
        </p>
      </div>
      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${video.is_published ? "bg-emerald-500/10 text-emerald-500" : "bg-[var(--admin-card)] text-[var(--admin-text-muted)]"}`}>
        {video.is_published ? "sichtbar" : "Entwurf"}
      </span>
      {canEdit && (
        <div className="flex flex-wrap items-center gap-1">
          <AdminSelect value={video.competency} aria-label="Kompetenz des Videos" className="h-8 w-40 text-xs" disabled={busy}
                       onChange={(e) => run(() => setVideoCompetency(video.id, e.target.value as CompetencyKind))}>
            {KINDS.map((k) => <option key={k} value={k}>{COMPETENCY_META[k].name}</option>)}
          </AdminSelect>
          <AdminButton size="sm" variant="ghost" disabled={busy} title={video.is_published ? "Verbergen" : "Veröffentlichen"} aria-label={video.is_published ? "Verbergen" : "Veröffentlichen"}
                       onClick={() => (video.is_published ? run(() => setVideoPublished(video.id, false)) : setConfirmPublish(true))}>
            {video.is_published ? <EyeOff size={14} /> : <Eye size={14} />}
          </AdminButton>
          <AdminButton size="sm" variant="ghost" disabled={busy} title="WebVTT-Untertitel hochladen" aria-label="Untertitel hochladen" onClick={() => input.current?.click()} data-testid="admin-subtitle-upload">
            <Captions size={14} />
          </AdminButton>
          {video.has_subtitles && (
            <AdminButton size="sm" variant="ghost" disabled={busy} title="Untertitel entfernen" aria-label="Untertitel entfernen" onClick={() => run(() => deleteSubtitles(video.id))}>
              <Trash2 size={14} />
            </AdminButton>
          )}
          <input ref={input} type="file" accept=".vtt,text/vtt" className="hidden" data-testid="admin-subtitle-file"
                 onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) run(() => uploadSubtitles(video.id, f)); }} />
        </div>
      )}
      <ConfirmDialog open={confirmPublish} onOpenChange={setConfirmPublish} title="Video veröffentlichen"
        description={`„${video.title}“ wird für Schüler abspielbar.`} confirmLabel="Veröffentlichen" pendingLabel="Wird veröffentlicht..." variant="primary"
        isPending={busy} onConfirm={() => { setConfirmPublish(false); run(() => setVideoPublished(video.id, true)); }} />
    </li>
  );
}

export default function CompetencyPanel({ data, competency, canEdit, onDirtyChange }: {
  data: AdminLmsLesson;
  competency: AdminCompetency;
  canEdit: boolean;
  onDirtyChange: (dirty: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const lessonId = data.lesson.id;
  const meta = COMPETENCY_META[competency.kind];
  const [body, setBody] = useState(competency.body ?? "");
  const [saved, setSaved] = useState(competency.body ?? "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [confirm, setConfirm] = useState<"publish" | "unpublish" | null>(null);
  const dirty = body !== saved;
  const empty = competencyIsEmpty(competency);
  const videos = data.videos.filter((v) => v.competency === competency.kind);
  const resources = data.resources.filter((r) => r.competency === competency.kind);

  useEffect(() => onDirtyChange(dirty), [dirty, onDirtyChange]);

  async function run(action: () => Promise<unknown>, ok: string) {
    setBusy(true);
    setMessage(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: adminLmsKeys.lesson(lessonId) });
      setMessage({ ok: true, text: ok });
      return true;
    } catch (err) {
      setMessage({ ok: false, text: lmsAdminError(err) });
      return false;
    } finally {
      setBusy(false);
    }
  }

  const Icon = meta.icon;
  return (
    <div className="space-y-6" data-testid="admin-competency-panel" data-kind={competency.kind}>
      <AdminCard className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--admin-primary)]/10 text-[var(--admin-primary)]"><Icon size={18} /></span>
            <div>
              <p className="text-xs font-semibold text-[var(--admin-text-muted)]">Kompetenz {competency.position} / 10</p>
              <h2 className="text-lg font-bold text-[var(--admin-text-primary)]">{meta.name}</h2>
              <p className="text-xs text-[var(--admin-text-secondary)]" data-testid="admin-competency-summary">{contentSummary(competency)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${competency.is_published ? "bg-emerald-500/10 text-emerald-500" : "bg-[var(--admin-hover)] text-[var(--admin-text-muted)]"}`} data-testid="admin-competency-state">
              {competency.is_published ? "Für Schüler sichtbar" : "Verborgen"}
            </span>
            {canEdit && (
              <AdminButton size="sm" variant={competency.is_published ? "secondary" : "primary"} disabled={busy} data-testid="admin-competency-publish"
                           onClick={() => setConfirm(competency.is_published ? "unpublish" : "publish")}>
                {competency.is_published ? <><EyeOff size={14} /> Verbergen</> : <><Upload size={14} /> Veröffentlichen</>}
              </AdminButton>
            )}
          </div>
        </div>

        {empty && (
          <p className="flex items-center gap-2 rounded-xl bg-amber-500/10 p-3 text-sm text-amber-600" data-testid="admin-competency-empty">
            <AlertTriangle size={15} /> Diese Kompetenz hat noch keinen Inhalt — Schüler sehen sie als „Nicht verfügbar“.
          </p>
        )}
        {message && <p className={`text-sm ${message.ok ? "text-emerald-500" : "text-[var(--admin-danger)]"}`} role="status" data-testid="admin-competency-message">{message.text}</p>}

        <div className="space-y-2">
          <p className="text-sm font-semibold text-[var(--admin-text-primary)]">Text {competency.kind === "EINFUEHRUNG" ? "(Thema und Ziele)" : competency.kind === "ZUSAMMENFASSUNG" ? "(Zusammenfassung)" : "(Erklärung, optional)"}</p>
          {canEdit ? (
            <>
              <div data-testid="admin-competency-body"><RichTextEditor value={body} onChange={setBody} placeholder="Text für die Schüler…" /></div>
              <div className="flex items-center gap-3">
                <AdminButton size="sm" disabled={busy || !dirty} data-testid="admin-competency-save"
                             onClick={async () => { const ok = await run(() => updateCompetency(lessonId, competency.kind, { body: body.trim() ? body : null }), "Text gespeichert."); if (ok) setSaved(body); }}>
                  <Save size={14} /> Text speichern
                </AdminButton>
                {dirty && <span className="text-xs text-amber-500" data-testid="admin-unsaved">Ungespeicherte Änderungen</span>}
              </div>
            </>
          ) : (
            // sanitised on the server
            <div className="prose-editor rounded-xl bg-[var(--admin-hover)] p-4 text-sm" dangerouslySetInnerHTML={{ __html: competency.body || "<p>—</p>" }} />
          )}
        </div>
      </AdminCard>

      <AdminCard className="space-y-3">
        <h3 className="font-semibold text-[var(--admin-text-primary)]">Videos dieser Kompetenz</h3>
        {videos.length === 0 ? (
          <p className="text-sm text-[var(--admin-text-muted)]">
            Keine Videos. {competency.kind === "EINFUEHRUNG" ? "Neue Videos unten hochladen." : "Videos werden unter „Einführung“ hochgeladen und hier per Auswahl zugeordnet."}
          </p>
        ) : (
          <ul className="space-y-2">
            {videos.map((v) => (
              <VideoRow key={v.id} video={v} canEdit={canEdit}
                        onDone={(error) => { setMessage(error ? { ok: false, text: error } : null); queryClient.invalidateQueries({ queryKey: adminLmsKeys.lesson(lessonId) }); queryClient.invalidateQueries({ queryKey: ["videos-by-lesson", lessonId] }); }} />
            ))}
          </ul>
        )}
        {competency.kind !== "EINFUEHRUNG" && data.videos.some((v) => v.competency !== competency.kind) && canEdit && (
          <p className="text-xs text-[var(--admin-text-muted)]">Andere Videos der Lektion: in ihrer Kompetenz unter „Kompetenz des Videos“ hierher verschieben.</p>
        )}
      </AdminCard>

      <AdminCard>
        <ContentManager lessonId={lessonId} kind={competency.kind} />
      </AdminCard>

      <AdminCard>
        <ResourceManager lessonId={lessonId} competency={competency.kind} resources={resources} canEdit={canEdit} />
      </AdminCard>

      <ConfirmDialog
        open={confirm !== null}
        onOpenChange={(o) => !o && setConfirm(null)}
        title={confirm === "publish" ? `${meta.name} veröffentlichen` : `${meta.name} verbergen`}
        description={confirm === "publish"
          ? (empty ? "Achtung: diese Kompetenz hat noch keinen Inhalt — Schüler sehen sie als „Nicht verfügbar“." : "Die Kompetenz wird für Schüler sichtbar (sofern die Lektion veröffentlicht ist).")
          : "Schüler sehen diese Kompetenz nicht mehr; ihre Reihenfolge bleibt erhalten."}
        confirmLabel={confirm === "publish" ? "Veröffentlichen" : "Verbergen"}
        pendingLabel="Wird gespeichert..."
        variant={confirm === "publish" ? "primary" : "danger"}
        isPending={busy}
        onConfirm={async () => {
          const publish = confirm === "publish";
          setConfirm(null);
          await run(() => updateCompetency(lessonId, competency.kind, { is_published: publish }), publish ? "Veröffentlicht." : "Verborgen.");
        }}
      />
    </div>
  );
}
