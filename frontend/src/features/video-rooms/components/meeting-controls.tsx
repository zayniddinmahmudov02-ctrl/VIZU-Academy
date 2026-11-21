"use client";

import { useState, type ReactNode } from "react";
import { useLocalParticipant, useLocalParticipantPermissions, useMediaDevices, useRoomContext } from "@livekit/components-react";
import {
  Hand,
  LayoutGrid,
  Lock,
  Maximize,
  MessageSquare,
  Mic,
  MicOff,
  Minimize,
  MonitorUp,
  MoreHorizontal,
  PhoneOff,
  Presentation,
  Settings,
  SwitchCamera,
  Users,
  Video,
  VideoOff,
  Volume2,
  X,
} from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import type { RoomPermissions } from "../video-rooms-service";
import { mediaErrorKey, SOURCE } from "../video-room-utils";
import { allows } from "./participant-list";
import type { Layout } from "./video-grid";

export type Panel = "participants" | "chat" | "hands" | null;

function Btn({ label, onClick, active, danger, off, disabled, badge, children, testId, className }: {
  label: string;
  onClick: () => void;
  active?: boolean;
  danger?: boolean;
  off?: boolean;
  disabled?: boolean;
  badge?: number;
  children: ReactNode;
  testId: string;
  className?: string;
}) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} disabled={disabled} data-testid={testId} aria-pressed={active}
            className={cn("relative inline-flex h-12 min-w-12 shrink-0 items-center justify-center gap-2 rounded-full px-3 text-white transition-colors disabled:opacity-50",
              danger ? "bg-red-600 hover:bg-red-500" : off ? "bg-red-600/90 hover:bg-red-500" : active ? "bg-sky-600 hover:bg-sky-500" : "bg-neutral-700 hover:bg-neutral-600",
              className)}>
      {children}
      {!!badge && <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-amber-400 px-1 text-center text-[11px] font-bold leading-5 text-black">{badge > 99 ? "99+" : badge}</span>}
    </button>
  );
}

/** Bottom bar. Publish buttons follow the LiveKit permissions the backend gave this participant (live: a teacher's
 *  change applies at once); the SFU refuses anything else anyway. Secondary buttons move into "More" on a phone. */
export default function MeetingControls({ fallback, isHost, panel, setPanel, layout, setLayout, unread, handCount, handRaised, onToggleHand,
  volume, setVolume, onSettings, onLeave, onEnd, onError, onSelfMute }: {
  fallback: RoomPermissions;
  isHost: boolean;
  panel: Panel;
  setPanel: (p: Panel) => void;
  layout: Layout;
  setLayout: (l: Layout) => void;
  unread: number;
  handCount: number;
  handRaised: boolean;
  onToggleHand: () => void;
  volume: number;
  setVolume: (v: number) => void;
  onSettings: () => void;
  onLeave: () => void;
  onEnd: () => void;
  onError: (key: string) => void;
  onSelfMute: (running: boolean) => void;
}) {
  const { t } = useTranslation();
  const room = useRoomContext();
  const { localParticipant, isMicrophoneEnabled, isCameraEnabled, isScreenShareEnabled } = useLocalParticipant();
  const perm = useLocalParticipantPermissions();
  const cameras = useMediaDevices({ kind: "videoinput" });
  const [more, setMore] = useState(false);
  const [showVolume, setShowVolume] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const canMic = allows(perm, SOURCE.microphone, fallback.microphone);
  const canScreen = allows(perm, SOURCE.screenShare, fallback.screen_share);
  const screenSupported = typeof navigator !== "undefined" && !!navigator.mediaDevices && "getDisplayMedia" in navigator.mediaDevices;
  const fullscreenSupported = typeof document !== "undefined" && document.fullscreenEnabled;

  async function run(fn: () => Promise<unknown>) {
    try {
      await fn();
    } catch (e) {
      onError(mediaErrorKey(e, window.isSecureContext));
    }
  }

  async function toggleMic() {
    onSelfMute(true); // a mute while our own toggle runs is not the teacher's
    try {
      await run(() => localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled));
    } finally {
      onSelfMute(false);
    }
  }

  async function switchCamera() {
    if (cameras.length < 2) return;
    const current = room.getActiveDevice("videoinput");
    const i = cameras.findIndex((d) => d.deviceId === current);
    await run(() => room.switchActiveDevice("videoinput", cameras[(i + 1) % cameras.length].deviceId));
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        setFullscreen(false);
      } else {
        await document.documentElement.requestFullscreen();
        setFullscreen(true);
      }
    } catch {
      setFullscreen(!!document.fullscreenElement);
    }
  }

  const toggle = (p: Exclude<Panel, null>) => setPanel(panel === p ? null : p);
  const secondary = (
    <>
      {cameras.length > 1 && isCameraEnabled && (
        <Btn label={t("videoRoom.switchCamera")} onClick={() => void switchCamera()} testId="ctl-switch-camera"><SwitchCamera size={20} /></Btn>
      )}
      {screenSupported && canScreen && (
        <Btn label={isScreenShareEnabled ? t("videoRoom.stopShare") : t("videoRoom.shareScreen")} active={isScreenShareEnabled} testId="ctl-screen"
             onClick={() => void run(() => localParticipant.setScreenShareEnabled(!isScreenShareEnabled, { audio: true, selfBrowserSurface: "exclude" }))}>
          <MonitorUp size={20} />
        </Btn>
      )}
      <Btn label={t("videoRoom.participants")} active={panel === "participants"} onClick={() => toggle("participants")} testId="ctl-participants"><Users size={20} /></Btn>
      {isHost && <Btn label={t("videoRoom.hands")} active={panel === "hands"} badge={handCount} onClick={() => toggle("hands")} testId="ctl-hands"><Hand size={20} /></Btn>}
      <Btn label={layout === "grid" ? t("videoRoom.layoutSpeaker") : t("videoRoom.layoutGrid")} onClick={() => setLayout(layout === "grid" ? "speaker" : "grid")} testId="ctl-layout">
        {layout === "grid" ? <Presentation size={20} /> : <LayoutGrid size={20} />}
      </Btn>
      <div className="relative" data-keep-open>
        <Btn label={t("videoRoom.volume")} active={showVolume} onClick={() => setShowVolume((v) => !v)} testId="ctl-volume"><Volume2 size={20} /></Btn>
        {showVolume && (
          <div className="absolute bottom-14 left-1/2 z-30 w-44 -translate-x-1/2 rounded-xl bg-neutral-900 p-3 shadow-xl ring-1 ring-white/10">
            <label className="block text-xs text-neutral-300">{t("videoRoom.volume")} {Math.round(volume * 100)}%
              <input type="range" min={0} max={1} step={0.05} value={volume} onChange={(e) => setVolume(Number(e.target.value))} data-testid="ctl-volume-range" className="mt-2 w-full accent-sky-500" />
            </label>
          </div>
        )}
      </div>
      <Btn label={t("videoRoom.settings")} onClick={onSettings} testId="ctl-settings"><Settings size={20} /></Btn>
      {fullscreenSupported && (
        <Btn label={fullscreen ? t("videoRoom.exitFullscreen") : t("videoRoom.fullscreen")} onClick={() => void toggleFullscreen()} testId="ctl-fullscreen">
          {fullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
        </Btn>
      )}
    </>
  );

  return (
    <div className="relative z-50 border-t border-white/10 bg-neutral-950/95 px-2 py-2">
      <div className="flex items-center justify-center gap-2">
        <Btn label={canMic ? (isMicrophoneEnabled ? t("videoRoom.micOn") : t("videoRoom.micOff")) : t("videoRoom.micLockedHint")}
             off={!isMicrophoneEnabled} disabled={!canMic} onClick={() => void toggleMic()} testId="ctl-mic">
          {!canMic ? <Lock size={18} /> : isMicrophoneEnabled ? <Mic size={20} /> : <MicOff size={20} />}
        </Btn>
        <Btn label={isCameraEnabled ? t("videoRoom.camOn") : t("videoRoom.camOff")} off={!isCameraEnabled} testId="ctl-camera"
             onClick={() => void run(() => localParticipant.setCameraEnabled(!isCameraEnabled))}>
          {isCameraEnabled ? <Video size={20} /> : <VideoOff size={20} />}
        </Btn>
        {!isHost && (
          <Btn label={handRaised ? t("videoRoom.lowerHand") : t("videoRoom.raiseHand")} active={handRaised} onClick={onToggleHand} testId="ctl-hand"
               className={handRaised ? "bg-amber-500 text-black hover:bg-amber-400" : ""}>
            <Hand size={20} />
          </Btn>
        )}
        <Btn label={t("videoRoom.chat")} active={panel === "chat"} badge={panel === "chat" ? 0 : unread} onClick={() => toggle("chat")} testId="ctl-chat">
          <MessageSquare size={20} />
        </Btn>
        <div className="hidden items-center gap-2 sm:flex">{secondary}</div>
        <Btn label={t("videoRoom.more")} active={more} onClick={() => setMore((v) => !v)} testId="ctl-more" className="sm:hidden"><MoreHorizontal size={20} /></Btn>
        <Btn label={t("videoRoom.leave")} danger onClick={onLeave} testId="ctl-leave" className="px-4"><PhoneOff size={20} /></Btn>
        {isHost && (
          <button type="button" onClick={onEnd} data-testid="ctl-end"
                  className="hidden h-12 shrink-0 items-center rounded-full bg-red-700 px-4 text-sm font-semibold text-white hover:bg-red-600 md:inline-flex">
            {t("videoRoom.end")}
          </button>
        )}
      </div>
      {more && (
        <div className="absolute inset-x-2 bottom-16 z-30 rounded-2xl bg-neutral-900 p-3 shadow-2xl ring-1 ring-white/10 sm:hidden">
          <div className="mb-2 flex justify-end">
            <button type="button" aria-label={t("videoRoom.close")} onClick={() => setMore(false)} className="rounded-lg p-1.5 text-neutral-300"><X size={16} /></button>
          </div>
          <div className="flex flex-wrap justify-center gap-2"
               onClick={(e) => { if (!(e.target as HTMLElement).closest("[data-keep-open]")) setMore(false); }}>{secondary}</div>
          {isHost && (
            <button type="button" onClick={onEnd} data-testid="ctl-end" className="mt-3 h-11 w-full rounded-xl bg-red-700 text-sm font-semibold text-white">{t("videoRoom.end")}</button>
          )}
        </div>
      )}
    </div>
  );
}
