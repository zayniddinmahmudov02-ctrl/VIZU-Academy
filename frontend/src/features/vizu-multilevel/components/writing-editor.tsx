"use client";

import { useRef } from "react";

import { useTranslation } from "@/lib/i18n/use-translation";
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

/** A deliberately minimal writing editor for VIZU-Multilevel's Schreiben
 * module: a plain <textarea> (native Enter/paragraph support, no rich
 * formatting), umlaut insert buttons, and a live word counter. This is
 * NOT the app's RichTextEditor — that one is a full WYSIWYG with bold/
 * italic/color, exactly what this module's spec explicitly forbids
 * ("Faqat oddiy yozuv... boshqa rang tanlay olmasin"), so a new, much
 * smaller component was written instead of reusing/stripping that one. */
export default function VizuMultilevelWritingEditor({ value, onChange, minWords, maxWords, disabled }: Props) {
  const { t } = useTranslation();
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

      <p
        data-testid="word-counter"
        className={cn("mt-2 text-sm font-bold tabular-nums", belowMin || aboveMax ? "text-orange-600" : "text-emerald-600")}
      >
        {t("vizuMultilevel.wordsOfMax", { count: wordCount, max: maxWords })}
      </p>
      {(belowMin || aboveMax) && (
        <p role="status" className="mt-1.5 rounded-lg bg-orange-50 px-3 py-2 text-xs font-semibold text-orange-700 ring-1 ring-orange-200 dark:bg-orange-500/10 dark:text-orange-300 dark:ring-orange-500/30">
          {belowMin
            ? t("vizuMultilevel.wordsBelowMin", { min: minWords, missing: minWords - wordCount })
            : t("vizuMultilevel.wordsAboveMax", { max: maxWords, extra: wordCount - maxWords })}
        </p>
      )}
    </div>
  );
}
