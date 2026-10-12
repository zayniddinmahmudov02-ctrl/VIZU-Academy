"use client";

import { Fragment } from "react";

import type { AnswerValue, PublicQuestion, QuestionResult } from "@/features/lessons/services/lesson-skills-service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";

export const CONFIG_TYPES = new Set(["MATCHING", "GAP_FILL", "SHORT_ANSWER"]);
const GAP_PATTERN = /\[\[([A-Za-z0-9_-]{1,20})\]\]/g;

/** Fully answered = every Zuordnung item / every Lücke filled; partial
 * answers are still submitted and earn partial credit. */
export function isAnswered(q: PublicQuestion, value: AnswerValue | undefined): boolean {
  if (value === undefined || value === null) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (q.question_type === "MATCHING") return (q.config?.items ?? []).every((i) => (value[i.id] ?? "").trim());
  if (q.question_type === "GAP_FILL") return (q.config?.gaps ?? []).every((g) => (value[g.id] ?? "").trim());
  return Object.values(value).some((v) => v.trim());
}

interface Props {
  question: PublicQuestion;
  value: AnswerValue | undefined;
  result?: QuestionResult;
  disabled: boolean;
  onChange: (value: AnswerValue) => void;
}

const fieldBase =
  "min-h-11 rounded-xl bg-surface-hover/50 px-3 text-sm text-text-primary ring-1 ring-surface-border outline-none transition focus:ring-2 focus:ring-accent-blue disabled:opacity-100";

function verdictRing(ok: boolean | undefined) {
  if (ok === undefined) return "";
  return ok ? "bg-success/10 ring-success/50 text-success font-semibold" : "bg-danger/10 ring-danger/40 text-danger";
}

/** Zuordnung, Lückentext and Kurzantwort. The key is never on the client
 * before submission; after it, `result` carries per item / gap verdicts. */
export default function ConfigQuestion({ question, value, result, disabled, onChange }: Props) {
  const { t } = useTranslation();
  const config = question.config ?? {};
  const obj = value && typeof value === "object" ? value : {};
  const key = result?.correct_answer;
  const keyObj = key && typeof key === "object" ? key : {};

  if (question.question_type === "MATCHING") {
    const targets = config.targets ?? [];
    const textOf = (id: string | undefined) => targets.find((x) => x.id === id)?.text ?? id ?? "";
    return (
      <div className="mt-3 space-y-3">
        <ul className="grid gap-1.5 rounded-xl bg-surface-hover/40 p-3 text-sm sm:grid-cols-2" aria-label={t("lessons.testMatchingTargets")}>
          {targets.map((x) => (
            <li key={x.id} className="text-text-secondary">
              <span className="mr-1.5 font-bold text-text-primary">{x.id})</span>
              {x.text}
            </li>
          ))}
        </ul>
        {(config.items ?? []).map((item) => {
          const ok = result?.details ? result.details[item.id] : undefined;
          return (
            <div key={item.id} className="grid gap-2 sm:grid-cols-[1fr_minmax(0,16rem)] sm:items-center">
              <p className="text-sm text-text-primary">
                <span className="mr-1.5 font-bold">{item.id}.</span>
                {item.text}
              </p>
              <div>
                <select
                  value={obj[item.id] ?? ""}
                  disabled={disabled}
                  onChange={(e) => onChange({ ...obj, [item.id]: e.target.value })}
                  className={cn(fieldBase, "w-full", verdictRing(ok))}
                  aria-label={`${item.id}. ${item.text}`}
                  data-testid="test-match-select"
                >
                  <option value="">{t("lessons.testChoose")}</option>
                  {targets.map((x) => (
                    <option key={x.id} value={x.id}>
                      {x.id}) {x.text}
                    </option>
                  ))}
                </select>
                {ok === false && (
                  <p className="mt-1 text-xs text-success">
                    {t("lessons.testCorrectAnswer")}: {keyObj[item.id]}) {textOf(keyObj[item.id])}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  if (question.question_type === "GAP_FILL") {
    const gaps = new Map((config.gaps ?? []).map((g) => [g.id, g]));
    const parts = (config.text ?? "").split(GAP_PATTERN);
    // split() with one capture group: even = text, odd = gap id
    return (
      <p className="mt-3 text-[15px] leading-[2.6] text-text-primary">
        {parts.map((part, i) => {
          if (i % 2 === 0) return <Fragment key={i}>{part}</Fragment>;
          const gap = gaps.get(part);
          const ok = result?.details ? result.details[part] : undefined;
          const common = {
            value: obj[part] ?? "",
            disabled,
            "aria-label": `${t("lessons.testGap")} ${part}`,
            className: cn(fieldBase, "mx-1 inline-block h-9 min-h-0 py-0 align-middle", verdictRing(ok)),
          };
          return (
            <span key={i} className="inline-flex flex-wrap items-center">
              {gap?.options?.length ? (
                <select {...common} onChange={(e) => onChange({ ...obj, [part]: e.target.value })} data-testid="test-gap">
                  <option value="">…</option>
                  {gap.options.map((o) => (
                    <option key={o.id} value={o.text}>
                      {o.text}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  {...common}
                  type="text"
                  maxLength={100}
                  autoComplete="off"
                  spellCheck={false}
                  onChange={(e) => onChange({ ...obj, [part]: e.target.value })}
                  style={{ width: `${Math.max(7, (obj[part] ?? "").length + 2)}ch` }}
                  data-testid="test-gap"
                />
              )}
              {ok === false && <span className="mr-1 text-xs font-semibold text-success">({keyObj[part]})</span>}
            </span>
          );
        })}
      </p>
    );
  }

  // SHORT_ANSWER
  const text = typeof value === "string" ? value : "";
  const ok = result ? result.is_correct : undefined;
  return (
    <div className="mt-3">
      <input
        type="text"
        value={text}
        disabled={disabled}
        maxLength={config.max_length ?? 100}
        autoComplete="off"
        onChange={(e) => onChange(e.target.value)}
        placeholder={t("lessons.testTypeAnswer")}
        className={cn(fieldBase, "w-full", verdictRing(ok))}
        aria-label={question.question}
        data-testid="test-short-answer"
      />
      {ok === false && typeof key === "string" && (
        <p className="mt-1 text-xs text-success">
          {t("lessons.testCorrectAnswer")}: {key}
        </p>
      )}
    </div>
  );
}
