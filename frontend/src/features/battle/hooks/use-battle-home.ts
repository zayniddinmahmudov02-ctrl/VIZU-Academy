"use client";

import { useQuery } from "@tanstack/react-query";

import { getBattleHome } from "@/features/battle/services/battle-service";

export const BATTLE_HOME_KEY = ["battle-home"] as const;

export function useBattleHome() {
  return useQuery({ queryKey: BATTLE_HOME_KEY, queryFn: getBattleHome, staleTime: 15_000, retry: 1 });
}
