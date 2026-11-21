"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Radio, Video } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { card, fmtDate, input, primaryBtn, secondaryBtn, textarea } from "@/features/groups/components/ui";
import { activeRoom, cancelRoom, createRoom, endRoom, listRooms, startRoom, type VideoRoom } from "../video-rooms-service";
import { errorKey, formatDuration, localInputToIso, toLocalInput } from "../video-room-utils";

const roomHref = (id: string) => `/video-room/${id}`;

function StatusPill({ status }: { status: VideoRoom["status"] }) {
  const { t } = useTranslation();
  const tone = status === "live" ? "bg-red-500/10 text-red-600 ring-red-500/30 dark:text-red-400"
    : status === "scheduled" ? "bg-accent-blue/10 text-accent-blue ring-accent-blue/30" : "bg-surface-hover text-text-secondary ring-surface-border";
  return <span className={cn("inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1", tone)}>
    {status === "live" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />}{t(`videoRoom.status_${status}`)}
  </span>;
}

/** Above the group tabs: the lesson that is live right now, with a join button (students and teacher). */
export function LiveBanner({ groupId }: { groupId: string }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["video-rooms", groupId, "active"], queryFn: () => activeRoom(groupId), refetchInterval: 20_000, retry: false });
  const room = q.data?.room;
  if (!room) return null;
  return (
    <div data-testid="video-live-banner" className="flex flex-col gap-3 rounded-card bg-red-500/10 p-4 ring-1 ring-red-500/30 sm:flex-row sm:items-center sm:justify-between">
      <p className="flex min-w-0 items-center gap-2 text-sm font-semibold text-text-primary">
        <Radio size={18} className="shrink-0 animate-pulse text-red-500" />
        <span className="truncate">{t("videoRoom.liveBanner", { title: room.title })}</span>
        <span className="shrink-0 text-xs font-normal text-text-muted">· {t("videoRoom.online", { n: room.online_count })}</span>
      </p>
      <Link href={roomHref(room.id)} data-testid="video-live-join" className={cn(primaryBtn, "bg-red-600")}>
        <Video size={16} /> {q.data?.is_manager ? t("videoRoom.joinAsHost") : t("videoRoom.join")}
      </Link>
    </div>
  );
}

function CreateForm({ groupId, configured }: { groupId: string; configured: boolean }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [now, setNow] = useState(true);
  const [when, setWhen] = useState("");
  const [chat, setChat] = useState(true);
  const [screen, setScreen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const create = useMutation({
    mutationFn: () => createRoom(groupId, {
      title: title.trim(), description: description.trim() || null, start_now: now, scheduled_at: now ? null : localInputToIso(when) || null,
      chat_enabled: chat, students_can_share_screen: screen,
    }),
    onSuccess: (room) => {
      setTitle(""); setDescription(""); setWhen(""); setError(null);
      void qc.invalidateQueries({ queryKey: ["video-rooms", groupId] });
      if (room.status === "live") router.push(roomHref(room.id));
    },
    onError: (e) => setError(t(errorKey(e))),
  });
  const valid = title.trim().length >= 2 && (now ? configured : !!when);

  return (
    <form data-testid="video-create-form" onSubmit={(e) => { e.preventDefault(); if (valid) create.mutate(); }} className={cn(card, "space-y-3 p-5")}>
      <p className="text-sm font-bold text-text-primary">{t("videoRoom.createTitle")}</p>
      <label className="block text-xs font-semibold text-text-secondary">{t("videoRoom.fieldTitle")}
        <input data-testid="video-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} placeholder={t("videoRoom.fieldTitlePh")} className={cn(input, "mt-1")} />
      </label>
      <label className="block text-xs font-semibold text-text-secondary">{t("videoRoom.fieldTopic")}
        <textarea data-testid="video-description" value={description} maxLength={2000} rows={2} onChange={(e) => setDescription(e.target.value)} className={cn(textarea, "mt-1")} />
      </label>
      <div role="radiogroup" className="flex flex-wrap gap-2">
        {[true, false].map((v) => (
          <button key={String(v)} type="button" role="radio" aria-checked={now === v} data-testid={v ? "video-when-now" : "video-when-later"}
                  onClick={() => { setNow(v); if (!v && !when) setWhen(toLocalInput(new Date(Date.now() + 60 * 60 * 1000))); }}
                  className={cn("min-h-11 rounded-xl px-4 text-sm font-semibold ring-1", now === v ? "bg-accent-blue text-white ring-accent-blue" : "bg-surface-hover text-text-secondary ring-surface-border")}>
            {v ? t("videoRoom.whenNow") : t("videoRoom.whenLater")}
          </button>
        ))}
      </div>
      {!now && (
        <label className="block text-xs font-semibold text-text-secondary">{t("videoRoom.fieldWhen")}
          <input type="datetime-local" data-testid="video-when" value={when} onChange={(e) => setWhen(e.target.value)} className={cn(input, "mt-1")} />
        </label>
      )}
      <label className="flex min-h-11 items-center gap-2 text-sm text-text-secondary">
        <input type="checkbox" checked={chat} onChange={(e) => setChat(e.target.checked)} className="h-5 w-5 accent-accent-blue" /> {t("videoRoom.allowChat")}
      </label>
      <label className="flex min-h-11 items-center gap-2 text-sm text-text-secondary">
        <input type="checkbox" checked={screen} onChange={(e) => setScreen(e.target.checked)} className="h-5 w-5 accent-accent-blue" data-testid="video-allow-screen" /> {t("videoRoom.allowScreen")}
      </label>
      {error && <p role="alert" data-testid="video-create-error" className="text-sm text-danger">{error}</p>}
      <button type="submit" disabled={!valid || create.isPending} data-testid="video-create" className={primaryBtn}>
        {now ? <Video size={16} /> : <CalendarClock size={16} />} {now ? t("videoRoom.createNow") : t("videoRoom.createLater")}
      </button>
    </form>
  );
}

function RoomRow({ room, manager, groupId }: { room: VideoRoom; manager: boolean; groupId: string }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const act = useMutation({
    mutationFn: async (what: "start" | "cancel" | "end"): Promise<unknown> =>
      what === "start" ? startRoom(room.id) : what === "cancel" ? cancelRoom(room.id) : endRoom(room.id),
    onSuccess: (_d, what) => {
      void qc.invalidateQueries({ queryKey: ["video-rooms", groupId] });
      if (what === "start") router.push(roomHref(room.id));
    },
    onError: (e) => setError(t(errorKey(e))),
  });
  const when = room.status === "live" ? t("videoRoom.startedAt", { time: fmtDate(room.started_at, true) })
    : room.status === "scheduled" ? t("videoRoom.scheduledFor", { time: fmtDate(room.scheduled_at, true) })
    : room.started_at && room.ended_at ? `${fmtDate(room.started_at, true)} · ${t("videoRoom.duration", { d: formatDuration(new Date(room.ended_at).getTime() - new Date(room.started_at).getTime()) })}`
    : fmtDate(room.ended_at ?? room.created_at, true);

  return (
    <li data-testid="video-room-row" data-status={room.status} className={cn(card, "flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between")}>
      <div className="min-w-0">
        <p className="flex items-center gap-2 text-sm font-bold text-text-primary"><span className="truncate">{room.title}</span> <StatusPill status={room.status} /></p>
        <p className="text-xs text-text-muted">{when}{room.status === "live" ? ` · ${t("videoRoom.online", { n: room.online_count })}` : ""}</p>
        {room.description && <p className="mt-1 line-clamp-2 whitespace-pre-wrap text-xs text-text-secondary">{room.description}</p>}
        {error && <p role="alert" className="mt-1 text-xs text-danger">{error}</p>}
      </div>
      <div className="flex shrink-0 flex-wrap gap-2">
        {room.status === "live" && (
          <Link href={roomHref(room.id)} data-testid="video-room-join" className={primaryBtn}><Video size={16} /> {manager ? t("videoRoom.joinAsHost") : t("videoRoom.join")}</Link>
        )}
        {manager && room.status === "live" && (
          <button type="button" disabled={act.isPending} data-testid="video-room-end" className={cn(secondaryBtn, "text-danger")}
                  onClick={() => { if (window.confirm(t("videoRoom.endConfirm"))) act.mutate("end"); }}>{t("videoRoom.end")}</button>
        )}
        {manager && room.status === "scheduled" && (
          <>
            <button type="button" disabled={act.isPending} data-testid="video-room-start" className={primaryBtn} onClick={() => act.mutate("start")}>{t("videoRoom.start")}</button>
            <button type="button" disabled={act.isPending} data-testid="video-room-cancel" className={secondaryBtn}
                    onClick={() => { if (window.confirm(t("videoRoom.cancelConfirm"))) act.mutate("cancel"); }}>{t("videoRoom.cancel")}</button>
          </>
        )}
      </div>
    </li>
  );
}

/** Group tab: the live lesson, scheduled and past lessons; for the group's teacher also the create / schedule form. */
export default function VideoLessonsTab({ groupId, manager }: { groupId: string; manager: boolean }) {
  const { t } = useTranslation();
  const q = useQuery({ queryKey: ["video-rooms", groupId], queryFn: () => listRooms(groupId), refetchInterval: 15_000 });
  if (q.isLoading) return <p className="p-6 text-sm text-text-muted">{t("groups.loading")}</p>;
  if (q.isError || !q.data) return <p role="alert" className="rounded-card bg-danger/10 p-4 text-sm text-danger">{t(errorKey(q.error))}</p>;
  const d = q.data;
  const canManage = manager && d.is_manager;

  return (
    <div data-testid="video-lessons" className="space-y-5">
      {!d.configured && (
        <p data-testid="video-not-configured" className="rounded-card bg-amber-500/10 p-4 text-sm text-amber-800 ring-1 ring-amber-500/30 dark:text-amber-200">
          {t("videoRoom.notConfigured")} {canManage && t("videoRoom.notConfiguredTeacher")}
        </p>
      )}
      <section className="space-y-2">
        {d.live ? <ul><RoomRow room={d.live} manager={canManage} groupId={groupId} /></ul>
          : <p className={cn(card, "p-5 text-center text-sm text-text-muted")}>{t("videoRoom.noLive")}</p>}
      </section>
      {canManage && !d.live && <CreateForm groupId={groupId} configured={d.configured} />}
      <section className="space-y-2">
        <h3 className="text-sm font-bold text-text-primary">{t("videoRoom.upcoming")}</h3>
        {d.upcoming.length ? <ul className="space-y-2">{d.upcoming.map((r) => <RoomRow key={r.id} room={r} manager={canManage} groupId={groupId} />)}</ul>
          : <p className="text-sm text-text-muted">{t("videoRoom.noUpcoming")}</p>}
      </section>
      <section className="space-y-2">
        <h3 className="text-sm font-bold text-text-primary">{t("videoRoom.past")}</h3>
        {d.past.length ? <ul className="space-y-2">{d.past.map((r) => <RoomRow key={r.id} room={r} manager={canManage} groupId={groupId} />)}</ul>
          : <p className="text-sm text-text-muted">{t("videoRoom.noPast")}</p>}
      </section>
    </div>
  );
}
