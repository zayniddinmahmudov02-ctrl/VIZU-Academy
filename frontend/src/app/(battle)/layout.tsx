import AuthGuard from "@/components/auth/auth-guard";
import BattleShell from "@/features/battle/components/battle-shell";

import "@/features/battle/battle.css";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <BattleShell>{children}</BattleShell>
    </AuthGuard>
  );
}
