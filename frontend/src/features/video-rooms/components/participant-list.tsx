"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParticipants } from "@livekit/components-react";
import type { Participant } from "livekit-client";
import { Ban, Hand, Mic, MicOff, MoreVertical, MonitorUp, Video, VideoOff } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import {
  chatPermission,
  getParticipants,
  micPermission,
  muteParticipant,
  raiseHand,
  removeParticipant,
  screenSharePermission,
  type ParticipantRow,
} from "../video-rooms-service";
import { ATTR_HAND, errorKey, roleOf, SOURCE } from "../video-room-utils";
import { QualityBars } from "./connection-status";

export function allows(perm: Participant["permissions"], source: number, fallback = true): boolean {
  if (!perm) return fallback;
  if (!perm.canPublish) return false;
  const sources = perm.canPublishSources as unknown as number[];
  return sources.length === 0 || sources.includes(source);
}

function HostActions({ roomId, p, row, onError, onChanged }: {
  roomId: string;
  p: Participant;
  row?: ParticipantRow;
  onError: (key: string) => void;
  onChanged: () => void;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const name = p.name || p.identity;
  const canMic = row ? row.can_speak : allows(p.permissions, SOURCE.microphone);
  const canScreen = row ? row.can_share_screen : allows(p.permissions, SOURCE.screenShare);
  const canChat = row ? row.can_chat : p.permissions?.canPublishData !== false;
  const hand = p.attributes?.[ATTR_HAND];

  async function run(fn: () => Promise<unknown>, confirmText?: string) {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusy(true);
    try {
      await fn();
      onChanged();
      setOpen(false);
    } catch (e) {
      onError(errorKey(e));
    } finally {
      setBusy(false);
    }
  }

  const item = "flex min-h-10 w-full items-center gap-2 rounded-lg px-3 text-left text-sm text-white hover:bg-white/10 disabled:opacity-50";
  return (
    <div className="relative">
      <button type="button" aria-label={t("videoRoom.actionsFor", { name })} aria-expanded={open} onClick={() => setOpen((v) => !v)}
              data-testid="participant-actions" className="rounded-lg p-2 text-neutral-300 hover:bg-white/10">
        <MoreVertical size={16} />
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-10 z-30 w-60 rounded-xl bg-neutral-900 p-1 shadow-xl ring-1 ring-white/10">
          {p.isMicrophoneEnabled && (
            <button type="button" role="menuitem" disabled={busy} className={item} data-testid="action-mute"
                    onClick={() => run(() => muteParticipant(roomId, p.identity))}><MicOff size={15} /> {t("videoRoom.mute")}</button>
          )}
          <button type="button" role="menuitem" disabled={busy} className={item} data-testid="action-mic"
                  onClick={() => run(() => micPermission(roomId, !canMic, p.identity))}>
            {canMic ? <MicOff size={15} /> : <Mic size={15} />} {canMic ? t("videoRoom.blockMic") : t("videoRoom.allowMic")}
          </button>
          <button type="button" role="menuitem" disabled={busy} className={item} data-testid="action-screen"
                  onClick={() => run(() => screenSharePermission(roomId, !canScreen, p.identity))}>
            <MonitorUp size={15} /> {canScreen ? t("videoRoom.blockScreen1") : t("videoRoom.allowScreen1")}
          </button>
          <button type="button" role="menuitem" disabled={busy} className={item} data-testid="action-chat"
                  onClick={() => run(() => chatPermission(roomId, !canChat, p.identity))}>
            {canChat ? t("videoRoom.blockChat1") : t("videoRoom.allowChat1")}
          </button>
          {hand && (
            <button type="button" role="menuitem" disabled={busy} className={item} data-testid="action-lower-hand"
                    onClick={() => run(() => raiseHand(roomId, false, p.identity))}><Hand size={15} /> {t("videoRoom.lowerHand")}</button>
          )}
          <button type="button" role="menuitem" disabled={busy} className={cn(item, "text-red-300")} data-testid="action-remove"
                  onClick={() => run(() => removeParticipant(roomId, p.identity, false), t("videoRoom.removeConfirm", { name }))}>
            {t("videoRoom.remove")}
          </button>
          <button type="button" role="menuitem" disabled={busy} className={cn(item, "text-red-400")} data-testid="action-remove-block"
                  onClick={() => run(() => removeParticipant(roomId, p.identity, true), t("videoRoom.removeBlockConfirm", { name }))}>
            <Ban size={15} /> {t("videoRoom.removeBlock")}
          </button>
        </div>
      )}
    </div>
  );
}

/** Who is in the room right now (live from LiveKit). Hosts also get the moderation menu per student and the group
 *  members who have not joined (from the backend). */
export default function ParticipantList({ roomId, isHost, onError }: { roomId: string; isHost: boolean; onError: (key: string) => void }) {
  const { t } = useTranslation();
  const participants = useParticipants();
  const rows = useQuery({ queryKey: ["video-room", roomId, "participants"], queryFn: () => getParticipants(roomId), enabled: isHost, refetchInterval: 10_000 });
  const byId = new Map((rows.data?.items ?? []).map((r) => [r.user_id, r]));
  const sorted = [...participants].sort((a, b) => {
    const ra = roleOf(a.metadata, a.attributes) === "host" ? 0 : 1;
    const rb = roleOf(b.metadata, b.attributes) === "host" ? 0 : 1;
    return ra - rb || (a.name || a.identity).localeCompare(b.name || b.identity);
  });

  return (
    <div className="pb-4">
      <ul data-testid="participant-list" className="divide-y divide-white/5">
        {sorted.map((p) => {
          const host = roleOf(p.metadata, p.attributes) === "host";
          const hand = p.attributes?.[ATTR_HAND];
          return (
            <li key={p.identity} data-testid="participant-row" data-identity={p.identity} className="flex items-center gap-2 px-3 py-2">
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 truncate text-sm font-medium text-white">
                  {p.name || p.identity}{p.isLocal ? ` (${t("videoRoom.you")})` : ""}
                  {host && <span className="rounded bg-sky-500 px-1 text-[10px] font-bold uppercase">{t("videoRoom.host")}</span>}
                </span>
              </span>
              {hand && <Hand size={15} className="shrink-0 text-amber-400" aria-label={t("videoRoom.raiseHand")} />}
              {p.isScreenShareEnabled && <MonitorUp size={15} className="shrink-0 text-sky-400" />}
              {p.isMicrophoneEnabled ? <Mic size={15} className="shrink-0 text-neutral-300" /> : <MicOff size={15} className="shrink-0 text-red-400" />}
              {p.isCameraEnabled ? <Video size={15} className="shrink-0 text-neutral-300" /> : <VideoOff size={15} className="shrink-0 text-neutral-500" />}
              <QualityBars participant={p} />
              {isHost && !p.isLocal && !host && (
                <HostActions roomId={roomId} p={p} row={byId.get(p.identity)} onError={onError} onChanged={() => void rows.refetch()} />
              )}
            </li>
          );
        })}
      </ul>
      {isHost && !!rows.data?.absent?.length && (
        <div className="mt-2 px-3">
          <p className="pb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">{t("videoRoom.absent")} · {rows.data.absent.length}</p>
          <ul data-testid="absent-list" className="space-y-1">
            {rows.data.absent.map((a) => <li key={a.user_id} className="truncate text-sm text-neutral-400">{a.name}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
