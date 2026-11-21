"use client";

import { isTrackReference, useIsMuted, useIsSpeaking, useParticipantAttributes, VideoTrack } from "@livekit/components-react";
import type { TrackReferenceOrPlaceholder } from "@livekit/components-react";
import { Track } from "livekit-client";
import { Hand, MicOff, MonitorUp, Pin, PinOff } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { ATTR_HAND, initials, roleOf } from "../video-room-utils";
import { QualityBars } from "./connection-status";

export function trackKey(ref: TrackReferenceOrPlaceholder): string {
  return `${ref.participant.identity}:${ref.source}`;
}

/** One participant's camera or screen share: video (or initials), name, role, mic state, raised hand,
 *  speaking ring and connection quality. */
export default function VideoTile({ trackRef, pinned, onPin, compact, className }: {
  trackRef: TrackReferenceOrPlaceholder;
  pinned?: boolean;
  onPin?: (key: string | null) => void;
  compact?: boolean;
  className?: string;
}) {
  const { t } = useTranslation();
  const p = trackRef.participant;
  const isScreen = trackRef.source === Track.Source.ScreenShare;
  const speaking = useIsSpeaking(p);
  const { attributes } = useParticipantAttributes({ participant: p });
  const micMuted = useIsMuted({ participant: p, source: Track.Source.Microphone });
  const hand = attributes?.[ATTR_HAND];
  const host = roleOf(p.metadata, attributes) === "host";
  const name = p.name || p.identity;
  const hasVideo = isTrackReference(trackRef) && !trackRef.publication.isMuted;
  const key = trackKey(trackRef);

  return (
    <div data-testid="video-tile" data-identity={p.identity} data-source={trackRef.source} data-speaking={speaking ? "1" : "0"}
         className={cn("group relative overflow-hidden rounded-xl bg-neutral-800", isScreen ? "bg-black" : "",
           speaking && !isScreen ? "ring-2 ring-emerald-400" : "ring-1 ring-white/10", className)}>
      {hasVideo && isTrackReference(trackRef) ? (
        <VideoTrack trackRef={trackRef} data-testid={isScreen ? "video-screen" : "video-camera"}
                    className={cn("h-full w-full", isScreen ? "object-contain" : "object-cover", p.isLocal && !isScreen && "-scale-x-100")} />
      ) : (
        <div className="flex h-full w-full items-center justify-center">
          <span className={cn("flex items-center justify-center rounded-full bg-gradient-to-br from-sky-500 to-indigo-600 font-bold text-white",
            compact ? "h-10 w-10 text-sm" : "h-16 w-16 text-xl sm:h-20 sm:w-20 sm:text-2xl")}>{initials(name)}</span>
        </div>
      )}

      {hand && !isScreen && (
        <span data-testid="tile-hand" className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full bg-amber-400 px-2 py-0.5 text-xs font-bold text-black">
          <Hand size={12} /> {!compact && t("videoRoom.raiseHand")}
        </span>
      )}
      <div className="absolute right-2 top-2 flex items-center gap-1.5">
        <span className="rounded-md bg-black/50 px-1.5 py-1"><QualityBars participant={p} /></span>
        {onPin && !compact && (
          <button type="button" aria-label={pinned ? "Unpin" : "Pin"} onClick={() => onPin(pinned ? null : key)}
                  className="rounded-md bg-black/50 p-1 text-white opacity-0 transition-opacity focus:opacity-100 group-hover:opacity-100">
            {pinned ? <PinOff size={14} /> : <Pin size={14} />}
          </button>
        )}
      </div>
      <div className="absolute inset-x-2 bottom-2 flex items-center gap-1.5">
        <span className="flex min-w-0 items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-xs font-medium text-white">
          {isScreen ? <MonitorUp size={12} className="shrink-0" /> : micMuted && <MicOff size={12} className="shrink-0 text-red-400" aria-label="mic off" />}
          <span className="truncate">{isScreen ? t("videoRoom.screenOf", { name }) : name}{p.isLocal && !isScreen ? ` (${t("videoRoom.you")})` : ""}</span>
          {host && !isScreen && <span className="shrink-0 rounded bg-sky-500 px-1 text-[10px] font-bold uppercase">{t("videoRoom.host")}</span>}
        </span>
      </div>
    </div>
  );
}
