"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { EmptyState, ErrorState, Loading } from "@/components/teacher/teacher-ui";
import { BackToCatalog } from "@/features/teacher-market/components/student-pages";
import TeacherProfileView from "@/features/teacher-market/components/teacher-profile-view";
import { getTeacherProfile } from "@/features/teacher-market/services/market-service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherProfilePage() {
  const { teacherId } = useParams<{ teacherId: string }>();
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["teacher-profile", teacherId], queryFn: () => getTeacherProfile(teacherId), retry: false });
  const status = (q.error as { response?: { status?: number } } | null)?.response?.status;
  return (
    <div>
      <BackToCatalog />
      {q.isLoading ? <Loading /> : status === 404 ? <EmptyState text={t("market.noTeachers")} testId="teacher-not-found" />
        : q.isError ? <ErrorState onRetry={() => q.refetch()} /> : <TeacherProfileView profile={q.data!} />}
    </div>
  );
}
