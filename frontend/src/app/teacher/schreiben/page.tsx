"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PenLine, RotateCcw, Sparkles } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import {
  aiEvaluateVorbereitungWriting,
  getTeacherLegacyWritingSubmissions,
  getTeacherVorbereitungWriting,
  gradeTeacherLegacyWritingSubmission,
  reviewVorbereitungWriting,
} from "@/features/teacher/services/teacher.service";
import type { TeacherLegacyWritingItem, TeacherMockWritingItem } from "@/features/teacher/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

type Source = "LEKTIONEN" | "VORBEREITUNG";

const LEKTIONEN_TABS = [
  { key: "", label: "Alle" },
  { key: "SUBMITTED", label: "Zu bewerten" },
  { key: "GRADED", label: "Bewertet" },
  { key: "NEEDS_REVISION", label: "Zur Überarbeitung" },
] as const;

type VorbereitungTabKey = "ALLE" | "NEU" | "KI_BEWERTET" | "GEPRUEFT";

const VORBEREITUNG_TABS: { key: VorbereitungTabKey; label: string }[] = [
  { key: "ALLE", label: "Alle" },
  { key: "NEU", label: "Neu" },
  { key: "KI_BEWERTET", label: "KI-bewertet" },
  { key: "GEPRUEFT", label: "Geprüft" },
];

function vorbereitungStatus(item: TeacherMockWritingItem): VorbereitungTabKey {
  if (item.submission.teacher_score !== null) return "GEPRUEFT";
  if (item.submission.ai_score !== null) return "KI_BEWERTET";
  return "NEU";
}

/** Two real, distinct Schreiben submission sources — never merged into
 * one fake list, never shown as duplicates of each other:
 *
 * "Lektionen" (default) — the legacy per-lesson Writing task's real
 * StudentWriting submissions (app/models/student_writing.py), scoped to
 * this teacher's TeacherAssignment courses, grouped by course level so a
 * submission's source is never ambiguous (Course: A1 -> 1. Unterricht).
 *
 * "Vorbereitung" — the real Zertifikat/Modelltest exam-attempt
 * submissions (app/models/mock_writing_submission.py, populated by the
 * mock-exam attempt flow with a Gemini AI pre-evaluation), grouped by
 * Zertifikat -> Level -> Modelltest. This used to point at the
 * Assessment Engine's own WritingSubmission, which that flow never
 * actually writes to — see backend/app/services/mock_exam/
 * teacher_review_service.py's module docstring. */
export default function TeacherSchreibenPage() {
  const [source, setSource] = useState<Source>("LEKTIONEN");

  return (
    <div className="space-y-6">
      <PageHeader icon={PenLine} titleKey="teacher.navSchreiben" gradient="from-accent-blue to-purple-600" />

      <div className="flex gap-1.5 rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
        <button
          onClick={() => setSource("LEKTIONEN")}
          className={cn(
            "min-h-11 flex-1 rounded-lg px-3 py-2 text-xs font-bold transition-colors",
            source === "LEKTIONEN" ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
          )}
        >
          Lektionen
        </button>
        <button
          onClick={() => setSource("VORBEREITUNG")}
          className={cn(
            "min-h-11 flex-1 rounded-lg px-3 py-2 text-xs font-bold transition-colors",
            source === "VORBEREITUNG" ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
          )}
        >
          Vorbereitung
        </button>
      </div>

      {source === "LEKTIONEN" ? <LegacyWritingQueue /> : <VorbereitungWritingQueue />}
    </div>
  );
}

function LegacyWritingQueue() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof LEKTIONEN_TABS)[number]["key"]>("");
  const [active, setActive] = useState<TeacherLegacyWritingItem | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["teacher-legacy-writing", tab],
    queryFn: () => getTeacherLegacyWritingSubmissions({ status: tab || undefined }),
  });

  const groups = useMemo(() => {
    const byLevel = new Map<string, TeacherLegacyWritingItem[]>();
    for (const item of items ?? []) {
      const list = byLevel.get(item.course_level) ?? [];
      list.push(item);
      byLevel.set(item.course_level, list);
    }
    return Array.from(byLevel.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [items]);

  function handleGraded(updated: TeacherLegacyWritingItem) {
    setActive(updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-legacy-writing"] });
    queryClient.invalidateQueries({ queryKey: ["teacher-overview"] });
  }

  return (
    <>
      <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
        {LEKTIONEN_TABS.map((tb) => (
          <button
            key={tb.key}
            onClick={() => {
              setTab(tb.key);
              setActive(null);
            }}
            className={cn(
              "min-h-11 flex-1 shrink-0 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
              tab === tb.key ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
            )}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="mt-4 text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && (items?.length ?? 0) === 0 && (
        <div className="mt-4 rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <PenLine className="mx-auto mb-2 text-text-muted" size={22} />
          <p className="text-sm text-text-muted">Keine Abgaben vorhanden.</p>
        </div>
      )}

      {!isLoading && (items?.length ?? 0) > 0 && (
        <div className="mt-4 grid gap-4 lg:grid-cols-[380px_1fr]">
          <div className="space-y-4">
            {groups.map(([level, levelItems]) => (
              <div key={level}>
                <p className="mb-1.5 px-1 text-[11px] font-bold uppercase tracking-wide text-text-muted">
                  Kurs: {level}
                </p>
                <div className="space-y-2">
                  {levelItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActive(item)}
                      className={cn(
                        "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
                        active?.id === item.id
                          ? "bg-accent-blue/10 ring-accent-blue/30"
                          : "bg-surface-card ring-surface-border hover:bg-surface-hover",
                      )}
                    >
                      <p className="text-sm font-bold text-text-primary">{item.student_name}</p>
                      <p className="mt-0.5 text-xs text-text-muted">
                        {level} · {item.lesson_number}. {item.lesson_title} · Schreiben
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div>
            {active ? (
              <LegacyWritingGradeCard item={active} onGraded={handleGraded} />
            ) : (
              <div className="flex h-full min-h-[200px] items-center justify-center rounded-card bg-surface-card text-sm text-text-muted ring-1 ring-surface-border">
                Wähle eine Abgabe aus der Liste.
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function LegacyWritingGradeCard({
  item,
  onGraded,
}: {
  item: TeacherLegacyWritingItem;
  onGraded: (updated: TeacherLegacyWritingItem) => void;
}) {
  const [score, setScore] = useState(item.score ?? 0);
  const [feedback, setFeedback] = useState(item.feedback ?? "");
  const [saving, setSaving] = useState<"GRADED" | "NEEDS_REVISION" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(nextStatus: "GRADED" | "NEEDS_REVISION") {
    if (score < 0 || score > 100 || feedback.trim().length === 0) {
      setError("Bewertung (0-100) und Feedback sind erforderlich.");
      return;
    }
    setError(null);
    setSaving(nextStatus);
    try {
      const updated = await gradeTeacherLegacyWritingSubmission(item.id, { score, feedback, status: nextStatus });
      onGraded(updated);
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="space-y-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div>
        <h3 className="text-base font-bold text-text-primary">{item.writing_title}</h3>
        <p className="text-xs text-text-muted">
          {item.student_name} ({item.student_email}) · {item.course_title} ({item.course_level}) · Lektion{" "}
          {item.lesson_number}: {item.lesson_title}
        </p>
      </div>

      <div className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary">{item.answer_text}</div>
      <p className="text-xs text-text-muted">
        {item.answer_text.split(/\s+/).filter(Boolean).length} Wörter ({item.min_words}–{item.max_words})
      </p>

      {item.status === "GRADED" ? (
        <div className="rounded-xl bg-surface-hover p-4 ring-1 ring-surface-border">
          <p className="text-sm font-semibold text-text-primary">{item.score}/100 Punkte</p>
          {item.feedback && <p className="mt-1 text-sm text-text-secondary">{item.feedback}</p>}
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Bewertung (0–100)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={score}
                onChange={(e) => setScore(Number(e.target.value))}
                className="h-11 w-full rounded-xl bg-surface-hover px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Feedback</label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={4}
                className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
              />
            </div>
          </div>

          {error && <p className="text-xs text-danger">{error}</p>}

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => submit("NEEDS_REVISION")}
              disabled={saving !== null}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border disabled:opacity-60"
            >
              <RotateCcw size={14} />
              {saving === "NEEDS_REVISION" ? "Wird gespeichert..." : "Zur Überarbeitung"}
            </button>
            <button
              onClick={() => submit("GRADED")}
              disabled={saving !== null}
              className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              <CheckCircle2 size={14} />
              {saving === "GRADED" ? "Wird gespeichert..." : "Bewertung speichern"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

interface WritingGroup {
  key: string;
  label: string;
  modelTests: { title: string; items: TeacherMockWritingItem[] }[];
}

function groupVorbereitungWriting(items: TeacherMockWritingItem[]): WritingGroup[] {
  const byZertifikat = new Map<string, Map<string, TeacherMockWritingItem[]>>();
  for (const item of items) {
    const zertifikatKey = `${item.provider_name} · ${item.level_code}`;
    const byModelTest = byZertifikat.get(zertifikatKey) ?? new Map<string, TeacherMockWritingItem[]>();
    const list = byModelTest.get(item.model_test_title) ?? [];
    list.push(item);
    byModelTest.set(item.model_test_title, list);
    byZertifikat.set(zertifikatKey, byModelTest);
  }
  return Array.from(byZertifikat.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, byModelTest]) => ({
      key,
      label: key,
      modelTests: Array.from(byModelTest.entries()).map(([title, modelTestItems]) => ({
        title,
        items: modelTestItems,
      })),
    }));
}

function VorbereitungWritingQueue() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<VorbereitungTabKey>("ALLE");
  const [active, setActive] = useState<TeacherMockWritingItem | null>(null);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-vorbereitung-writing"],
    queryFn: () => getTeacherVorbereitungWriting(),
  });

  const items = useMemo(
    () => (allItems ?? []).filter((item) => tab === "ALLE" || vorbereitungStatus(item) === tab),
    [allItems, tab],
  );
  const groups = useMemo(() => groupVorbereitungWriting(items), [items]);

  function handleReviewed(updated: TeacherMockWritingItem) {
    setActive(updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-vorbereitung-writing"] });
  }

  return (
    <>
      <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
        {VORBEREITUNG_TABS.map((tb) => (
          <button
            key={tb.key}
            onClick={() => {
              setTab(tb.key);
              setActive(null);
            }}
            className={cn(
              "min-h-11 flex-1 shrink-0 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
              tab === tb.key ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
            )}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="mt-4 text-sm text-text-muted">{t("common.loading")}</p>}

      {!isLoading && items.length === 0 && (
        <div className="mt-4 rounded-card bg-surface-card p-10 text-center shadow-[var(--shadow-md)] ring-1 ring-surface-border">
          <PenLine className="mx-auto mb-2 text-text-muted" size={22} />
          <p className="text-sm text-text-muted">Keine Abgaben vorhanden.</p>
        </div>
      )}

      {!isLoading && items.length > 0 && (
        <div className="mt-4 grid gap-4 lg:grid-cols-[380px_1fr]">
          <div className="space-y-4">
            {groups.map((group) => (
              <div key={group.key}>
                <p className="mb-1.5 px-1 text-[11px] font-bold uppercase tracking-wide text-text-muted">
                  Zertifikat: {group.label}
                </p>
                {group.modelTests.map((mt) => (
                  <div key={mt.title} className="mb-2 space-y-2">
                    <p className="px-1 text-[11px] font-semibold text-text-muted">{mt.title}</p>
                    {mt.items.map((item) => (
                      <button
                        key={item.submission.id}
                        onClick={() => setActive(item)}
                        className={cn(
                          "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
                          active?.submission.id === item.submission.id
                            ? "bg-accent-blue/10 ring-accent-blue/30"
                            : "bg-surface-card ring-surface-border hover:bg-surface-hover",
                        )}
                      >
                        <p className="text-sm font-bold text-text-primary">{item.student_username}</p>
                        <p className="mt-0.5 text-xs text-text-muted">
                          {group.label} · {mt.title} · Schreiben
                        </p>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div>
            {active ? (
              <MockWritingReviewCard key={active.submission.id} item={active} onReviewed={handleReviewed} />
            ) : (
              <div className="flex h-full min-h-[200px] items-center justify-center rounded-card bg-surface-card text-sm text-text-muted ring-1 ring-surface-border">
                Wähle eine Abgabe aus der Liste.
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function MockWritingReviewCard({
  item,
  onReviewed,
}: {
  item: TeacherMockWritingItem;
  onReviewed: (updated: TeacherMockWritingItem) => void;
}) {
  const sub = item.submission;
  const [teacherScore, setTeacherScore] = useState(sub.teacher_score?.toString() ?? "");
  const [teacherFeedback, setTeacherFeedback] = useState(sub.teacher_feedback ?? "");
  const [evaluating, setEvaluating] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleEvaluate() {
    setEvaluating(true);
    try {
      const updated = await aiEvaluateVorbereitungWriting(sub.id);
      onReviewed(updated);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await reviewVorbereitungWriting(sub.id, {
        teacher_score: teacherScore ? Number(teacherScore) : null,
        teacher_feedback: teacherFeedback || null,
      });
      onReviewed(updated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div>
        <h3 className="text-base font-bold text-text-primary">
          {item.provider_name} · {item.level_code} — {item.model_test_title}
        </h3>
        <p className="text-xs text-text-muted">
          {item.student_username} ({item.student_email}) · {item.teil_title}
        </p>
      </div>

      <div className="rounded-xl bg-surface-hover/60 p-4 text-xs text-text-secondary">{item.task_text}</div>

      <div className="rounded-xl bg-surface-hover p-4 text-sm text-text-secondary">{sub.answer_text}</div>
      <p className="text-xs text-text-muted">
        {sub.word_count} Wörter{item.word_limit ? ` (Limit: ${item.word_limit})` : ""}
      </p>

      {sub.ai_score !== null ? (
        <div className="rounded-xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-accent-blue">
            <Sparkles size={12} /> KI-Bewertung
          </p>
          <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-text-secondary">
            <p>Grammatik: {sub.ai_grammar_score}</p>
            <p>Wortschatz: {sub.ai_vocabulary_score}</p>
            <p>Struktur: {sub.ai_structure_score}</p>
            <p>Aufgabe: {sub.ai_task_achievement_score}</p>
            <p>Kohärenz: {sub.ai_coherence_score}</p>
            <p className="font-semibold text-text-primary">Gesamt: {sub.ai_score}</p>
          </div>
          {sub.ai_feedback && <p className="mt-2 whitespace-pre-line text-xs text-text-secondary">{sub.ai_feedback}</p>}
        </div>
      ) : (
        <button
          onClick={handleEvaluate}
          disabled={evaluating}
          className="flex min-h-11 items-center gap-1.5 rounded-xl bg-surface-hover px-4 py-2 text-sm font-semibold text-text-primary ring-1 ring-surface-border disabled:opacity-60"
        >
          <Sparkles size={14} />
          {evaluating ? "Wird bewertet..." : "KI-Bewertung starten"}
        </button>
      )}

      <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Lehrerpunkte</label>
          <input
            type="number"
            value={teacherScore}
            onChange={(e) => setTeacherScore(e.target.value)}
            className="h-11 w-full rounded-xl bg-surface-hover px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Lehrer-Feedback</label>
          <textarea
            value={teacherFeedback}
            onChange={(e) => setTeacherFeedback(e.target.value)}
            rows={4}
            className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
          />
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
      >
        <CheckCircle2 size={14} />
        {saving ? "Wird gespeichert..." : "Bewertung speichern"}
      </button>
    </div>
  );
}
