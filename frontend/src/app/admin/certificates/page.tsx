"use client";

import { Suspense, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import {
  AdminButton,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminPageHeader,
  AdminSelect,
} from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import ZertifikateClient from "@/features/admin/components/certificates/zertifikate-client";
import { useCrudMutations } from "@/features/admin/hooks/use-crud";
import { certificatesApi } from "@/features/admin/services/certificates-service";
import type { CertificateSource } from "@/features/admin/types/certificate.types";

const SOURCE_OPTIONS: { value: CertificateSource; label: string }[] = [
  { value: "COURSE", label: "Kursabschluss" },
  { value: "VORBEREITUNG", label: "Vorbereitung" },
  { value: "VIZU_MULTILEVEL", label: "VIZU-Multilevel" },
];

const EMPTY_FORM = {
  user_id: "",
  course_id: "",
  source: "COURSE" as CertificateSource,
  level: "",
  score: 0,
  lesen_score: 0,
  hoeren_score: 0,
  schreiben_score: 0,
  sprechen_score: 0,
  is_valid: true,
};

/** Admin -> Zertifikate: every student's certificates (course certificates +
 * VIZU-Multilevel) with filters, pagination and PDF; manual issuing below. */
export default function CertificatesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const { create } = useCrudMutations("certificates", certificatesApi);

  async function handleSubmit() {
    setError(null);
    try {
      await create.mutateAsync({
        ...form,
        course_id: form.source === "COURSE" ? form.course_id : null,
      });
      setDialogOpen(false);
      setForm(EMPTY_FORM);
      await queryClient.invalidateQueries({ queryKey: ["admin-zertifikate"] });
    } catch {
      setError("Zertifikat konnte nicht ausgestellt werden. Prüfe, ob Nutzer- und Kurs-ID korrekt sind.");
    }
  }

  return (
    <div>
      <AdminPageHeader
        title="Zertifikate"
        description="Alle Zertifikate der Lernenden — Kursabschluss und VIZU-Multilevel — nach Niveau, Typ, Status und Datum."
        action={
          <AdminButton onClick={() => setDialogOpen(true)}>
            <Plus size={16} />
            Zertifikat ausstellen
          </AdminButton>
        }
      />

      <Suspense fallback={<p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Lädt …</p>}>
        <ZertifikateClient />
      </Suspense>

      <FormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="Zertifikat manuell ausstellen"
        description="Zertifikatsnummer und Verifizierungscode werden automatisch generiert."
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
                !form.user_id ||
                !form.level ||
                (form.source === "COURSE" && !form.course_id)
              }
            >
              {create.isPending ? "Wird ausgestellt..." : "Ausstellen"}
            </AdminButton>
          </>
        }
      >
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--admin-danger)]">{error}</p>}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <AdminLabel>Nutzer-ID</AdminLabel>
              <AdminInput
                value={form.user_id}
                onChange={(e) => setForm({ ...form, user_id: e.target.value })}
                placeholder="UUID des Nutzers"
              />
            </div>
            <div>
              <AdminLabel>Quelle</AdminLabel>
              <AdminSelect
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value as CertificateSource })}
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </AdminSelect>
            </div>
          </div>

          {form.source === "COURSE" && (
            <div>
              <AdminLabel>Kurs-ID</AdminLabel>
              <AdminInput
                value={form.course_id}
                onChange={(e) => setForm({ ...form, course_id: e.target.value })}
                placeholder="UUID des Kurses"
              />
            </div>
          )}

          <div>
            <AdminLabel>Level</AdminLabel>
            <AdminInput
              value={form.level}
              onChange={(e) => setForm({ ...form, level: e.target.value })}
              placeholder="B1"
            />
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <AdminLabel>Gesamt %</AdminLabel>
              <AdminInput
                type="number"
                value={form.score}
                onChange={(e) => setForm({ ...form, score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Lesen</AdminLabel>
              <AdminInput
                type="number"
                value={form.lesen_score}
                onChange={(e) => setForm({ ...form, lesen_score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Hören</AdminLabel>
              <AdminInput
                type="number"
                value={form.hoeren_score}
                onChange={(e) => setForm({ ...form, hoeren_score: Number(e.target.value) })}
              />
            </div>
            <div>
              <AdminLabel>Schreiben</AdminLabel>
              <AdminInput
                type="number"
                value={form.schreiben_score}
                onChange={(e) => setForm({ ...form, schreiben_score: Number(e.target.value) })}
              />
            </div>
          </div>

          <label className="flex cursor-pointer items-center gap-2.5">
            <AdminCheckbox
              checked={form.is_valid}
              onCheckedChange={(checked) => setForm({ ...form, is_valid: checked })}
            />
            <span className="text-sm text-[var(--admin-text-secondary)]">Gültig</span>
          </label>
        </div>
      </FormDialog>
    </div>
  );
}
