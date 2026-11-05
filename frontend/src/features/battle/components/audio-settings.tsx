"use client";

import { Popover } from "@base-ui/react/popover";
import { Music, Volume2, VolumeX, Waves } from "lucide-react";

import { playSfx, updateAudioSettings } from "@/features/battle/audio/battle-audio";
import { useAudioSettings } from "@/features/battle/audio/use-battle-audio";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

function Toggle({ on, onChange, label, testId }: { on: boolean; onChange: (v: boolean) => void; label: string; testId: string }) {
  return (
    <button type="button" role="switch" aria-checked={on} aria-label={label} onClick={() => onChange(!on)} data-testid={testId}
            className={cn("relative h-6 w-11 shrink-0 rounded-full transition-colors", on ? "bg-[#3984E8]" : "bg-white/20")}>
      <span className={cn("absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform", on ? "translate-x-[22px]" : "translate-x-0.5")} />
    </button>
  );
}

/** Battle audio settings (saved on this device): master mute, music / effects on-off and volume. */
export default function AudioSettingsButton({ className }: { className?: string }) {
  const { t } = useTranslation();
  const s = useAudioSettings();
  const silent = s.muted || (!s.music && !s.sfx);

  return (
    <Popover.Root>
      <Popover.Trigger aria-label={t("battle.audioSettings")} data-testid="battle-audio-button"
                       className={cn("grid h-9 w-9 place-items-center rounded-xl text-white/80 hover:bg-white/10 hover:text-white", className)}>
        {silent ? <VolumeX size={18} aria-hidden="true" /> : <Volume2 size={18} aria-hidden="true" />}
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Positioner align="end" sideOffset={8} className="z-[60] outline-none">
          <Popover.Popup data-testid="battle-audio-panel"
                         className="w-72 rounded-2xl bg-[#101d35]/95 p-4 text-white shadow-2xl outline-none ring-1 ring-white/15 backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-black">{t("battle.audioSettings")}</p>
              <button type="button" onClick={() => updateAudioSettings({ muted: !s.muted })} data-testid="battle-audio-mute"
                      className={cn("inline-flex min-h-9 items-center gap-1.5 rounded-xl px-3 text-xs font-bold ring-1",
                        s.muted ? "bg-[#D83B43] ring-[#D83B43]" : "bg-white/10 ring-white/20 hover:bg-white/20")}>
                {s.muted ? <VolumeX size={14} aria-hidden="true" /> : <Volume2 size={14} aria-hidden="true" />}
                {s.muted ? t("battle.audioUnmute") : t("battle.audioMute")}
              </button>
            </div>

            <div className={cn("mt-4 space-y-4", s.muted && "opacity-50")}>
              <div>
                <div className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-sm font-semibold"><Music size={15} aria-hidden="true" />{t("battle.audioMusic")}</span>
                  <Toggle on={s.music} onChange={(music) => updateAudioSettings({ music })} label={t("battle.audioMusic")} testId="battle-audio-music" />
                </div>
                <input type="range" min={0} max={100} value={Math.round(s.musicVolume * 100)} aria-label={t("battle.audioMusicVolume")}
                       disabled={!s.music} onChange={(e) => updateAudioSettings({ musicVolume: Number(e.target.value) / 100 })}
                       className="mt-2 w-full accent-[#F2C45B]" data-testid="battle-audio-music-volume" />
              </div>
              <div>
                <div className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-2 text-sm font-semibold"><Waves size={15} aria-hidden="true" />{t("battle.audioSfx")}</span>
                  <Toggle on={s.sfx} onChange={(sfx) => updateAudioSettings({ sfx })} label={t("battle.audioSfx")} testId="battle-audio-sfx" />
                </div>
                <input type="range" min={0} max={100} value={Math.round(s.sfxVolume * 100)} aria-label={t("battle.audioSfxVolume")}
                       disabled={!s.sfx} onChange={(e) => updateAudioSettings({ sfxVolume: Number(e.target.value) / 100 })}
                       onPointerUp={() => playSfx("select")} className="mt-2 w-full accent-[#F2C45B]" data-testid="battle-audio-sfx-volume" />
              </div>
            </div>
            <p className="mt-3 text-[11px] text-white/50">{t("battle.audioSaved")}</p>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}
