"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, RotateCcw, Save, Square } from "lucide-react";

import Button from "@/components/ui/button";
import VizuMultilevelFinishConfirmDialog from "@/features/vizu-multilevel/components/finish-confirm-dialog";
import VizuMultilevelTimer from "@/features/vizu-multilevel/components/timer";
import { useSprechenRecorder } from "@/features/vizu-multilevel/hooks/use-sprechen-recorder";
import { useTranslation } from "@/lib/i18n/use-translation";

import { saveAnswer, saveWriting, submitSection, uploadRecording } from "../../services/multilevel-exam-service";
import type { PaperQuestion, PaperTeil, SectionPaper } from "../../types/multilevel-exam.types";
import PaperTeilView from "./paper-teil";

type SaveState = "saving" | "saved" | "error";

function errorCode(err: unknown): string | undefined {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const value = data?.message ?? data?.detail;
  return typeof value === "string" ? value : undefined;
}

/** One running section of a Multilevel attempt. Every change is saved at once (answers) or debounced (texts); the
 * server checks the deadline on every save and grades the section when it is handed in. The timer is display only. */
export default function ExamSection({ paper, onClosed }: { paper: SectionPaper; onClosed: () => void }) {
  const { t } = useTranslation();
  const [answers, setAnswers] = useState<Record<string, string[]>>(paper.answers);
  const [saving, setSaving] = useState<Record<string, SaveState>>({});
  const [confirm, setConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [closedMessage, setClosedMessage] = useState<string | null>(null);
  const closedRef = useRef(false);

  const handleClosed = useCallback(
    (message: string | null) => {
      if (closedRef.current) return;
      closedRef.current = true;
      setClosedMessage(message);
      onClosed();
    },
    [onClosed],
  );

  const onSaveError = useCallback(
    (err: unknown) => {
      if (errorCode(err) === "SECTION_CLOSED") handleClosed(t("multilevelExam.timeUp"));
    },
    [handleClosed, t],
  );

  async function answer(q: PaperQuestion, optionIds: string[]) {
    setAnswers((prev) => ({ ...prev, [q.id]: optionIds }));
    setSaving((prev) => ({ ...prev, [q.id]: "saving" }));
    try {
      await saveAnswer(paper.attempt_id, paper.section_type, q.id, optionIds);
      setSaving((prev) => ({ ...prev, [q.id]: "saved" }));
    } catch (err) {
      setSaving((prev) => ({ ...prev, [q.id]: "error" }));
      onSaveError(err);
    }
  }

  async function submit() {
    setSubmitting(true);
    try {
      await submitSection(paper.attempt_id, paper.section_type);
    } finally {
      setSubmitting(false);
      setConfirm(false);
      handleClosed(null);
    }
  }

  const expire = useCallback(() => {
    // the server closes the section itself at deadline + grace; handing it in now just shows it immediately
    void submitSection(paper.attempt_id, paper.section_type).finally(() => handleClosed(t("multilevelExam.timeUp")));
  }, [paper.attempt_id, paper.section_type, handleClosed, t]);

  return (
    <div className="space-y-5" data-testid="exam-section">
      <div className="sticky top-0 z-20 -mx-4 flex flex-wrap items-center justify-between gap-3 border-b border-surface-border bg-surface-card/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-2xl sm:border sm:px-5">
        <h1 className="text-lg font-bold text-text-primary sm:text-xl">{paper.title}</h1>
        <div className="flex items-center gap-2">
          <VizuMultilevelTimer initialSeconds={paper.remaining_seconds} onExpire={expire} />
          <Button onClick={() => setConfirm(true)} disabled={submitting} data-testid="submit-section">
            {t("multilevelExam.submitSection")}
          </Button>
        </div>
      </div>

      {closedMessage && <p className="rounded-xl bg-warning/10 px-4 py-3 text-sm font-semibold text-warning">{closedMessage}</p>}

      {paper.teile.map((teil) => (
        <PaperTeilView
          key={teil.id}
          teil={teil}
          mode="exam"
          answers={answers}
          onAnswer={answer}
          savingState={saving}
          disabled={!!closedMessage}
        >
          {teil.writing_task && (
            <WritingBox attemptId={paper.attempt_id} teil={teil} initial={paper.writings[teil.writing_task.id] ?? ""} onError={onSaveError} />
          )}
          {teil.speaking_task && (
            <SpeakingBox attemptId={paper.attempt_id} teil={teil} saved={!!paper.recordings[teil.speaking_task.id]} onError={onSaveError} />
          )}
        </PaperTeilView>
      ))}

      <div className="flex justify-end pb-6">
        <Button onClick={() => setConfirm(true)} disabled={submitting}>
          {t("multilevelExam.submitSection")}
        </Button>
      </div>

      <VizuMultilevelFinishConfirmDialog
        open={confirm}
        onCancel={() => setConfirm(false)}
        onConfirm={submit}
        isSubmitting={submitting}
        title={t("multilevelExam.submitSection")}
        body={t("multilevelExam.confirmSubmit")}
        confirmLabel={t("multilevelExam.submitSection")}
      />
    </div>
  );
}

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

const UMLAUTS = ["Ä", "Ö", "Ü", "ä", "ö", "ü", "ß"];

function WritingBox({ attemptId, teil, initial, onError }: { attemptId: string; teil: PaperTeil; initial: string; onError: (e: unknown) => void }) {
  const { t } = useTranslation();
  const [value, setValue] = useState(initial);
  const [state, setState] = useState<SaveState | null>(null);
  const lastSaved = useRef(initial);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ref = useRef<HTMLTextAreaElement>(null);
  const taskId = teil.writing_task!.id;

  const flush = useCallback(
    async (text: string) => {
      if (text === lastSaved.current) return;
      setState("saving");
      try {
        await saveWriting(attemptId, taskId, text);
        lastSaved.current = text;
        setState("saved");
      } catch (err) {
        setState("error");
        onError(err);
      }
    },
    [attemptId, taskId, onError],
  );

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  function change(text: string) {
    setValue(text);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => void flush(text), 1500);
  }

  function insert(char: string) {
    const el = ref.current;
    const start = el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? value.length;
    change(value.slice(0, start) + char + value.slice(end));
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(start + 1, start + 1);
    });
  }

  return (
    <div className="mt-4">
      <div className="mb-2 flex flex-wrap gap-1.5">
        {UMLAUTS.map((c) => (
          <button key={c} type="button" onClick={() => insert(c)}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-hover text-sm font-bold text-text-primary ring-1 ring-surface-border hover:bg-surface-border">
            {c}
          </button>
        ))}
      </div>
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => change(e.target.value)}
        onBlur={() => void flush(value)}
        rows={10}
        maxLength={20000}
        data-testid="writing-answer"
        className="w-full resize-y rounded-2xl bg-white p-4 text-sm leading-relaxed text-black ring-1 ring-surface-border outline-none focus:ring-2 focus:ring-accent-blue"
      />
      <div className="mt-1.5 flex items-center justify-between text-xs font-semibold text-text-muted">
        <span>{t("multilevelExam.words", { count: countWords(value) })}{teil.writing_task!.word_limit ? ` / ~${teil.writing_task!.word_limit}` : ""}</span>
        {state && (
          <span className={state === "error" ? "text-danger" : ""}>
            {state === "saving" ? t("multilevelExam.saving") : state === "saved" ? t("multilevelExam.saved") : t("multilevelExam.saveError")}
          </span>
        )}
      </div>
    </div>
  );
}

function SpeakingBox({ attemptId, teil, saved, onError }: { attemptId: string; teil: PaperTeil; saved: boolean; onError: (e: unknown) => void }) {
  const { t } = useTranslation();
  const recorder = useSprechenRecorder();
  const [state, setState] = useState<SaveState | null>(saved ? "saved" : null);
  const max = teil.speaking_task!.max_recording_duration_seconds || 120;

  async function save() {
    if (!recorder.answer) return;
    setState("saving");
    try {
      await uploadRecording(attemptId, teil.speaking_task!.id, recorder.answer.blob);
      setState("saved");
    } catch (err) {
      setState("error");
      onError(err);
    }
  }

  return (
    <div className="mt-4 space-y-3 rounded-xl bg-surface-hover/60 p-4 ring-1 ring-surface-border" data-testid="speaking-box">
      <div className="flex flex-wrap items-center gap-2">
        {recorder.status === "recording" ? (
          <Button onClick={recorder.stop} variant="secondary">
            <Square size={14} /> {t("multilevelExam.stop")} · {recorder.elapsed}s
          </Button>
        ) : (
          <Button onClick={() => void recorder.start(max)} variant={recorder.answer ? "secondary" : "primary"}>
            {recorder.answer ? <RotateCcw size={14} /> : <Mic size={14} />}
            {recorder.answer ? t("multilevelExam.reRecord") : t("multilevelExam.record")}
          </Button>
        )}
        {recorder.answer && recorder.status === "recorded" && (
          <Button onClick={() => void save()} disabled={state === "saving"} data-testid="save-recording">
            <Save size={14} /> {t("multilevelExam.saveRecording")}
          </Button>
        )}
        <span className="text-xs text-text-muted">{t("multilevelExam.maxSeconds", { count: max })}</span>
      </div>
      {recorder.answer && <audio controls src={recorder.answer.url} className="w-full" />}
      {recorder.status === "denied" && <p className="text-sm text-danger">{t("multilevelExam.micDenied")}</p>}
      {recorder.status === "unsupported" && <p className="text-sm text-danger">{t("multilevelExam.recUnsupported")}</p>}
      {state && (
        <p className={`text-xs font-semibold ${state === "error" ? "text-danger" : "text-success"}`}>
          {state === "saving" ? t("multilevelExam.saving") : state === "saved" ? t("multilevelExam.recordingSaved") : t("multilevelExam.saveError")}
        </p>
      )}
    </div>
  );
}
