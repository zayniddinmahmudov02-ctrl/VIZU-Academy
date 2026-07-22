"use client";

import { Headphones } from "lucide-react";

import Loading from "@/components/common/loading";
import { useLesson } from "@/features/lessons/hooks/use-lesson";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";
import ListeningPlayer from "./listening-player";

interface Props {
  lessonId: string;
}

export default function ListeningSection({ lessonId }: Props) {
  const { t } = useTranslation();
  const { lesson, loading } = useLesson(lessonId);

  return (
    <LessonSection
      title={t("lessons.sectionListening")}
      description={t("lessons.listeningDescription")}
      icon={Headphones}
    >
      {loading ? (
        <Loading />
      ) : lesson?.audioUrl ? (
        <ListeningPlayer src={lesson.audioUrl} />
      ) : (
        <div className="flex aspect-video items-center justify-center rounded-2xl bg-surface-hover text-center">
          <p className="px-6 text-text-secondary">{t("lessons.listeningNotAvailable")}</p>
        </div>
      )}
    </LessonSection>
  );
}
