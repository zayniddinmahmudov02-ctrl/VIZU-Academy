"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ChevronRight, FileJson } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  getCourseStructure,
  resetResultConfig,
  saveResultConfig,
  SKILL_KEYS,
  SKILL_LABELS,
  type ResultConfig,
  type SkillCount,
  type SkillKey,
} from "@/features/admin/services/lms-service";

const TAB_OF: Record<SkillKey, string> = { lesen: "lesen", hoeren: "hoeren", schreiben: "writing", sprechen: "speaking" };

function CountCell({ count, href }: { count: SkillCount; href: string }) {
  const tone =
    count.total === 0
      ? "text-[var(--admin-text-muted)]"
      : count.published === count.total
        ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
        : "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]";
  return (
    <Link
      href={href}
      className={`inline-flex min-w-14 justify-center rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums ${tone}`}
      title={count.total ? `${count.published} veröffentlicht von ${count.total}` : "Noch kein Inhalt"}
    >
      {count.total === 0 ? "—" : `${count.published}/${count.total}`}
    </Link>
  );
}

function ResultConfigCard({ courseId, config, isDefault }: { courseId: string; config: ResultConfig; isDefault: boolean }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ResultConfig>(config);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const required = SKILL_KEYS.filter((k) => form.required.includes(k));
  const total = required.reduce((s, k) => s + (form.weights[k] || 0), 0);
  const equal = new Set(required.map((k) => form.weights[k])).size <= 1;
  const formula = !required.length
    ? "—"
    : equal
      ? `(${required.map((k) => SKILL_LABELS[k]).join(" + ")}) / ${required.length}`
      : `(${required.map((k) => `${SKILL_LABELS[k]}×${form.weights[k]}`).join(" + ")}) / ${total}`;

  async function run(action: () => Promise<{ result_config: ResultConfig }>, ok: string) {
    setBusy(true);
    setMessage(null);
    try {
      const saved = await action();
      // the form shows what the server stored (a reset returns the defaults)
      setForm(saved.result_config);
      await queryClient.invalidateQueries({ queryKey: ["lms-structure", courseId] });
      setMessage({ ok: true, text: ok });
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setBusy(false);
    }
  }

  function save() {
    if (!required.length) return setMessage({ ok: false, text: "Mindestens eine Fertigkeit muss Pflicht sein." });
    if (required.some((k) => !form.weights[k])) return setMessage({ ok: false, text: "Pflicht-Fertigkeiten brauchen ein Gewicht über 0." });
    void run(() => saveResultConfig(courseId, form), "Gespeichert.");
  }

  return (
    <AdminCard className="mb-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-[var(--admin-text-primary)]">Gesamtergebnis einer Lektion</h2>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            Endgültig erst, wenn alle Pflicht-Fertigkeiten bewertet sind; vorher als Zwischenstand. {isDefault ? "Standard: gleiche Gewichte, alle vier Pflicht." : "Eigene Einstellung für dieses Niveau."}
          </p>
        </div>
        <span className="rounded-lg bg-white/[0.04] px-3 py-1.5 font-mono text-xs text-[var(--admin-text-secondary)]" data-testid="result-formula">
          {formula}
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {SKILL_KEYS.map((k) => (
          <div key={k} className="flex items-center justify-between gap-3 rounded-xl bg-white/[0.03] px-3 py-2.5 ring-1 ring-[var(--admin-border)]">
            <label className="flex items-center gap-2 text-sm font-medium text-[var(--admin-text-primary)]">
              <AdminCheckbox
                checked={form.required.includes(k)}
                onCheckedChange={(v) => setForm({ ...form, required: v ? [...form.required, k] : form.required.filter((x) => x !== k) })}
                aria-label={`${SKILL_LABELS[k]} Pflicht`}
              />
              {SKILL_LABELS[k]}
            </label>
            <AdminInput
              type="number"
              min={0}
              max={100}
              className="h-9 w-20"
              value={form.weights[k]}
              onChange={(e) => setForm({ ...form, weights: { ...form.weights, [k]: Number(e.target.value) } })}
              aria-label={`Gewicht ${SKILL_LABELS[k]}`}
            />
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <AdminButton size="sm" onClick={save} disabled={busy} data-testid="result-config-save">
          Speichern
        </AdminButton>
        {!isDefault && (
          <AdminButton size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => resetResultConfig(courseId), "Auf Standard zurückgesetzt.")}>
            Standard wiederherstellen
          </AdminButton>
        )}
        {message && (
          <span className={`text-xs ${message.ok ? "text-[var(--admin-accent)]" : "text-[var(--admin-danger)]"}`} role="status">
            {message.text}
          </span>
        )}
      </div>
    </AdminCard>
  );
}

export default function CourseStructureClient({ courseId }: { courseId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["lms-structure", courseId],
    queryFn: () => getCourseStructure(courseId),
  });

  const lessonCount = data?.modules.reduce((s, m) => s + m.lessons.length, 0) ?? 0;

  return (
    <div>
      <Link
        href="/admin/lms"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        LMS A1–C1
      </Link>

      <AdminPageHeader
        title={data ? `${data.course.level} — ${data.course.title}` : "Kurs"}
        description={data ? `${data.modules.length} Module · ${lessonCount} Lektionen · Zellen: veröffentlicht / gesamt` : undefined}
        action={
          <Link href="/admin/lms/import">
            <AdminButton variant="secondary">
              <FileJson size={16} /> Inhalte importieren
            </AdminButton>
          </Link>
        }
      />

      {isLoading && <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>}
      {isError && <p className="py-10 text-center text-sm text-[var(--admin-danger)]">Kurs konnte nicht geladen werden.</p>}

      {data && <ResultConfigCard courseId={courseId} config={data.result_config} isDefault={data.result_config_is_default} />}

      {data && data.modules.length === 0 && (
        <AdminCard>
          <p className="text-center text-sm text-[var(--admin-text-muted)]">Noch keine Module. Lege sie unter Modules an oder lass sie beim Import anlegen.</p>
        </AdminCard>
      )}

      <div className="space-y-5">
        {data?.modules.map((m) => (
          <AdminCard key={m.id} className="p-0">
            <div className="flex items-center justify-between gap-3 border-b border-[var(--admin-border)] px-5 py-3.5">
              <h2 className="font-bold text-[var(--admin-text-primary)]">
                Modul {m.number}: {m.title}
              </h2>
              <span className="text-xs text-[var(--admin-text-muted)]">
                {m.lessons.length} Lektionen{!m.is_active && " · Inaktiv"}
              </span>
            </div>
            {m.lessons.length === 0 ? (
              <p className="px-5 py-4 text-sm text-[var(--admin-text-muted)]">Keine Lektionen.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] text-sm" data-testid="lms-module-table">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                      <th className="px-5 py-2.5 font-semibold">Lektion</th>
                      {SKILL_KEYS.map((k) => (
                        <th key={k} className="px-2 py-2.5 text-center font-semibold">
                          {SKILL_LABELS[k]}
                        </th>
                      ))}
                      <th className="w-10" />
                    </tr>
                  </thead>
                  <tbody>
                    {m.lessons.map((l) => (
                      <tr key={l.id} className="border-t border-[var(--admin-border)] hover:bg-[var(--admin-hover)]">
                        <td className="px-5 py-2.5">
                          <Link href={`/admin/lessons/${l.id}`} className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]">
                            {l.number}. {l.title}
                          </Link>
                        </td>
                        {SKILL_KEYS.map((k) => (
                          <td key={k} className="px-2 py-2.5 text-center">
                            <CountCell count={l.skills[k]} href={`/admin/lessons/${l.id}?tab=${TAB_OF[k]}`} />
                          </td>
                        ))}
                        <td className="pr-4 text-right">
                          <Link href={`/admin/lessons/${l.id}`} aria-label={`Lektion ${l.number} öffnen`}>
                            <ChevronRight size={16} className="text-[var(--admin-text-muted)]" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </AdminCard>
        ))}
      </div>
    </div>
  );
}
