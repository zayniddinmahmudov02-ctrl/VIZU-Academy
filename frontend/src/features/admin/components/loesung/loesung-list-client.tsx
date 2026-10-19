"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, Headphones, Loader2, Search } from "lucide-react";

import { AdminButton, AdminInput, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getLoesungOverview, taskHref, type LoesungItem, type OverviewFilters } from "@/features/admin/services/loesung-service";

import { KeyStatusBadge, PublishBadge, AudioBadge } from "./loesung-badges";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)]";
const FILTER_KEYS: (keyof OverviewFilters)[] = ["level", "lesson_id", "section", "status", "publication", "q"];

/** Admin -> LMS A1–C1 -> Lösung: every Lesen / Hören Aufgabe of A1–C1 with
 * its answer-key and publish state. All numbers come from
 * GET /admin/loesung/overview for the current filters. Filters live in the
 * URL, so the editor's "back" returns to the same list. */
export default function LoesungListClient() {
  const router = useRouter();
  const params = useSearchParams();
  const filters: OverviewFilters = useMemo(
    () => Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) ?? ""])) as OverviewFilters,
    [params],
  );

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ["loesung", "overview", filters],
    queryFn: () => getLoesungOverview(filters),
  });

  function setFilter(patch: Partial<OverviewFilters>) {
    const next = { ...filters, ...patch };
    if ("level" in patch) next.lesson_id = "";
    const sp = new URLSearchParams(Object.entries(next).filter(([, v]) => v) as [string, string][]);
    router.replace(`/admin/lms/loesung${sp.toString() ? `?${sp}` : ""}`);
  }

  const firstOpen = data?.items.find((i) => i.key_status !== "complete");
  const s = data?.stats;
  const tiles: [string, number | undefined, Partial<OverviewFilters>][] = [
    ["Lesen-Aufgaben", s?.lesen_total, { section: "lesen", status: "" }],
    ["Hören-Aufgaben", s?.hoeren_total, { section: "hoeren", status: "" }],
    ["Lösung vollständig & geprüft", s?.complete, { status: "complete" }],
    ["Lösung fehlt / unvollständig", s?.missing, { status: "missing" }],
    ["Manuelle Prüfung nötig", s?.needs_review, { status: "needs_review" }],
    ["Audio fehlt", s?.missing_audio, { status: "missing_audio" }],
    ["Entwurf, bereit zur Veröffentlichung", s?.ready, { status: "ready" }],
    ["Veröffentlicht", s?.published, { status: "published" }],
  ];

  return (
    <div className="space-y-6" data-testid="loesung-page">
      <AdminPageHeader title="Lösung" description="Lösungen der Lesen- und Hören-Aufgaben (A1–C1) prüfen, ergänzen, bestätigen und veröffentlichen." />

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="loesung-stats">
        {tiles.map(([label, value, patch]) => (
          <button key={label} onClick={() => setFilter(patch)} className={`${card} text-left transition hover:ring-[var(--admin-primary)]`}>
            <p className="text-2xl font-extrabold text-[var(--admin-text-primary)]">{value ?? "–"}</p>
            <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
          </button>
        ))}
      </section>

      <section className={`${card} space-y-3`}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <AdminSelect value={filters.level} onChange={(e) => setFilter({ level: e.target.value })} aria-label="Niveau" data-testid="loesung-level">
            <option value="">Alle Niveaus</option>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.lesson_id} onChange={(e) => setFilter({ lesson_id: e.target.value })} aria-label="Lektion" data-testid="loesung-lesson">
            <option value="">Alle Lektionen</option>
            {data?.lessons.map((l) => <option key={l.id} value={l.id}>{l.level} · {l.number}. {l.title}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.section} onChange={(e) => setFilter({ section: e.target.value })} aria-label="Bereich" data-testid="loesung-section">
            <option value="">Lesen & Hören</option><option value="lesen">Lesen</option><option value="hoeren">Hören</option>
          </AdminSelect>
          <AdminSelect value={filters.status} onChange={(e) => setFilter({ status: e.target.value })} aria-label="Lösungsstatus" data-testid="loesung-status">
            <option value="">Alle Lösungsstatus</option>
            <option value="complete">Vollständig & geprüft</option><option value="missing">Lösung fehlt</option>
            <option value="needs_review">Prüfung nötig</option><option value="missing_audio">Audio fehlt</option>
            <option value="ready">Bereit zur Veröffentlichung</option><option value="published">Veröffentlicht</option>
          </AdminSelect>
          <AdminSelect value={filters.publication} onChange={(e) => setFilter({ publication: e.target.value })} aria-label="Veröffentlichung" data-testid="loesung-publication">
            <option value="">Entwurf & veröffentlicht</option><option value="draft">Entwurf</option><option value="published">Veröffentlicht</option>
          </AdminSelect>
          <form className="relative" key={filters.q}
                onSubmit={(e) => { e.preventDefault(); setFilter({ q: String(new FormData(e.currentTarget).get("q") ?? "").trim() }); }}>
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
            <AdminInput name="q" className="pl-8" placeholder="Lektion, Aufgabe, Frage … (Enter)" defaultValue={filters.q} data-testid="loesung-search" />
          </form>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {firstOpen && (
            <Link href={taskHref(firstOpen.kind, firstOpen.id)} data-testid="loesung-next-open">
              <AdminButton size="sm"><ArrowRight size={14} /> Nächste offene Aufgabe</AdminButton>
            </Link>
          )}
          {FILTER_KEYS.some((k) => filters[k]) && (
            <AdminButton size="sm" variant="ghost" onClick={() => router.replace("/admin/lms/loesung")}>Filter zurücksetzen</AdminButton>
          )}
          {isFetching && <Loader2 size={14} className="animate-spin text-[var(--admin-text-muted)]" />}
        </div>
      </section>

      {error && <p className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Übersicht konnte nicht geladen werden.")}</p>}
      {isLoading ? (
        <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Lädt …</p>
      ) : data && data.items.length === 0 ? (
        <p className={`${card} py-10 text-center text-sm text-[var(--admin-text-muted)]`} data-testid="loesung-empty">
          Keine Aufgaben für diese Filter{filters.level && !["A1", "A2"].includes(filters.level) ? ` — für ${filters.level} sind noch keine Lesen- oder Hören-Aufgaben angelegt.` : "."}
        </p>
      ) : (
        <div className="space-y-2" data-testid="loesung-list">
          {data?.items.map((i) => <Row key={`${i.kind}-${i.id}`} item={i} />)}
        </div>
      )}
    </div>
  );
}

function Row({ item: i }: { item: LoesungItem }) {
  return (
    <Link href={taskHref(i.kind, i.id)} className={`${card} flex flex-wrap items-center gap-x-4 gap-y-2 transition hover:ring-[var(--admin-primary)]`}
          data-testid="loesung-row" data-kind={i.kind} data-status={i.key_status} data-published={i.is_published}>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[var(--admin-hover)] text-[var(--admin-primary)]">
        {i.kind === "hoeren" ? <Headphones size={16} /> : <BookOpen size={16} />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-[var(--admin-text-muted)]">
          {i.level} · Lektion {i.lesson_number}: {i.lesson_title} · {i.kind === "hoeren" ? "Hören" : "Lesen"} · Aufgabe {i.number}
        </p>
        <p className="truncate font-semibold text-[var(--admin-text-primary)]">{i.title}</p>
        {i.import_note && <p className="truncate text-xs text-[var(--admin-warning)]" title={i.import_note}>Hinweis: {i.import_note}</p>}
      </div>
      <div className="text-xs text-[var(--admin-text-secondary)]">
        <p>{i.questions} Fragen{i.answer_fields !== i.questions ? ` · ${i.answer_fields} Antwortfelder` : ""}</p>
        <p>{i.answer_fields_keyed}/{i.answer_fields} mit Lösung · {i.verified} geprüft</p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <KeyStatusBadge status={i.key_status} />
        {i.kind === "hoeren" && <AudioBadge audio={i.audio} />}
        <PublishBadge published={i.is_published} ready={i.ready_to_publish} />
      </div>
      <p className="w-24 text-right text-[11px] text-[var(--admin-text-muted)]">{new Date(i.updated_at).toLocaleDateString("de-DE")}</p>
    </Link>
  );
}
