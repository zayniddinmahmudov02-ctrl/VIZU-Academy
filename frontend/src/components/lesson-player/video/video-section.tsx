"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PlayCircle, RotateCcw } from "lucide-react";

import Loading from "@/components/common/loading";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useSectionGate } from "@/features/lessons/hooks/use-section-gate";
import { useVideoProgress } from "@/features/lessons/hooks/use-video-progress";
import { computeSectionProgress } from "@/features/lessons/utils/section-progress";
import { useTranslation } from "@/lib/i18n/use-translation";
import { resolveMediaUrl } from "@/lib/media";
import LessonSection from "../common/lesson-section";
import VideoPlayer from "./video-player";

interface Props {
  lessonId: string;
}

function buildWatermarkText(user: { id: string; firstName: string | null; lastName: string | null } | null): string | undefined {
  if (!user) return undefined;

  const name = [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
  const maskedId = user.id.slice(0, 8);

  return name ? `VIZU Academy · ${name} · ${maskedId}` : `VIZU Academy · ${maskedId}`;
}

function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function VideoSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const { video, progress, loading, error, errorKind, reportProgress, markComplete, reload } = useVideoProgress(lessonId);
  const { user } = useCurrentUser();
  const { data: gate } = useSectionGate(lessonId);
  const router = useRouter();
  const queryClient = useQueryClient();
  const watermarkText = buildWatermarkText(user);

  // A lesson without a published video: the sidebar already hides the
  // Video step (gate.video.applicable = false), but /lessons/{id} always
  // lands here (DEFAULT_SECTION_SLUG). Only when both the backend 404 and
  // the gate agree there is no video, continue with the lesson's first
  // available step instead of parking the student on an empty page. A 404
  // for a video the gate still counts (published, stored file missing)
  // stays here and shows the message + retry.
  const noVideoInLesson = errorKind === "not_found" && gate?.video?.applicable === false;
  const videoFileMissing = errorKind === "not_found" && gate?.video?.applicable === true;
  const firstStepSlug = noVideoInLesson ? computeSectionProgress(gate).visibleSections[0]?.slug : undefined;
  useEffect(() => {
    if (firstStepSlug && firstStepSlug !== "video") router.replace(`/lessons/${lessonId}/${firstStepSlug}`);
  }, [firstStepSlug, lessonId, router]);

  const showResume = Boolean(progress && progress.lastPosition > 0 && !progress.completed);

  function handleProgress(position: number, ended: boolean) {
    reportProgress(position, ended);

    if (ended || (video && video.durationSeconds > 0 && position / video.durationSeconds >= 0.7)) {
      markComplete(ended).then((updated) => {
        if (updated?.completed) {
          queryClient.invalidateQueries({ queryKey: ["section-gate", lessonId] });
        }
      });
    }
  }

  return (
    <LessonSection
      title={t("lessons.sectionVideo")}
      description={t("lessons.videoDescription")}
      icon={PlayCircle}
    >
      {loading ? (
        <Loading />
      ) : error || !video ? (
        <div
          className="flex aspect-video flex-col items-center justify-center gap-4 rounded-card bg-surface-hover text-center"
          role={errorKind === "failed" ? "alert" : undefined}
          data-testid="video-unavailable"
          data-reason={errorKind ?? "empty"}
        >
          <p className="max-w-md px-6 text-text-secondary">
            {t(videoFileMissing ? "lessons.videoFileMissing" : (error ?? "lessons.videoNotAvailable"))}
          </p>
          {(errorKind === "failed" || videoFileMissing) && (
            <button
              type="button"
              onClick={reload}
              className="flex items-center gap-2 rounded-full bg-surface-card px-5 py-2.5 text-sm font-semibold text-text-primary shadow-[var(--shadow-3d-soft)] ring-1 ring-surface-border transition-colors hover:text-accent-blue"
            >
              <RotateCcw size={16} />
              {t("lessons.videoRetry")}
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {progress?.completed ? (
            <div className="mx-auto flex w-full max-w-[960px] items-center gap-2 text-sm font-medium text-success">
              <CheckCircle2 size={16} />
              {t("lessons.videoCompleted")}
            </div>
          ) : showResume ? (
            <p className="mx-auto w-full max-w-[960px] text-sm text-text-secondary">
              {t("lessons.videoResumeFrom", { time: formatTime(progress!.lastPosition) })}
            </p>
          ) : null}

          <VideoPlayer
            src={resolveMediaUrl(video.videoUrl) ?? video.videoUrl}
            poster={resolveMediaUrl(video.thumbnailUrl) ?? undefined}
            lessonId={lessonId}
            initialPosition={progress?.lastPosition ?? 0}
            onProgress={handleProgress}
            watermarkText={watermarkText}
            onRetryLoad={reload}
          />
        </div>
      )}
    </LessonSection>
  );
}
