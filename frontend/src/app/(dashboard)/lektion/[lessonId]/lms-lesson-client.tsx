"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, ChevronRight, Clock, PlayCircle, Video } from "lucide-react";

import LmsCompetencyContent from "@/components/lms/lms-competency-content";
import LmsCompetencyNav from "@/components/lms/lms-competency-nav";
import LmsErrorCard from "@/components/lms/lms-error-card";
import LmsLessonLock from "@/components/lms/lms-lesson-lock";
import LmsResourceList from "@/components/lms/lms-resource-list";
import LmsSkeleton from "@/components/lms/lms-skeleton";
import LmsVideos from "@/components/lms/lms-video";
import LmsStatusBadge from "@/components/lms/lms-status-badge";
import ProgressBar from "@/components/ui/progress-bar";
import { COMPETENCY_META, VIDEO_SLUG, competencyHref, kindFromSlug, lessonHref, levelHref, videoHref } from "@/features/lms/competencies";
import { lmsKeys, useLmsLesson } from "@/features/lms/hooks/use-lms";
import { useLmsLessonSync } from "@/features/lms/hooks/use-lms-sync";
import { visitCompetency } from "@/features/lms/services/lms-service";
import type { LmsCompetency, LmsLesson } from "@/features/lms/types";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function CompetencyCard({ lessonId, c, index }: { lessonId: string; c: LmsCompetency; index: number }) {
  const { t } = useTranslation();
  const meta = COMPETENCY_META[c.kind];
  const Icon = meta.icon;
  const unavailable = c.status === "not_available";
  const locked = c.status === "locked";
  return (
    <li className={cn("lms-card lms-fade-in flex flex-col gap-3 rounded-card bg-surface-card p-4 ring-1 ring-surface-border shadow-[var(--shadow-sm)]", unavailable && "opacity-70")}
        style={{ animationDelay: `${Math.min(index, 9) * 40}ms` }}
        data-testid="lms-competency-card" data-kind={c.kind} data-status={c.status}>
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-blue/10 text-accent-blue"><Icon size={18} /></span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-text-muted">{c.position}.</p>
          <h3 className="font-semibold text-text-primary">{meta.name}</h3>
          <p className="text-xs text-text-secondary">{t(meta.descKey)}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <LmsStatusBadge status={c.status} detail={c.detail} />
        {c.score !== null && c.status !== "locked" && <span className="text-xs font-semibold text-text-secondary">{c.score}%</span>}
        {c.videos > 0 && <span className="inline-flex items-center gap-1 text-xs text-text-muted"><Video size={12} /> {c.videos}</span>}
      </div>
      {unavailable || locked ? (
        <span className="mt-auto rounded-xl bg-surface-hover px-3 py-2 text-center text-sm text-text-muted">
          {t(unavailable ? "lms.statusNotAvailable" : "lms.statusLocked")}
        </span>
      ) : (
        <Link href={competencyHref(lessonId, c.kind)} data-testid="lms-competency-open"
              className="mt-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-3 py-2 text-sm font-semibold text-white hover:opacity-90">
          {t(c.status === "not_started" ? "lms.open" : c.status === "completed" ? "lms.review" : "lms.continue")} <ArrowRight size={14} />
        </Link>
      )}
    </li>
  );
}

/** Overview card of Video-Unterricht — the first item, before Einführung. */
function VideoCard({ lessonId, count, unlocked }: { lessonId: string; count: number; unlocked: boolean }) {
  const { t } = useTranslation();
  return (
    <li className="lms-card lms-fade-in flex flex-col gap-3 rounded-card bg-surface-card p-4 ring-1 ring-surface-border shadow-[var(--shadow-sm)]"
        data-testid="lms-video-card" data-videos={count}>
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-blue/10 text-accent-blue"><PlayCircle size={18} /></span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-text-muted">{t("lms.descVideo")}</p>
          <h3 className="font-semibold text-text-primary">{t("lms.videoLesson")}</h3>
          <p className="text-xs text-text-secondary">{count > 0 ? t("lms.videoCount", { n: count }) : t("lms.noVideos")}</p>
        </div>
      </div>
      {unlocked && count > 0 ? (
        <Link href={videoHref(lessonId)} data-testid="lms-video-open"
              className="mt-auto inline-flex items-center justify-center gap-1.5 rounded-xl bg-accent-blue px-3 py-2 text-sm font-semibold text-white hover:opacity-90">
          {t("lms.open")} <ArrowRight size={14} />
        </Link>
      ) : (
        <span className="mt-auto rounded-xl bg-surface-hover px-3 py-2 text-center text-sm text-text-muted">
          {t(unlocked ? "lms.statusNotAvailable" : "lms.statusLocked")}
        </span>
      )}
    </li>
  );
}

function LessonHeader({ data }: { data: LmsLesson }) {
  const { t } = useTranslation();
  const level = data.lesson.level;
  return (
    <header className="lms-fade-in space-y-4 rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-6">
      <nav className="flex flex-wrap items-center gap-1 text-xs text-text-muted" aria-label="Breadcrumb">
        <Link href="/kurse" className="hover:text-accent-blue">{t("lms.levelsTitle")}</Link>
        {level && (
          <>
            <ChevronRight size={12} />
            <Link href={levelHref(level)} className="hover:text-accent-blue">{level}</Link>
          </>
        )}
        <ChevronRight size={12} />
        <Link href={lessonHref(data.lesson.id)} className="hover:text-accent-blue">{t("lms.lessonNumber", { n: data.lesson.number })}</Link>
      </nav>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl" data-testid="lms-lesson-title">{data.lesson.title}</h1>
          {data.lesson.description && <p className="mt-1 text-text-secondary">{data.lesson.description}</p>}
          {data.lesson.duration > 0 && (
            <p className="mt-1 inline-flex items-center gap-1 text-xs text-text-muted"><Clock size={12} /> {t("lms.minutes", { n: data.lesson.duration })}</p>
          )}
        </div>
        <LmsStatusBadge status={data.status} />
      </div>
      {data.access.unlocked && data.competencies_total > 0 && (
        <div>
          <div className="mb-1.5 flex justify-between text-xs">
            <span className="text-text-secondary" data-testid="lms-lesson-progress">
              {t("lms.competenciesDone", { done: data.competencies_completed, total: data.competencies_total })}
            </span>
            <span className="font-bold text-accent-blue">{data.percent}%</span>
          </div>
          <ProgressBar value={data.percent} trackClassName="h-1.5" />
        </div>
      )}
    </header>
  );
}

/** VIZU LMS lesson page — the lesson overview (ten competencies as cards)
 * or, with `kompetenz`, one competency with the navigation beside it. All
 * states come from GET /lms/lessons/{id}. */
export default function LmsLessonClient({ lessonId, kompetenz }: { lessonId: string; kompetenz?: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useLmsLesson(lessonId);
  useLmsLessonSync(lessonId);

  const videoPage = kompetenz?.toLowerCase() === VIDEO_SLUG;
  const kind = kompetenz && !videoPage ? kindFromSlug(kompetenz) : null;
  const competency = data && kind ? data.competencies.find((c) => c.kind === kind) : undefined;
  const visitable = Boolean(data?.access.unlocked && competency?.available);

  // Opening a competency is recorded on the server (completes only text /
  // resource competencies there); the answer is the server's new state.
  useEffect(() => {
    if (!visitable || !kind) return;
    let cancelled = false;
    visitCompetency(lessonId, kind)
      .then((res) => {
        if (cancelled) return;
        queryClient.setQueryData<LmsLesson>(lmsKeys.lesson(lessonId), (old) =>
          old
            ? { ...old, status: res.status, completed: res.completed, percent: res.percent, competencies_total: res.competencies_total,
                competencies_completed: res.competencies_completed, competencies: res.competencies }
            : old,
        );
        queryClient.invalidateQueries({ queryKey: ["lms", "level"] });
        queryClient.invalidateQueries({ queryKey: lmsKeys.levels });
      })
      .catch((err) => console.warn("Failed to record competency visit:", err));
    return () => {
      cancelled = true;
    };
  }, [visitable, kind, lessonId, queryClient]);

  if (isLoading) return <LmsSkeleton variant="lesson" />;
  if (error || !data) return <LmsErrorCard error={error} onRetry={() => refetch()} backHref="/kurse" backLabelKey="lms.levelsTitle" />;

  const ordered = [...data.competencies].sort((a, b) => a.position - b.position);
  const reachable = ordered.filter((c) => c.status !== "not_available");
  const idx = competency ? reachable.findIndex((c) => c.kind === competency.kind) : -1;
  const prevC = idx > 0 ? reachable[idx - 1] : null;
  const nextC = videoPage ? reachable[0] ?? null : idx >= 0 && idx < reachable.length - 1 ? reachable[idx + 1] : null;
  // Video-Unterricht comes before the first competency
  const prevIsVideo = idx === 0;
  const reloadVideos = async () => (await refetch()).data?.videos;
  const reloadResources = async () => (await refetch()).data?.resources;
  const lessonResources = data.resources.filter((r) => r.competency === null);

  return (
    <div className="space-y-6" data-testid="lms-lesson" data-lesson-id={data.lesson.id}>
      <LessonHeader data={data} />

      {kompetenz ? (
        <div className="lg:grid lg:grid-cols-[16rem_minmax(0,1fr)] lg:items-start lg:gap-6">
          <aside className="mb-5 lg:sticky lg:top-4 lg:mb-0 lg:rounded-card lg:bg-surface-card lg:p-3 lg:ring-1 lg:ring-surface-border">
            <LmsCompetencyNav lessonId={data.lesson.id} competencies={data.competencies} current={kind ?? undefined}
                              videoActive={videoPage} videoCount={data.videos.length} />
            <Link href={lessonHref(data.lesson.id)} className="mt-3 hidden items-center gap-1.5 px-2 text-xs font-medium text-text-secondary hover:text-accent-blue lg:inline-flex">
              <ArrowLeft size={13} /> {t("lms.lessonOverview")}
            </Link>
          </aside>

          <section className="min-w-0 space-y-6">
            {!data.access.unlocked ? (
              <LmsLessonLock data={data} />
            ) : videoPage ? (
              <>
                <div>
                  <h2 className="text-xl font-bold text-text-primary">{t("lms.videoLesson")}</h2>
                  <p className="text-sm text-text-secondary">{t("lms.descVideo")}</p>
                </div>
                {/* only published videos whose file exists come from the API — no empty player */}
                {data.videos.length > 0 ? (
                  <div data-testid="lms-video-lesson"><LmsVideos lessonId={data.lesson.id} videos={data.videos} onReload={reloadVideos} /></div>
                ) : (
                  <p className="rounded-card bg-surface-hover/60 p-8 text-center text-text-secondary ring-1 ring-surface-border" data-testid="lms-no-videos">
                    {t("lms.noVideos")}
                  </p>
                )}
                <div className="flex flex-wrap justify-end gap-3 border-t border-surface-border pt-5">
                  {nextC && (
                    <Link href={competencyHref(data.lesson.id, nextC.kind)} data-testid="lms-next-competency" className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90">
                      {COMPETENCY_META[nextC.kind].name} <ArrowRight size={15} />
                    </Link>
                  )}
                </div>
              </>
            ) : !kind || !competency ? (
              <p className="rounded-card bg-surface-card p-8 text-center text-text-secondary ring-1 ring-surface-border" data-testid="lms-competency-missing">
                {t("lms.competencyMissing")}
              </p>
            ) : (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{t("lms.competency")} {competency.position} / {data.competency_order.length}</p>
                    <h2 className="text-xl font-bold text-text-primary">{COMPETENCY_META[competency.kind].name}</h2>
                    <p className="text-sm text-text-secondary">{t(COMPETENCY_META[competency.kind].descKey)}</p>
                  </div>
                  <LmsStatusBadge status={competency.status} detail={competency.detail} />
                </div>

                {competency.status === "not_available" ? (
                  <p className="rounded-card bg-surface-hover/60 p-8 text-center text-text-secondary ring-1 ring-surface-border" data-testid="lms-not-available">
                    {t("lms.notAvailableHint")}
                  </p>
                ) : (
                  <LmsCompetencyContent data={data} competency={competency} reloadVideos={reloadVideos} reloadResources={reloadResources} />
                )}

                <div className="flex flex-wrap justify-between gap-3 border-t border-surface-border pt-5">
                  {prevIsVideo ? (
                    <Link href={videoHref(data.lesson.id)} className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
                      <ArrowLeft size={15} /> {t("lms.videoLesson")}
                    </Link>
                  ) : prevC ? (
                    <Link href={competencyHref(data.lesson.id, prevC.kind)} className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
                      <ArrowLeft size={15} /> {COMPETENCY_META[prevC.kind].name}
                    </Link>
                  ) : <span />}
                  {nextC ? (
                    <Link href={competencyHref(data.lesson.id, nextC.kind)} data-testid="lms-next-competency" className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90">
                      {COMPETENCY_META[nextC.kind].name} <ArrowRight size={15} />
                    </Link>
                  ) : data.navigation.next ? (
                    <Link href={lessonHref(data.navigation.next.id)} className="inline-flex items-center gap-1.5 rounded-xl bg-accent-blue px-4 py-2.5 text-sm font-semibold text-white hover:opacity-90">
                      {t("lms.nextLesson", { n: data.navigation.next.number })} <ArrowRight size={15} />
                    </Link>
                  ) : null}
                </div>
              </>
            )}
          </section>
        </div>
      ) : (
        <>
          {!data.access.unlocked && <LmsLessonLock data={data} />}
          <section className="space-y-3">
            <h2 className="text-lg font-bold text-text-primary">{t("lms.competencies")}</h2>
            {ordered.length === 0 ? (
              <p className="rounded-card bg-surface-card p-8 text-center text-text-secondary ring-1 ring-surface-border">{t("lms.noCompetencies")}</p>
            ) : (
              <ol className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="lms-competencies">
                <VideoCard lessonId={data.lesson.id} count={data.videos.length} unlocked={data.access.unlocked} />
                {ordered.map((c, i) => <CompetencyCard key={c.kind} lessonId={data.lesson.id} c={c} index={i + 1} />)}
              </ol>
            )}
          </section>
          {data.access.unlocked && <LmsResourceList resources={lessonResources} onReload={reloadResources} />}
          <div className="flex flex-wrap justify-between gap-3">
            {data.navigation.previous ? (
              <Link href={lessonHref(data.navigation.previous.id)} className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
                <ArrowLeft size={15} /> {t("lms.lessonNumber", { n: data.navigation.previous.number })}
              </Link>
            ) : <span />}
            {data.navigation.next && (
              <Link href={lessonHref(data.navigation.next.id)} className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-semibold text-text-secondary ring-1 ring-surface-border hover:text-accent-blue">
                {t("lms.lessonNumber", { n: data.navigation.next.number })} <ArrowRight size={15} />
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}
