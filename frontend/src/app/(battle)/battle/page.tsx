"use client";

import { Suspense } from "react";

import BattleHome from "@/features/battle/components/battle-home";

export default function BattlePage() {
  return (
    <Suspense fallback={null}>
      <BattleHome />
    </Suspense>
  );
}
