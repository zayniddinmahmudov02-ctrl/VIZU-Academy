"use client";

import { Check } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

import { COLORS, FONTS, LANGUAGE_NAMES, SIZES, subtitleStyle, type SubtitlePrefs } from "../lib/subtitles";
import type { WatchSubtitle } from "../types";

interface Props {
  subtitles: readonly WatchSubtitle[];
  subtitle: string;
  dual: boolean;
  secondary: string | null;
  prefs: SubtitlePrefs;
  pauseOnWord: boolean;
  onSubtitle: (language: string) => void;
  onDual: (on: boolean) => void;
  onSecondary: (language: string) => void;
  onPrefs: (patch: Partial<SubtitlePrefs>) => void;
  onPauseOnWord: (on: boolean) => void;
}

const row = "flex min-h-[44px] w-full items-center justify-between gap-2 rounded-lg px-3 py-1.5 text-left text-sm hover:bg-white/15 sm:min-h-10";

/** The subtitle panel of the player: language (only the tracks the film has) or off, dual subtitles, and the student's look settings with a
 * live preview. Choosing a language closes the panel; the look settings stay open so the effect can be seen. */
export default function SubtitleMenu({ subtitles, subtitle, dual, secondary, prefs, pauseOnWord, onSubtitle, onDual, onSecondary, onPrefs, onPauseOnWord }: Props) {
  const { t } = useTranslation();
  const canDual = subtitles.length >= 2;
  const style = subtitleStyle(prefs, 0);
  const others = subtitles.filter((s) => s.language !== subtitle);
  const chip = (active: boolean) => cn("flex min-h-[44px] min-w-[3rem] flex-1 items-center justify-center rounded-lg px-2 text-xs font-semibold ring-1 ring-white/15 hover:bg-white/15 sm:min-h-9", active && "bg-accent-blue text-white ring-accent-blue");

  return (
    <div>
      <ul>
        <li><button type="button" className={cn(row, subtitle === "off" && "font-bold text-accent-blue")} onClick={() => onSubtitle("off")} data-testid="film-subtitle-off">{t("medien.subtitlesOff")}{subtitle === "off" && <Check size={15} />}</button></li>
        {subtitles.map((s) => (
          <li key={s.id}><button type="button" className={cn(row, subtitle === s.language && "font-bold text-accent-blue")} onClick={() => onSubtitle(s.language)} data-testid="film-subtitle-option" data-language={s.language}>
            {s.label}{subtitle === s.language && <Check size={15} />}</button></li>
        ))}
        {!subtitles.length && <li className="px-3 py-2 text-xs text-white/60" data-testid="film-no-subtitles">{t("medien.noSubtitles")}</li>}
      </ul>

      {!!subtitles.length && (
        <div className="mt-2 space-y-3 border-t border-white/10 px-1 pt-3">
          <label className="flex items-start justify-between gap-3">
            <span><span className="block font-semibold">{t("medien.fp.dual")}</span><span className="block text-xs text-white/60">{canDual ? t("medien.fp.dualHint") : t("medien.fp.dualNeed")}</span></span>
            <input type="checkbox" role="switch" checked={dual && canDual} disabled={!canDual} onChange={(e) => onDual(e.target.checked)} data-testid="sub-dual" className="mt-1 h-5 w-9 shrink-0 cursor-pointer accent-[var(--color-accent-blue,#2563eb)] disabled:cursor-not-allowed disabled:opacity-40" />
          </label>
          {dual && canDual && subtitle !== "off" && (
            <label className="block">
              <span className="mb-1 block text-xs text-white/70">{t("medien.fp.second")}</span>
              <select value={secondary ?? ""} onChange={(e) => onSecondary(e.target.value)} data-testid="sub-secondary" className="h-9 w-full rounded-lg bg-white/10 px-2 text-sm text-white outline-none ring-1 ring-white/15">
                {others.map((s) => <option key={s.language} value={s.language} className="text-black">{LANGUAGE_NAMES[s.language] ?? s.label}</option>)}
              </select>
            </label>
          )}
        </div>
      )}

      <div className="mt-3 space-y-3 border-t border-white/10 px-1 pt-3" data-testid="sub-appearance">
        <p className="text-xs font-semibold uppercase tracking-wide text-white/60">{t("medien.fp.appearance")}</p>
        <div><p className="mb-1 text-xs text-white/70">{t("medien.fp.size")}</p>
          <div className="flex gap-1.5">{SIZES.map((s) => <button key={s} type="button" aria-pressed={prefs.size === s} className={chip(prefs.size === s)} onClick={() => onPrefs({ size: s })} data-testid={`sub-size-${s}`}>{t(`medien.fp.size.${s}`)}</button>)}</div></div>
        <div><p className="mb-1 text-xs text-white/70">{t("medien.fp.color")}</p>
          <div className="flex gap-2">{COLORS.map((c) => (
            <button key={c} type="button" aria-label={c} aria-pressed={prefs.color === c} onClick={() => onPrefs({ color: c })} data-testid={`sub-color-${c.slice(1)}`} style={{ backgroundColor: c }}
                    className={cn("h-[40px] w-[40px] rounded-full ring-2 ring-white/20 sm:h-8 sm:w-8", prefs.color === c && "ring-accent-blue ring-offset-2 ring-offset-black")} />))}</div></div>
        <label className="block"><span className="mb-1 flex justify-between text-xs text-white/70"><span>{t("medien.fp.background")}</span><span className="tabular-nums" data-testid="sub-opacity-value">{prefs.bg_opacity}%</span></span>
          <input type="range" min={0} max={100} step={5} value={prefs.bg_opacity} onChange={(e) => onPrefs({ bg_opacity: Number(e.target.value) })} data-testid="sub-opacity" className="h-2 w-full cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" /></label>
        <div><p className="mb-1 text-xs text-white/70">{t("medien.fp.position")}</p>
          <div className="flex gap-1.5">{(["bottom", "higher"] as const).map((p) => <button key={p} type="button" aria-pressed={prefs.position === p} className={chip(prefs.position === p)} onClick={() => onPrefs({ position: p })} data-testid={`sub-position-${p}`}>{t(`medien.fp.pos.${p}`)}</button>)}</div></div>
        <div><p className="mb-1 text-xs text-white/70">{t("medien.fp.font")}</p>
          <div className="flex gap-1.5">{FONTS.map((f) => <button key={f} type="button" aria-pressed={prefs.font === f} className={chip(prefs.font === f)} onClick={() => onPrefs({ font: f })} data-testid={`sub-font-${f}`}>{t(`medien.fp.font.${f}`)}</button>)}</div></div>
        <div className="flex h-16 items-end justify-center overflow-hidden rounded-lg bg-gradient-to-b from-slate-700 to-slate-900 p-2" aria-hidden="true">
          <p className="rounded-md px-2 py-1 text-center [font-size:inherit]" style={{ ...style.line, fontFamily: style.block.fontFamily, color: style.block.color, fontSize: "14px" }} data-testid="sub-preview">{t("medien.fp.sample")}</p>
        </div>
        <label className="flex items-center justify-between gap-3 text-xs text-white/80">
          <span>{t("medien.fp.pauseOnWord")}</span>
          <input type="checkbox" role="switch" checked={pauseOnWord} onChange={(e) => onPauseOnWord(e.target.checked)} data-testid="sub-pause-on-word" className="h-5 w-9 shrink-0 cursor-pointer accent-[var(--color-accent-blue,#2563eb)]" />
        </label>
      </div>
    </div>
  );
}
