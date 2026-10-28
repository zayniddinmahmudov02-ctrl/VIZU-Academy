"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { KeyRound, Loader2, MessageCircle, Users, UsersRound } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { getMyGroups, joinGroup, previewJoin, type JoinPreview } from "../groups-service";
import { card, ErrorBox, fmtDate, input, LevelPill, Loading, primaryBtn, secondaryBtn, useErrorText } from "./ui";

function JoinCard() {
  const { t } = useTranslation();
  const router = useRouter();
  const errorText = useErrorText();
  const [code, setCode] = useState("");
  const [preview, setPreview] = useState<JoinPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function check() {
    setBusy(true);
    setError(null);
    try {
      const p = await previewJoin(code);
      if (p.already_member) router.push(`/groups/${p.id}`);
      else setPreview(p);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function join() {
    setBusy(true);
    setError(null);
    try {
      const res = await joinGroup(code);
      router.push(`/groups/${res.group.id}`);
    } catch (err) {
      setError(errorText(err));
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={cn(card, "space-y-3 p-5")} data-testid="group-join">
      <div>
        <h2 className="flex items-center gap-2 text-base font-bold text-text-primary"><KeyRound size={18} /> {t("groups.joinTitle")}</h2>
        <p className="mt-1 text-sm text-text-secondary">{t("groups.joinHint")}</p>
      </div>
      {!preview ? (
        <form className="flex flex-col gap-2 sm:flex-row" onSubmit={(e) => { e.preventDefault(); check(); }}>
          <input className={cn(input, "font-mono uppercase tracking-widest sm:max-w-xs")} value={code} maxLength={20} autoComplete="off"
                 placeholder="XXXX-XXXX" aria-label={t("groups.code")} onChange={(e) => setCode(e.target.value.toUpperCase())} data-testid="group-code" />
          <button type="submit" className={primaryBtn} disabled={busy || code.replace(/[^A-Za-z0-9]/g, "").length < 8}>
            {busy && <Loader2 size={14} className="animate-spin" />} {t("groups.check")}
          </button>
        </form>
      ) : (
        <div className="space-y-3 rounded-xl bg-accent-blue/5 p-4 ring-1 ring-accent-blue/20" role="dialog" aria-label={preview.name}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-base font-bold text-text-primary">{preview.name}</p>
              <p className="text-sm text-text-secondary">{t("groups.teacher")}: {preview.teacher.name}</p>
              <p className="text-xs text-text-muted">
                {preview.courses.map((c) => c.title).join(", ") || t("groups.noCourses")} · {t("groups.members")}: {preview.student_count}{preview.capacity ? `/${preview.capacity}` : ""}
              </p>
            </div>
            <LevelPill level={preview.level} />
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className={primaryBtn} disabled={busy} onClick={join} data-testid="group-join-confirm">
              {busy && <Loader2 size={14} className="animate-spin" />} {t("groups.joinButton")}
            </button>
            <button type="button" className={secondaryBtn} disabled={busy} onClick={() => setPreview(null)}>{t("groups.cancel")}</button>
          </div>
        </div>
      )}
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
    </div>
  );
}

/** Student → "Gruppen": own groups as cards (unread chat, last message,
 *  task status) and joining with a teacher's code. */
export default function StudentGroups() {
  const { t } = useTranslation();
  const groups = useQuery({ queryKey: ["groups", "my"], queryFn: getMyGroups, refetchInterval: 30_000 });

  return (
    <div className="space-y-6">
      <PageHeader icon={UsersRound} titleKey="groups.title" subtitleKey="groups.subtitle" gradient="from-brand-900 to-brand-600" />
      <JoinCard />
      <h2 className="text-sm font-bold uppercase tracking-wide text-text-muted">{t("groups.myGroups")}</h2>
      {groups.isLoading ? <Loading /> : groups.isError ? <ErrorBox error={groups.error} onRetry={() => groups.refetch()} /> : (groups.data ?? []).length === 0 ? (
        <p className={cn(card, "p-8 text-center text-sm text-text-muted")}>{t("groups.noGroups")}</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {groups.data!.map((g) => (
            <Link key={g.id} href={`/groups/${g.id}`} className={cn(card, "block p-5 transition-colors hover:ring-accent-blue/40")} data-testid="group-card">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-base font-bold text-text-primary">{g.name}</p>
                  <p className="text-sm text-text-secondary">{t("groups.teacher")}: {g.teacher.name}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {g.unread > 0 && <span className="rounded-full bg-accent-blue px-2 py-0.5 text-[11px] font-bold text-white">{t("groups.unread", { n: g.unread })}</span>}
                  <LevelPill level={g.level} />
                </div>
              </div>
              <p className="mt-2 flex items-center gap-1.5 text-xs text-text-muted"><Users size={12} /> {g.student_count} · {g.courses.map((c) => c.title).join(", ") || t("groups.noCourses")}</p>
              {g.last_message && (
                <p className="mt-2 flex items-start gap-1.5 truncate text-xs text-text-secondary">
                  <MessageCircle size={12} className="mt-0.5 shrink-0" />
                  <span className="truncate">{g.last_message.sender ? `${g.last_message.sender}: ` : ""}{g.last_message.body}</span>
                  <span className="shrink-0 text-text-muted">· {fmtDate(g.last_message.created_at)}</span>
                </p>
              )}
              {g.tasks.total > 0 && (
                <p className="mt-2 text-xs font-semibold text-text-secondary">
                  {t("groups.tasksDone", { done: g.tasks.done, total: g.tasks.total })}
                  {g.tasks.overdue > 0 && <span className="ml-2 text-danger">{t("groups.overdue", { n: g.tasks.overdue })}</span>}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
