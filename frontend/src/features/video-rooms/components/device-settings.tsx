"use client";

import { useEffect, useRef, useState } from "react";
import { useLocalParticipant, useMediaDeviceSelect, useTrackVolume } from "@livekit/components-react";
import { createLocalAudioTrack, createLocalVideoTrack, VideoPresets, type LocalAudioTrack, type LocalVideoTrack } from "livekit-client";
import { Mic, MicOff, Video, VideoOff, X } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { mediaErrorKey } from "../video-room-utils";

export interface DeviceChoices { videoEnabled: boolean; audioEnabled: boolean; videoDeviceId: string; audioDeviceId: string; audioOutputId: string }

const KEY = "vizu.video.devices";
const DEFAULTS: DeviceChoices = { videoEnabled: true, audioEnabled: true, videoDeviceId: "", audioDeviceId: "", audioOutputId: "" };

/** Per-browser device choice (a convenience only; nothing breaks without storage). */
export function loadChoices(): DeviceChoices {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? { ...DEFAULTS, ...(JSON.parse(raw) as Partial<DeviceChoices>) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

export function saveChoices(choices: DeviceChoices): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(choices));
  } catch {
    // private mode / blocked storage
  }
}

const sinkSupported = () => typeof HTMLMediaElement !== "undefined" && "setSinkId" in HTMLMediaElement.prototype;

export function LevelMeter({ level, testId }: { level: number; testId?: string }) {
  const { t } = useTranslation();
  const pct = Math.min(100, Math.round(level * 140));
  return (
    <div>
      <p className="mb-1 text-[11px] text-neutral-400">{t("videoRoom.micLevel")}</p>
      <div role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} data-testid={testId}
           className="h-2 overflow-hidden rounded-full bg-white/10">
        <div className={cn("h-full rounded-full transition-[width] duration-75", pct > 70 ? "bg-amber-400" : "bg-emerald-400")} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DeviceSelect({ label, devices, value, onChange, testId }: {
  label: string;
  devices: MediaDeviceInfo[];
  value: string;
  onChange: (id: string) => void;
  testId: string;
}) {
  const { t } = useTranslation();
  return (
    <label className="block text-xs font-semibold text-neutral-300">
      {label}
      <select data-testid={testId} value={value} onChange={(e) => onChange(e.target.value)}
              className="mt-1 h-11 w-full rounded-xl bg-neutral-800 px-3 text-sm font-normal text-white outline-none ring-1 ring-white/10 focus:ring-sky-500">
        <option value="">{t("videoRoom.defaultDevice")}</option>
        {devices.filter((d) => d.deviceId && d.deviceId !== "default").map((d, i) => (
          <option key={d.deviceId} value={d.deviceId}>{d.label || `${label} ${i + 1}`}</option>
        ))}
      </select>
    </label>
  );
}

function listDevices(): Promise<MediaDeviceInfo[]> {
  return navigator.mediaDevices?.enumerateDevices ? navigator.mediaDevices.enumerateDevices() : Promise.resolve([]);
}

/** Before joining: camera preview, microphone level, device choice and clear permission errors. Preview tracks are
 *  stopped when the choice changes or the page leaves pre-join; LiveKit opens its own tracks on join. */
export function PrejoinDevices({ choices, onChange, micAllowed }: {
  choices: DeviceChoices;
  onChange: (patch: Partial<DeviceChoices>) => void;
  micAllowed: boolean;
}) {
  const { t } = useTranslation();
  const [video, setVideo] = useState<{ track: LocalVideoTrack; key: string } | null>(null);
  const [audio, setAudio] = useState<{ track: LocalAudioTrack; key: string } | null>(null);
  const [error, setError] = useState<{ key: string; kind: "video" | "audio" } | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const videoEl = useRef<HTMLVideoElement>(null);
  const { videoDeviceId, audioDeviceId } = choices;
  const videoKey = choices.videoEnabled ? `v:${videoDeviceId}` : "";
  const audioKey = choices.audioEnabled && micAllowed ? `a:${audioDeviceId}` : "";
  const shownVideo = video && video.key === videoKey ? video.track : null;
  const shownAudio = audio && audio.key === audioKey ? audio.track : undefined;
  const level = useTrackVolume(shownAudio);

  useEffect(() => {
    if (!videoKey) return;
    let stopped = false;
    let made: LocalVideoTrack | null = null;
    createLocalVideoTrack({ deviceId: videoDeviceId || undefined, resolution: VideoPresets.h540.resolution })
      .then((track) => {
        if (stopped) return track.stop();
        made = track;
        setVideo({ track, key: videoKey });
        setError((e) => (e?.kind === "video" ? null : e));
        return listDevices().then(setDevices);
      })
      .catch((e: unknown) => {
        if (stopped) return;
        setError({ key: mediaErrorKey(e, window.isSecureContext), kind: "video" });
        onChange({ videoEnabled: false });
      });
    return () => {
      stopped = true;
      made?.stop();
    };
  }, [videoKey, videoDeviceId, onChange]);

  useEffect(() => {
    if (!audioKey) return;
    let stopped = false;
    let made: LocalAudioTrack | null = null;
    createLocalAudioTrack({ deviceId: audioDeviceId || undefined, echoCancellation: true, noiseSuppression: true })
      .then((track) => {
        if (stopped) return track.stop();
        made = track;
        setAudio({ track, key: audioKey });
        setError((e) => (e?.kind === "audio" ? null : e));
        return listDevices().then(setDevices);
      })
      .catch((e: unknown) => {
        if (stopped) return;
        setError({ key: mediaErrorKey(e, window.isSecureContext), kind: "audio" });
        onChange({ audioEnabled: false });
      });
    return () => {
      stopped = true;
      made?.stop();
    };
  }, [audioKey, audioDeviceId, onChange]);

  useEffect(() => {
    const el = videoEl.current;
    if (!el || !shownVideo) return;
    shownVideo.attach(el);
    return () => {
      shownVideo.detach(el);
    };
  }, [shownVideo]);

  const cams = devices.filter((d) => d.kind === "videoinput");
  const mics = devices.filter((d) => d.kind === "audioinput");
  const outs = devices.filter((d) => d.kind === "audiooutput");
  const toggle = "inline-flex h-12 w-12 items-center justify-center rounded-full text-white ring-1 ring-white/10";

  return (
    <div className="grid gap-4 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="relative aspect-video overflow-hidden rounded-2xl bg-neutral-800 ring-1 ring-white/10">
        {shownVideo ? (
          <video ref={videoEl} data-testid="prejoin-preview" muted playsInline autoPlay className="h-full w-full -scale-x-100 object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-neutral-400"><VideoOff size={20} className="mr-2" /> {t("videoRoom.cameraOff")}</div>
        )}
        <div className="absolute inset-x-0 bottom-3 flex justify-center gap-3">
          <button type="button" data-testid="prejoin-mic" aria-pressed={choices.audioEnabled && micAllowed} disabled={!micAllowed}
                  aria-label={choices.audioEnabled ? t("videoRoom.micOn") : t("videoRoom.micOff")}
                  onClick={() => onChange({ audioEnabled: !choices.audioEnabled })}
                  className={cn(toggle, choices.audioEnabled && micAllowed ? "bg-neutral-700/90" : "bg-red-600", !micAllowed && "opacity-60")}>
            {choices.audioEnabled && micAllowed ? <Mic size={20} /> : <MicOff size={20} />}
          </button>
          <button type="button" data-testid="prejoin-camera" aria-pressed={choices.videoEnabled}
                  aria-label={choices.videoEnabled ? t("videoRoom.camOn") : t("videoRoom.camOff")}
                  onClick={() => onChange({ videoEnabled: !choices.videoEnabled })}
                  className={cn(toggle, choices.videoEnabled ? "bg-neutral-700/90" : "bg-red-600")}>
            {choices.videoEnabled ? <Video size={20} /> : <VideoOff size={20} />}
          </button>
        </div>
      </div>
      <div className="space-y-3">
        {error && <p role="alert" data-testid="prejoin-error" className="rounded-xl bg-red-500/10 p-3 text-xs text-red-300 ring-1 ring-red-500/30">{t(error.key)}</p>}
        {!micAllowed && <p className="rounded-xl bg-amber-500/10 p-3 text-xs text-amber-200 ring-1 ring-amber-500/30">{t("videoRoom.micLockedHint")}</p>}
        <DeviceSelect label={t("videoRoom.camera")} devices={cams} value={videoDeviceId} testId="prejoin-camera-select"
                      onChange={(id) => onChange({ videoDeviceId: id })} />
        <DeviceSelect label={t("videoRoom.microphone")} devices={mics} value={audioDeviceId} testId="prejoin-mic-select"
                      onChange={(id) => onChange({ audioDeviceId: id })} />
        {sinkSupported() && outs.length > 0 && (
          <DeviceSelect label={t("videoRoom.speaker")} devices={outs} value={choices.audioOutputId} testId="prejoin-speaker-select"
                        onChange={(id) => onChange({ audioOutputId: id })} />
        )}
        {shownAudio && <LevelMeter level={level} testId="prejoin-mic-level" />}
      </div>
    </div>
  );
}

/** In the room: switch camera / microphone / speaker of the running call, with a live microphone level. */
export default function DeviceSettings({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const mic = useMediaDeviceSelect({ kind: "audioinput" });
  const cam = useMediaDeviceSelect({ kind: "videoinput" });
  const out = useMediaDeviceSelect({ kind: "audiooutput" });
  const { microphoneTrack } = useLocalParticipant();
  const level = useTrackVolume(microphoneTrack?.track as LocalAudioTrack | undefined);

  function pick(kind: "audioDeviceId" | "videoDeviceId" | "audioOutputId", select: typeof mic, id: string) {
    void select.setActiveMediaDevice(id || "default");
    saveChoices({ ...loadChoices(), [kind]: id });
  }

  return (
    <div role="dialog" aria-modal="true" aria-label={t("videoRoom.settings")} className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4">
      <div data-testid="device-settings" className="w-full max-w-md space-y-3 rounded-t-2xl bg-neutral-900 p-4 ring-1 ring-white/10 sm:rounded-2xl">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-white">{t("videoRoom.settings")}</h2>
          <button type="button" onClick={onClose} aria-label={t("videoRoom.close")} className="rounded-lg p-2 text-neutral-300 hover:bg-white/10"><X size={18} /></button>
        </div>
        <DeviceSelect label={t("videoRoom.camera")} devices={cam.devices} value={cam.activeDeviceId === "default" ? "" : cam.activeDeviceId}
                      testId="room-camera-select" onChange={(id) => pick("videoDeviceId", cam, id)} />
        <DeviceSelect label={t("videoRoom.microphone")} devices={mic.devices} value={mic.activeDeviceId === "default" ? "" : mic.activeDeviceId}
                      testId="room-mic-select" onChange={(id) => pick("audioDeviceId", mic, id)} />
        {sinkSupported() && out.devices.length > 0 && (
          <DeviceSelect label={t("videoRoom.speaker")} devices={out.devices} value={out.activeDeviceId === "default" ? "" : out.activeDeviceId}
                        testId="room-speaker-select" onChange={(id) => pick("audioOutputId", out, id)} />
        )}
        {microphoneTrack?.track && <LevelMeter level={level} testId="room-mic-level" />}
      </div>
    </div>
  );
}
