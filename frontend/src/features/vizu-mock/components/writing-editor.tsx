"use client";

import { useRef } from "react";

import { cn } from "@/lib/utils";

const UMLAUT_KEYS = ["Ä", "Ö", "Ü", "ä", "ö", "ü", "ß"];

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

interface Props {
  value: string;
  onChange: (value: string) => void;
  minWords: number;
  maxWords: number;
  disabled?: boolean;
}

/** A deliberately minimal writing editor for VIZU-Mock's Schreiben
 * module: a plain <textarea> (native Enter/paragraph support, no rich
 * formatting), umlaut insert buttons, and a live word counter. This is
 * NOT the app's RichTextEditor — that one is a full WYSIWYG with bold/
 * italic/color, exactly what this module's spec explicitly forbids
 * ("Faqat oddiy yozuv... boshqa rang tanlay olmasin"), so a new, much
 * smaller component was written instead of reusing/stripping that one. */
export default function VizuMockWritingEditor({ value, onChange, minWords, maxWords, disabled }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const wordCount = countWords(value);
  const belowMin = wordCount < minWords;
  const aboveMax = wordCount > maxWords;

  function insertChar(char: string) {
    const el = textareaRef.current;
    if (!el) return;
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    const next = value.slice(0, start) + char + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start + char.length, start + char.length);
    });
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-1.5">
        {UMLAUT_KEYS.map((char) => (
          <button
            key={char}
            type="button"
            onClick={() => insertChar(char)}
            disabled={disabled}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-hover text-sm font-bold text-black ring-1 ring-surface-border transition-colors hover:bg-surface-border disabled:cursor-not-allowed disabled:opacity-50"
          >
            {char}
          </button>
        ))}
      </div>

      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={10}
        style={{ color: "#000000" }}
        className="w-full resize-y rounded-2xl bg-white p-4 text-sm leading-relaxed text-black ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue disabled:cursor-not-allowed disabled:opacity-70"
        placeholder="Schreiben Sie hier Ihren Text..."
      />

      <p className={cn("mt-1.5 text-xs font-medium", belowMin || aboveMax ? "text-warning" : "text-text-muted")}>
        Wörter: {wordCount} / {minWords}–{maxWords}
        {belowMin && " — Mindestwortzahl noch nicht erreicht."}
        {aboveMax && " — Maximale Wortzahl überschritten."}
      </p>
    </div>
  );
}
