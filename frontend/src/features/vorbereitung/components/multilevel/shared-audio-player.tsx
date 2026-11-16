"use client";

import { useCallback, useEffect, useRef } from "react";
import { Headphones } from "lucide-react";

import { API_URL } from "@/constants/api";
import { useTranslation } from "@/lib/i18n/use-translation";

const SAVE_EVERY_MS = 2000;

function clock(ms: number): string {
  const s = Math.round(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

interface Props {
  /** signed stream URL of the section's ONE audio (from the exam paper) */
  url: string;
  durationMs: number | null;
  /** where the playing position is kept while the page is open (a reload continues there, it does not start over) */
  storageKey: string;
}

/** The single audio of a shared-audio Hören section (Modelltest 1): one player for ALL Teile, docked on screen by the exam section, so scrolling from
 * Teil to Teil never touches it — no remount, no restart. The position is remembered for this browser tab, so a reload continues near where the audio was.
 * It never starts by itself; the audio length has nothing to do with the exam time (that is the section timer at the top). */
export default function SharedAudioPlayer({ url, durationMs, storageKey }: Props) {
  const { t } = useTranslation();
  const ref = useRef<HTMLAudioElement>(null);
  const lastSaved = useRef(0);
  const src = /^https?:\/\//i.test(url) ? url : `${API_URL.replace(/\/$/, "")}${url}`;

  const save = useCallback(() => {
    const audio = ref.current;
    if (!audio) return;
    try {
      window.sessionStorage.setItem(storageKey, String(audio.ended ? 0 : audio.currentTime));
    } catch {
      /* storage may be blocked: the audio simply starts at the beginning after a reload */
    }
  }, [storageKey]);

  useEffect(() => {
    const onHide = () => save();
    document.addEventListener("visibilitychange", onHide);
    window.addEventListener("pagehide", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      window.removeEventListener("pagehide", onHide);
      save();
    };
  }, [save]);

  function restore() {
    const audio = ref.current;
    if (!audio) return;
    try {
      const saved = Number(window.sessionStorage.getItem(storageKey));
      if (Number.isFinite(saved) && saved > 1 && (!Number.isFinite(audio.duration) || saved < audio.duration - 1)) audio.currentTime = saved;
    } catch {
      /* nothing saved */
    }
  }

  return (
    <div className="w-full rounded-xl bg-surface-card/95 px-3 py-2 shadow-[var(--shadow-md)] ring-1 ring-surface-border backdrop-blur" data-testid="shared-audio-box">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-x-3 text-xs font-bold uppercase tracking-wide text-text-muted">
        <span className="flex items-center gap-1.5"><Headphones size={14} className="text-purple-500" /> {t("multilevelExam.sharedAudioTitle")}</span>
        {durationMs ? <span className="font-semibold normal-case" data-testid="shared-audio-length">{t("multilevelExam.sharedAudioLength", { time: clock(durationMs) })}</span> : null}
      </div>
      <audio ref={ref} key={src} controls preload="auto" controlsList="nodownload noplaybackrate" src={src} className="w-full" data-testid="shared-audio"
             onLoadedMetadata={restore} onPause={save} onEnded={save}
             onTimeUpdate={() => {
               const now = Date.now();
               if (now - lastSaved.current >= SAVE_EVERY_MS) {
                 lastSaved.current = now;
                 save();
               }
             }}>
        <track kind="captions" />
      </audio>
      <p className="mt-1 text-[11px] text-text-muted">{t("multilevelExam.sharedAudioNote")}</p>
    </div>
  );
}
