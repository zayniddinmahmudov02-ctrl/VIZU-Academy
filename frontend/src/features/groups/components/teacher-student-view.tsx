"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { getStudentDetail } from "../groups-service";
import ProgressDetail from "./progress-detail";
import { card, ErrorBox, fmtDate, Loading } from "./ui";

/** One student inside one group: LMS progress, tasks, submissions (gradable), activity. */
export default function TeacherStudentView({ groupId, studentId }: { groupId: string; studentId: string }) {
  const { t } = useTranslation();
  const detail = useQuery({ queryKey: ["groups", groupId, "student", studentId], queryFn: () => getStudentDetail(groupId, studentId), retry: false });

  return (
    <div className="space-y-5">
      <Link href={`/teacher/groups/${groupId}?tab=students`} className="inline-flex items-center gap-1 text-sm font-semibold text-text-secondary hover:text-text-primary">
        <ArrowLeft size={14} /> {t("groups.back")}
      </Link>
      {detail.isLoading ? <Loading /> : detail.isError || !detail.data ? <ErrorBox error={detail.error} /> : (
        <>
          <div className={cn(card, "p-5")}>
            <h1 className="text-xl font-bold text-text-primary">{detail.data.student.name}</h1>
            <p className="text-sm text-text-secondary">{detail.data.student.email} · {fmtDate(detail.data.student.joined_at)}</p>
          </div>
          <ProgressDetail detail={detail.data} grading onGraded={() => detail.refetch()} />
        </>
      )}
    </div>
  );
}
