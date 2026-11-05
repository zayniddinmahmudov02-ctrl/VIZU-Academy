"use client";

import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Camera, Check, Lock, Trash2, Upload, X } from "lucide-react";

import BattleAvatar from "@/features/battle/components/battle-avatar";
import PlayerAvatar from "@/features/battle/components/player-avatar";
import { BATTLE_HOME_KEY } from "@/features/battle/hooks/use-battle-home";
import { setAvatar, type AvatarOption, type BattleHome, type PlayerCard } from "@/features/battle/services/battle-service";
import PhotoCropper from "@/features/profile/components/photo-cropper";
import { useRemoveProfilePhoto, useUploadProfilePhoto } from "@/features/profile/hooks/use-profile-photo";
import type { Crop } from "@/features/profile/utils/photo-crop";
import { ALLOWED_PHOTO_TYPES, MAX_PHOTO_SIZE_BYTES } from "@/features/profile/validation/profile.schema";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

/** Profile photo (shared with Profile Settings, wins over the game avatar) + the unlockable game avatars. */
export default function AvatarPicker({ avatars, accent, player, onClose }: { avatars: AvatarOption[]; accent: string; player: PlayerCard; onClose: () => void }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const dialog = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<{ file: File; url: string } | null>(null);
  const [crop, setCrop] = useState<Crop | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const onCrop = useCallback((c: Crop) => setCrop(c), []);
  const upload = useUploadProfilePhoto();
  const remove = useRemoveProfilePhoto();
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

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview.url); }, [preview]);

  const onFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!ALLOWED_PHOTO_TYPES.includes(file.type)) return setPhotoError(t("profile.photoInvalidType"));
    if (file.size > MAX_PHOTO_SIZE_BYTES) return setPhotoError(t("profile.photoTooLarge"));
    setPhotoError(null);
    setPreview({ file, url: URL.createObjectURL(file) });
  };
  const onSave = () => preview && upload.mutate({ file: preview.file, crop }, {
    onSuccess: () => setPreview(null),
    onError: (err) => setPhotoError(t((err as { response?: { status?: number } })?.response?.status === 400 ? "profile.photoRejected" : "profile.saveError")),
  });

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#050a14]/75 p-3 backdrop-blur-sm" onClick={onClose}>
      <div ref={dialog} tabIndex={-1} role="dialog" aria-modal="true" aria-label={t("battle.changeAvatar")} onClick={(e) => e.stopPropagation()}
           className="bt-glass-strong max-h-[90dvh] w-full max-w-3xl overflow-y-auto rounded-3xl p-5 outline-none sm:p-7" data-testid="avatar-picker">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="bt-display text-xl">{t("battle.changeAvatar")}</h2>
          <button type="button" onClick={onClose} aria-label={t("battle.close")} className="grid h-9 w-9 place-items-center rounded-xl hover:bg-white/10"><X size={18} /></button>
        </div>

        <section className="mb-6 rounded-2xl bg-white/5 p-4 ring-1 ring-white/10" data-testid="battle-photo-section">
          <h3 className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-wider"><Camera size={16} className="text-[var(--bt-gold)]" />{t("battle.profilePhoto")}</h3>
          <p className="mt-1 text-xs text-white/65">{t("battle.profilePhotoHint")}</p>
          <input ref={input} type="file" accept={ALLOWED_PHOTO_TYPES.join(",")} className="hidden" onChange={onFile} data-testid="battle-photo-input" />
          <div className="mt-4 flex flex-col items-center gap-4 sm:flex-row sm:items-start">
            {preview ? <PhotoCropper src={preview.url} onChange={onCrop} /> : <PlayerAvatar player={player} size={120} accent={accent} animated={false} />}
            <div className="flex flex-col gap-2">
              {photoError && <p role="alert" className="text-sm font-semibold text-[#ff8a8f]" data-testid="battle-photo-error">{photoError}</p>}
              {preview ? (
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={onSave} disabled={upload.isPending} data-testid="battle-photo-save"
                          className="inline-flex h-10 items-center gap-2 rounded-xl bg-[var(--bt-blue)] px-4 text-sm font-black disabled:opacity-60">
                    <Upload size={15} />{upload.isPending ? t("profile.saving") : t("profile.save")}
                  </button>
                  <button type="button" onClick={() => setPreview(null)} className="h-10 rounded-xl px-4 text-sm font-bold hover:bg-white/10">{t("profile.cancel")}</button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => input.current?.click()} data-testid="battle-photo-pick"
                          className="inline-flex h-10 items-center gap-2 rounded-xl bg-white/10 px-4 text-sm font-bold ring-1 ring-white/20 hover:bg-white/15">
                    <Upload size={15} />{player.photo ? t("profile.replacePhoto") : t("profile.uploadPhoto")}
                  </button>
                  {player.photo && (
                    <button type="button" onClick={() => remove.mutate()} disabled={remove.isPending} data-testid="battle-photo-remove"
                            className="inline-flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-bold text-white/80 hover:bg-white/10 disabled:opacity-60">
                      <Trash2 size={15} />{t("profile.removePhoto")}
                    </button>
                  )}
                </div>
              )}
              <p className="text-[11px] text-white/55">{t("profile.photoHint")}</p>
            </div>
          </div>
        </section>

        <h3 className="mb-3 text-sm font-extrabold uppercase tracking-wider">{t("battle.gameAvatars")}</h3>
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
