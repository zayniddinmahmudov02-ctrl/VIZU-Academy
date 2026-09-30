"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PenLine, RotateCcw, Sparkles } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import LevelFilter, { ALL_LEVELS, levelSortKey } from "@/components/teacher/level-filter";
import {
  aiEvaluateVorbereitungWriting,
  getTeacherLegacyWritingSubmissions,
  getTeacherVizuMockWriting,
  getTeacherVizuMockWritingDetail,
  getTeacherVorbereitungWriting,
  gradeTeacherLegacyWritingSubmission,
  gradeTeacherVizuMockWritingTask,
  reviewVorbereitungWriting,
  setTeacherVizuMockWritingFeedback,
} from "@/features/teacher/services/teacher.service";
import type {
  TeacherLegacyWritingItem,
  TeacherMockWritingItem,
  VizuMockTeacherWritingDetail,
  VizuMockTeacherWritingListItem,
} from "@/features/teacher/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

type Source = "LEKTIONEN" | "VORBEREITUNG" | "VIZU_MOCK";

const COURSE_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
const EXAM_LEVELS = [...COURSE_LEVELS, "Multilevel"] as const;

// A Multilevel Modelltest is its own exam level, never filed under B1/B2/C1.
function examLevel(item: TeacherMockWritingItem): string {
  return item.provider_name.toLowerCase().includes("multilevel") ? "Multilevel" : item.level_code;
}

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
  const { t } = useTranslation();
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
          {t("teacher.sourceCourses")}
        </button>
        <button
          onClick={() => setSource("VORBEREITUNG")}
          className={cn(
            "min-h-11 flex-1 rounded-lg px-3 py-2 text-xs font-bold transition-colors",
            source === "VORBEREITUNG" ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
          )}
        >
          {t("vorbereitung.title")}
        </button>
        <button
          onClick={() => setSource("VIZU_MOCK")}
          className={cn(
            "min-h-11 flex-1 rounded-lg px-3 py-2 text-xs font-bold transition-colors",
            source === "VIZU_MOCK" ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
          )}
        >
          VIZU-MOCK
        </button>
      </div>

      {source === "LEKTIONEN" && <LegacyWritingQueue />}
      {source === "VORBEREITUNG" && <VorbereitungWritingQueue />}
      {source === "VIZU_MOCK" && <VizuMockWritingQueue />}
    </div>
  );
}

function LegacyWritingQueue() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof LEKTIONEN_TABS)[number]["key"]>("");
  const [active, setActive] = useState<TeacherLegacyWritingItem | null>(null);
  const [level, setLevel] = useState<string>(ALL_LEVELS);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-legacy-writing", tab],
    queryFn: () => getTeacherLegacyWritingSubmissions({ status: tab || undefined }),
  });

  const counts = useMemo(() => {
    const result: Record<string, number> = {};
    for (const item of allItems ?? []) result[item.course_level] = (result[item.course_level] ?? 0) + 1;
    return result;
  }, [allItems]);
  const items = useMemo(
    () => (allItems ?? []).filter((item) => level === ALL_LEVELS || item.course_level === level),
    [allItems, level],
  );

  const groups = useMemo(() => {
    const byLevel = new Map<string, TeacherLegacyWritingItem[]>();
    for (const item of items) {
      const list = byLevel.get(item.course_level) ?? [];
      list.push(item);
      byLevel.set(item.course_level, list);
    }
    return Array.from(byLevel.entries()).sort(([a], [b]) => levelSortKey(a) - levelSortKey(b));
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

      <div className="mt-3">
        <LevelFilter
          levels={COURSE_LEVELS}
          counts={counts}
          active={level}
          onChange={(next) => {
            setLevel(next);
            setActive(null);
          }}
        />
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
  // Grouped per exam level, so a level's submissions are never mixed with
  // another's (Multilevel is its own level, labelled by its provider).
  const byZertifikat = new Map<string, { level: string; byModelTest: Map<string, TeacherMockWritingItem[]> }>();
  for (const item of items) {
    const level = examLevel(item);
    const zertifikatKey = level === "Multilevel" ? item.provider_name : `${item.provider_name} · ${item.level_code}`;
    const group = byZertifikat.get(zertifikatKey) ?? { level, byModelTest: new Map<string, TeacherMockWritingItem[]>() };
    const list = group.byModelTest.get(item.model_test_title) ?? [];
    list.push(item);
    group.byModelTest.set(item.model_test_title, list);
    byZertifikat.set(zertifikatKey, group);
  }
  return Array.from(byZertifikat.entries())
    .sort(([, a], [, b]) => levelSortKey(a.level) - levelSortKey(b.level))
    .map(([key, group]) => ({
      key,
      label: key,
      modelTests: Array.from(group.byModelTest.entries()).map(([title, modelTestItems]) => ({
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
  const [level, setLevel] = useState<string>(ALL_LEVELS);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-vorbereitung-writing"],
    queryFn: () => getTeacherVorbereitungWriting(),
  });

  const statusItems = useMemo(
    () => (allItems ?? []).filter((item) => tab === "ALLE" || vorbereitungStatus(item) === tab),
    [allItems, tab],
  );
  const counts = useMemo(() => {
    const result: Record<string, number> = {};
    for (const item of statusItems) result[examLevel(item)] = (result[examLevel(item)] ?? 0) + 1;
    return result;
  }, [statusItems]);
  const items = useMemo(
    () => statusItems.filter((item) => level === ALL_LEVELS || examLevel(item) === level),
    [statusItems, level],
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

      <div className="mt-3">
        <LevelFilter
          levels={EXAM_LEVELS}
          counts={counts}
          active={level}
          onChange={(next) => {
            setLevel(next);
            setActive(null);
          }}
        />
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

// ==========================
// VIZU-MOCK Schreiben — flat list (VIZU-Mock has no course/Zertifikat
// grouping to speak of, one item per attempt, all 5 Aufgabe graded
// together). Status buckets are computed server-side from graded_count.
// ==========================

const VIZU_MOCK_TABS: { key: "" | "NEW" | "IN_PROGRESS" | "GRADED"; label: string }[] = [
  { key: "", label: "Alle" },
  { key: "NEW", label: "Neue Einsendungen" },
  { key: "IN_PROGRESS", label: "In Bewertung" },
  { key: "GRADED", label: "Bewertet" },
];

function VizuMockWritingQueue() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<(typeof VIZU_MOCK_TABS)[number]["key"]>("");
  const [activeId, setActiveId] = useState<string | null>(null);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-vizu-mock-writing"],
    queryFn: getTeacherVizuMockWriting,
  });

  const items = useMemo(
    () => (allItems ?? []).filter((item) => tab === "" || item.status === tab),
    [allItems, tab],
  );

  return (
    <>
      <div className="flex gap-1.5 overflow-x-auto rounded-xl bg-surface-hover p-1 ring-1 ring-surface-border">
        {VIZU_MOCK_TABS.map((tb) => (
          <button
            key={tb.key}
            onClick={() => {
              setTab(tb.key);
              setActiveId(null);
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
          <div className="space-y-2">
            {items.map((item) => (
              <VizuMockWritingListRow
                key={item.attempt_id}
                item={item}
                active={activeId === item.attempt_id}
                onClick={() => setActiveId(item.attempt_id)}
              />
            ))}
          </div>

          <div>
            {activeId ? (
              <VizuMockWritingDetailCard attemptId={activeId} />
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

const VIZU_MOCK_STATUS_LABEL: Record<string, string> = {
  NEW: "Neu",
  IN_PROGRESS: "In Bewertung",
  GRADED: "Bewertet",
};

function VizuMockWritingListRow({
  item,
  active,
  onClick,
}: {
  item: VizuMockTeacherWritingListItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full rounded-2xl p-4 text-left ring-1 transition-colors",
        active ? "bg-accent-blue/10 ring-accent-blue/30" : "bg-surface-card ring-surface-border hover:bg-surface-hover",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-bold text-text-primary">{item.student_name}</p>
          <p className="mt-0.5 text-xs text-text-muted">
            VIZU-MOCK · {new Date(item.schreiben_submitted_at).toLocaleDateString("de-DE")}
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-accent-blue/10 px-2 py-0.5 text-[10px] font-bold text-accent-blue">
          {VIZU_MOCK_STATUS_LABEL[item.status]}
        </span>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        {item.schreiben_score !== null ? `${item.schreiben_score}/${item.max_score} Punkte` : `${item.graded_count}/${item.total_tasks} bewertet`}
      </p>
    </button>
  );
}

function VizuMockWritingDetailCard({ attemptId }: { attemptId: string }) {
  const queryClient = useQueryClient();
  const { data: detail, isLoading } = useQuery({
    queryKey: ["teacher-vizu-mock-writing-detail", attemptId],
    queryFn: () => getTeacherVizuMockWritingDetail(attemptId),
  });

  const [feedback, setFeedback] = useState("");
  const [feedbackSaving, setFeedbackSaving] = useState(false);
  const [feedbackTouched, setFeedbackTouched] = useState(false);

  const currentFeedback = feedbackTouched ? feedback : detail?.schreiben_feedback ?? "";

  function invalidate(updated: VizuMockTeacherWritingDetail) {
    queryClient.setQueryData(["teacher-vizu-mock-writing-detail", attemptId], updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-vizu-mock-writing"] });
  }

  async function handleSaveFeedback() {
    setFeedbackSaving(true);
    try {
      const updated = await setTeacherVizuMockWritingFeedback(attemptId, currentFeedback || null);
      invalidate(updated);
      setFeedbackTouched(false);
    } finally {
      setFeedbackSaving(false);
    }
  }

  if (isLoading || !detail) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center rounded-card bg-surface-card text-sm text-text-muted ring-1 ring-surface-border">
        Wird geladen...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h3 className="text-base font-bold text-text-primary">VIZU-MOCK — Schreiben</h3>
        <p className="text-xs text-text-muted">
          {detail.student_name} ({detail.email}) · {detail.username} · eingereicht am{" "}
          {new Date(detail.schreiben_submitted_at).toLocaleString("de-DE")}
        </p>
        <div className="mt-3 flex items-center gap-4">
          <p className="text-lg font-bold text-text-primary">
            Gesamt: {detail.schreiben_score ?? 0}/100 Punkte
          </p>
          {detail.schreiben_level && (
            <span className="rounded-full bg-accent-blue/10 px-2.5 py-1 text-xs font-bold text-accent-blue">
              Schreiben-Niveau: {detail.schreiben_level}
            </span>
          )}
        </div>
      </div>

      {detail.submissions.map((submission) => (
        <VizuMockWritingTaskGradeCard
          key={submission.task_id}
          attemptId={attemptId}
          submission={submission}
          onGraded={invalidate}
        />
      ))}

      <div className="rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <label className="mb-1 block text-xs font-medium text-text-secondary">Gesamtfeedback</label>
        <textarea
          value={currentFeedback}
          onChange={(e) => {
            setFeedback(e.target.value);
            setFeedbackTouched(true);
          }}
          rows={3}
          className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
        />
        <button
          onClick={handleSaveFeedback}
          disabled={feedbackSaving}
          className="mt-2 flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          <CheckCircle2 size={14} />
          {feedbackSaving ? "Wird gespeichert..." : "Gesamtfeedback speichern"}
        </button>
      </div>
    </div>
  );
}

function VizuMockWritingTaskGradeCard({
  attemptId,
  submission,
  onGraded,
}: {
  attemptId: string;
  submission: VizuMockTeacherWritingDetail["submissions"][number];
  onGraded: (updated: VizuMockTeacherWritingDetail) => void;
}) {
  const [scores, setScores] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const c of submission.rubric_criteria) {
      initial[c.id] = submission.criterion_scores[c.id]?.toString() ?? "";
    }
    return initial;
  });
  const [comment, setComment] = useState(submission.teacher_comment ?? "");
  const [saving, setSaving] = useState(false);

  const total = submission.rubric_criteria.reduce((sum, c) => sum + (Number(scores[c.id]) || 0), 0);
  const maxTotal = submission.rubric_criteria.reduce((sum, c) => sum + c.max_score, 0);

  async function handleSave() {
    setSaving(true);
    try {
      const criterionScores: Record<string, number> = {};
      for (const c of submission.rubric_criteria) {
        criterionScores[c.id] = Math.min(c.max_score, Math.max(0, Number(scores[c.id]) || 0));
      }
      const updated = await gradeTeacherVizuMockWritingTask(attemptId, submission.task_id, {
        criterion_scores: criterionScores,
        comment: comment || null,
      });
      onGraded(updated);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-card bg-surface-card p-6 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-bold text-text-primary">
          Aufgabe {submission.order_index} — {submission.title}
        </h4>
        <span className="shrink-0 rounded-full bg-accent-blue/10 px-2 py-0.5 text-[10px] font-bold text-accent-blue">
          {submission.level}
        </span>
      </div>

      <p className="whitespace-pre-line rounded-xl bg-surface-hover/60 p-3 text-xs text-text-secondary">
        {submission.instruction}
      </p>

      {submission.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={submission.image_url} alt="" className="max-h-48 w-auto rounded-xl object-cover" />
      )}

      <div className="whitespace-pre-line rounded-xl bg-surface-hover p-3 text-sm text-text-primary">
        {submission.content || <span className="text-text-muted">(keine Antwort)</span>}
      </div>
      <p className="text-xs text-text-muted">
        {submission.word_count} Wörter ({submission.min_words}–{submission.max_words})
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        {submission.rubric_criteria.map((c) => (
          <div key={c.id}>
            <label className="mb-1 block text-xs font-medium text-text-secondary">
              {c.name} (0–{c.max_score})
            </label>
            <input
              type="number"
              min={0}
              max={c.max_score}
              value={scores[c.id] ?? ""}
              onChange={(e) => setScores((prev) => ({ ...prev, [c.id]: e.target.value }))}
              className="h-11 w-full rounded-xl bg-surface-hover px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-text-secondary">Kommentar</label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={2}
          className="w-full rounded-xl bg-surface-hover p-3 text-sm text-text-primary ring-1 ring-surface-border outline-none focus:ring-accent-blue"
        />
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-text-primary">
          Aufgabe {submission.order_index}: {total}/{maxTotal}
        </p>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex min-h-11 items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          <CheckCircle2 size={14} />
          {saving ? "Wird gespeichert..." : "Aufgabe speichern"}
        </button>
      </div>
    </div>
  );
}
