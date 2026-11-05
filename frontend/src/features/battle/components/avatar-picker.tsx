"use client";

import { useEffect, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Lock, X } from "lucide-react";

import BattleAvatar from "@/features/battle/components/battle-avatar";
import { BATTLE_HOME_KEY } from "@/features/battle/hooks/use-battle-home";
import { setAvatar, type AvatarOption, type BattleHome } from "@/features/battle/services/battle-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export default function AvatarPicker({ avatars, accent, onClose }: { avatars: AvatarOption[]; accent: string; onClose: () => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const dialog = useRef<HTMLDivElement>(null);
  const save = useMutation({
    mutationFn: setAvatar,
    onSuccess: (res) => {
      qc.setQueryData<BattleHome>(BATTLE_HOME_KEY, (old) => (old ? { ...old, avatars: res.avatars, player: { ...old.player, avatar: res.avatar } } : old));
      onClose();
    },
  });

  useEffect(() => {
    dialog.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#050a14]/75 p-3 backdrop-blur-sm" onClick={onClose}>
      <div ref={dialog} tabIndex={-1} role="dialog" aria-modal="true" aria-label={t("battle.changeAvatar")} onClick={(e) => e.stopPropagation()}
           className="bt-glass-strong max-h-[90dvh] w-full max-w-3xl overflow-y-auto rounded-3xl p-5 outline-none sm:p-7" data-testid="avatar-picker">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="bt-display text-xl">{t("battle.changeAvatar")}</h2>
          <button type="button" onClick={onClose} aria-label={t("battle.close")} className="grid h-9 w-9 place-items-center rounded-xl hover:bg-white/10"><X size={18} /></button>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {avatars.map((a) => (
            <button key={a.key} type="button" disabled={!a.unlocked || save.isPending} onClick={() => save.mutate(a.key)} data-testid={`avatar-${a.key}`}
                    className={cn("group relative flex flex-col items-center rounded-2xl p-3 text-center ring-1 transition",
                      a.selected ? "bg-[var(--bt-blue)]/20 ring-[var(--bt-blue)]" : "bg-white/5 ring-white/10 hover:bg-white/10",
                      !a.unlocked && "cursor-not-allowed opacity-60")}>
              <BattleAvatar avatar={a.key} size={104} accent={accent} animated={false} />
              <span className="mt-1 text-sm font-extrabold">{a.title}</span>
              <span className="mt-0.5 text-[11px] text-white/60">{a.unlocked ? t("battle.unlocked") : t("battle.avatarLocked", { rank: a.unlock_rank })}</span>
              {a.selected && <Check className="absolute right-2 top-2 text-[var(--bt-gold)]" size={18} aria-hidden="true" />}
              {!a.unlocked && <Lock className="absolute right-2 top-2 text-white/60" size={16} aria-hidden="true" />}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
