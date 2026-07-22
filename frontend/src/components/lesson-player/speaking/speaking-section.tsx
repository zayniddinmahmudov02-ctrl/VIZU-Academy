"use client";

import { useRef, useState } from "react";
import { Loader2, Mic, RotateCcw, Sparkles, Square } from "lucide-react";

import Button from "@/components/ui/button";
import EvaluationResult from "@/features/assessment/components/evaluation-result";
import { useSpeakingEvaluation } from "@/features/assessment/hooks/use-speaking-evaluation";
import { useTranslation } from "@/lib/i18n/use-translation";
import LessonSection from "../common/lesson-section";

interface Props {
  lessonId: string;
  prompt?: string;
  targetLevel?: string;
}

type RecorderStatus = "idle" | "recording" | "recorded";

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export default function SpeakingSection({
  lessonId,
  prompt = "Stelle dich in ein bis zwei Minuten auf Deutsch vor.",
  targetLevel = "A1",
}: Props) {
  const { t } = useTranslation();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBase64, setAudioBase64] = useState<string | null>(null);
  const [recorderError, setRecorderError] = useState<string | null>(null);

  const { result, loading, error, evaluate, reset } = useSpeakingEvaluation();

  async function startRecording() {
    setRecorderError(null);

    if (typeof window === "undefined" || !navigator.mediaDevices || !window.MediaRecorder) {
      setRecorderError(t("lessons.speakingNotSupported"));
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setAudioBase64(await blobToBase64(blob));

        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        setStatus("recorded");
      };

      recorder.start();
      setStatus("recording");
    } catch (err) {
      console.error("Microphone access failed:", err);
      setRecorderError(t("lessons.speakingPermissionDenied"));
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
  }

  function rerecord() {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
    setAudioBase64(null);
    setStatus("idle");
    reset();
  }

  function handleEvaluate() {
    if (!audioBase64) return;
    evaluate({ prompt, audioUrl: audioBase64, targetLevel, lessonId });
  }

  return (
    <LessonSection
      title={t("lessons.sectionSpeaking")}
      description={t("lessons.speakingDescription")}
      icon={Mic}
    >
      <div className="rounded-2xl bg-accent-blue/5 p-10 text-center ring-2 ring-dashed ring-accent-blue/25 sm:p-12">
        <Mic size={56} className="mx-auto text-accent-blue" />

        <p className="mx-auto mt-4 max-w-md text-text-secondary">{prompt}</p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {status === "idle" && (
            <Button type="button" size="sm" onClick={startRecording}>
              <Mic size={16} />
              {t("lessons.speakingRecord")}
            </Button>
          )}

          {status === "recording" && (
            <Button type="button" variant="danger" size="sm" onClick={stopRecording}>
              <Square size={16} />
              {t("lessons.speakingStop")}
            </Button>
          )}

          {status === "recorded" && audioUrl && (
            <div className="flex w-full flex-col items-center gap-3">
              <audio controls src={audioUrl} className="w-full max-w-sm" />
              <Button type="button" variant="secondary" size="sm" onClick={rerecord}>
                <RotateCcw size={16} />
                {t("lessons.speakingRerecord")}
              </Button>
            </div>
          )}
        </div>

        {recorderError && (
          <p className="mt-4 text-sm font-medium text-danger">{recorderError}</p>
        )}
      </div>

      {status === "recorded" && (
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleEvaluate}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-button bg-gradient-to-r from-accent-blue-hover to-accent-blue px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-accent-blue/25 transition enabled:hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {loading ? t("lessons.speakingEvaluating") : t("lessons.speakingStartEvaluation")}
          </button>
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-2xl bg-danger/10 p-4 text-sm font-medium text-danger">{t(error)}</p>
      )}

      {result && (
        <div className="mt-6">
          <EvaluationResult data={result} />
        </div>
      )}
    </LessonSection>
  );
}
