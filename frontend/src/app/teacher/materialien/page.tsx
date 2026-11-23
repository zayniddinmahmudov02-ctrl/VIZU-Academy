"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Library } from "lucide-react";

import { EmptyState, ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { getTeacherMaterials } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function TeacherMaterialsPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["teacher-materials"], queryFn: getTeacherMaterials });

  return (
    <div data-testid="teacher-materialien">
      <TeacherPageTitle title={t("tpanel.materialsTitle")} subtitle={t("tpanel.materialsSubtitle")}
                        actions={<Link href="/medien/bibliothek" className="inline-flex items-center gap-2 rounded-xl bg-surface-card px-3 py-2 text-sm font-medium text-text-primary ring-1 ring-surface-border hover:bg-surface-hover"><Library size={16} /> {t("tpanel.library")}</Link>} />
      {isLoading && <Loading />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.length === 0 && <EmptyState text={t("tpanel.emptyMaterials")} />}
      <div className="space-y-4">
        {data?.map((c) => (
          <Panel key={c.course_id} title={`${c.level} · ${c.title}`}>
            {c.lessons.length === 0 ? <p className="text-sm text-text-muted">—</p> : (
              <ol className="grid gap-1.5 sm:grid-cols-2">
                {c.lessons.map((l) => (
                  <li key={l.id}><Link href={`/lektion/${l.id}`} className="block truncate rounded-lg px-2 py-1.5 text-sm text-text-primary hover:bg-surface-hover">{l.number}. {l.title}</Link></li>
                ))}
              </ol>
            )}
          </Panel>
        ))}
      </div>
    </div>
  );
}
