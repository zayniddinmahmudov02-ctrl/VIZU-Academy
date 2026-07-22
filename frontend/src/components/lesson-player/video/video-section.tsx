"use client";

import { PlayCircle } from "lucide-react";

import Loading from "@/components/common/loading";
import { useLesson } from "@/features/lessons/hooks/use-lesson";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import VideoPlayer from "./video-player";

interface Props {
  lessonId: string;
}

export default function VideoSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const { lesson, loading } = useLesson(lessonId);

  return (
    <LessonSection
      title={t("lessons.sectionVideo")}
      description={t("lessons.videoDescription")}
      icon={PlayCircle}
    >
      {loading ? (
        <Loading />
      ) : lesson?.videoUrl ? (
        <VideoPlayer src={lesson.videoUrl} lessonId={lessonId} />
      ) : (
        <div className="flex aspect-video items-center justify-center rounded-card bg-surface-hover text-center">
          <p className="px-6 text-text-secondary">{t("lessons.videoNotAvailable")}</p>
        </div>
      )}
    </LessonSection>
  );
}
