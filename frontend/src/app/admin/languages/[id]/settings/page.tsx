"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminPageHeader } from "@/components/admin/admin-ui";
import {
  getLanguage,
  getLanguageSettings,
  updateLanguageSettings,
} from "@/features/admin/services/language-management-service";
import type { LanguageSettings } from "@/features/admin/types/language.types";

const TOGGLE_GROUPS: { title: string; keys: (keyof Omit<LanguageSettings, "language_id">)[] }[] = [
  {
    title: "Kompetenzen",
    keys: ["vocabulary_enabled", "grammar_enabled", "reading_enabled", "listening_enabled", "writing_enabled", "speaking_enabled"],
  },
  {
    title: "Bewertung & Prüfungen",
    keys: ["homework_enabled", "quiz_enabled", "mock_exams_enabled", "certificates_enabled"],
  },
  {
    title: "KI-Funktionen",
    keys: ["ai_writing_enabled", "ai_speaking_enabled"],
  },
  {
    title: "Plattform",
    keys: ["leaderboard_enabled", "video_lessons_enabled", "media_library_enabled"],
  },
];

const LABELS: Record<string, string> = {
  certificates_enabled: "Certificates",
  leaderboard_enabled: "Leaderboard",
  vocabulary_enabled: "Vocabulary",
  grammar_enabled: "Grammar",
  reading_enabled: "Reading",
  listening_enabled: "Listening",
  writing_enabled: "Writing",
  speaking_enabled: "Speaking",
  homework_enabled: "Homework",
  quiz_enabled: "Quiz",
  ai_writing_enabled: "AI Writing",
  ai_speaking_enabled: "AI Speaking",
  mock_exams_enabled: "Mock Exams",
  video_lessons_enabled: "Video Lessons",
  media_library_enabled: "Media Library",
};

export default function LanguageSettingsPage() {
  const { id } = useParams<{ id: string }>();

  const { data: language } = useQuery({ queryKey: ["language", id], queryFn: () => getLanguage(id) });
  const { data: settings, isLoading } = useQuery({
    queryKey: ["language-settings", id],
    queryFn: () => getLanguageSettings(id),
  });

  const [form, setForm] = useState<LanguageSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) setForm(settings);
  }, [settings]);

  async function handleSave() {
    if (!form) return;
    setSaving(true);
    setSaved(false);
    try {
      const { language_id: _languageId, ...updates } = form;
      const updated = await updateLanguageSettings(id, updates);
      setForm(updated);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <Link
        href="/admin/languages"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Languages
      </Link>

      <AdminPageHeader
        title={`Einstellungen — ${language?.name ?? ""}`}
        description="Feature-Toggles für diese Sprache."
        action={
          <AdminButton onClick={handleSave} disabled={saving || !form}>
            {saving ? "Wird gespeichert..." : saved ? "Gespeichert ✓" : "Speichern"}
          </AdminButton>
        }
      />

      {isLoading || !form ? (
        <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {TOGGLE_GROUPS.map((group) => (
            <AdminCard key={group.title}>
              <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">{group.title}</h3>
              <div className="space-y-3">
                {group.keys.map((key) => (
                  <label key={key} className="flex cursor-pointer items-center justify-between">
                    <span className="text-sm text-[var(--admin-text-secondary)]">{LABELS[key]}</span>
                    <AdminCheckbox
                      checked={form[key]}
                      onCheckedChange={(checked) => {
                        setSaved(false);
                        setForm({ ...form, [key]: checked });
                      }}
                    />
                  </label>
                ))}
              </div>
            </AdminCard>
          ))}
        </div>
      )}
    </div>
  );
}
