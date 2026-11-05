"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clockOffset, pollInterval } from "@/features/battle/lib/battle-utils";
import { getMatch, leaveMatch, sendAnswer, type MatchState } from "@/features/battle/services/battle-service";

import { BATTLE_HOME_KEY } from "./use-battle-home";

/** Polls a match (the server is the clock and the judge) and keeps the server-time offset for countdowns. */
export function useMatch(id: string) {
  const qc = useQueryClient();
  const offset = useRef(0);
  const [hidden, setHidden] = useState(false);
  const key = ["battle-match", id];

  useEffect(() => {
    const on = () => setHidden(document.hidden);
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);

  const query = useQuery({
    queryKey: key,
    queryFn: async ({ signal }) => {
      const sent = Date.now();
      const state = await getMatch(id, signal);
      const now = Date.now();
      offset.current = clockOffset(state.server_time, now, now - sent);
      return state;
    },
    refetchInterval: (q) => pollInterval(q.state.data?.status, hidden),
    refetchIntervalInBackground: true,
    retry: 3,
    retryDelay: 800,
  });

  const status = query.data?.status;
  useEffect(() => {
    if (status === "finished" || status === "cancelled") qc.invalidateQueries({ queryKey: BATTLE_HOME_KEY });
  }, [status, qc]);

  const store = useCallback((s: MatchState) => qc.setQueryData(["battle-match", s.id], s), [qc]);

  const answer = useMutation({
    mutationFn: ({ round, choice }: { round: number; choice: number }) => {
      const sent = Date.now();
      return sendAnswer(id, round, choice).then((s) => {
        const now = Date.now();
        offset.current = clockOffset(s.server_time, now, now - sent);
        return s;
      });
    },
    onSuccess: store,
    onError: () => query.refetch(),
  });

  const leave = useMutation({ mutationFn: () => leaveMatch(id), onSuccess: store });

  return { ...query, offset, answer, leave };
}

/** Re-renders every `ms` while `active` and returns the current time. */
export function useNow(active: boolean, ms = 100): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const id = window.setInterval(() => setNow(Date.now()), ms);
    return () => window.clearInterval(id);
  }, [active, ms]);
  return now;
}
