"use client";

import { useEffect, useState } from "react";
import { Headphones } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  getHoerenAudioBlobUrl,
  getHoerenTasks,
  reviewHoeren,
  startHoeren,
  submitHoeren,
  type HoerenTask,
} from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";

import LessonSection from "../common/lesson-section";
import SkillTest from "../skill-test/skill-test";
import ListeningPlayer from "./listening-player";

interface Props {
  lessonId: string;
}

function formatTime(seconds: number | null): string {
  if (!seconds) return "—";
  return `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

/** One audio file of a task: uploaded audio is fetched with the session
 * (never a public URL) and played from memory; legacy tasks keep their URL. */
function TrackAudio({ lessonId, taskId, trackId, external }: { lessonId: string; taskId: string; trackId: string; external: string | null }) {
  const { t } = useTranslation();
  const [src, setSrc] = useState<string | null>(external);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (external) return;
    let url: string | null = null;
    let cancelled = false;
    getHoerenAudioBlobUrl(lessonId, taskId, trackId)
      .then((u) => {
        url = u;
        if (!cancelled) setSrc(u);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [lessonId, taskId, trackId, external]);

  if (failed) return <p className="rounded-xl bg-danger/10 p-4 text-sm text-danger">{t("lessons.hoerenAudioError")}</p>;
  if (!src) return <p className="flex min-h-[56px] items-center text-sm text-text-muted">{t("common.loading")}</p>;
  return <ListeningPlayer src={src} />;
}

/** Every audio file of the task: one player each, labelled when the task has
 * several (e.g. "Audio von Alisa" / "Audio von Alex"). */
function TaskAudio({ lessonId, task }: { lessonId: string; task: HoerenTask }) {
  const tracks = task.external_audio_url ? [] : (task.audio_tracks ?? [{ id: "main", label: null, duration_seconds: null }]);
  if (task.external_audio_url) return <TrackAudio lessonId={lessonId} taskId={task.id} trackId="main" external={task.external_audio_url} />;
  if (tracks.length <= 1 && !tracks[0]?.label) return <TrackAudio lessonId={lessonId} taskId={task.id} trackId={tracks[0]?.id ?? "main"} external={null} />;
  return (
    <div className="grid gap-4 md:grid-cols-2" data-testid="hoeren-audio-tracks">
      {tracks.map((track) => (
        <div key={track.id} className="min-w-0 space-y-2 rounded-xl bg-surface-card p-3 ring-1 ring-surface-border">
          <p className="text-sm font-semibold text-text-primary">
            {track.label ?? "Audio"}
            {track.duration_seconds ? <span className="ml-2 text-xs font-normal text-text-muted">{formatTime(track.duration_seconds)}</span> : null}
          </p>
          <TrackAudio lessonId={lessonId} taskId={task.id} trackId={track.id} external={null} />
        </div>
      ))}
    </div>
  );
}

function HoerenTaskCard({ lessonId, task }: { lessonId: string; task: HoerenTask }) {
  const { t } = useTranslation();
  const [transcript, setTranscript] = useState<string | null>(task.transcript);

  return (
    <div className="space-y-4 rounded-2xl bg-surface-hover p-4 sm:p-6" data-testid="hoeren-task">
      <div>
        <h3 className="text-lg font-bold text-text-primary">{task.title}</h3>
        {task.instruction && <p className="mt-1 text-sm text-text-secondary">{task.instruction}</p>}
        {task.audio_duration_seconds ? (
          <p className="mt-1 text-xs text-text-muted">{t("lessons.hoerenDuration", { time: formatTime(task.audio_duration_seconds) })}</p>
        ) : null}
      </div>

      <TaskAudio lessonId={lessonId} task={task} />

      {task.questions.length > 0 && (
        <SkillTest
          testId="hoeren-test"
          sections={[{ id: task.id, questions: task.questions }]}
          summary={task.summary}
          attempts={task.attempts}
          start={() => startHoeren(lessonId, task.id)}
          submit={(attemptId, answers) => submitHoeren(lessonId, task.id, attemptId, answers)}
          review={(attemptId) => reviewHoeren(lessonId, task.id, attemptId)}
          invalidate={[["hoeren-tasks", lessonId], ["lesson-skill-results", lessonId], ["lesson-score", lessonId]]}
          onResult={(r) => r.transcript && setTranscript(r.transcript)}
        />
      )}

      {transcript && (
        <details className="rounded-xl bg-surface-card p-4 ring-1 ring-surface-border" data-testid="hoeren-transcript">
          <summary className="cursor-pointer text-sm font-semibold text-text-primary">{t("lessons.hoerenTranscript")}</summary>
          <p className="mt-2 whitespace-pre-line text-sm text-text-secondary">{transcript}</p>
        </details>
      )}
    </div>
  );
}

/** Hören: published tasks with audio; questions are graded on the server,
 * the transcript is revealed only after the first submitted attempt. */
export default function ListeningSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const { data: tasks, isLoading, isError } = useQuery({
    queryKey: ["hoeren-tasks", lessonId],
    queryFn: () => getHoerenTasks(lessonId),
  });

  return (
    <LessonSection title={t("lessons.sectionListening")} description={t("lessons.listeningDescription")} icon={Headphones}>
      {isLoading && <p className="text-sm text-text-muted">{t("common.loading")}</p>}
      {isError && <p className="text-sm text-danger">{t("lessons.loadError")}</p>}
      {!isLoading && !isError && (tasks?.length ?? 0) === 0 && (
        <div className="rounded-2xl bg-surface-hover/60 p-6 text-center ring-1 ring-surface-border sm:p-8">
          <p className="text-text-secondary">{t("lessons.hoerenEmpty")}</p>
        </div>
      )}
      <div className="space-y-6">
        {tasks?.map((task) => (
          <HoerenTaskCard key={task.id} lessonId={lessonId} task={task} />
        ))}
      </div>
    </LessonSection>
  );
}
