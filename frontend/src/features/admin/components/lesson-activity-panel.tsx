"use client";

import { useCallback, useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import type { ActivityTypeConfig } from "../config/lesson-activity-configs";
import {
  type ActivityRecord,
  createActivityItem,
  deleteActivityItem,
  listActivityItems,
  updateActivityItem,
} from "../services/generic-activity-service";
import AdminModal from "./admin-modal";
import DataTable, { type DataTableColumn } from "./data-table";
import { Badge } from "./badges";

const inputClass =
  "w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50";

interface Props {
  lessonId: string;
  config: ActivityTypeConfig;
}

function emptyFormState(config: ActivityTypeConfig): Record<string, string | number | boolean> {
  const state: Record<string, string | number | boolean> = {};
  for (const field of config.fields) {
    state[field.key] = field.defaultValue ?? (field.type === "checkbox" ? false : field.type === "number" ? 0 : "");
  }
  return state;
}

export default function LessonActivityPanel({ lessonId, config }: Props) {
  const [items, setItems] = useState<ActivityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string | number | boolean>>(() => emptyFormState(config));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    listActivityItems(config)
      .then((all) => setItems(all.filter((item) => item.lesson_id === lessonId)))
      .catch((err) => {
        console.warn(`Failed to load ${config.type} items:`, err);
        setError(`Could not load ${config.label.toLowerCase()}.`);
      })
      .finally(() => setLoading(false));
  }, [config, lessonId]);

  useEffect(() => {
    load();
  }, [load]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyFormState(config));
    setSaveError(null);
    setModalOpen(true);
  }

  function openEdit(item: ActivityRecord) {
    const next = emptyFormState(config);
    for (const field of config.fields) {
      if (item[field.key] !== undefined && item[field.key] !== null) {
        next[field.key] = item[field.key] as string | number | boolean;
      }
    }
    setEditingId(String(item.id));
    setForm(next);
    setSaveError(null);
    setModalOpen(true);
  }

  async function handleSave() {
    const missingRequired = config.fields.some(
      (field) => field.required && !String(form[field.key] ?? "").trim(),
    );
    if (missingRequired) return;

    setSaving(true);
    setSaveError(null);

    try {
      if (editingId) {
        await updateActivityItem(config, editingId, form);
      } else {
        await createActivityItem(config, { ...form, lesson_id: lessonId });
      }
      setModalOpen(false);
      load();
    } catch (err) {
      console.warn(`Failed to save ${config.type} item:`, err);
      setSaveError(`Failed to save. Please try again.`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(item: ActivityRecord) {
    if (!window.confirm(`Delete this ${config.label.toLowerCase()} item?`)) return;
    await deleteActivityItem(config, String(item.id));
    load();
  }

  const columns: DataTableColumn<ActivityRecord>[] = [
    ...config.columns.map((column): DataTableColumn<ActivityRecord> => ({
      key: column.key,
      label: column.label,
      render: (item) => {
        const value = item[column.key];
        if (typeof value === "boolean") {
          return <Badge label={value ? "Yes" : "No"} tone={value ? "success" : "neutral"} />;
        }
        return <span className="text-[var(--admin-text-secondary)]">{value === null || value === undefined || value === "" ? "—" : String(value)}</span>;
      },
    })),
    {
      key: "actions",
      label: "Actions",
      render: (item) => (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => openEdit(item)}
            className="rounded-lg border border-[var(--admin-border)] px-2.5 py-1.5 text-xs font-semibold text-[var(--admin-text-secondary)] transition-colors hover:bg-white/5 hover:text-white"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => handleDelete(item)}
            aria-label={`Delete ${config.label.toLowerCase()} item`}
            className="rounded-lg border border-[var(--admin-border)] p-1.5 text-[var(--admin-text-secondary)] transition-colors hover:border-[var(--admin-danger)]/40 hover:text-[var(--admin-danger)]"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-[var(--admin-text-muted)]">{items.length} {config.label.toLowerCase()} item(s)</p>
        <button
          type="button"
          onClick={openCreate}
          className="rounded-xl bg-[var(--admin-primary)] px-4 py-2 text-xs font-semibold text-white"
        >
          + Add {config.label}
        </button>
      </div>

      {error ? (
        <div className="admin-glass rounded-2xl p-8 text-center">
          <p className="text-sm font-semibold text-white">{error}</p>
        </div>
      ) : (
        <DataTable
          columns={columns}
          rows={items}
          getRowKey={(item) => String(item.id)}
          loading={loading}
          emptyLabel={`No ${config.label.toLowerCase()} items yet.`}
          minWidth="640px"
        />
      )}

      <AdminModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        title={editingId ? `Edit ${config.label}` : `New ${config.label}`}
      >
        <div className="space-y-3">
          {config.fields.map((field) => {
            if (field.type === "checkbox") {
              return (
                <label key={field.key} className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
                  <input
                    type="checkbox"
                    checked={Boolean(form[field.key])}
                    onChange={(event) => setForm((prev) => ({ ...prev, [field.key]: event.target.checked }))}
                    className="h-4 w-4 rounded border-[var(--admin-border)] accent-[var(--admin-primary)]"
                  />
                  {field.label}
                </label>
              );
            }

            if (field.type === "textarea") {
              return (
                <textarea
                  key={field.key}
                  value={String(form[field.key] ?? "")}
                  onChange={(event) => setForm((prev) => ({ ...prev, [field.key]: event.target.value }))}
                  placeholder={field.label}
                  rows={3}
                  className={inputClass}
                />
              );
            }

            return (
              <input
                key={field.key}
                type={field.type === "number" ? "number" : "text"}
                value={String(form[field.key] ?? "")}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    [field.key]: field.type === "number" ? Number(event.target.value) : event.target.value,
                  }))
                }
                placeholder={field.label + (field.required ? " *" : "")}
                className={inputClass}
              />
            );
          })}

          {saveError && <p className="text-xs text-[#ef4444]">{saveError}</p>}

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {saving ? "Saving…" : editingId ? "Save Changes" : "Create"}
          </button>
        </div>
      </AdminModal>
    </div>
  );
}
