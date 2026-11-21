"use client";

import { useEffect, useRef, useState } from "react";
import { isTrackReference, useSpeakingParticipants } from "@livekit/components-react";
import type { TrackReferenceOrPlaceholder } from "@livekit/components-react";
import { Track } from "livekit-client";

import { gridColumns } from "../video-room-utils";
import VideoTile, { trackKey } from "./video-tile";

export type Layout = "grid" | "speaker";

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(1024);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

/** Grid view (everyone the same size) or speaker view (a screen share, the pinned tile or the active speaker large,
 *  the others in a strip). Screen shares always come first. */
export default function VideoGrid({ tracks, layout, pinned, onPin }: {
  tracks: TrackReferenceOrPlaceholder[];
  layout: Layout;
  pinned: string | null;
  onPin: (key: string | null) => void;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const speaking = useSpeakingParticipants();
  const screens = tracks.filter((t) => t.source === Track.Source.ScreenShare && isTrackReference(t));
  const cameras = tracks.filter((t) => t.source === Track.Source.Camera);
  const ordered = [...screens, ...cameras];

  if (layout === "speaker" && ordered.length > 1) {
    const speakerCam = cameras.find((t) => !t.participant.isLocal && speaking.some((s) => s.identity === t.participant.identity));
    const main = ordered.find((t) => trackKey(t) === pinned) ?? screens[0] ?? speakerCam ?? cameras.find((t) => !t.participant.isLocal) ?? ordered[0];
    const rest = ordered.filter((t) => t !== main);
    return (
      <div ref={ref} data-testid="video-grid" data-layout="speaker" className="flex h-full min-h-0 flex-col gap-2 p-2 lg:flex-row">
        <div className="min-h-0 flex-1">
          <VideoTile trackRef={main} pinned={trackKey(main) === pinned} onPin={onPin} className="h-full w-full" />
        </div>
        <div className="flex shrink-0 gap-2 overflow-x-auto lg:w-56 lg:flex-col lg:overflow-y-auto lg:overflow-x-hidden">
          {rest.map((t) => (
            <VideoTile key={trackKey(t)} trackRef={t} compact onPin={onPin} pinned={trackKey(t) === pinned}
                       className="aspect-video w-36 shrink-0 sm:w-44 lg:w-full" />
          ))}
        </div>
      </div>
    );
  }

  const cols = gridColumns(ordered.length, width);
  return (
    <div ref={ref} data-testid="video-grid" data-layout="grid" className="h-full min-h-0 overflow-y-auto p-2">
      <div className="grid min-h-full content-center gap-2" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
        {ordered.map((t) => (
          <VideoTile key={trackKey(t)} trackRef={t} onPin={onPin} pinned={trackKey(t) === pinned}
                     className={ordered.length === 1 ? "mx-auto aspect-video max-h-full w-full max-w-5xl" : "aspect-video w-full"} />
        ))}
      </div>
    </div>
  );
}
