"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Check, FileText, Headphones, Mic, PenLine } from "lucide-react";

import { getPublicModelTest } from "@/features/vorbereitung/services/vorbereitung-service";
import type { KompetenzType, PublicKompetenzSummary } from "@/features/vorbereitung/types/vorbereitung.types";

const KOMPETENZ_META: Record<
  KompetenzType,
  { label: string; icon: typeof FileText }
> = {
  LESEN: { label: "Lesen", icon: FileText },
  HOEREN: { label: "Hören", icon: Headphones },
  SCHREIBEN: { label: "Schreiben", icon: PenLine },
  SPRECHEN: { label: "Sprechen", icon: Mic },
};

const KOMPETENZ_ORDER: KompetenzType[] = ["LESEN", "HOEREN", "SCHREIBEN", "SPRECHEN"];

export default function PublicModelTestPage() {
  const { modelTestId } = useParams<{ modelTestId: string }>();

  const { data: modelTest, isLoading, isError } = useQuery({
    queryKey: ["public-model-test", modelTestId],
    queryFn: () => getPublicModelTest(modelTestId),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <Link
        href="/vorbereitung"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-accent-blue"
      >
        <ArrowLeft size={16} />
        Vorbereitung
      </Link>

      {isLoading && <p className="text-sm text-text-secondary">Wird geladen…</p>}

      {isError && (
        <p className="rounded-2xl bg-surface-card p-6 text-center text-sm text-text-secondary shadow-[var(--shadow-sm)] ring-1 ring-surface-border">
          Dieser Modelltest ist nicht verfügbar.
        </p>
      )}

      {modelTest && (
        <>
          <header>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">{modelTest.title}</h1>
            {modelTest.description && <p className="mt-2 text-text-secondary">{modelTest.description}</p>}
          </header>

          <div className="grid gap-4 sm:grid-cols-2">
            {KOMPETENZ_ORDER.map((type) => {
              const kompetenz = modelTest.kompetenzen.find((k) => k.type === type);
              return <KompetenzCard key={type} type={type} modelTestId={modelTest.id} kompetenz={kompetenz} />;
            })}
          </div>
        </>
      )}
    </div>
  );
}

function KompetenzCard({
  type,
  modelTestId,
  kompetenz,
}: {
  type: KompetenzType;
  modelTestId: string;
  kompetenz: PublicKompetenzSummary | undefined;
}) {
  const { label, icon: Icon } = KOMPETENZ_META[type];
  const available = kompetenz?.has_content ?? false;

  const card = (
    <div
      className={`flex items-center justify-between gap-4 rounded-2xl bg-surface-card p-5 shadow-[var(--shadow-sm)] ring-1 ring-surface-border transition-all duration-200 ${
        available ? "hover:-translate-y-1 hover:shadow-[var(--shadow-lg)]" : "opacity-60"
      }`}
    >
      <div className="flex items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-blue/10 text-accent-blue">
          <Icon size={20} />
        </div>
        <div>
          <p className="font-semibold text-text-primary">{label}</p>
          <p
            className={`flex items-center gap-1 text-sm ${
              available ? "text-success" : "text-text-muted"
            }`}
          >
            {available ? (
              <>
                <Check size={14} /> Verfügbar
              </>
            ) : (
              "— Noch nicht verfügbar"
            )}
          </p>
        </div>
      </div>
    </div>
  );

  if (!available || !kompetenz) return card;

  return <Link href={`/vorbereitung/modelltest/${modelTestId}/${kompetenz.id}`}>{card}</Link>;
}
