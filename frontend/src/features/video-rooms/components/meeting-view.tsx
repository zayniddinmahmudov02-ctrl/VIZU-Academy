"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  RoomAudioRenderer,
  StartAudio,
  useChat,
  useLocalParticipant,
  useLocalParticipantPermissions,
  useParticipantAttribute,
  useParticipants,
  useRoomContext,
  useRoomInfo,
  useTracks,
} from "@livekit/components-react";
import { ConnectionState, ParticipantEvent, RoomEvent, Track, type TrackPublication } from "livekit-client";
import { Users, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { raiseHand, reportConnection, type JoinInfo } from "../video-rooms-service";
import { ATTR_HAND, clockOffset, errorKey, FIVE_MINUTES_MS, formatDuration, handsInOrder, parseRoomMeta, remainingMs, SOURCE } from "../video-room-utils";
import ConnectionStatus, { QualityBars } from "./connection-status";
import DeviceSettings from "./device-settings";
import MeetingChat from "./meeting-chat";
import MeetingControls, { type Panel } from "./meeting-controls";
import ParticipantList, { allows } from "./participant-list";
import RaiseHandPanel from "./raise-hand-panel";
import TeacherControls from "./teacher-controls";
import VideoGrid, { type Layout } from "./video-grid";

function useToasts() {
  const [items, setItems] = useState<{ id: number; key: string; tone: "info" | "error" }[]>([]);
  const seq = useRef(0);
  const push = useCallback((key: string, tone: "info" | "error" = "info") => {
    seq.current += 1;
    const id = seq.current;
    setItems((x) => [...x.filter((i) => i.key !== key).slice(-2), { id, key, tone }]);
    window.setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), 5000);
  }, []);
  return [items, push] as const;
}

function Duration({ startedAt }: { startedAt: string | null }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);
  const start = startedAt ? new Date(startedAt).getTime() : null;
  return <>{formatDuration(now && start ? now - start : 0)}</>;
}

/** Special lessons: time until the backend closes the room (server clock). The 5-minute warning fires once; at zero the
 *  backend ends the room and LiveKit disconnects everyone — the UI only shows it. */
function TimeLeft({ endsAt, offset, onFiveMinutes }: { endsAt: string; offset: number; onFiveMinutes: () => void }) {
  const { t } = useTranslation();
  const [now, setNow] = useState<number | null>(null);
  const warned = useRef(false);
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);
  const left = now === null ? null : remainingMs(endsAt, now, offset);
  useEffect(() => {
    if (left !== null && left > 0 && left <= FIVE_MINUTES_MS && !warned.current) {
      warned.current = true;
      onFiveMinutes();
    }
  }, [left, onFiveMinutes]);
  const soon = left !== null && left <= FIVE_MINUTES_MS;
  return (
    <span data-testid="meeting-time-left" data-soon={soon ? "1" : undefined}
          className={cn("shrink-0 rounded-md px-1.5 py-0.5 text-xs font-semibold tabular-nums", soon ? "bg-amber-500 text-neutral-950" : "bg-white/10 text-neutral-200")}>
      {t("videoRoom.timeLeft", { time: formatDuration(left ?? 0) })}
    </span>
  );
}

/** Everything inside the LiveKit room: top bar, video stage, side panels, controls, toasts. */
export default function MeetingView({ join, onLeave, onEnd }: { join: JoinInfo; onLeave: () => void; onEnd: () => void }) {
  const { t } = useTranslation();
  const room = useRoomContext();
  const roomId = join.room.id;
  const isHost = join.permissions.moderate;
  const { localParticipant } = useLocalParticipant();
  const perm = useLocalParticipantPermissions();
  const participants = useParticipants();
  const tracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }, { source: Track.Source.ScreenShare, withPlaceholder: false }],
    { onlySubscribed: false });
  const { metadata } = useRoomInfo();
  const meta = parseRoomMeta(metadata ?? JSON.stringify({ title: join.room.title, chat: join.room.chat_enabled,
    screen_share: join.room.students_can_share_screen, mic: join.room.students_mic_allowed, camera: join.room.students_camera_allowed ?? true,
    ends_at: join.room.hard_end_at ?? null }));
  const endsAt = meta.endsAt ?? join.room.hard_end_at ?? null;
  // server time − local time, measured once when the join answer arrived (the backend decides when the room closes)
  const [offset] = useState(() => clockOffset(join.server_time, Date.now()));
  const subtitle = join.group ? `${join.group.name} · ${join.group.level}`
    : join.lesson ? `${t("videoRoom.specialLesson")} · ${join.lesson.teacher} · ${join.lesson.level}` : "";
  const localHand = useParticipantAttribute(ATTR_HAND, { participant: localParticipant });
  const chat = useChat();
  const [panel, setPanelState] = useState<Panel>(null);
  const [layout, setLayout] = useState<Layout>("grid");
  const [pinned, setPinned] = useState<string | null>(null);
  const [volume, setVolume] = useState(1);
  const [settings, setSettings] = useState(false);
  const [seen, setSeen] = useState(0);
  const [toasts, push] = useToasts();
  const selfMute = useRef(false);
  const selfHand = useRef(0);

  const others = chat.chatMessages.filter((m) => !m.from?.isLocal).length;
  const unread = Math.max(0, others - seen);
  const hands = handsInOrder(participants.map((p) => ({ identity: p.identity, name: p.name || p.identity, hand: p.attributes?.[ATTR_HAND] ?? "" })));
  const canChat = perm ? perm.canPublishData : join.permissions.chat;
  const sharing = tracks.some((tr) => tr.source === Track.Source.ScreenShare);
  const shownLayout: Layout = sharing && !pinned ? "speaker" : layout;

  function setPanel(p: Panel) {
    if (p === "chat" || panel === "chat") setSeen(others);
    setPanelState(p);
  }

  function onPin(key: string | null) {
    setPinned(key);
    if (key) setLayout("speaker");
  }

  async function toggleHand() {
    if (localHand) selfHand.current = Date.now(); // lowering my own hand: no "lowered by the teacher" toast
    try {
      await raiseHand(roomId, !localHand);
    } catch (e) {
      push(errorKey(e), "error");
    }
  }

  function end() {
    if (window.confirm(t("videoRoom.endConfirm"))) onEnd();
  }

  const fiveMinutes = useCallback(() => push("videoRoom.toastFiveMinutes"), [push]);

  // tell the backend about our connection (also where no LiveKit webhook is configured)
  useEffect(() => {
    const report = (state: "connected" | "reconnecting") => void reportConnection(roomId, state).catch(() => undefined);
    const onConnected = () => report("connected");
    const onReconnecting = () => report("reconnecting");
    room.on(RoomEvent.Connected, onConnected).on(RoomEvent.Reconnected, onConnected).on(RoomEvent.Reconnecting, onReconnecting);
    if (room.state === ConnectionState.Connected) report("connected");
    return () => {
      room.off(RoomEvent.Connected, onConnected).off(RoomEvent.Reconnected, onConnected).off(RoomEvent.Reconnecting, onReconnecting);
    };
  }, [room, roomId]);

  // what the teacher changed for me
  useEffect(() => {
    const onPerm = (prev?: typeof localParticipant.permissions) => {
      const now = localParticipant.permissions;
      if (isHost || !prev || !now) return;
      const micBefore = allows(prev, SOURCE.microphone), micNow = allows(now, SOURCE.microphone);
      if (micBefore && !micNow) push("videoRoom.toastMicBlocked");
      if (!micBefore && micNow) push("videoRoom.toastMicAllowed");
      const screenBefore = allows(prev, SOURCE.screenShare), screenNow = allows(now, SOURCE.screenShare);
      if (!screenBefore && screenNow) push("videoRoom.toastScreenAllowed");
      if (screenBefore && !screenNow) push("videoRoom.toastScreenBlocked");
      const camBefore = allows(prev, SOURCE.camera), camNow = allows(now, SOURCE.camera);
      if (camBefore && !camNow) push("videoRoom.toastCamBlocked");
      if (!camBefore && camNow) push("videoRoom.toastCamAllowed");
      if (prev.canPublishData && !now.canPublishData) push("videoRoom.toastChatOff");
      if (!prev.canPublishData && now.canPublishData) push("videoRoom.toastChatOn");
    };
    const onMuted = (pub: TrackPublication) => {
      if (pub.source === Track.Source.Microphone && !selfMute.current && !isHost) push("videoRoom.toastMuted");
    };
    let hand = localParticipant.attributes?.[ATTR_HAND] ?? "";
    const onAttrs = (changed: Record<string, string>) => {
      if (!(ATTR_HAND in changed)) return;
      const before = hand;
      hand = changed[ATTR_HAND];
      // only a raised hand someone else lowered (the initial attributes after joining are no change)
      if (before && !hand && !isHost && Date.now() - selfHand.current > 3000) push("videoRoom.toastHandLowered");
    };
    localParticipant.on(ParticipantEvent.ParticipantPermissionsChanged, onPerm);
    localParticipant.on(ParticipantEvent.TrackMuted, onMuted);
    localParticipant.on(ParticipantEvent.AttributesChanged, onAttrs);
    return () => {
      localParticipant.off(ParticipantEvent.ParticipantPermissionsChanged, onPerm);
      localParticipant.off(ParticipantEvent.TrackMuted, onMuted);
      localParticipant.off(ParticipantEvent.AttributesChanged, onAttrs);
    };
  }, [localParticipant, isHost, push]);

  const panelTitle = panel === "chat" ? t("videoRoom.chat") : panel === "hands" ? t("videoRoom.hands") : t("videoRoom.participants");

  return (
    <div data-testid="meeting" className="flex h-[100dvh] flex-col overflow-hidden bg-neutral-950 text-white">
      <header className="flex items-center gap-3 border-b border-white/10 px-3 py-2">
        <span className="shrink-0 rounded-lg bg-sky-600 px-2 py-1 text-xs font-black tracking-wider">VIZU</span>
        <div className="min-w-0 flex-1">
          <p data-testid="meeting-title" className="truncate text-sm font-semibold">{meta.title || join.room.title}</p>
          <p className="truncate text-[11px] text-neutral-400">{subtitle}{join.room.description ? ` · ${join.room.description}` : ""}</p>
        </div>
        {endsAt ? <TimeLeft endsAt={endsAt} offset={offset} onFiveMinutes={fiveMinutes} />
          : <span data-testid="meeting-duration" className="shrink-0 text-xs tabular-nums text-neutral-300"><Duration startedAt={join.room.started_at} /></span>}
        <span data-testid="meeting-count" className="flex shrink-0 items-center gap-1 text-xs text-neutral-300"><Users size={14} /> {participants.length}</span>
        <QualityBars participant={localParticipant} className="shrink-0" />
      </header>

      <div className="relative flex min-h-0 flex-1">
        <main className="relative min-h-0 min-w-0 flex-1">
          <ConnectionStatus />
          <VideoGrid tracks={tracks} layout={shownLayout} pinned={pinned} onPin={onPin} />
          <StartAudio label={t("videoRoom.startAudio")}
                      className="absolute bottom-3 left-1/2 z-20 -translate-x-1/2 rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-lg" />
        </main>
        {panel && (
          <aside data-testid={`panel-${panel}`}
                 className="absolute inset-0 z-40 flex flex-col bg-neutral-900 md:static md:z-auto md:w-80 md:shrink-0 md:border-l md:border-white/10">
            <div className="flex items-center justify-between border-b border-white/10 px-3 py-2">
              <h2 className="text-sm font-semibold">{panelTitle}{panel === "hands" && hands.length ? ` · ${hands.length}` : ""}</h2>
              <button type="button" aria-label={t("videoRoom.close")} onClick={() => setPanel(null)} className="rounded-lg p-2 text-neutral-300 hover:bg-white/10"><X size={16} /></button>
            </div>
            <div className={cn("min-h-0 flex-1", panel === "chat" ? "flex flex-col" : "overflow-y-auto")}>
              {panel === "participants" && (
                <>
                  {isHost && <TeacherControls roomId={roomId} meta={meta} onEnd={end} onError={(k) => push(k, "error")} />}
                  <ParticipantList roomId={roomId} isHost={isHost} onError={(k) => push(k, "error")} />
                </>
              )}
              {panel === "chat" && <MeetingChat chat={chat} canSend={canChat} onError={(k) => push(k, "error")} />}
              {panel === "hands" && <RaiseHandPanel roomId={roomId} hands={hands} isHost={isHost} onError={(k) => push(k, "error")} />}
            </div>
          </aside>
        )}
      </div>

      <MeetingControls fallback={join.permissions} isHost={isHost} panel={panel} setPanel={setPanel} layout={shownLayout} setLayout={(l) => { setPinned(null); setLayout(l); }}
                       unread={unread} handCount={hands.length} handRaised={!!localHand} onToggleHand={() => void toggleHand()} volume={volume} setVolume={setVolume}
                       onSettings={() => setSettings(true)} onLeave={onLeave} onEnd={end} onError={(k) => push(k, "error")}
                       onSelfMute={(running) => { selfMute.current = running; }} />

      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 top-14 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((x) => (
          <p key={x.id} data-testid="meeting-toast"
             className={cn("max-w-md rounded-xl px-4 py-2 text-sm shadow-lg", x.tone === "error" ? "bg-red-600 text-white" : "bg-neutral-100 text-neutral-900")}>{t(x.key)}</p>
        ))}
      </div>
      {settings && <DeviceSettings onClose={() => setSettings(false)} />}
      <RoomAudioRenderer volume={volume} />
    </div>
  );
}
