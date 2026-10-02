"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Mic, Pause, Play, RotateCcw, Sparkles } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import LevelFilter, { ALL_LEVELS, levelSortKey } from "@/components/teacher/level-filter";
import {
  aiEvaluateVorbereitungSpeaking,
  getTeacherLegacySpeakingAudioBlobUrl,
  getTeacherLegacySpeakingSubmissions,
  getTeacherVorbereitungSpeaking,
  gradeTeacherLegacySpeakingSubmission,
  reviewVorbereitungSpeaking,
} from "@/features/teacher/services/teacher.service";
import VizuMultilevelSpeakingQueue from "@/features/teacher/components/vizu-multilevel-speaking-queue";
import type { TeacherLegacySpeakingItem, TeacherMockSpeakingItem } from "@/features/teacher/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

type Source = "LEKTIONEN" | "VORBEREITUNG" | "VIZU_MULTILEVEL";

const COURSE_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
const EXAM_LEVELS = [...COURSE_LEVELS, "Multilevel"] as const;

// A Multilevel Modelltest is its own exam level, never filed under B1/B2/C1.
function examLevel(item: TeacherMockSpeakingItem): string {
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

function vorbereitungStatus(item: TeacherMockSpeakingItem): VorbereitungTabKey {
  if (item.submission.teacher_score !== null) return "GEPRUEFT";
  if (item.submission.ai_score !== null) return "KI_BEWERTET";
  return "NEU";
}

/** Two real, distinct Sprechen submission sources — never merged into
 * one fake list:
 *
 * "Lektionen" (default) — the legacy per-lesson Speaking task's real
 * StudentSpeaking recordings (app/models/student_speaking.py), scoped to
 * this teacher's TeacherAssignment courses, grouped by course level;
 * audio served through the private, authorization-checked
 * GET /speakings/submissions/{id}/audio.
 *
 * "Vorbereitung" — the real Zertifikat/Modelltest exam-attempt
 * submissions (app/models/mock_speaking_submission.py, populated by the
 * mock-exam attempt flow with a Gemini AI pre-evaluation + transcript),
 * grouped by Zertifikat -> Level -> Modelltest. */
export default function TeacherSprechenPage() {
  const { t } = useTranslation();
  const [source, setSource] = useState<Source>("LEKTIONEN");

  return (
    <div className="space-y-6">
      <PageHeader icon={Mic} titleKey="teacher.navSprechen" gradient="from-accent-blue to-purple-600" />

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
          onClick={() => setSource("VIZU_MULTILEVEL")}
          className={cn(
            "min-h-11 flex-1 rounded-lg px-3 py-2 text-xs font-bold transition-colors",
            source === "VIZU_MULTILEVEL" ? "bg-accent-blue text-white" : "text-text-secondary hover:bg-surface-card",
          )}
        >
          VIZU-Multilevel
        </button>
      </div>

      {source === "LEKTIONEN" && <LegacySpeakingQueue />}
      {source === "VORBEREITUNG" && <VorbereitungSpeakingQueue />}
      {source === "VIZU_MULTILEVEL" && <VizuMultilevelSpeakingQueue />}
    </div>
  );
}

function LegacySpeakingQueue() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof LEKTIONEN_TABS)[number]["key"]>("");
  const [active, setActive] = useState<TeacherLegacySpeakingItem | null>(null);
  const [level, setLevel] = useState<string>(ALL_LEVELS);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-legacy-speaking", tab],
    queryFn: () => getTeacherLegacySpeakingSubmissions({ status: tab || undefined }),
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
    const byLevel = new Map<string, TeacherLegacySpeakingItem[]>();
    for (const item of items) {
      const list = byLevel.get(item.course_level) ?? [];
      list.push(item);
      byLevel.set(item.course_level, list);
    }
    return Array.from(byLevel.entries()).sort(([a], [b]) => levelSortKey(a) - levelSortKey(b));
  }, [items]);

  function handleGraded(updated: TeacherLegacySpeakingItem) {
    setActive(updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-legacy-speaking"] });
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
          <Mic className="mx-auto mb-2 text-text-muted" size={22} />
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
                        {level} · {item.lesson_number}. {item.lesson_title} · Sprechen
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div>
            {active ? (
              <LegacySpeakingGradeCard key={active.id} item={active} onGraded={handleGraded} />
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

function LegacySpeakingGradeCard({
  item,
  onGraded,
}: {
  item: TeacherLegacySpeakingItem;
  onGraded: (updated: TeacherLegacySpeakingItem) => void;
}) {
  const [score, setScore] = useState(item.score ?? 0);
  const [feedback, setFeedback] = useState(item.feedback ?? "");
  const [saving, setSaving] = useState<"GRADED" | "NEEDS_REVISION" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  async function togglePlay() {
    const audio = document.getElementById("teacher-legacy-sprechen-audio") as HTMLAudioElement | null;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    if (!audioUrl) {
      const url = await getTeacherLegacySpeakingAudioBlobUrl(item.id);
      setAudioUrl(url);
      requestAnimationFrame(() => audio.play());
    } else {
      audio.play();
    }
    setPlaying(true);
  }

  async function submit(nextStatus: "GRADED" | "NEEDS_REVISION") {
    if (score < 0 || score > 100 || feedback.trim().length === 0) {
      setError("Bewertung (0-100) und Feedback sind erforderlich.");
      return;
    }
    setError(null);
    setSaving(nextStatus);
    try {
      const updated = await gradeTeacherLegacySpeakingSubmission(item.id, { score, feedback, status: nextStatus });
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
        <h3 className="text-base font-bold text-text-primary">{item.speaking_title}</h3>
        <p className="text-xs text-text-muted">
          {item.student_name} ({item.student_email}) · {item.course_title} ({item.course_level}) · Lektion{" "}
          {item.lesson_number}: {item.lesson_title}
        </p>
      </div>

      <div className="flex items-center gap-3 rounded-xl bg-surface-hover p-4">
        <button
          onClick={togglePlay}
          aria-label={playing ? "Pause" : "Abspielen"}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent-blue text-white"
        >
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <span className="text-xs text-text-secondary">
          {item.duration_seconds != null ? `${item.duration_seconds}s` : "Aufnahme"}
        </span>
        {audioUrl && (
          <audio
            id="teacher-legacy-sprechen-audio"
            src={audioUrl}
            controls
            onEnded={() => setPlaying(false)}
            className="ml-2 h-9 flex-1"
          />
        )}
      </div>

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

interface SpeakingGroup {
  key: string;
  label: string;
  modelTests: { title: string; items: TeacherMockSpeakingItem[] }[];
}

function groupVorbereitungSpeaking(items: TeacherMockSpeakingItem[]): SpeakingGroup[] {
  // Grouped per exam level, so a level's submissions are never mixed with
  // another's (Multilevel is its own level, labelled by its provider).
  const byZertifikat = new Map<string, { level: string; byModelTest: Map<string, TeacherMockSpeakingItem[]> }>();
  for (const item of items) {
    const level = examLevel(item);
    const zertifikatKey = level === "Multilevel" ? item.provider_name : `${item.provider_name} · ${item.level_code}`;
    const group = byZertifikat.get(zertifikatKey) ?? { level, byModelTest: new Map<string, TeacherMockSpeakingItem[]>() };
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

function VorbereitungSpeakingQueue() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<VorbereitungTabKey>("ALLE");
  const [active, setActive] = useState<TeacherMockSpeakingItem | null>(null);
  const [level, setLevel] = useState<string>(ALL_LEVELS);

  const { data: allItems, isLoading } = useQuery({
    queryKey: ["teacher-vorbereitung-speaking"],
    queryFn: () => getTeacherVorbereitungSpeaking(),
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
  const groups = useMemo(() => groupVorbereitungSpeaking(items), [items]);

  function handleReviewed(updated: TeacherMockSpeakingItem) {
    setActive(updated);
    queryClient.invalidateQueries({ queryKey: ["teacher-vorbereitung-speaking"] });
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
          <Mic className="mx-auto mb-2 text-text-muted" size={22} />
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
                          {group.label} · {mt.title} · Sprechen
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
              <MockSpeakingReviewCard key={active.submission.id} item={active} onReviewed={handleReviewed} />
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

function MockSpeakingReviewCard({
  item,
  onReviewed,
}: {
  item: TeacherMockSpeakingItem;
  onReviewed: (updated: TeacherMockSpeakingItem) => void;
}) {
  const sub = item.submission;
  const [teacherScore, setTeacherScore] = useState(sub.teacher_score?.toString() ?? "");
  const [teacherFeedback, setTeacherFeedback] = useState(sub.teacher_feedback ?? "");
  const [evaluating, setEvaluating] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleEvaluate() {
    setEvaluating(true);
    try {
      const updated = await aiEvaluateVorbereitungSpeaking(sub.id);
      onReviewed(updated);
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await reviewVorbereitungSpeaking(sub.id, {
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

      <audio controls src={sub.audio_url} className="w-full">
        <track kind="captions" />
      </audio>

      {sub.ai_score !== null ? (
        <div className="rounded-xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-accent-blue">
            <Sparkles size={12} /> KI-Bewertung — {sub.ai_score} Pkt.
          </p>
          {sub.transcript && (
            <p className="mt-2 whitespace-pre-line text-xs text-text-secondary">Transkript: {sub.transcript}</p>
          )}
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
