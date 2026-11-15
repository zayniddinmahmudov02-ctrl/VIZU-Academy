"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

import { useActiveCues } from "../hooks/use-film-subtitles";
import { subtitleStyle, tokenize, type Cue, type SubtitlePrefs } from "../lib/subtitles";

/** Fired when the student clicks a word (or selects a phrase) of a German subtitle — the word popup listens to it, and so can anything
 * else (`detail`: word, language, time = film second, filmId). */
export const SUBTITLE_WORD_EVENT = "medien:subtitle-word";

export interface WordPick { word: string; language: string; time: number; sentence: string; phrase?: boolean }

interface Line { language: string; cues: readonly Cue[] | undefined }

interface Props {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  lines: Line[];
  prefs: SubtitlePrefs;
  /** height (px) of the control bar while it is shown, 0 while it is hidden */
  barHeight: number;
  activeWord: string | null;
  onPick: (pick: WordPick) => void;
}

/** The subtitles drawn over the video: one line, or two (German on top, the translation below). Only German words are clickable; every
 * line can be selected for copying. The look (size, colour, background, position, font) comes from the student's settings. */
export default function SubtitleOverlay({ videoRef, lines, prefs, barHeight, activeWord, onPick }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const style = subtitleStyle(prefs, barHeight);
  const pickRef = useRef(onPick);
  useEffect(() => { pickRef.current = onPick; });

  // a selected phrase (mouse drag or touch selection handles) inside the subtitles opens the popup for the whole phrase
  useEffect(() => {
    let timer: number | undefined;
    const onSelection = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const sel = window.getSelection();
        const text = sel?.toString().replace(/\s+/g, " ").trim() ?? "";
        if (!sel || sel.isCollapsed || !box.current || !sel.anchorNode || !box.current.contains(sel.anchorNode) || text.length < 3 || text.length > 60 || !/\s/.test(text)) return;
        const line = (sel.anchorNode.parentElement?.closest("[data-line-language]") as HTMLElement | null);
        const language = line?.dataset.lineLanguage ?? "de";
        pickRef.current({ word: text, language, time: videoRef.current?.currentTime ?? 0, sentence: line?.textContent?.trim() ?? text, phrase: true });
      }, 450);
    };
    document.addEventListener("selectionchange", onSelection);
    return () => { window.clearTimeout(timer); document.removeEventListener("selectionchange", onSelection); };
  }, [videoRef]);

  // at most two lines (dual): both are looked up on the video's clock; the box exists only while a cue is shown
  const first = useActiveCues(videoRef, lines[0]?.cues);
  const second = useActiveCues(videoRef, lines[1]?.cues);
  const shown = [{ language: lines[0]?.language, active: first }, { language: lines[1]?.language, active: second }].filter((l) => l.language && l.active.length);
  if (!shown.length) return null;
  return (
    <div ref={box} className="pointer-events-none absolute inset-x-0 flex select-text flex-col items-center gap-1 px-3 transition-[bottom] duration-200" style={style.block}
         data-testid="film-cue" data-language={shown[0].language} data-dual={lines.length > 1 ? "1" : "0"}>
      {shown.map((line) => (
        <CueLine key={line.language} videoRef={videoRef} language={line.language!} active={line.active} lineStyle={style.line} activeWord={activeWord} onPick={onPick} />
      ))}
    </div>
  );
}

function CueLine({ videoRef, language, active, lineStyle, activeWord, onPick }: {
  videoRef: React.RefObject<HTMLVideoElement | null>; language: string; active: readonly Cue[]; lineStyle: React.CSSProperties;
  activeWord: string | null; onPick: (pick: WordPick) => void;
}) {
  const clickable = language === "de";
  return (
    <>
      {active.map((cue) => (
        <p key={cue[0]} className="max-w-3xl rounded-lg px-3 py-1.5 text-center font-medium leading-snug [text-shadow:0_1px_2px_rgb(0_0_0/0.6)]" style={lineStyle}
           data-testid="film-cue-line" data-language={language} data-line-language={language} lang={language}>
          {cue[2].split("\n").map((line, li) => (
            <span key={li} className="block">
              {tokenize(line).map((t, wi) => (clickable && t.word
                ? (
                  <span key={wi} role="button" tabIndex={-1} data-word={t.word} data-active={activeWord === t.word ? "1" : undefined}
                        className={cn("pointer-events-auto cursor-pointer rounded px-px transition-colors hover:bg-white/25", activeWord === t.word && "bg-white/30 underline decoration-2 underline-offset-4")}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.getSelection()?.toString().trim()) return; // finishing a text selection is not a click on a word
                          onPick({ word: t.word!, language, time: videoRef.current?.currentTime ?? 0, sentence: cue[2].replace(/\s*\n\s*/g, " ") });
                        }}>{t.text}</span>
                )
                : <span key={wi} className="pointer-events-auto">{t.text}</span>))}
            </span>
          ))}
        </p>
      ))}
    </>
  );
}
