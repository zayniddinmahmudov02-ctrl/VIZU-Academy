"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { AdminButton, AdminInput, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import RichTextEditor from "@/components/admin/rich-text-editor";
import {
  getListeningContentByTeil,
  getReadingContentByTeil,
  getSpeakingTaskByTeil,
  getWritingTaskByTeil,
  listQuestions,
  mockExamListeningContentApi,
  mockExamReadingContentApi,
  mockExamSpeakingTasksApi,
  mockExamWritingTasksApi,
} from "@/features/admin/services/mock-exam-service";
import type { KompetenzType } from "@/features/admin/types/mock-exam.types";

import MediaUploadButton from "./media-upload-button";
import MockQuestionEditor from "./mock-question-editor";

export default function TeilContentEditor({
  teilId,
  kompetenzType,
}: {
  teilId: string;
  kompetenzType: KompetenzType;
}) {
  if (kompetenzType === "LESEN") return <ReadingTeilContent teilId={teilId} />;
  if (kompetenzType === "HOEREN") return <ListeningTeilContent teilId={teilId} />;
  if (kompetenzType === "SCHREIBEN") return <WritingTeilContent teilId={teilId} />;
  return <SpeakingTeilContent teilId={teilId} />;
}

// ============================================================
// Lesen — Reading content + questions
// ============================================================

function ReadingTeilContent({ teilId }: { teilId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["mock-exam-reading-content", teilId];
  const { data: content, isLoading } = useQuery({
    queryKey,
    queryFn: () => getReadingContentByTeil(teilId),
  });

  const questionsKey = `mock-exam-questions-reading-${content?.id}`;
  const { data: questions } = useQuery({
    queryKey: [questionsKey],
    queryFn: () => listQuestions({ reading_content_id: content!.id }),
    enabled: !!content,
  });

  async function handleCreate() {
    await mockExamReadingContentApi.create({ teil_id: teilId, content_type: "TEXT", text: "", image_url: null });
    queryClient.invalidateQueries({ queryKey });
  }

  if (isLoading) return <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>;

  if (!content) {
    return (
      <AdminButton variant="secondary" size="sm" onClick={handleCreate}>
        Lesetext-Inhalt anlegen
      </AdminButton>
    );
  }

  async function patch(data: Partial<{ content_type: "TEXT" | "IMAGE" | "TEXT_IMAGE"; text: string; image_url: string | null }>) {
    await mockExamReadingContentApi.update(content!.id, data);
    queryClient.invalidateQueries({ queryKey });
  }

  return (
    <div className="space-y-4">
      <div>
        <AdminLabel>Inhaltstyp</AdminLabel>
        <AdminSelect
          defaultValue={content.content_type}
          onChange={(e) => patch({ content_type: e.target.value as "TEXT" | "IMAGE" | "TEXT_IMAGE" })}
          className="h-9 text-sm"
        >
          <option value="TEXT">Nur Text</option>
          <option value="IMAGE">Nur Bild</option>
          <option value="TEXT_IMAGE">Text + Bild</option>
        </AdminSelect>
      </div>

      {content.content_type !== "IMAGE" && (
        <div>
          <AdminLabel>Lesetext</AdminLabel>
          <RichTextEditor
            value={content.text ?? ""}
            onChange={(html) => patch({ text: html })}
            placeholder="Lesetext mit Absätzen..."
          />
        </div>
      )}

      {content.content_type !== "TEXT" && (
        <MediaUploadButton
          value={content.image_url}
          onChange={(url) => patch({ image_url: url })}
          folder="images"
          label="Bild"
          accept="image/*"
        />
      )}

      <div>
        <AdminLabel>Fragen</AdminLabel>
        <MockQuestionEditor
          parentKey="reading_content_id"
          parentId={content.id}
          questions={questions ?? []}
          queryKey={questionsKey}
        />
      </div>
    </div>
  );
}

// ============================================================
// Hören — Listening content + questions
// ============================================================

function ListeningTeilContent({ teilId }: { teilId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["mock-exam-listening-content", teilId];
  const { data: content, isLoading } = useQuery({
    queryKey,
    queryFn: () => getListeningContentByTeil(teilId),
  });

  const questionsKey = `mock-exam-questions-listening-${content?.id}`;
  const { data: questions } = useQuery({
    queryKey: [questionsKey],
    queryFn: () => listQuestions({ listening_content_id: content!.id }),
    enabled: !!content,
  });

  async function handleCreate() {
    await mockExamListeningContentApi.create({ teil_id: teilId, audio_url: "", image_url: null, transcript: null });
    queryClient.invalidateQueries({ queryKey });
  }

  if (isLoading) return <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>;

  if (!content) {
    return (
      <AdminButton variant="secondary" size="sm" onClick={handleCreate}>
        Hörverstehen-Inhalt anlegen
      </AdminButton>
    );
  }

  async function patch(data: Partial<{ audio_url: string; image_url: string | null; transcript: string | null }>) {
    await mockExamListeningContentApi.update(content!.id, data);
    queryClient.invalidateQueries({ queryKey });
  }

  return (
    <div className="space-y-4">
      <MediaUploadButton
        value={content.audio_url || null}
        onChange={(url) => patch({ audio_url: url ?? "" })}
        folder="audio"
        label="Audiodatei (MP3, WAV, M4A)"
        accept="audio/*"
      />

      {content.audio_url && (
        <audio controls src={content.audio_url} className="w-full">
          <track kind="captions" />
        </audio>
      )}

      <MediaUploadButton
        value={content.image_url}
        onChange={(url) => patch({ image_url: url })}
        folder="images"
        label="Bild (optional)"
        accept="image/*"
      />

      <div>
        <AdminLabel>Transkript (optional)</AdminLabel>
        <RichTextEditor
          value={content.transcript ?? ""}
          onChange={(html) => patch({ transcript: html })}
          placeholder="Transkript des Audios..."
        />
      </div>

      <div>
        <AdminLabel>Fragen</AdminLabel>
        <MockQuestionEditor
          parentKey="listening_content_id"
          parentId={content.id}
          questions={questions ?? []}
          queryKey={questionsKey}
        />
      </div>
    </div>
  );
}

// ============================================================
// Schreiben — Writing task + AI evaluation config
// ============================================================

function WritingTeilContent({ teilId }: { teilId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["mock-exam-writing-task", teilId];
  const { data: task, isLoading } = useQuery({ queryKey, queryFn: () => getWritingTaskByTeil(teilId) });

  async function handleCreate() {
    await mockExamWritingTasksApi.create({
      teil_id: teilId,
      task_text: "",
      image_url: null,
      reference_document_url: null,
      word_limit: 200,
      time_limit_minutes: 30,
      points: 0,
      difficulty: null,
      max_points: 100,
      evaluation_rubric: null,
      passing_score: 60,
    });
    queryClient.invalidateQueries({ queryKey });
  }

  if (isLoading) return <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>;

  if (!task) {
    return (
      <AdminButton variant="secondary" size="sm" onClick={handleCreate}>
        Schreibaufgabe anlegen
      </AdminButton>
    );
  }

  async function patch(data: Record<string, unknown>) {
    await mockExamWritingTasksApi.update(task!.id, data);
    queryClient.invalidateQueries({ queryKey });
  }

  return (
    <div className="space-y-4">
      <div>
        <AdminLabel>Aufgabenstellung</AdminLabel>
        <RichTextEditor
          value={task.task_text}
          onChange={(html) => patch({ task_text: html })}
          placeholder="Schreiben Sie einen Brief an..."
        />
      </div>

      <MediaUploadButton
        value={task.image_url}
        onChange={(url) => patch({ image_url: url })}
        folder="images"
        label="Bild (optional)"
        accept="image/*"
      />

      <MediaUploadButton
        value={task.reference_document_url}
        onChange={(url) => patch({ reference_document_url: url })}
        folder="documents"
        label="Referenzdokument (optional)"
        accept=".pdf,.doc,.docx"
      />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <AdminLabel>Wortlimit</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.word_limit ?? ""}
            onBlur={(e) => patch({ word_limit: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
        <div>
          <AdminLabel>Zeitlimit (Min.)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.time_limit_minutes ?? ""}
            onBlur={(e) => patch({ time_limit_minutes: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
        <div>
          <AdminLabel>Punkte (Teil)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.points}
            onBlur={(e) => patch({ points: Number(e.target.value) })}
          />
        </div>
        <div>
          <AdminLabel>Schwierigkeit</AdminLabel>
          <AdminInput
            defaultValue={task.difficulty ?? ""}
            onBlur={(e) => patch({ difficulty: e.target.value || null })}
            placeholder="mittel"
          />
        </div>
      </div>

      <div className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-[var(--admin-border)]">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">
          KI-Bewertung (Gemini)
        </p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <AdminLabel>Max. Punkte</AdminLabel>
            <AdminInput
              type="number"
              defaultValue={task.max_points}
              onBlur={(e) => patch({ max_points: Number(e.target.value) })}
            />
          </div>
          <div>
            <AdminLabel>Bestehensgrenze</AdminLabel>
            <AdminInput
              type="number"
              defaultValue={task.passing_score}
              onBlur={(e) => patch({ passing_score: Number(e.target.value) })}
            />
          </div>
        </div>
        <div className="mt-3">
          <AdminLabel>Bewertungsrichtlinie (Rubric, optional)</AdminLabel>
          <RichTextEditor
            value={task.evaluation_rubric ?? ""}
            onChange={(html) => patch({ evaluation_rubric: html })}
            placeholder="Kriterien für Grammatik, Wortschatz, Aufgabenerfüllung..."
          />
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Sprechen — Speaking task + AI evaluation
// ============================================================

function SpeakingTeilContent({ teilId }: { teilId: string }) {
  const queryClient = useQueryClient();
  const queryKey = ["mock-exam-speaking-task", teilId];
  const { data: task, isLoading } = useQuery({ queryKey, queryFn: () => getSpeakingTaskByTeil(teilId) });

  async function handleCreate() {
    await mockExamSpeakingTasksApi.create({
      teil_id: teilId,
      task_text: "",
      image_url: null,
      preparation_time_seconds: 60,
      speaking_time_seconds: 90,
      max_recording_duration_seconds: 120,
    });
    queryClient.invalidateQueries({ queryKey });
  }

  if (isLoading) return <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>;

  if (!task) {
    return (
      <AdminButton variant="secondary" size="sm" onClick={handleCreate}>
        Sprechaufgabe anlegen
      </AdminButton>
    );
  }

  async function patch(data: Record<string, unknown>) {
    await mockExamSpeakingTasksApi.update(task!.id, data);
    queryClient.invalidateQueries({ queryKey });
  }

  return (
    <div className="space-y-4">
      <div>
        <AdminLabel>Aufgabenstellung</AdminLabel>
        <RichTextEditor
          value={task.task_text}
          onChange={(html) => patch({ task_text: html })}
          placeholder="Beschreiben Sie das Bild und..."
        />
      </div>

      <MediaUploadButton
        value={task.image_url}
        onChange={(url) => patch({ image_url: url })}
        folder="images"
        label="Bild (optional)"
        accept="image/*"
      />

      <div className="grid grid-cols-3 gap-3">
        <div>
          <AdminLabel>Vorbereitungszeit (Sek.)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.preparation_time_seconds}
            onBlur={(e) => patch({ preparation_time_seconds: Number(e.target.value) })}
          />
        </div>
        <div>
          <AdminLabel>Sprechzeit (Sek.)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.speaking_time_seconds}
            onBlur={(e) => patch({ speaking_time_seconds: Number(e.target.value) })}
          />
        </div>
        <div>
          <AdminLabel>Max. Aufnahme (Sek.)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={task.max_recording_duration_seconds}
            onBlur={(e) => patch({ max_recording_duration_seconds: Number(e.target.value) })}
          />
        </div>
      </div>

      <p className="text-xs text-[var(--admin-text-muted)]">
        Bewertung erfolgt automatisch per Gemini Speech-to-Text nach Einreichung durch den Schüler (Transkript,
        Punktzahl, Feedback).
      </p>
    </div>
  );
}
