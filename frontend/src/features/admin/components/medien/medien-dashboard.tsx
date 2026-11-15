"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Check, Clapperboard, Music, Undo2, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import { decidePurchase, getPurchases, getStats, grantAccess, listItems, medienError, type Kind, type PurchaseRow } from "@/features/admin/services/medien-admin-service";

import { MedienTabs } from "./shared";

const KIND_DE: Record<Kind, string> = { BOOK: "Buch", SONG: "Song", FILM: "Film" };
const PURCHASE_DE: Record<string, string> = { REQUESTED: "Angefragt", GRANTED: "Freigeschaltet", REJECTED: "Abgelehnt", REVOKED: "Entzogen" };

function Stat({ label, value, testId }: { label: string; value: number | string; testId: string }) {
  return <div className="rounded-xl bg-[var(--admin-hover)] p-4" data-testid={testId}><p className="text-2xl font-extrabold text-[var(--admin-text-primary)]">{value}</p><p className="text-xs text-[var(--admin-text-muted)]">{label}</p></div>;
}

function Top({ title, rows, unit }: { title: string; rows: { id: string; title: string; views?: number; plays?: number }[]; unit: string }) {
  return (
    <AdminCard>
      <h3 className="mb-2 text-sm font-semibold text-[var(--admin-text-primary)]">{title}</h3>
      {rows.length ? <ol className="space-y-1 text-sm">{rows.map((r, i) => <li key={r.id} className="flex justify-between gap-3"><span className="truncate">{i + 1}. {r.title}</span><span className="shrink-0 text-[var(--admin-text-muted)]">{r.views ?? r.plays} {unit}</span></li>)}</ol>
        : <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Daten.</p>}
    </AdminCard>
  );
}

function Purchases() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("REQUESTED");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [grant, setGrant] = useState({ kind: "BOOK" as Kind, content_id: "", email: "" });
  const rows = useQuery({ queryKey: ["admin-medien-purchases", filter], queryFn: () => getPurchases(filter || undefined), retry: false });
  const paid = useQuery({ queryKey: ["admin-medien-paid", grant.kind], queryFn: () => listItems(grant.kind, { access: "PAID", page_size: 100 }), enabled: !rows.isError });
  const refresh = () => { void queryClient.invalidateQueries({ queryKey: ["admin-medien-purchases"] }); void queryClient.invalidateQueries({ queryKey: ["admin-medien-stats"] }); };
  const decide = useMutation({ mutationFn: (v: { id: string; status: "GRANTED" | "REJECTED" | "REVOKED" }) => decidePurchase(v.id, v.status), onSuccess: () => { setMsg({ ok: true, text: "Entscheidung gespeichert." }); refresh(); }, onError: (e) => setMsg({ ok: false, text: medienError(e) }) });
  const direct = useMutation({ mutationFn: () => grantAccess({ ...grant, email: grant.email.trim().toLowerCase() }), onSuccess: () => { setMsg({ ok: true, text: "Zugang freigeschaltet." }); setGrant({ ...grant, email: "" }); refresh(); }, onError: (e) => setMsg({ ok: false, text: medienError(e) }) });

  if (rows.isError) return <AdminCard><h2 className="mb-1 text-sm font-semibold text-[var(--admin-text-primary)]">Kaufanfragen</h2><p className="text-sm text-[var(--admin-text-muted)]" data-testid="purchases-forbidden">Kaufanfragen und Freischaltungen sind dem Super Admin vorbehalten.</p></AdminCard>;
  return (
    <div data-testid="purchases"><AdminCard>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-[var(--admin-text-primary)]">Kaufanfragen & Freischaltungen</h2>
        <AdminSelect className="w-48" value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Status" data-testid="purchases-filter"><option value="">Alle</option>{Object.entries(PURCHASE_DE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</AdminSelect>
      </div>
      {msg && <p role="status" className={`mb-3 text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`} data-testid="purchases-message">{msg.text}</p>}
      <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm" data-testid="purchases-table">
        <thead><tr className="text-xs uppercase text-[var(--admin-text-muted)]"><th className="py-2">Student</th><th>Inhalt</th><th>Preis</th><th>Status</th><th className="text-right">Aktion</th></tr></thead>
        <tbody>
          {(rows.data ?? []).map((p: PurchaseRow) => (
            <tr key={p.id} className="border-t border-[var(--admin-border)]" data-testid="purchase-row" data-status={p.status}>
              <td className="py-2">{p.user_email}</td><td>{KIND_DE[p.kind]}: {p.title ?? "—"}</td><td>{p.price ? `${new Intl.NumberFormat("de-DE").format(p.price)} UZS` : "—"}</td><td>{PURCHASE_DE[p.status] ?? p.status}</td>
              <td><div className="flex justify-end gap-1">
                {p.status === "REQUESTED" && <><AdminButton size="sm" onClick={() => decide.mutate({ id: p.id, status: "GRANTED" })} data-testid="purchase-grant"><Check size={13} /> Freischalten</AdminButton><AdminButton size="sm" variant="danger" onClick={() => decide.mutate({ id: p.id, status: "REJECTED" })} data-testid="purchase-reject"><X size={13} /> Ablehnen</AdminButton></>}
                {p.status === "GRANTED" && <AdminButton size="sm" variant="secondary" onClick={() => decide.mutate({ id: p.id, status: "REVOKED" })} data-testid="purchase-revoke"><Undo2 size={13} /> Entziehen</AdminButton>}
              </div></td>
            </tr>
          ))}
          {rows.data && !rows.data.length && <tr><td colSpan={5} className="py-6 text-center text-[var(--admin-text-muted)]">Keine Einträge.</td></tr>}
        </tbody>
      </table></div>
      <form className="mt-4 grid gap-2 rounded-xl bg-[var(--admin-hover)] p-3 sm:grid-cols-[8rem_1fr_1fr_auto]" onSubmit={(e) => { e.preventDefault(); if (grant.content_id && grant.email) direct.mutate(); }} data-testid="grant-form">
        <div><AdminLabel>Art</AdminLabel><AdminSelect value={grant.kind} onChange={(e) => setGrant({ kind: e.target.value as Kind, content_id: "", email: grant.email })} data-testid="grant-kind"><option value="BOOK">Buch</option><option value="SONG">Song</option><option value="FILM">Film</option></AdminSelect></div>
        <div><AdminLabel>Kostenpflichtiger Inhalt</AdminLabel><AdminSelect value={grant.content_id} onChange={(e) => setGrant({ ...grant, content_id: e.target.value })} data-testid="grant-content"><option value="">Wählen …</option>{(paid.data?.items ?? []).map((i) => <option key={i.id} value={i.id}>{i.title}</option>)}</AdminSelect></div>
        <div><AdminLabel>E-Mail des Studenten</AdminLabel><AdminInput type="email" value={grant.email} onChange={(e) => setGrant({ ...grant, email: e.target.value })} placeholder="name@example.com" data-testid="grant-email" /></div>
        <div className="flex items-end"><AdminButton disabled={!grant.content_id || !grant.email || direct.isPending} data-testid="grant-submit">Direkt freischalten</AdminButton></div>
      </form>
    </AdminCard></div>
  );
}

/** Admin → Medien: real statistics (from the database), the three management pages and the purchase requests. */
export default function MedienDashboard() {
  const { data } = useQuery({ queryKey: ["admin-medien-stats"], queryFn: getStats });
  const s = data;
  return (
    <div className="space-y-6" data-testid="medien-dashboard">
      <AdminPageHeader title="Medien" description="VIZU Medienwelt: Bibliothek, Musik und Filme verwalten." />
      <MedienTabs />
      <div className="grid gap-4 md:grid-cols-3">
        {([["/admin/medien/bibliothek", "Bibliothek", BookOpen, s ? `${s.books.total} Bücher` : "…"], ["/admin/medien/musik", "Musik", Music, s ? `${s.songs.total} Songs` : "…"], ["/admin/medien/filme", "Filme", Clapperboard, s ? `${s.films.total} Filme` : "…"]] as const).map(([href, label, Icon, sub]) => (
          <Link key={href} href={href} className="flex items-center gap-3 rounded-2xl bg-[var(--admin-card)] p-5 shadow-[var(--admin-shadow-card)] ring-1 ring-[var(--admin-border)] transition hover:ring-[var(--admin-primary)]"><Icon size={26} className="text-[var(--admin-primary)]" /><span><span className="block font-semibold text-[var(--admin-text-primary)]">{label}</span><span className="text-xs text-[var(--admin-text-muted)]">{sub}</span></span></Link>
        ))}
      </div>
      {s && (
        <AdminCard>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5" data-testid="medien-stats">
            <Stat label="Bücher gesamt" value={s.books.total} testId="stat-books" /><Stat label="Kostenlose Bücher" value={s.books.free} testId="stat-books-free" /><Stat label="Kostenpflichtige Bücher" value={s.books.paid} testId="stat-books-paid" />
            <Stat label="Songs gesamt" value={s.songs.total} testId="stat-songs" /><Stat label="Playlists (VIZU)" value={s.songs.playlists} testId="stat-playlists" /><Stat label="Playlists (Studenten)" value={s.songs.student_playlists} testId="stat-student-playlists" />
            <Stat label="Filme gesamt" value={s.films.total} testId="stat-films" /><Stat label="Veröffentlicht" value={s.published} testId="stat-published" /><Stat label="Entwurf / ausgeblendet" value={s.draft} testId="stat-draft" />
            <Stat label="Offene Kaufanfragen" value={s.pending_purchases} testId="stat-pending" />
            <Link href="/admin/medien/bibliothek" className="rounded-xl bg-[var(--admin-hover)] p-4 transition hover:ring-1 hover:ring-[var(--admin-primary)]" data-testid="stat-pending-payments">
              <p className="text-2xl font-extrabold text-[var(--admin-text-primary)]">{s.pending_book_payments}</p><p className="text-xs text-[var(--admin-text-muted)]">Offene Buch-Zahlungen (prüfen →)</p>
            </Link>
          </div>
        </AdminCard>
      )}
      {s && <div className="grid gap-4 md:grid-cols-3" data-testid="medien-top">
        <Top title="Meistgelesene Bücher" rows={s.most_read_books} unit="Aufrufe" /><Top title="Meistgehörte Songs" rows={s.most_played_songs} unit="Wiedergaben" /><Top title="Meistgesehene Filme" rows={s.most_watched_films} unit="Aufrufe" />
      </div>}
      <Purchases />
    </div>
  );
}
