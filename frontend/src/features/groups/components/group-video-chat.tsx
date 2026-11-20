"use client";

import { useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track, type Participant } from "livekit-client";
import { Mic, MicOff, MonitorUp, PhoneOff, Video, VideoOff, Hand, Users, Maximize2, Settings } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import {
  controlVideo,
  endVideo,
  getVideoStatus,
  joinVideo,
  scheduleVideo,
  sendVideoEvent,
  startVideo,
  type VideoRoomStatus,
} from "../groups-service";
import { card, ErrorBox, Loading, primaryBtn, secondaryBtn } from "./ui";

function ParticipantTile({ participant, isManager = false }: { participant: Participant; isManager?: boolean }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const publication = participant.getTrackPublication(Track.Source.Camera);
  const isScreen = participant.getTrackPublication(Track.Source.ScreenShare)?.track;

  useEffect(() => {
    const track = isScreen ?? publication?.track;
    const video = videoRef.current;
    if (!track || !video) return;
    track.attach(video);
    return () => {
      track.detach(video);
    };
  }, [isScreen, publication?.track]);

  const speaking = participant.isSpeaking;
  return (
    <div className={cn("relative min-h-40 overflow-hidden rounded-xl bg-black", speaking && "ring-2 ring-accent-blue")}>
      <video ref={videoRef} autoPlay playsInline muted={participant.isLocal} className="h-full min-h-40 w-full object-cover" />
      {(!publication?.isSubscribed || !publication.track) && (
        <div className="absolute inset-0 flex items-center justify-center text-4xl font-bold text-white/80">
          {participant.name?.slice(0, 1).toUpperCase() || "?"}
        </div>
      )}
      <div className="absolute bottom-2 left-2 rounded-md bg-black/65 px-2 py-1 text-xs font-semibold text-white">
        {participant.name || participant.identity}{isManager ? " · Teacher" : ""}
      </div>
    </div>
  );
}

export default function GroupVideoChat({ groupId, manager }: { groupId: string; manager: boolean }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<VideoRoomStatus | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [activeSpeakers, setActiveSpeakers] = useState<Participant[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mic, setMic] = useState(false);
  const [camera, setCamera] = useState(false);
  const [screen, setScreen] = useState(false);
  const [raised, setRaised] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");

  useEffect(() => {
    getVideoStatus(groupId).then((value) => {
      setStatus(value);
      setScheduledAt(value.scheduled_at ? new Date(value.scheduled_at).toISOString().slice(0, 16) : "");
    }).catch((err) => setError(err instanceof Error ? err.message : "Unable to load video room"));
  }, [groupId]);

  useEffect(() => () => { if (room) room.disconnect(); }, [room]);

  async function refresh() {
    setStatus(await getVideoStatus(groupId));
  }

  async function start() {
    setBusy(true);
    setError(null);
    try {
      setStatus(await startVideo(groupId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start video room");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    setBusy(true);
    try {
      setStatus(await endVideo(groupId));
      if (room) room.disconnect();
      setRoom(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to end video room");
    } finally {
      setBusy(false);
    }
  }

  async function connect() {
    setBusy(true);
    setError(null);
    try {
      const join = await joinVideo(groupId);
      const next = new Room({ adaptiveStream: true, dynacast: true });
      await next.connect(join.url, join.token);
      await next.localParticipant.setMicrophoneEnabled(false);
      await next.localParticipant.setCameraEnabled(false);

      const sync = () => setParticipants([next.localParticipant, ...Array.from(next.remoteParticipants.values())]);
      next.on(RoomEvent.ParticipantConnected, () => sync());
      next.on(RoomEvent.ParticipantDisconnected, () => sync());
      next.on(RoomEvent.TrackSubscribed, sync);
      next.on(RoomEvent.TrackUnsubscribed, sync);
      next.on(RoomEvent.LocalTrackPublished, sync);
      next.on(RoomEvent.LocalTrackUnpublished, sync);
      next.on(RoomEvent.ActiveSpeakersChanged, (speakers: Participant[]) => setActiveSpeakers(speakers));
      next.on(RoomEvent.Disconnected, () => setRoom(null));
      sync();
      setRoom(next);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to join video room");
    } finally {
      setBusy(false);
    }
  }

  async function leave() {
    if (room) {
      room.disconnect();
      setRoom(null);
    }
    await sendVideoEvent(groupId, "leave").catch(() => undefined);
  }

  async function toggleMic() {
    if (!room) return;
    await room.localParticipant.setMicrophoneEnabled(!mic);
    const enabled = room.localParticipant.isMicrophoneEnabled;
    setMic(enabled);
    await sendVideoEvent(groupId, enabled ? "mic_on" : "mic_off");
  }

  async function toggleCamera() {
    if (!room) return;
    await room.localParticipant.setCameraEnabled(!camera);
    const enabled = room.localParticipant.isCameraEnabled;
    setCamera(enabled);
    await sendVideoEvent(groupId, enabled ? "camera_on" : "camera_off");
  }

  async function toggleScreen() {
    if (!room) return;
    await room.localParticipant.setScreenShareEnabled(!screen);
    const enabled = room.localParticipant.isScreenShareEnabled;
    setScreen(enabled);
    await sendVideoEvent(groupId, enabled ? "screen_share_start" : "screen_share_stop");
  }

  async function toggleRaised() {
    const next = !raised;
    setRaised(next);
    await sendVideoEvent(groupId, next ? "raise_hand" : "lower_hand");
  }

  async function saveSchedule() {
    setBusy(true);
    setError(null);
    try {
      setStatus(await scheduleVideo(groupId, { scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to schedule video room");
    } finally {
      setBusy(false);
    }
  }

  async function muteAll() {
    await controlVideo(groupId, "mute_all");
  }

  async function enterFullscreen() {
    await document.documentElement.requestFullscreen?.();
  }

  if (!status) return error ? <ErrorBox error={error} /> : <Loading />;

  if (!room) {
    return (
      <div className={cn(card, "space-y-4 p-5")}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-text-primary">{t("groups.tabVideoChat")}</p>
            <p className="text-xs text-text-muted">
              {status.status === "live" ? "Live" : status.scheduled_at ? new Date(status.scheduled_at).toLocaleString() : "Not scheduled"}
            </p>
          </div>
          <span className={cn("rounded-full px-3 py-1 text-xs font-bold", status.status === "live" ? "bg-emerald-100 text-emerald-700" : "bg-surface-hover text-text-muted")}>
            {status.status}
          </span>
        </div>
        {manager && (
          <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto]">
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} className="rounded-lg border border-surface-border bg-surface-card px-3 py-2 text-sm text-text-primary" aria-label="Videochat schedule" />
            <button type="button" className={secondaryBtn} onClick={saveSchedule} disabled={busy}>Schedule</button>
            {status.status === "live" ? (
              <button type="button" className={primaryBtn} onClick={finish} disabled={busy}>End room</button>
            ) : (
              <button type="button" className={primaryBtn} onClick={start} disabled={busy || !status.livekit_configured}>Start videochat</button>
            )}
          </div>
        )}
        {!status.livekit_configured && <p className="text-sm text-danger">LiveKit server is not configured.</p>}
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        {status.status === "live" && (
          <button type="button" className={primaryBtn} onClick={connect} disabled={busy}>Join videochat</button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {participants.map((participant) => (
          <ParticipantTile key={participant.identity} participant={participant} isManager={participant.isLocal ? manager : false} />
        ))}
      </div>
      {activeSpeakers.length > 0 && <p className="text-xs text-text-muted">Speaking: {activeSpeakers.map((p) => p.name || p.identity).join(", ")}</p>}
      <div className="sticky bottom-3 z-10 flex flex-wrap items-center justify-center gap-2 rounded-2xl border border-surface-border bg-surface-card/95 p-2 shadow-lg backdrop-blur">
        <button type="button" className={secondaryBtn} onClick={toggleMic} aria-label={mic ? "Mute microphone" : "Unmute microphone"}>{mic ? <Mic size={18} /> : <MicOff size={18} />}</button>
        <button type="button" className={secondaryBtn} onClick={toggleCamera} aria-label={camera ? "Turn camera off" : "Turn camera on"}>{camera ? <Video size={18} /> : <VideoOff size={18} />}</button>
        <button type="button" className={secondaryBtn} onClick={toggleScreen} aria-label="Share screen"><MonitorUp size={18} /></button>
        <button type="button" className={cn(secondaryBtn, raised && "border-accent-blue text-accent-blue")} onClick={toggleRaised} aria-label="Raise hand"><Hand size={18} /></button>
        <button type="button" className={secondaryBtn} aria-label="Participants"><Users size={18} /> <span className="text-xs">{participants.length}</span></button>
        {manager && <button type="button" className={secondaryBtn} onClick={muteAll} aria-label="Mute all"><MicOff size={18} /></button>}
        <button type="button" className={secondaryBtn} onClick={enterFullscreen} aria-label="Fullscreen"><Maximize2 size={18} /></button>
        <button type="button" className={secondaryBtn} aria-label="Settings"><Settings size={18} /></button>
        {manager ? (
          <button type="button" className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm font-bold text-white" onClick={finish}><PhoneOff size={18} /> End</button>
        ) : (
          <button type="button" className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm font-bold text-white" onClick={leave}><PhoneOff size={18} /> Leave</button>
        )}
      </div>
    </div>
  );
}
