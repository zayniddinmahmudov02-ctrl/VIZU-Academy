"use client";

import { useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  Bold,
  Italic,
  Loader2,
  RotateCcw,
  Sparkles,
  Underline as UnderlineIcon,
} from "lucide-react";

import { useWritingEvaluation } from "@/features/assessment/hooks/use-writing-evaluation";
import EvaluationResult from "@/features/assessment/components/evaluation-result";
import { useTranslation } from "@/lib/i18n/use-translation";

interface WritingEditorProps {
  prompt: string;
  targetLevel?: string;
  lessonId?: string;
  minWords?: number;
}

const FONTS = [
  { titleKey: "lessons.writingFontSans", value: "Inter, system-ui, sans-serif" },
  { titleKey: "lessons.writingFontSerif", value: "Georgia, 'Times New Roman', serif" },
  { titleKey: "lessons.writingFontMono", value: "'JetBrains Mono', 'Courier New', monospace" },
];

const SIZES = [
  { label: "S", value: 15 },
  { label: "M", value: 17 },
  { label: "L", value: 20 },
  { label: "XL", value: 24 },
];

const BACKGROUNDS = [
  { titleKey: "lessons.writingBgWhite", bg: "#ffffff", fg: "#0f172a" },
  { titleKey: "lessons.writingBgCream", bg: "#fdf6e3", fg: "#3b3222" },
  { titleKey: "lessons.writingBgBlue", bg: "#eff6ff", fg: "#0b1e3f" },
  { titleKey: "lessons.writingBgMint", bg: "#ecfdf5", fg: "#064e3b" },
  { titleKey: "lessons.writingBgDark", bg: "#0b1e3f", fg: "#e2e8f0" },
];

export default function WritingEditor({
  prompt,
  targetLevel,
  lessonId,
  minWords = 30,
}: WritingEditorProps) {
  const { t } = useTranslation();
  const editorRef = useRef<HTMLDivElement>(null);

  const [font, setFont] = useState(FONTS[0].value);
  const [size, setSize] = useState(SIZES[1].value);
  const [bg, setBg] = useState(BACKGROUNDS[0]);
  const [words, setWords] = useState(0);

  const { result, loading, error, evaluate, reset } = useWritingEvaluation();

  function format(command: "bold" | "italic" | "underline") {
    document.execCommand(command);
    editorRef.current?.focus();
  }

  function updateCount() {
    const text = editorRef.current?.innerText.trim() ?? "";
    setWords(text ? text.split(/\s+/).length : 0);
  }

  function clearEditor() {
    if (editorRef.current) editorRef.current.innerHTML = "";
    setWords(0);
    reset();
  }

  function handleEvaluate() {
    const text = editorRef.current?.innerText.trim() ?? "";
    if (!text) return;
    evaluate({ prompt, text, targetLevel, lessonId });
  }

  const enoughWords = words >= minWords;

  return (
    <div className="space-y-5">
      {/* Prompt */}
      <div className="rounded-2xl bg-surface-hover p-6">
        <h3 className="text-lg font-bold text-text-primary">{t("lessons.writingTaskLabel")}</h3>
        <p className="mt-2 text-text-secondary">{prompt}</p>
        <p className="mt-3 text-xs font-medium text-text-muted">
          {t("lessons.writingMinWords", { count: minWords })}
        </p>
      </div>

      {/* Editor card */}
      <div className="overflow-hidden rounded-card ring-1 ring-surface-border">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3 border-b border-surface-border bg-surface-card p-3">
          {/* Text format */}
          <div className="flex items-center gap-1">
            <ToolButton onClick={() => format("bold")} label={t("lessons.writingBold")}>
              <Bold size={16} />
            </ToolButton>
            <ToolButton onClick={() => format("italic")} label={t("lessons.writingItalic")}>
              <Italic size={16} />
            </ToolButton>
            <ToolButton onClick={() => format("underline")} label={t("lessons.writingUnderline")}>
              <UnderlineIcon size={16} />
            </ToolButton>
          </div>

          <div className="h-6 w-px bg-surface-border" />

          {/* Font */}
          <select
            value={font}
            onChange={(e) => setFont(e.target.value)}
            className="rounded-lg bg-surface-hover px-2 py-1.5 text-sm text-text-primary outline-none ring-1 ring-surface-border focus:ring-2 focus:ring-accent-blue/50"
            aria-label={t("lessons.writingFontLabel")}
          >
            {FONTS.map((f) => (
              <option key={f.titleKey} value={f.value}>
                {t(f.titleKey)}
              </option>
            ))}
          </select>

          {/* Size */}
          <div className="flex items-center gap-1">
            {SIZES.map((s) => (
              <button
                key={s.label}
                type="button"
                onClick={() => setSize(s.value)}
                className={`h-8 w-8 rounded-lg text-xs font-semibold transition-colors ${
                  size === s.value
                    ? "bg-accent-blue text-white"
                    : "bg-surface-hover text-text-secondary hover:bg-surface-border/40"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-surface-border" />

          {/* Background */}
          <div className="flex items-center gap-1.5">
            {BACKGROUNDS.map((b) => {
              const label = t(b.titleKey);
              return (
                <button
                  key={b.titleKey}
                  type="button"
                  onClick={() => setBg(b)}
                  title={label}
                  aria-label={t("lessons.writingBackgroundLabel", { label })}
                  className={`h-7 w-7 rounded-full ring-2 transition-shadow ${
                    bg.titleKey === b.titleKey ? "ring-accent-blue" : "ring-surface-border"
                  }`}
                  style={{ backgroundColor: b.bg }}
                />
              );
            })}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs font-medium text-text-muted">
              {t("lessons.writingWordsLabel", { count: words })}
            </span>
            <ToolButton onClick={clearEditor} label={t("lessons.writingReset")}>
              <RotateCcw size={16} />
            </ToolButton>
          </div>
        </div>

        {/* Writing surface */}
        <div
          ref={editorRef}
          contentEditable
          suppressContentEditableWarning
          onInput={updateCount}
          data-placeholder={t("lessons.writingPlaceholder")}
          className="min-h-[280px] p-6 leading-relaxed outline-none transition-colors empty:before:text-text-muted empty:before:content-[attr(data-placeholder)]"
          style={{
            fontFamily: font,
            fontSize: size,
            backgroundColor: bg.bg,
            color: bg.fg,
          }}
        />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={handleEvaluate}
          disabled={!enoughWords || loading}
          className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Sparkles size={16} />
          )}
          {loading ? t("lessons.writingEvaluating") : t("lessons.writingStartEvaluation")}
        </button>

        {!enoughWords && (
          <span className="text-sm text-text-muted">
            {t("lessons.writingWordsRemaining", { count: Math.max(minWords - words, 0) })}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <p className="rounded-2xl bg-danger/10 p-4 text-sm font-medium text-danger">{t(error)}</p>
      )}

      {/* Result */}
      {result && <EvaluationResult data={result} />}
    </div>
  );
}

function ToolButton({
  onClick,
  label,
  children,
}: {
  onClick: () => void;
  label: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-hover text-text-secondary transition-colors hover:bg-accent-blue/10 hover:text-accent-blue"
    >
      {children}
    </button>
  );
}
