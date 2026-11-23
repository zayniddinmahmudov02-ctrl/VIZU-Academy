"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { usePlayerStore } from "@/features/medien/store/player-store";

import { HEARTBEAT_MS, heartbeatContexts, isActive, newTabId, pageContext, type MediaNow } from "../lib/activity-context";
import { sendFinalHeartbeat, sendHeartbeat, type HeartbeatBody } from "../services/activity-service";
import { useActivityStore } from "../store/activity-store";

const INPUT_EVENTS = ["pointerdown", "keydown", "wheel", "touchstart", "scroll", "mousemove"] as const;

/** Student panel only (mounted in the dashboard layout): every 30 s, while the student is active or a song / film plays, one
 * heartbeat says what is open. Nothing is sent from an idle or hidden tab without media; closing the page sends a last one.
 * The server decides how much time that is (its own clock) — see backend app/services/activity/tracker.py. */
export default function ActivityTracker() {
  const { user } = useCurrentUser();
  const pathname = usePathname() ?? "";
  const pathRef = useRef(pathname);
  const lastInput = useRef(Date.now());
  const tabId = useRef<string>("");

  useEffect(() => {
    pathRef.current = pathname;
    lastInput.current = Date.now();
  }, [pathname]);

  const enabled = user?.role === "STUDENT";

  useEffect(() => {
    if (!enabled) return;
    if (!tabId.current) tabId.current = newTabId();
    let lastMove = 0;
    const onInput = (event: Event) => {
      const now = Date.now();
      if (event.type === "mousemove" && now - lastMove < 2000) return;
      lastMove = now;
      lastInput.current = now;
    };
    INPUT_EVENTS.forEach((name) => window.addEventListener(name, onInput, { passive: true, capture: true }));

    const build = (): HeartbeatBody | null => {
      const visible = document.visibilityState === "visible";
      const active = isActive(lastInput.current, Date.now(), visible);
      const media: MediaNow[] = [];
      const player = usePlayerStore.getState();
      const song = player.queue[player.index];
      if (song) media.push({ area: "MUSIC", refId: String(song.id), position: player.currentTime, playing: player.playing });
      const registered = useActivityStore.getState().media;
      if (registered) {
        media.push({
          area: registered.area,
          refId: registered.refId,
          position: registered.getPosition?.() ?? null,
          playing: registered.isPlaying?.() ?? false,
        });
      }
      const contexts = heartbeatContexts(pageContext(pathRef.current), media, active);
      return contexts === null ? null : { tab_id: tabId.current, active, contexts };
    };

    const beat = () => {
      const body = build();
      if (body) void sendHeartbeat(body).catch(() => undefined);
    };
    const first = window.setTimeout(beat, 1500);
    const timer = window.setInterval(beat, HEARTBEAT_MS);
    const onHide = () => {
      const body = build();
      if (body) sendFinalHeartbeat(body);
    };
    window.addEventListener("pagehide", onHide);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(timer);
      window.removeEventListener("pagehide", onHide);
      INPUT_EVENTS.forEach((name) => window.removeEventListener(name, onInput, { capture: true }));
    };
  }, [enabled]);

  return null;
}
