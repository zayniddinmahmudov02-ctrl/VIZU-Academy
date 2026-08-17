"use client";

import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, PlayCircle } from "lucide-react";

import Loading from "@/components/common/loading";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useVideoProgress } from "@/features/lessons/hooks/use-video-progress";
import { useTranslation } from "@/lib/i18n/use-translation";
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
  const { video, progress, loading, error, reportProgress, markComplete, reload } = useVideoProgress(lessonId);
  const { user } = useCurrentUser();
  const queryClient = useQueryClient();
  const watermarkText = buildWatermarkText(user);

  const showResume = Boolean(progress && progress.lastPosition > 0 && !progress.completed);

  function handleProgress(position: number, ended: boolean) {
    reportProgress(position, ended);

    if (ended || (video && video.durationSeconds > 0 && position / video.durationSeconds >= 0.95)) {
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
        <div className="flex aspect-video items-center justify-center rounded-card bg-surface-hover text-center">
          <p className="px-6 text-text-secondary">{t("lessons.videoNotAvailable")}</p>
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
            src={video.videoUrl}
            poster={video.thumbnailUrl ?? undefined}
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
