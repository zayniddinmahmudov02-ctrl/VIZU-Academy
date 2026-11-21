"use client";

import { useCallback, useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LiveKitRoom } from "@livekit/components-react";
import { DisconnectReason, isBrowserSupported, VideoPresets, type RoomOptions } from "livekit-client";
import { ArrowLeft, Loader2, Video } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { endRoom, getRoom, joinRoom, leaveRoom, type JoinInfo } from "../video-rooms-service";
import { errorKey } from "../video-room-utils";
import { loadChoices, PrejoinDevices, saveChoices, type DeviceChoices } from "./device-settings";
import MeetingView from "./meeting-view";

type Over = "ended" | "left" | "removed" | "duplicate" | "lost";
type Phase = { kind: "prejoin" } | { kind: "joining" } | { kind: "in"; join: JoinInfo } | { kind: "over"; why: Over };

const OVER_TITLE: Record<Over, string> = {
  ended: "videoRoom.endedTitle", left: "videoRoom.leftTitle", removed: "videoRoom.removedTitle",
  duplicate: "videoRoom.duplicateTitle", lost: "videoRoom.lostTitle",
};

function overFor(reason?: DisconnectReason): Over {
  if (reason === DisconnectReason.ROOM_DELETED || reason === DisconnectReason.ROOM_CLOSED) return "ended";
  if (reason === DisconnectReason.PARTICIPANT_REMOVED) return "removed";
  if (reason === DisconnectReason.DUPLICATE_IDENTITY) return "duplicate";
  if (reason === DisconnectReason.CLIENT_INITIATED) return "left";
  return "lost";
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-[100dvh] bg-neutral-950 px-4 py-6 text-white sm:py-10"><div className="mx-auto max-w-4xl">{children}</div></div>;
}

/** /video-room/[roomId]: pre-join (devices, permissions) → LiveKit room → end screen. The join token comes from the
 *  backend only after it checked group membership, room state, blocks and seats; it is kept in memory only. */
export default function VideoRoomPage({ roomId }: { roomId: string }) {
  const { t } = useTranslation();
  const detail = useQuery({ queryKey: ["video-room", roomId], queryFn: () => getRoom(roomId), retry: false });
  const [phase, setPhase] = useState<Phase>({ kind: "prejoin" });
  const [choices, setChoices] = useState<DeviceChoices>(loadChoices);
  const [error, setError] = useState<string | null>(null);
  const supported = typeof window === "undefined" || isBrowserSupported();

  const patch = useCallback((p: Partial<DeviceChoices>) => {
    setChoices((c) => {
      const next = { ...c, ...p };
      saveChoices(next);
      return next;
    });
  }, []);

  const options = useMemo<RoomOptions>(() => ({
    adaptiveStream: true,
    dynacast: true,
    disconnectOnPageLeave: true,
    videoCaptureDefaults: { resolution: VideoPresets.h720.resolution },
    publishDefaults: { simulcast: true, videoSimulcastLayers: [VideoPresets.h180, VideoPresets.h360], red: true, dtx: true },
    audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    audioOutput: choices.audioOutputId ? { deviceId: choices.audioOutputId } : undefined,
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the output device is chosen before joining; later changes go through DeviceSettings
  }), []);

  const g = detail.data?.group;
  const manager = !!detail.data?.viewer.is_manager;
  const back = g ? (manager ? `/teacher/groups/${g.id}?tab=video` : `/groups/${g.id}?tab=video`) : "/groups";

  async function join() {
    setError(null);
    setPhase({ kind: "joining" });
    try {
      setPhase({ kind: "in", join: await joinRoom(roomId) });
    } catch (e) {
      setError(t(errorKey(e)));
      setPhase({ kind: "prejoin" });
      void detail.refetch();
    }
  }

  function leave() {
    void leaveRoom(roomId).catch(() => undefined);
    setPhase({ kind: "over", why: "left" });
  }

  async function endForAll() {
    try {
      await endRoom(roomId);
      setPhase({ kind: "over", why: "ended" });
    } catch (e) {
      setError(t(errorKey(e)));
    }
  }

  if (phase.kind === "in") {
    const j = phase.join;
    const micAllowed = j.permissions.microphone;
    return (
      <LiveKitRoom serverUrl={j.server_url} token={j.token} connect options={options} data-testid="livekit-room"
                   audio={choices.audioEnabled && micAllowed ? { deviceId: choices.audioDeviceId || undefined } : false}
                   video={choices.videoEnabled ? { deviceId: choices.videoDeviceId || undefined, resolution: VideoPresets.h720.resolution } : false}
                   onDisconnected={(reason) => setPhase((p) => (p.kind === "in" ? { kind: "over", why: overFor(reason) } : p))}
                   onError={() => undefined}>
        <MeetingView join={j} onLeave={leave} onEnd={() => void endForAll()} />
      </LiveKitRoom>
    );
  }

  if (phase.kind === "over") {
    const canRejoin = phase.why !== "ended" && phase.why !== "removed";
    return (
      <Shell>
        <div data-testid="video-over" data-reason={phase.why} className="mx-auto max-w-md space-y-4 rounded-2xl bg-neutral-900 p-6 text-center ring-1 ring-white/10">
          <Video size={32} className="mx-auto text-sky-400" />
          <h1 className="text-lg font-semibold">{t(OVER_TITLE[phase.why])}</h1>
          {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            {canRejoin && <button type="button" onClick={() => void join()} data-testid="video-rejoin" className="h-11 rounded-xl bg-sky-600 px-4 text-sm font-semibold">{t("videoRoom.rejoin")}</button>}
            <Link href={back} className="inline-flex h-11 items-center justify-center rounded-xl bg-white/10 px-4 text-sm font-semibold">{t("videoRoom.backToGroup")}</Link>
          </div>
        </div>
      </Shell>
    );
  }

  const room = detail.data?.room;
  const notJoinable = room && room.status !== "live";
  return (
    <Shell>
      <Link href={back} className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-neutral-300 hover:text-white"><ArrowLeft size={14} /> {t("videoRoom.backToGroup")}</Link>
      {detail.isLoading ? (
        <p className="flex items-center gap-2 text-sm text-neutral-400"><Loader2 size={16} className="animate-spin" /> {t("videoRoom.joining")}</p>
      ) : detail.isError || !detail.data ? (
        <p role="alert" data-testid="video-error" className="rounded-xl bg-red-500/10 p-4 text-sm text-red-300 ring-1 ring-red-500/30">{t(errorKey(detail.error))}</p>
      ) : (
        <div data-testid="prejoin" className="space-y-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">{detail.data.group.name} · {detail.data.group.level}</p>
            <h1 className="text-xl font-bold">{room?.title}</h1>
            {room?.description && <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-300">{room.description}</p>}
          </div>
          {!supported ? (
            <p role="alert" className="rounded-xl bg-red-500/10 p-4 text-sm text-red-300">{t("videoRoom.browserUnsupported")}</p>
          ) : (
            <>
              <h2 className="text-sm font-semibold text-neutral-200">{t("videoRoom.prejoinTitle")} <span className="font-normal text-neutral-400">{t("videoRoom.prejoinHint")}</span></h2>
              <PrejoinDevices choices={choices} onChange={patch} micAllowed={detail.data.viewer.permissions.microphone} />
            </>
          )}
          {error && <p role="alert" data-testid="video-join-error" className="rounded-xl bg-red-500/10 p-3 text-sm text-red-300 ring-1 ring-red-500/30">{error}</p>}
          {notJoinable && <p className="text-sm text-amber-300">{t(room.status === "scheduled" ? "videoRoom.err_VIDEO_ROOM_NOT_STARTED" : "videoRoom.err_VIDEO_ROOM_NOT_LIVE")}</p>}
          <button type="button" onClick={() => void join()} disabled={!supported || phase.kind === "joining" || !!notJoinable || !detail.data.configured}
                  data-testid="video-join" className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-sky-600 px-6 text-base font-semibold disabled:opacity-50 sm:w-auto">
            {phase.kind === "joining" && <Loader2 size={18} className="animate-spin" />}
            {manager ? t("videoRoom.joinAsHost") : t("videoRoom.join")}
          </button>
          {!detail.data.configured && <p className="text-sm text-neutral-400">{t("videoRoom.notConfigured")}</p>}
        </div>
      )}
    </Shell>
  );
}
