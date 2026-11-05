"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";

import {
  getAudioSettings, getServerAudioSettings, playSfx, setTrack, subscribeAudioSettings, type AudioSettings,
} from "@/features/battle/audio/battle-audio";
import type { MatchState } from "@/features/battle/services/battle-service";

export function useAudioSettings(): AudioSettings {
  return useSyncExternalStore(subscribeAudioSettings, getAudioSettings, getServerAudioSettings);
}

/** Maps server match state to music + one-shot effects. Every effect fires once per event: keys (round, second,
 * outcome) are remembered in refs, so polling the same state again never repeats a sound. Time comes from the
 * server deadline (msLeft / countdownMs are derived from it) — audio never changes match time. */
export function useMatchAudio(m: MatchState | undefined, msLeft: number, countdownMs: number | null) {
  const seen = useRef(new Set<string>());
  const once = (key: string, fn: () => void) => {
    if (seen.current.has(key)) return;
    seen.current.add(key);
    fn();
  };
  const status = m?.status;
  const round = m?.round ?? null;

  // music per phase
  useEffect(() => {
    if (!status) return;
    if (status === "waiting") setTrack("search");
    else if (status === "active") setTrack(round && round.no >= round.total - 1 ? "final" : "arena");
    else setTrack("off");
  }, [status, round?.no, round?.total]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!m) return;
    // opponent found → VS countdown 3, 2, 1
    if (m.status === "active" && !m.round) {
      once(`found-${m.id}`, () => playSfx("matchFound"));
      if (countdownMs !== null && countdownMs > 0) {
        const s = Math.ceil(countdownMs / 1000);
        if (s <= 3) once(`count-${m.id}-${s}`, () => playSfx("count"));
      }
    }
    if (m.status === "active" && round) {
      const r = round.no;
      once(`go-${m.id}`, () => playSfx("go"));
      if (r > 1) once(`next-${m.id}-${r}`, () => playSfx("transition"));
      if (round.phase === "question") {
        const s = Math.ceil(msLeft / 1000);
        const answered = !!round.my_answer;
        if (!answered && s > 0) once(`tick-${m.id}-${r}-${s}`, () => playSfx(s <= 5 ? "tickUrgent" : "tick"));
        if (!answered && msLeft <= 0) once(`timeup-${m.id}-${r}`, () => playSfx("timeUp"));
      }
      if (round.my_answer && round.my_answer.choice !== null) {
        once(`answer-${m.id}-${r}`, () => playSfx(round.my_answer!.correct ? "correct" : "wrong"));
      }
      if (round.opponent_answered) once(`opp-${m.id}-${r}`, () => playSfx("opponent"));
      if (round.phase === "reveal") {
        const h = m.history[r - 1];
        once(`round-${m.id}-${r}`, () => playSfx(h?.me && !h?.opponent ? "roundWin" : !h?.me && h?.opponent ? "roundLose" : "transition"));
      }
    }
    if (m.status === "finished" && m.result) {
      const res = m.result;
      once(`end-${m.id}`, () => playSfx(res.outcome === "win" ? "victory" : res.outcome === "loss" ? "defeat" : "draw"));
      if (res.rank_up) once(`rank-${m.id}`, () => setTimeout(() => playSfx("rankUp"), 1600));
      if (res.stage_up) once(`stage-${m.id}`, () => setTimeout(() => playSfx("unlock"), 3200));
    }
  });
}
