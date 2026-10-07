"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Play } from "lucide-react";

import { AdminButton } from "@/components/admin/admin-ui";
import {
  getVizuMultilevelAttemptSprechen,
  getVizuMultilevelAttemptSprechenAudio,
} from "@/features/admin/vizu-multilevel/services/vizu-multilevel-admin-service";
import type { VizuMultilevelSpeakingAttemptDetail } from "@/features/admin/vizu-multilevel/types/vizu-multilevel-admin.types";

type Submission = VizuMultilevelSpeakingAttemptDetail["submissions"][number];

const STATUS_LABEL: Record<string, string> = {
  PROCESSING: "Wird transkribiert",
  TRANSCRIBED: "Transkribiert",
  EVALUATING: "Wird bewertet",
  EVALUATED: "Bewertet",
  FAILED: "Fehlgeschlagen",
};

/** Admin view of one student's Sprechen: per Aufgabe the internal level, the
 * recording (private — loaded with the admin's token), transcript, what the
 * speech recognition heard, AI score per criterion and the AI feedback. */
export default function SprechenAttemptDetail({ attemptId }: { attemptId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["vizu-multilevel-admin-attempt-sprechen", attemptId],
    queryFn: () => getVizuMultilevelAttemptSprechen(attemptId),
  });

  if (isLoading) {
    return (
      <div className="flex h-20 items-center justify-center">
        <Loader2 size={18} className="animate-spin text-[var(--admin-primary)]" />
      </div>
    );
  }
  if (isError) return <p className="text-sm text-[var(--admin-danger)]">Sprechen konnte nicht geladen werden.</p>;
  if (!data) return <p className="text-sm text-[var(--admin-text-muted)]">Sprechen wurde noch nicht abgegeben.</p>;

  return (
    <div className="space-y-3" data-testid="admin-sprechen-detail">
      <p className="text-sm text-[var(--admin-text-secondary)]">
        Sprechen gesamt:{" "}
        <span className="font-bold text-[var(--admin-text-primary)]">
          {data.sprechen_score !== null ? `${data.sprechen_score}/100` : "in Auswertung"}
        </span>
        {data.sprechen_level && <span className="ml-2 font-bold text-[var(--admin-primary)]">{data.sprechen_level}</span>}
      </p>
      {data.submissions.map((sub) => (
        <SubmissionCard key={sub.task_id} attemptId={attemptId} sub={sub} />
      ))}
    </div>
  );
}

function SubmissionCard({ attemptId, sub }: { attemptId: string; sub: Submission }) {
  const fb = sub.ai_feedback ?? {};
  const score = sub.teacher_score ?? sub.ai_score;
  return (
    <div className="rounded-xl p-3 ring-1 ring-[var(--admin-border)]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-[var(--admin-text-primary)]">
          Aufgabe {sub.order_index} · {sub.title}{" "}
          <span className="ml-1 rounded-full bg-[var(--admin-primary)]/10 px-2 py-0.5 text-[10px] font-bold text-[var(--admin-primary)]">{sub.level}</span>
        </p>
        <p className="text-sm font-bold text-[var(--admin-text-primary)]">
          {score !== null ? `${score}/${sub.points}` : "—"}
          {sub.teacher_score !== null && <span className="ml-1 text-[10px] font-semibold text-[var(--admin-text-muted)]">(Lehrkraft)</span>}
        </p>
      </div>
      {!sub.submission_id ? (
        <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Keine Antwort gespeichert.</p>
      ) : (
        <div className="mt-2 space-y-2 text-xs text-[var(--admin-text-secondary)]">
          <p>
            Status: <span className="font-semibold">{STATUS_LABEL[sub.status ?? ""] ?? sub.status ?? "—"}</span>
            {sub.duration_seconds ? ` · ${sub.duration_seconds} s` : ""}
            {sub.transcript_confidence !== null ? ` · Erkennung ${Math.round(sub.transcript_confidence * 100)} %` : ""}
          </p>
          {sub.evaluation_error && <p className="text-[var(--admin-danger)]">{sub.evaluation_error}</p>}
          <AudioButton attemptId={attemptId} submissionId={sub.submission_id} />
          {sub.transcript !== null && (
            <p className="rounded-lg bg-[var(--admin-surface-hover,rgba(0,0,0,0.04))] p-2 text-[var(--admin-text-primary)]">
              <span className="font-semibold">Transkript: </span>
              {sub.transcript || "— (keine Sprache erkannt)"}
            </p>
          )}
          {sub.audio_observations && (
            <p>
              <span className="font-semibold">Höreindruck: </span>
              {Object.entries(sub.audio_observations)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")}
            </p>
          )}
          {fb.justification && (
            <ul className="list-disc space-y-0.5 pl-4">
              {Object.entries(fb.justification)
                .filter(([, v]) => v)
                .map(([k, v]) => (
                  <li key={k}>
                    <span className="font-semibold">{k}:</span> {v}
                  </li>
                ))}
            </ul>
          )}
          {fb.errors && fb.errors.length > 0 && (
            <ul className="space-y-0.5">
              {fb.errors.map((e, i) => (
                <li key={i}>
                  „{e.original}“ → <span className="font-semibold text-[var(--admin-success,#16a34a)]">„{e.correction}“</span> — {e.explanation}
                </li>
              ))}
            </ul>
          )}
          {fb.feedback && <p className="text-[var(--admin-text-primary)]">{fb.feedback}</p>}
          {fb.next_step && (
            <p>
              <span className="font-semibold">Tipp: </span>
              {fb.next_step}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function AudioButton({ attemptId, submissionId }: { attemptId: string; submissionId: string }) {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => () => void (url && URL.revokeObjectURL(url)), [url]);

  async function load() {
    setLoading(true);
    setFailed(false);
    try {
      const blob = await getVizuMultilevelAttemptSprechenAudio(attemptId, submissionId);
      setUrl(URL.createObjectURL(blob));
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }

  if (url) return <audio controls src={url} className="h-9 w-full" data-testid="admin-sprechen-audio" />;
  return (
    <div className="flex items-center gap-2">
      <AdminButton size="sm" variant="secondary" onClick={load} disabled={loading}>
        {loading ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
        Aufnahme anhören
      </AdminButton>
      {failed && <span className="text-[var(--admin-danger)]">Audio nicht verfügbar.</span>}
    </div>
  );
}
