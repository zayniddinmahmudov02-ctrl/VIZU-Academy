"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import LanguageForm, {
  toLanguageCreatePayload,
  type LanguageFormValues,
} from "@/features/admin/components/language/language-form";
import { getLanguage, languageManagementApi } from "@/features/admin/services/language-management-service";
import type { Language } from "@/features/admin/types/language.types";

export default function EditLanguagePage() {
  const { id } = useParams<{ id: string }>();

  const { data: language, isLoading } = useQuery({
    queryKey: ["language", id],
    queryFn: () => getLanguage(id),
  });

  return (
    <div>
      <Link
        href="/admin/languages"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Languages
      </Link>

      <AdminPageHeader title="Sprache bearbeiten" description={language?.name} />

      {isLoading || !language ? (
        <p className="text-sm text-[var(--admin-text-muted)]">Wird geladen...</p>
      ) : (
        <EditLanguageForm id={id} language={language} />
      )}
    </div>
  );
}

function languageToFormValues(language: Language): LanguageFormValues {
  return {
    code: language.code,
    locale: language.locale,
    name: language.name,
    native_name: language.native_name ?? "",
    english_name: language.english_name ?? "",
    flag_file: language.flag_file ?? "",
    primary_color: language.primary_color ?? "#5b5bf8",
    description: language.description ?? "",
    is_default: language.is_default,
    is_active: language.is_active,
    sort_order: language.sort_order,
  };
}

// Only mounted once `language` has loaded, so its form state can be
// derived once at mount time (lazy useState initializer) instead of
// synced in afterward via an effect.
function EditLanguageForm({ id, language }: { id: string; language: Language }) {
  const router = useRouter();
  const [form, setForm] = useState<LanguageFormValues>(() => languageToFormValues(language));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await languageManagementApi.update(id, toLanguageCreatePayload(form));
      router.push("/admin/languages");
    } catch (err) {
      const message =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        "Speichern fehlgeschlagen.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AdminCard className="max-w-2xl">
      {error && <p className="mb-4 text-sm text-[var(--admin-danger)]">{error}</p>}
      <LanguageForm form={form} onChange={setForm} />
      <div className="mt-6 flex justify-end gap-3">
        <Link href="/admin/languages">
          <AdminButton variant="ghost">Abbrechen</AdminButton>
        </Link>
        <AdminButton onClick={handleSubmit} disabled={submitting || !form.code || !form.locale || !form.name}>
          {submitting ? "Wird gespeichert..." : "Speichern"}
        </AdminButton>
      </div>
    </AdminCard>
  );
}
