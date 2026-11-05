import AuthGuard from "@/components/auth/auth-guard";
import BattleShell from "@/features/battle/components/battle-shell";

import "@/features/battle/battle.css";

export const metadata = {
  title: "VIZU DEUTSCH BATTLE",
  icons: { icon: [{ url: "/battle/battle-icon.svg", type: "image/svg+xml" }] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <BattleShell>{children}</BattleShell>
    </AuthGuard>
  );
}
