"use client";

import { useParams } from "next/navigation";

import MatchView from "@/features/battle/components/match-view";

export default function BattleMatchPage() {
  const { matchId } = useParams<{ matchId: string }>();
  return <MatchView key={matchId} matchId={matchId} />;
}
