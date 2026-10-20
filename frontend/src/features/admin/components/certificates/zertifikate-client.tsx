"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Award, ChevronLeft, ChevronRight, Download, Eye, Loader2, Search, X } from "lucide-react";

import { AdminButton, AdminInput, AdminSelect } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { fetchZertifikatPdf, listZertifikate, type ZertifikatFilters, type ZertifikatItem } from "@/features/admin/services/certificates-service";
import { openBlob } from "@/lib/save-blob";

const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)]";
const LEVELS = ["BELOW_A1", "A1", "A2", "B1", "B2", "C1"];
const SOURCES: Record<string, string> = { COURSE: "Kursabschluss", VORBEREITUNG: "Vorbereitung", VIZU_MULTILEVEL: "VIZU-Multilevel" };
const STATUS: Record<ZertifikatItem["status"], { label: string; cls: string }> = {
  valid: { label: "Gültig", cls: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" },
  issued: { label: "Ausgestellt", cls: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" },
  available: { label: "Verfügbar (Nr. noch nicht vergeben)", cls: "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]" },
  revoked: { label: "Widerrufen", cls: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" },
};
const KEYS: (keyof ZertifikatFilters)[] = ["q", "level", "source", "status", "date_from", "date_to", "user_id"];
const date = (v: string | null) => (v ? new Date(v).toLocaleDateString("de-DE") : "—");
const levelText = (lv: string | null) => (lv === "BELOW_A1" ? "unter A1" : lv ?? "—");

/** Every certificate of every student — course certificates and the
 * VIZU-Multilevel exam certificates — from GET /admin/zertifikate. Filters
 * live in the URL. */
export default function ZertifikateClient({ userId }: { userId?: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const filters: ZertifikatFilters = Object.fromEntries(KEYS.map((k) => [k, params.get(k) ?? ""]));
  if (userId) filters.user_id = userId;
  const page = Number(params.get("page") ?? "1") || 1;
  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["admin-zertifikate", filters, page],
    queryFn: () => listZertifikate({ ...filters, page, page_size: 25 }),
  });
  const [open, setOpen] = useState<ZertifikatItem | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function setFilter(patch: Partial<ZertifikatFilters> & { page?: number }) {
    const merged = { ...filters, ...patch };
    const next: Record<string, string> = {};
    for (const k of KEYS) if (k !== "user_id" && merged[k]) next[k] = String(merged[k]);
    if (patch.page && patch.page > 1) next.page = String(patch.page); // a filter change goes back to page 1
    const qs = new URLSearchParams(next).toString();
    router.replace(`${userId ? `/admin/certificates/${userId}` : "/admin/certificates"}${qs ? `?${qs}` : ""}`);
  }

  async function pdf(item: ZertifikatItem, save: boolean) {
    setBusy(item.id);
    setMsg(null);
    try {
      const blob = await fetchZertifikatPdf(item.id);
      openBlob(blob, save ? `Zertifikat-${item.certificate_number ?? item.level ?? "VIZU"}.pdf` : undefined);
    } catch (err) {
      setMsg(apiErrorMessage(err, "PDF konnte nicht geladen werden."));
    } finally {
      setBusy(null);
    }
  }

  const s = data?.stats;
  return (
    <div className="space-y-5" data-testid="zertifikate">
      {!userId && s && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <button className={`${card} text-left`} onClick={() => setFilter({ source: "", page: 1 })}>
            <p className="text-2xl font-extrabold text-[var(--admin-text-primary)]">{s.total}</p>
            <p className="text-xs text-[var(--admin-text-muted)]">Zertifikate gesamt</p>
          </button>
          {Object.entries(SOURCES).map(([k, label]) => (
            <button key={k} className={`${card} text-left`} onClick={() => setFilter({ source: k, page: 1 })} data-testid={`zt-stat-${k}`}>
              <p className="text-2xl font-extrabold text-[var(--admin-text-primary)]">{s.by_source[k] ?? 0}</p>
              <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
            </button>
          ))}
        </section>
      )}

      <section className={`${card} space-y-3`}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          {!userId && (
            <form className="relative lg:col-span-2" key={filters.q}
                  onSubmit={(e) => { e.preventDefault(); setFilter({ q: String(new FormData(e.currentTarget).get("q") ?? "").trim(), page: 1 }); }}>
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
              <AdminInput name="q" className="pl-8" placeholder="Name, E-Mail, Nummer … (Enter)" defaultValue={filters.q} data-testid="zt-search" />
            </form>
          )}
          <AdminSelect value={filters.level} onChange={(e) => setFilter({ level: e.target.value, page: 1 })} aria-label="Niveau" data-testid="zt-level">
            <option value="">Alle Niveaus</option>
            {LEVELS.map((l) => <option key={l} value={l}>{levelText(l)}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.source} onChange={(e) => setFilter({ source: e.target.value, page: 1 })} aria-label="Zertifikatstyp" data-testid="zt-source">
            <option value="">Alle Typen</option>
            {Object.entries(SOURCES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </AdminSelect>
          <AdminSelect value={filters.status} onChange={(e) => setFilter({ status: e.target.value, page: 1 })} aria-label="Status" data-testid="zt-status">
            <option value="">Alle Status</option>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </AdminSelect>
          <div className="flex items-center gap-2">
            <AdminInput type="date" value={filters.date_from} onChange={(e) => setFilter({ date_from: e.target.value, page: 1 })} aria-label="Ausgestellt ab" />
            <AdminInput type="date" value={filters.date_to} onChange={(e) => setFilter({ date_to: e.target.value, page: 1 })} aria-label="Ausgestellt bis" />
          </div>
        </div>
        {KEYS.some((k) => k !== "user_id" && filters[k]) && (
          <AdminButton size="sm" variant="ghost" onClick={() => router.replace(userId ? `/admin/certificates/${userId}` : "/admin/certificates")}>Filter zurücksetzen</AdminButton>
        )}
      </section>

      {msg && <p role="alert" className="text-sm text-[var(--admin-danger)]">{msg}</p>}
      {error ? (
        <p className={`${card} flex items-center gap-2 text-sm text-[var(--admin-danger)]`} role="alert"><AlertTriangle size={15} /> {apiErrorMessage(error, "Zertifikate konnten nicht geladen werden.")}</p>
      ) : isLoading ? (
        <div className={`${card} space-y-2`} aria-busy="true">{[0, 1, 2, 3].map((i) => <div key={i} className="h-10 animate-pulse rounded-lg bg-[var(--admin-hover)]" />)}</div>
      ) : !data || data.items.length === 0 ? (
        <p className={`${card} py-10 text-center text-sm text-[var(--admin-text-muted)]`} data-testid="zt-empty">Keine Zertifikate für diese Filter.</p>
      ) : (
        <section className={`${card} overflow-x-auto p-0`}>
          <table className="w-full min-w-[880px] text-left text-sm" data-testid="zt-table">
            <thead className="text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr>{["Lernende/r", "Typ", "Niveau", "Kurs", "Nummer", "Ausgestellt", "Ergebnis", "Status", ""].map((h) => <th key={h} className="px-3 py-2.5">{h}</th>)}</tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-t border-[var(--admin-border)]" data-testid="zt-row" data-source={c.source}>
                  <td className="px-3 py-2.5">
                    {c.user ? (
                      <Link href={`/admin/certificates/${c.user.id}`} className="font-medium text-[var(--admin-text-primary)] hover:text-[var(--admin-primary)]">
                        {c.user.name}<span className="block text-xs font-normal text-[var(--admin-text-muted)]">{c.user.email}</span>
                      </Link>
                    ) : "—"}
                  </td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{c.type_label}{c.attempt_number ? ` · Versuch ${c.attempt_number}` : ""}</td>
                  <td className="px-3 py-2.5 font-semibold text-[var(--admin-text-primary)]">{levelText(c.level)}</td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{c.course?.title ?? "—"}</td>
                  <td className="px-3 py-2.5 font-mono text-xs text-[var(--admin-text-secondary)]">{c.certificate_number ?? "—"}</td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{date(c.issued_at)}</td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-secondary)]">{c.score !== null ? `${c.score}%` : "—"}</td>
                  <td className="px-3 py-2.5"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS[c.status].cls}`}>{STATUS[c.status].label}</span></td>
                  <td className="px-3 py-2.5">
                    <span className="flex gap-1.5">
                      <AdminButton size="sm" variant="secondary" onClick={() => setOpen(c)} aria-label="Öffnen" data-testid="zt-open"><Eye size={13} /></AdminButton>
                      <AdminButton size="sm" variant="secondary" disabled={!c.pdf_available || busy === c.id} onClick={() => pdf(c, true)} aria-label="PDF herunterladen"
                                   title={c.pdf_available ? "PDF herunterladen" : "Für dieses Zertifikat gibt es keine PDF-Datei"} data-testid="zt-pdf">
                        {busy === c.id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                      </AdminButton>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-[var(--admin-text-secondary)]">
          <span>Seite {data.page} von {data.total_pages} ({data.total} Zertifikate){isFetching ? " …" : ""}</span>
          <span className="flex gap-2">
            <AdminButton size="sm" variant="secondary" disabled={data.page <= 1} onClick={() => setFilter({ page: data.page - 1 })} aria-label="Vorherige Seite"><ChevronLeft size={14} /></AdminButton>
            <AdminButton size="sm" variant="secondary" disabled={data.page >= data.total_pages} onClick={() => setFilter({ page: data.page + 1 })} aria-label="Nächste Seite"><ChevronRight size={14} /></AdminButton>
          </span>
        </div>
      )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" onClick={() => setOpen(null)}>
          <div className={`${card} w-full max-w-lg space-y-4`} onClick={(e) => e.stopPropagation()} data-testid="zt-dialog">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"><Award size={20} /></span>
                <div>
                  <p className="font-bold text-[var(--admin-text-primary)]">{open.type_label} · {levelText(open.level)}</p>
                  <p className="text-xs text-[var(--admin-text-muted)]">{open.user?.name} · {open.user?.email}</p>
                </div>
              </div>
              <AdminButton size="sm" variant="ghost" onClick={() => setOpen(null)} aria-label="Schließen"><X size={15} /></AdminButton>
            </div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              {[["Nummer", open.certificate_number ?? "wird beim ersten Öffnen vergeben"], ["Ausgestellt", date(open.issued_at)],
                ["Ergebnis", open.score !== null ? `${open.score}%` : "—"], ["Status", STATUS[open.status].label],
                ["Kurs", open.course?.title ?? "—"], ["Quelle", SOURCES[open.source] ?? open.source]].map(([k, v]) => (
                <div key={k}><dt className="text-xs text-[var(--admin-text-muted)]">{k}</dt><dd className="text-[var(--admin-text-primary)]">{v}</dd></div>
              ))}
            </dl>
            {open.source === "VIZU_MULTILEVEL" && open.status === "available" && (
              <p className="text-xs text-[var(--admin-text-muted)]">Die Zertifikatsnummer wird beim ersten Öffnen des PDFs vergeben — wie beim Studenten.</p>
            )}
            <div className="flex flex-wrap gap-2">
              <AdminButton disabled={!open.pdf_available || busy === open.id} onClick={() => pdf(open, false)} data-testid="zt-view-pdf"><Eye size={14} /> PDF ansehen</AdminButton>
              <AdminButton variant="secondary" disabled={!open.pdf_available || busy === open.id} onClick={() => pdf(open, true)}><Download size={14} /> Herunterladen</AdminButton>
              {!open.pdf_available && <p className="text-xs text-[var(--admin-text-muted)]">Für dieses Zertifikat wurde noch keine PDF-Datei erzeugt.</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
