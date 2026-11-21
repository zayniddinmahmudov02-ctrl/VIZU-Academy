"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Room, RoomEvent, Track, type Participant } from "livekit-client";
import {
  Hand, Maximize2, MessageSquare, Mic, MicOff, MonitorUp, PhoneOff, RefreshCw, UserRoundX, Users, Video, VideoOff,
} from "lucide-react";

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
import { card, ErrorBox, Loading, primaryBtn, secondaryBtn, useErrorText } from "./ui";
import GroupChat from "./group-chat";

type VideoControl = "mute" | "kick" | "deny_mic" | "allow_mic" | "deny_screen" | "allow_screen";
type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

function ParticipantTile({ participant, raised, onControl }: {
  participant: Participant;
  raised: boolean;
  onControl?: (action: VideoControl, id: string) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const camera = participant.getTrackPublication(Track.Source.Camera);
  const microphone = participant.getTrackPublication(Track.Source.Microphone);
  const screen = participant.getTrackPublication(Track.Source.ScreenShare)?.track;
  const videoTrack = screen ?? camera?.track;
  const audioTrack = microphone?.track;

  useEffect(() => {
    const video = videoRef.current;
    if (!videoTrack || !video) return;
    videoTrack.attach(video);
    return () => { videoTrack.detach(video); };
  }, [videoTrack]);

  useEffect(() => {
    const audio = audioRef.current;
    if (participant.isLocal || !audioTrack || !audio) return;
    audioTrack.attach(audio);
    return () => { audioTrack.detach(audio); };
  }, [audioTrack, participant.isLocal]);

  let participantRole = "student";
  try {
    participantRole = JSON.parse(participant.metadata || "{}").role || participantRole;
  } catch {
    participantRole = "student";
  }

  return (
    <div className={cn("relative min-h-40 overflow-hidden rounded-xl bg-black", participant.isSpeaking && "ring-2 ring-accent-blue")}>
      <video ref={videoRef} autoPlay playsInline muted className={cn("h-full min-h-40 w-full object-cover", !videoTrack && "hidden")} />
      <audio ref={audioRef} autoPlay playsInline className="hidden" />
      {!videoTrack && (
        <div className="absolute inset-0 flex items-center justify-center text-4xl font-bold text-white/80">
          {participant.name?.slice(0, 1).toUpperCase() || "?"}
        </div>
      )}
      <div className="absolute bottom-2 left-2 flex items-center gap-2 rounded-md bg-black/65 px-2 py-1 text-xs font-semibold text-white">
        <span>{participant.name || participant.identity}{participantRole === "teacher" ? " · Teacher" : participantRole === "admin" ? " · Admin" : ""}</span>
        {(!microphone || microphone.isMuted) && <MicOff size={13} aria-label="Microphone muted" />}
        {raised && <Hand size={13} aria-label="Hand raised" className="text-amber-300" />}
        {screen && <MonitorUp size={13} aria-label="Sharing screen" />}
      </div>
      {onControl && !participant.isLocal && participantRole === "student" && (
        <div className="absolute right-2 top-2 flex gap-1">
          <button type="button" className="rounded-md bg-black/65 p-2 text-white" aria-label="Mute participant"
            onClick={() => onControl("mute", participant.identity)}><MicOff size={15} /></button>
          <button type="button" className="rounded-md bg-black/65 p-2 text-white" aria-label="Remove participant"
            onClick={() => onControl("kick", participant.identity)}><UserRoundX size={15} /></button>
        </div>
      )}
    </div>
  );
}

export default function GroupVideoChat({ groupId, manager }: { groupId: string; manager: boolean }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const rootRef = useRef<HTMLDivElement>(null);
  const roomRef = useRef<Room | null>(null);
  const connectingRef = useRef(false);
  const [status, setStatus] = useState<VideoRoomStatus | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [activeSpeakers, setActiveSpeakers] = useState<Participant[]>([]);
  const [raisedIds, setRaisedIds] = useState<Set<string>>(new Set());
  const [deniedMic, setDeniedMic] = useState<Set<string>>(new Set());
  const [deniedScreen, setDeniedScreen] = useState<Set<string>>(new Set());
  const [connection, setConnection] = useState<ConnectionStatus>("disconnected");
  const [connectionQuality, setConnectionQuality] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mic, setMic] = useState(false);
  const [camera, setCamera] = useState(false);
  const [screen, setScreen] = useState(false);
  const [raised, setRaised] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [participantsOpen, setParticipantsOpen] = useState(false);
  const [cameraDevices, setCameraDevices] = useState<MediaDeviceInfo[]>([]);
  const [scheduledAt, setScheduledAt] = useState("");

  const showError = useCallback((err: unknown, fallback: string) => setError(errorText(err) || fallback), [errorText]);

  useEffect(() => {
    let active = true;
    getVideoStatus(groupId).then((value) => {
      if (!active) return;
      setStatus(value);
      setScheduledAt(value.scheduled_at ? new Date(value.scheduled_at).toISOString().slice(0, 16) : "");
    }).catch((err) => active && showError(err, "Unable to load video room"));
    return () => { active = false; };
  }, [groupId, showError]);

  useEffect(() => {
    const current = room;
    return () => {
      if (current && current !== roomRef.current) current.disconnect(true);
    };
  }, [room]);

  const refresh = useCallback(async () => {
    setStatus(await getVideoStatus(groupId));
  }, [groupId]);

  const recordEvent = useCallback((kind: string) => {
    void sendVideoEvent(groupId, kind).catch((err) => showError(err, "Could not save room event"));
  }, [groupId, showError]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      setStatus(await startVideo(groupId));
    } catch (err) {
      showError(err, "Unable to start video room");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    setBusy(true);
    setError(null);
    try {
      setStatus(await endVideo(groupId));
      const current = roomRef.current;
      roomRef.current = null;
      current?.disconnect(true);
      setRoom(null);
      setParticipants([]);
      setConnection("disconnected");
    } catch (err) {
      showError(err, "Unable to end video room");
    } finally {
      setBusy(false);
    }
  }

  async function connect() {
    if (connectingRef.current || roomRef.current) return;
    connectingRef.current = true;
    setBusy(true);
    setError(null);
    setConnection("connecting");
    try {
      const grant = await joinVideo(groupId);
      const next = new Room({ adaptiveStream: true, dynacast: true });
      await next.connect(grant.url, grant.token);
      await next.localParticipant.setMicrophoneEnabled(false);
      await next.localParticipant.setCameraEnabled(false);
      roomRef.current = next;

      const sync = () => setParticipants([next.localParticipant, ...Array.from(next.remoteParticipants.values())]);
      next.on(RoomEvent.ParticipantConnected, () => sync());
      next.on(RoomEvent.ParticipantDisconnected, () => sync());
      next.on(RoomEvent.TrackSubscribed, () => sync());
      next.on(RoomEvent.TrackUnsubscribed, () => sync());
      next.on(RoomEvent.TrackPublished, (...args) => {
        const participant = args[1];
        sync();
        if (participant.isLocal) recordEvent("track_published");
      });
      next.on(RoomEvent.TrackUnpublished, (...args) => {
        const participant = args[1];
        sync();
        if (participant.isLocal) recordEvent("track_unpublished");
      });
      next.on(RoomEvent.ParticipantMetadataChanged, () => sync());
      next.on(RoomEvent.ActiveSpeakersChanged, (speakers: Participant[]) => setActiveSpeakers(speakers));
      next.on(RoomEvent.ConnectionQualityChanged, (quality, participant) => {
        if (participant.isLocal) setConnectionQuality(String(quality));
      });
      next.on(RoomEvent.Reconnecting, () => {
        setConnection("reconnecting");
        recordEvent("connection_reconnecting");
      });
      next.on(RoomEvent.Reconnected, () => {
        setConnection("connected");
        recordEvent("connection_reconnected");
        sync();
      });
      next.on(RoomEvent.DataReceived, (...args) => {
        const [payload, participant, , topic] = args;
        if (topic !== "group-video" || !participant) return;
        try {
          const message = JSON.parse(new TextDecoder().decode(payload));
          if (message.type !== "hand" || typeof message.raised !== "boolean") return;
          setRaisedIds((current) => {
            const updated = new Set(current);
            if (message.raised) updated.add(participant.identity);
            else updated.delete(participant.identity);
            return updated;
          });
        } catch {
          setError("Received an invalid room event.");
        }
      });
      next.on(RoomEvent.Disconnected, () => {
        roomRef.current = null;
        setRoom(null);
        setParticipants([]);
        setActiveSpeakers([]);
        setMic(false);
        setCamera(false);
        setScreen(false);
        setConnection("disconnected");
        void refresh().catch((err) => showError(err, "Unable to refresh room status"));
      });
      sync();
      setRoom(next);
      setConnection("connected");
      recordEvent("join");
      void navigator.mediaDevices?.enumerateDevices().then((devices) => setCameraDevices(devices.filter((d) => d.kind === "videoinput")))
        .catch((err) => showError(err, "Unable to list camera devices"));
      await refresh();
    } catch (err) {
      setConnection("disconnected");
      showError(err, "Unable to join video room");
      const failedRoom = roomRef.current;
      roomRef.current = null;
      failedRoom?.disconnect(true);
    } finally {
      connectingRef.current = false;
      setBusy(false);
    }
  }

  async function leave() {
    const current = roomRef.current;
    roomRef.current = null;
    current?.disconnect(true);
    setRoom(null);
    setParticipants([]);
    setActiveSpeakers([]);
    setMic(false);
    setCamera(false);
    setScreen(false);
    setRaised(false);
    setRaisedIds(new Set());
    setConnection("disconnected");
    recordEvent("leave");
  }

  async function toggleMic() {
    if (!room) return;
    try {
      await room.localParticipant.setMicrophoneEnabled(!mic);
      const enabled = room.localParticipant.isMicrophoneEnabled;
      setMic(enabled);
      recordEvent(enabled ? "mic_on" : "mic_off");
    } catch (err) {
      showError(err, "Unable to access the microphone");
    }
  }

  async function refreshCameraDevices() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    setCameraDevices(devices.filter((device) => device.kind === "videoinput"));
  }

  async function toggleCamera() {
    if (!room) return;
    try {
      await room.localParticipant.setCameraEnabled(!camera);
      setCamera(room.localParticipant.isCameraEnabled);
      await refreshCameraDevices();
      recordEvent(room.localParticipant.isCameraEnabled ? "camera_on" : "camera_off");
    } catch (err) {
      showError(err, "Unable to access the camera");
    }
  }

  async function switchCamera() {
    if (!room || cameraDevices.length < 2) return;
    const activeId = room.localParticipant.getTrackPublication(Track.Source.Camera)?.track?.mediaStreamTrack.getSettings().deviceId;
    const currentIndex = cameraDevices.findIndex((device) => device.deviceId === activeId);
    const next = cameraDevices[(currentIndex + 1) % cameraDevices.length];
    try {
      await room.switchActiveDevice("videoinput", next.deviceId);
      await refreshCameraDevices();
    } catch (err) {
      showError(err, "Camera switching is not supported on this device.");
    }
  }

  async function toggleScreen() {
    if (!room || typeof navigator.mediaDevices?.getDisplayMedia !== "function") return;
    try {
      await room.localParticipant.setScreenShareEnabled(!screen);
      setScreen(room.localParticipant.isScreenShareEnabled);
      recordEvent(room.localParticipant.isScreenShareEnabled ? "screen_share_start" : "screen_share_stop");
    } catch (err) {
      showError(err, "Screen sharing is not available in this browser.");
    }
  }

  async function toggleRaised() {
    if (!room) return;
    const next = !raised;
    try {
      await room.localParticipant.publishData(
        new TextEncoder().encode(JSON.stringify({ type: "hand", raised: next })),
        { reliable: true, topic: "group-video" },
      );
      setRaised(next);
      setRaisedIds((current) => {
        const updated = new Set(current);
        if (next) updated.add(room.localParticipant.identity);
        else updated.delete(room.localParticipant.identity);
        return updated;
      });
      recordEvent(next ? "raise_hand" : "lower_hand");
    } catch (err) {
      showError(err, "Unable to update raised hand");
    }
  }

  async function saveSchedule() {
    setBusy(true);
    setError(null);
    try {
      setStatus(await scheduleVideo(groupId, { scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null }));
    } catch (err) {
      showError(err, "Unable to schedule video room");
    } finally {
      setBusy(false);
    }
  }

  async function runControl(action: VideoControl | "mute_all", targetId?: string) {
    setError(null);
    try {
      await controlVideo(groupId, action, targetId);
      if (action === "kick" && targetId) {
        setRaisedIds((current) => {
          const updated = new Set(current);
          updated.delete(targetId);
          return updated;
        });
      } else if (targetId && action === "deny_mic") {
        setDeniedMic((current) => new Set(current).add(targetId));
      } else if (targetId && action === "allow_mic") {
        setDeniedMic((current) => {
          const updated = new Set(current);
          updated.delete(targetId);
          return updated;
        });
      } else if (targetId && action === "deny_screen") {
        setDeniedScreen((current) => new Set(current).add(targetId));
      } else if (targetId && action === "allow_screen") {
        setDeniedScreen((current) => {
          const updated = new Set(current);
          updated.delete(targetId);
          return updated;
        });
      }
    } catch (err) {
      showError(err, "Video room control failed");
    }
  }

  async function enterFullscreen() {
    const root = rootRef.current;
    if (!root?.requestFullscreen) {
      setError("Fullscreen is not supported by this browser.");
      return;
    }
    try {
      await root.requestFullscreen();
    } catch (err) {
      showError(err, "Unable to enter fullscreen");
    }
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
            <input type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)}
              className="rounded-lg border border-surface-border bg-surface-card px-3 py-2 text-sm text-text-primary" aria-label="Videochat schedule" />
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
          <button type="button" className={primaryBtn} onClick={connect} disabled={busy || connection === "connecting"}>
            {busy ? "Connecting…" : "Join videochat"}
          </button>
        )}
      </div>
    );
  }

  return (
    <div ref={rootRef} className="space-y-3 bg-surface-page p-1" data-testid="group-video-room">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className={cn("rounded-full px-3 py-1 text-xs font-bold", connection === "connected" ? "bg-emerald-100 text-emerald-700" : connection === "reconnecting" ? "bg-amber-100 text-amber-700" : "bg-surface-hover text-text-muted")}>
          {connection === "connected" ? "Connected" : connection === "reconnecting" ? "Reconnecting…" : connection === "connecting" ? "Connecting…" : "Disconnected"}
          {connectionQuality && connection === "connected" ? ` · ${connectionQuality}` : ""}
        </span>
        <span className="text-xs text-text-secondary"><Users size={14} className="mr-1 inline" />{participants.length}</span>
      </div>

      {connection === "reconnecting" && <p role="status" className="text-sm text-amber-700">Connection interrupted. Trying to reconnect…</p>}
      {error && <p role="alert" className="rounded-lg bg-danger/10 p-2 text-sm text-danger">{error}</p>}
      <div className={cn("grid gap-3", chatOpen && "lg:grid-cols-[minmax(0,1fr)_320px]")}>
        <div className="grid content-start gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {participants.map((participant) => (
            <ParticipantTile
              key={participant.identity}
              participant={participant}
              raised={raisedIds.has(participant.identity)}
              onControl={manager ? (action, id) => void runControl(action, id) : undefined}
            />
          ))}
        </div>
        {chatOpen && <GroupChat groupId={groupId} />}
      </div>

      {participantsOpen && (
        <div className={cn(card, "space-y-2 p-3")} aria-label="Participants">
          {[...participants].sort((a, b) => Number(raisedIds.has(b.identity)) - Number(raisedIds.has(a.identity))).map((participant) => (
            <div key={participant.identity} className="flex flex-wrap items-center justify-between gap-2 border-b border-surface-border py-2 last:border-0">
              <span className="text-sm font-semibold text-text-primary">
                {participant.name || participant.identity}{participant.isLocal ? " (you)" : ""}
                {raisedIds.has(participant.identity) ? " · ✋" : ""}
              </span>
              {manager && !participant.isLocal && (
                <div className="flex flex-wrap gap-1">
                  <button type="button" className={secondaryBtn} onClick={() => void runControl("mute", participant.identity)}>Mute</button>
                  <button type="button" className={secondaryBtn} onClick={() => void runControl(deniedMic.has(participant.identity) ? "allow_mic" : "deny_mic", participant.identity)}>
                    {deniedMic.has(participant.identity) ? "Allow mic" : "Disable mic"}
                  </button>
                  <button type="button" className={secondaryBtn} onClick={() => void runControl(deniedScreen.has(participant.identity) ? "allow_screen" : "deny_screen", participant.identity)}>
                    {deniedScreen.has(participant.identity) ? "Allow sharing" : "Disable sharing"}
                  </button>
                  <button type="button" className={secondaryBtn} onClick={() => void runControl("kick", participant.identity)}>Remove</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="sticky bottom-3 z-10 flex flex-wrap items-center justify-center gap-2 rounded-2xl border border-surface-border bg-surface-card/95 p-2 shadow-lg backdrop-blur">
        <button type="button" className={secondaryBtn} onClick={() => void toggleMic()} aria-label={mic ? "Mute microphone" : "Unmute microphone"}>
          {mic ? <Mic size={18} /> : <MicOff size={18} />}
        </button>
        <button type="button" className={secondaryBtn} onClick={() => void toggleCamera()} aria-label={camera ? "Turn camera off" : "Turn camera on"}>
          {camera ? <Video size={18} /> : <VideoOff size={18} />}
        </button>
        <button type="button" className={secondaryBtn} onClick={() => void switchCamera()} disabled={cameraDevices.length < 2} aria-label="Switch camera">
          <RefreshCw size={18} />
        </button>
        <button type="button" className={secondaryBtn} onClick={() => void toggleScreen()}
          disabled={typeof navigator.mediaDevices?.getDisplayMedia !== "function"} aria-label="Share screen"><MonitorUp size={18} /></button>
        <button type="button" className={cn(secondaryBtn, raised && "border-accent-blue text-accent-blue")} onClick={() => void toggleRaised()} aria-label="Raise hand"><Hand size={18} /></button>
        <button type="button" className={cn(secondaryBtn, participantsOpen && "border-accent-blue text-accent-blue")}
          onClick={() => setParticipantsOpen((open) => !open)} aria-label="Participants"><Users size={18} /> <span className="text-xs">{participants.length}</span></button>
        <button type="button" className={cn(secondaryBtn, chatOpen && "border-accent-blue text-accent-blue")}
          onClick={() => setChatOpen((open) => !open)} aria-label="Group chat"><MessageSquare size={18} /></button>
        {manager && <button type="button" className={secondaryBtn} onClick={() => void runControl("mute_all")} aria-label="Mute all students"><MicOff size={18} /></button>}
        <button type="button" className={secondaryBtn} onClick={() => void enterFullscreen()} aria-label="Fullscreen"><Maximize2 size={18} /></button>
        {manager ? (
          <button type="button" disabled={busy} className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm font-bold text-white" onClick={() => void finish()}>
            <PhoneOff size={18} /> End meeting
          </button>
        ) : (
          <button type="button" disabled={busy} className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-sm font-bold text-white" onClick={() => void leave()}>
            <PhoneOff size={18} /> Leave room
          </button>
        )}
      </div>

      {activeSpeakers.length > 0 && (
        <p className="text-xs text-text-muted">Speaking: {activeSpeakers.map((participant) => participant.name || participant.identity).join(", ")}</p>
      )}
    </div>
  );
}
