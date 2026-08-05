"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import LanguageForm, {
  EMPTY_LANGUAGE_FORM,
  toLanguageCreatePayload,
  type LanguageFormValues,
} from "@/features/admin/components/language/language-form";
import { languageManagementApi } from "@/features/admin/services/language-management-service";

export default function NewLanguagePage() {
  const router = useRouter();
  const [form, setForm] = useState<LanguageFormValues>(EMPTY_LANGUAGE_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await languageManagementApi.create(toLanguageCreatePayload(form));
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
    <div>
      <Link
        href="/admin/languages"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Languages
      </Link>

      <AdminPageHeader title="Neue Sprache" description="Eine neue Sprache für die Plattform anlegen." />

      <AdminCard className="max-w-2xl">
        {error && <p className="mb-4 text-sm text-[var(--admin-danger)]">{error}</p>}
        <LanguageForm form={form} onChange={setForm} />
        <div className="mt-6 flex justify-end gap-3">
          <Link href="/admin/languages">
            <AdminButton variant="ghost">Abbrechen</AdminButton>
          </Link>
          <AdminButton onClick={handleSubmit} disabled={submitting || !form.code || !form.locale || !form.name}>
            {submitting ? "Wird gespeichert..." : "Sprache anlegen"}
          </AdminButton>
        </div>
      </AdminCard>
    </div>
  );
}
