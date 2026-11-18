"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { setFavorite } from "../services/medien-service";
import { currentSong, usePlayerStore } from "../store/player-store";

/** Heart of the current song (bar, large player): optimistic, rolled back when the server refuses. */
export function usePlayerFavorite(): () => Promise<void> {
  const queryClient = useQueryClient();
  return useCallback(async () => {
    const song = currentSong(usePlayerStore.getState());
    if (!song) return;
    const on = !song.favorite;
    usePlayerStore.getState().patchSong(song.id, { favorite: on });
    try {
      await setFavorite(song.id, on);
      void queryClient.invalidateQueries({ queryKey: ["medien-songs"] });
    } catch {
      usePlayerStore.getState().patchSong(song.id, { favorite: !on });
    }
  }, [queryClient]);
}
