"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminPageHeader } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import { useCrudList, useCrudMutations } from "@/features/admin/hooks/use-crud";
import TeilContentEditor from "@/features/admin/components/mock-exam/teil-content-editor";
import {
  getModelTestScore,
  mockExamKompetenzenApi,
  mockExamModelTestsApi,
  mockExamTeileApi,
} from "@/features/admin/services/mock-exam-service";
import { KOMPETENZ_TYPES, type Kompetenz, type KompetenzType, type Teil } from "@/features/admin/types/mock-exam.types";

const KOMPETENZ_LABELS: Record<KompetenzType, string> = {
  LESEN: "Lesen",
  HOEREN: "Hören",
  SCHREIBEN: "Schreiben",
  SPRECHEN: "Sprechen",
};

export default function ModelTestEditorPage() {
  const { providerId, levelId, modelTestId } = useParams<{
    providerId: string;
    levelId: string;
    modelTestId: string;
  }>();

  const { data: modelTests } = useCrudList("mock-exam-model-tests", mockExamModelTestsApi, { level_id: levelId });
  const modelTest = modelTests?.find((m) => m.id === modelTestId);

  const { data: kompetenzen } = useCrudList("mock-exam-kompetenzen", mockExamKompetenzenApi, {
    model_test_id: modelTestId,
  });
  const { create: createKompetenz } = useCrudMutations("mock-exam-kompetenzen", mockExamKompetenzenApi);

  const { data: score } = useQuery({
    queryKey: ["mock-exam-model-test-score", modelTestId],
    queryFn: () => getModelTestScore(modelTestId),
  });

  const [activeType, setActiveType] = useState<KompetenzType>("LESEN");
  const activeKompetenz = kompetenzen?.find((k) => k.type === activeType);

  async function handleCreateKompetenz(type: KompetenzType) {
    await createKompetenz.mutateAsync({
      model_test_id: modelTestId,
      type,
      title: KOMPETENZ_LABELS[type],
      description: null,
      total_points: 0,
      duration_minutes: 0,
      sort_order: KOMPETENZ_TYPES.indexOf(type) + 1,
    });
  }

  return (
    <div>
      <Link
        href={`/admin/mock-exams/${providerId}/${levelId}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Modelltests
      </Link>

      <AdminPageHeader
        title={modelTest?.title ?? "Modelltest"}
        description={score ? `Gesamtpunktzahl: ${score.total_points} Punkte` : undefined}
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {KOMPETENZ_TYPES.map((type) => {
          const exists = kompetenzen?.some((k) => k.type === type);
          const points = score?.kompetenz_points[type];
          return (
            <button
              key={type}
              onClick={() => (exists ? setActiveType(type) : handleCreateKompetenz(type))}
              className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
                activeType === type && exists
                  ? "bg-[var(--admin-primary)] text-white"
                  : exists
                    ? "bg-[var(--admin-card)] text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] hover:bg-[var(--admin-card-hover)]"
                    : "bg-transparent text-[var(--admin-text-muted)] ring-1 ring-dashed ring-[var(--admin-border-strong)] hover:text-[var(--admin-primary)]"
              }`}
            >
              {exists ? KOMPETENZ_LABELS[type] : `+ ${KOMPETENZ_LABELS[type]}`}
              {exists && points !== undefined && (
                <span className="ml-2 opacity-70">({points} P.)</span>
              )}
            </button>
          );
        })}
      </div>

      {activeKompetenz ? (
        <KompetenzPanel kompetenz={activeKompetenz} />
      ) : (
        <p className="text-sm text-[var(--admin-text-muted)]">
          Wähle oder erstelle eine Kompetenz oben, um Teile zu verwalten.
        </p>
      )}
    </div>
  );
}

function KompetenzPanel({ kompetenz }: { kompetenz: Kompetenz }) {
  const { update: updateKompetenz } = useCrudMutations("mock-exam-kompetenzen", mockExamKompetenzenApi);
  const { data: teile, isLoading } = useCrudList("mock-exam-teile", mockExamTeileApi, {
    kompetenz_id: kompetenz.id,
  });
  const { create, remove } = useCrudMutations("mock-exam-teile", mockExamTeileApi);

  const [expanded, setExpanded] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<Teil | null>(null);

  const sorted = [...(teile ?? [])].sort((a, b) => a.sort_order - b.sort_order);

  async function handleAddTeil() {
    const created = await create.mutateAsync({
      kompetenz_id: kompetenz.id,
      title: `Teil ${sorted.length + 1}`,
      description: null,
      instructions: null,
      points: 0,
      time_limit_minutes: null,
      sort_order: sorted.length + 1,
    });
    setExpanded(created.id);
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3 rounded-2xl bg-[var(--admin-card)] p-5 ring-1 ring-[var(--admin-border)]">
        <div>
          <AdminLabel>Titel</AdminLabel>
          <AdminInput
            defaultValue={kompetenz.title}
            onBlur={(e) => {
              if (e.target.value !== kompetenz.title) {
                updateKompetenz.mutate({ id: kompetenz.id, data: { title: e.target.value } });
              }
            }}
          />
        </div>
        <div>
          <AdminLabel>Gesamtpunkte (Anzeige)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={kompetenz.total_points}
            onBlur={(e) => updateKompetenz.mutate({ id: kompetenz.id, data: { total_points: Number(e.target.value) } })}
          />
        </div>
        <div>
          <AdminLabel>Dauer (Minuten)</AdminLabel>
          <AdminInput
            type="number"
            defaultValue={kompetenz.duration_minutes}
            onBlur={(e) =>
              updateKompetenz.mutate({ id: kompetenz.id, data: { duration_minutes: Number(e.target.value) } })
            }
          />
        </div>
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Teile</h3>
          <AdminButton size="sm" variant="secondary" onClick={handleAddTeil} disabled={create.isPending}>
            <Plus size={14} />
            Teil hinzufügen
          </AdminButton>
        </div>

        {isLoading && <p className="text-xs text-[var(--admin-text-muted)]">Wird geladen...</p>}

        <div className="space-y-3">
          {sorted.map((teil) => (
            <div key={teil.id} className="rounded-xl bg-[var(--admin-card)] ring-1 ring-[var(--admin-border)]">
              <div className="flex items-center gap-2 p-3">
                <button
                  onClick={() => setExpanded(expanded === teil.id ? null : teil.id)}
                  className="flex h-6 w-6 shrink-0 items-center justify-center text-[var(--admin-text-muted)]"
                >
                  {expanded === teil.id ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                </button>
                <TeilInlineFields teil={teil} />
                <button
                  onClick={() => setDeleting(teil)}
                  aria-label="Teil löschen"
                  className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[var(--admin-text-muted)] hover:bg-[var(--admin-danger)]/10 hover:text-[var(--admin-danger)]"
                >
                  <Trash2 size={13} />
                </button>
              </div>

              {expanded === teil.id && (
                <div className="border-t border-[var(--admin-border)] p-4">
                  <TeilFullFields teil={teil} />
                  <div className="mt-4">
                    <TeilContentEditor teilId={teil.id} kompetenzType={kompetenz.type} />
                  </div>
                </div>
              )}
            </div>
          ))}

          {!isLoading && sorted.length === 0 && (
            <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Teile angelegt.</p>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Teil löschen"
        description={`"${deleting?.title}" wird dauerhaft gelöscht, inklusive Inhalt und Fragen.`}
        isPending={remove.isPending}
        onConfirm={async () => {
          if (!deleting) return;
          await remove.mutateAsync(deleting.id);
          setDeleting(null);
        }}
      />
    </div>
  );
}

function TeilInlineFields({ teil }: { teil: Teil }) {
  const { update } = useCrudMutations("mock-exam-teile", mockExamTeileApi);
  return (
    <>
      <AdminInput
        defaultValue={teil.title}
        onBlur={(e) => {
          if (e.target.value !== teil.title) update.mutate({ id: teil.id, data: { title: e.target.value } });
        }}
        className="h-8 flex-1 text-sm"
      />
      <AdminInput
        type="number"
        defaultValue={teil.points}
        title="Punkte"
        onBlur={(e) => {
          const value = Number(e.target.value);
          if (value !== teil.points) update.mutate({ id: teil.id, data: { points: value } });
        }}
        className="h-8 w-16 text-center text-sm"
      />
    </>
  );
}

function TeilFullFields({ teil }: { teil: Teil }) {
  const { update } = useCrudMutations("mock-exam-teile", mockExamTeileApi);
  return (
    <div className="mb-4 grid grid-cols-2 gap-3">
      <div>
        <AdminLabel>Beschreibung</AdminLabel>
        <AdminInput
          defaultValue={teil.description ?? ""}
          onBlur={(e) => {
            if (e.target.value !== (teil.description ?? "")) {
              update.mutate({ id: teil.id, data: { description: e.target.value } });
            }
          }}
        />
      </div>
      <div>
        <AdminLabel>Anweisungen für Schüler</AdminLabel>
        <AdminInput
          defaultValue={teil.instructions ?? ""}
          onBlur={(e) => {
            if (e.target.value !== (teil.instructions ?? "")) {
              update.mutate({ id: teil.id, data: { instructions: e.target.value } });
            }
          }}
        />
      </div>
      <div>
        <AdminLabel>Zeitlimit (Minuten, optional)</AdminLabel>
        <AdminInput
          type="number"
          defaultValue={teil.time_limit_minutes ?? ""}
          onBlur={(e) =>
            update.mutate({
              id: teil.id,
              data: { time_limit_minutes: e.target.value ? Number(e.target.value) : null },
            })
          }
        />
      </div>
    </div>
  );
}
