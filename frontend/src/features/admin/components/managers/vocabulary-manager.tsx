"use client";

import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus, Sparkles } from "lucide-react";

import {
  AdminButton,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
} from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import DataTable, { DataTableColumn } from "@/components/admin/data-table";
import FileUploadField from "@/components/admin/file-upload-field";
import FormDialog from "@/components/admin/form-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import { regenerateVocabularyAudio, vocabularyApi } from "@/features/admin/services/vocabulary-service";
import type { Vocabulary } from "@/features/admin/types/content.types";

import BulkVocabularyDialog from "../vocabulary/bulk-vocabulary-dialog";
import LessonPicker from "./lesson-picker";

const EMPTY_FORM = {
  lesson_id: "",
  german_word: "",
  article: "",
  plural: "",
  translation: "",
  example_sentence: "",
  example_translation: "",
  audio_url: "",
  order_index: 1,
  is_published: false,
};

export default function VocabularyManager({ lessonId }: { lessonId?: string }) {
  const queryClient = useQueryClient();
  const { data: all, isLoading } = useCrudList("vocabularies", vocabularyApi);
  const { create, update, remove } = useCrudMutations("vocabularies", vocabularyApi);

  const data = useMemo(
    () => (lessonId ? (all ?? []).filter((v) => v.lesson_id === lessonId) : all),
    [all, lessonId],
  );

  const [dialogOpen, setDialogOpen] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [editing, setEditing] = useState<Vocabulary | null>(null);
  const [deleting, setDeleting] = useState<Vocabulary | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  function openCreate() {
    setEditing(null);
    setForm({ ...EMPTY_FORM, lesson_id: lessonId ?? "" });
    setError(null);
    setDialogOpen(true);
  }

  function openEdit(item: Vocabulary) {
    setEditing(item);
    setForm({
      lesson_id: item.lesson_id,
      german_word: item.german_word,
      article: item.article ?? "",
      plural: item.plural ?? "",
      translation: item.translation,
      example_sentence: item.example_sentence ?? "",
      example_translation: item.example_translation ?? "",
      audio_url: item.audio_url ?? "",
      order_index: item.order_index,
      is_published: item.is_published,
    });
    setError(null);
    setDialogOpen(true);
  }

  async function handleSubmit() {
    setError(null);
    try {
      if (editing) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { lesson_id: _lessonId, ...updateData } = form;
        await update.mutateAsync({ id: editing.id, data: updateData });
      } else {
        await create.mutateAsync(form);
      }
      setDialogOpen(false);
    } catch {
      setError("Speichern fehlgeschlagen.");
    }
  }

  async function handleRegenerateAudio() {
    if (!editing) return;
    setRegenerating(true);
    setError(null);
    try {
      const { audio_url } = await regenerateVocabularyAudio(editing.id);
      setForm((prev) => ({ ...prev, audio_url }));
    } catch {
      setError("Audio konnte nicht erstellt werden.");
    } finally {
      setRegenerating(false);
    }
  }

  const columns: DataTableColumn<Vocabulary>[] = [
    {
      key: "word",
      header: "Wort",
      render: (item) => (
        <span className="font-medium">
          {item.article && <span className="text-[var(--admin-text-muted)]">{item.article} </span>}
          {item.german_word}
        </span>
      ),
    },
    { key: "translation", header: "Übersetzung", render: (item) => item.translation },
    { key: "plural", header: "Plural", render: (item) => item.plural || "—" },
    {
      key: "is_published",
      header: "Status",
      render: (item) => (
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
            item.is_published
              ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]"
              : "bg-white/5 text-[var(--admin-text-muted)]"
          }`}
        >
          {item.is_published ? "Veröffentlicht" : "Entwurf"}
        </span>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex justify-end gap-2.5">
        <AdminButton onClick={openCreate}>
          <Plus size={16} />
          Neues Wort
        </AdminButton>
        {lessonId && (
          <AdminButton variant="secondary" onClick={() => setBulkOpen(true)}>
            <Sparkles size={16} />
            Wörter importieren
          </AdminButton>
        )}
      </div>

      <DataTable
        columns={columns}
        data={data}
        isLoading={isLoading}
        getRowId={(item) => item.id}
        onEdit={openEdit}
        onDelete={setDeleting}
        emptyMessage="Noch keine Vokabeln angelegt."
      />

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing ? "Vokabel bearbeiten" : "Neue Vokabel"}
        size="lg"
        footer={
          <>
            <AdminButton variant="ghost" onClick={() => setDialogOpen(false)}>
              Abbrechen
            </AdminButton>
            <AdminButton
              onClick={handleSubmit}
              disabled={
                create.isPending ||
                update.isPending ||
                !form.german_word ||
                !form.translation ||
                !form.lesson_id
              }
            >
              {create.isPending || update.isPending ? "Wird gespeichert..." : "Speichern"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          {!lessonId && !editing && (
            <LessonPicker
              value={form.lesson_id}
              onChange={(id) => setForm({ ...form, lesson_id: id })}
            />
          )}

          <div className="grid grid-cols-3 gap-3">
            <div>
              <AdminLabel>Artikel</AdminLabel>
              <AdminInput
                value={form.article}
                onChange={(e) => setForm({ ...form, article: e.target.value })}
                placeholder="der/die/das"
              />
            </div>
            <div className="col-span-2">
              <AdminLabel>Wort</AdminLabel>
              <AdminInput
                value={form.german_word}
                onChange={(e) => setForm({ ...form, german_word: e.target.value })}
                placeholder="Haus"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Plural</AdminLabel>
              <AdminInput
                value={form.plural}
                onChange={(e) => setForm({ ...form, plural: e.target.value })}
                placeholder="Häuser"
              />
            </div>
            <div>
              <AdminLabel>Übersetzung</AdminLabel>
              <AdminInput
                value={form.translation}
                onChange={(e) => setForm({ ...form, translation: e.target.value })}
                placeholder="house"
              />
            </div>
          </div>

          <div>
            <AdminLabel>Beispielsatz</AdminLabel>
            <AdminInput
              value={form.example_sentence}
              onChange={(e) => setForm({ ...form, example_sentence: e.target.value })}
            />
          </div>

          <div>
            <AdminLabel>Beispielsatz-Übersetzung</AdminLabel>
            <AdminInput
              value={form.example_translation}
              onChange={(e) => setForm({ ...form, example_translation: e.target.value })}
            />
          </div>

          <div>
            <FileUploadField
              label="Audio"
              folder="audio"
              accept="audio/*"
              value={form.audio_url || null}
              onChange={(url) => setForm({ ...form, audio_url: url })}
            />
            {editing && (
              <AdminButton
                type="button"
                variant="ghost"
                size="sm"
                className="mt-2"
                onClick={handleRegenerateAudio}
                disabled={regenerating || !form.german_word}
              >
                🔊 {regenerating ? "Wird erstellt..." : "Audio neu generieren"}
              </AdminButton>
            )}
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_published}
              onCheckedChange={(checked) => setForm({ ...form, is_published: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Veröffentlicht</span>
          </label>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Vokabel löschen"
        description={`"${deleting?.german_word}" wird dauerhaft gelöscht.`}
        isPending={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          setDeleting(null);
        }}
      />

      {lessonId && (
        <BulkVocabularyDialog
          lessonId={lessonId}
          open={bulkOpen}
          onOpenChange={setBulkOpen}
          onSaved={() => queryClient.invalidateQueries({ queryKey: ["vocabularies"] })}
        />
      )}
    </div>
  );
}
