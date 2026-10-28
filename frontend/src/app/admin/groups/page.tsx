"use client";

import { useState } from "react";
import Link from "next/link";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader, AdminSelect } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { getAdminStats, getAllGroups, getGroupOptions, LEVELS, updateGroup, type GroupStatus } from "@/features/groups/groups-service";

const STATUS_LABEL: Record<string, string> = { active: "Aktiv", paused: "Pausiert", archived: "Archiviert", blocked: "Gesperrt" };
const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—");

type Filters = { search?: string; level?: string; status?: string; teacher_id?: string; course_id?: string; created_from?: string; created_to?: string; page: number };

/** Admin -> Gruppen: every group with server-side filters, statistics and the
 *  administrator-only actions (block / unblock, archive). A group itself is
 *  opened in the Teacher Panel view, where a SUPER_ADMIN has full access. */
export default function AdminGroupsPage() {
  const qc = useQueryClient();
  const [f, setF] = useState<Filters>({ page: 1 });
  const set = (p: Partial<Filters>) => setF((cur) => ({ ...cur, ...p, page: p.page ?? 1 }));
  const list = useQuery({ queryKey: ["admin", "groups", f], queryFn: () => getAllGroups(f), placeholderData: keepPreviousData });
  const stats = useQuery({ queryKey: ["admin", "groups", "stats"], queryFn: getAdminStats });
  const options = useQuery({ queryKey: ["groups", "options"], queryFn: getGroupOptions });
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  async function setStatus(id: string, status: GroupStatus) {
    setBusy(id);
    setMsg(null);
    try {
      await updateGroup(id, { status });
      await qc.invalidateQueries({ queryKey: ["admin", "groups"] });
      setMsg({ ok: true, text: `Status: ${STATUS_LABEL[status]}` });
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Aktion fehlgeschlagen.") });
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6" data-testid="admin-groups">
      <AdminPageHeader title="Gruppen / Guruhlar" description="Alle Lerngruppen, ihre Lehrkräfte und Aktivität. Gruppen werden archiviert, nie gelöscht." />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {[["Gruppen", stats.data?.groups], ["Aktiv", stats.data?.by_status?.active ?? 0], ["Schüler", stats.data?.students], ["Lehrkräfte", stats.data?.teachers], ["Nachrichten (7 T.)", stats.data?.messages_7d]].map(([label, value]) => (
          <AdminCard key={label as string}><p className="text-xs text-[var(--admin-text-muted)]">{label}</p><p className="text-2xl font-bold text-[var(--admin-text-primary)]">{value ?? "—"}</p></AdminCard>
        ))}
      </div>

      <AdminCard>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div><AdminLabel>Suche</AdminLabel><AdminInput placeholder="Gruppenname" value={f.search ?? ""} onChange={(e) => set({ search: e.target.value || undefined })} /></div>
          <div><AdminLabel>Lehrkraft</AdminLabel>
            <AdminSelect value={f.teacher_id ?? ""} onChange={(e) => set({ teacher_id: e.target.value || undefined })}>
              <option value="">Alle</option>{(options.data?.teachers ?? []).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </AdminSelect></div>
          <div><AdminLabel>Niveau</AdminLabel>
            <AdminSelect value={f.level ?? ""} onChange={(e) => set({ level: e.target.value || undefined })}>
              <option value="">Alle</option>{LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
            </AdminSelect></div>
          <div><AdminLabel>Status</AdminLabel>
            <AdminSelect value={f.status ?? ""} onChange={(e) => set({ status: e.target.value || undefined })}>
              <option value="">Alle</option>{Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </AdminSelect></div>
          <div><AdminLabel>Kurs</AdminLabel>
            <AdminSelect value={f.course_id ?? ""} onChange={(e) => set({ course_id: e.target.value || undefined })}>
              <option value="">Alle</option>{(options.data?.courses ?? []).map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </AdminSelect></div>
          <div><AdminLabel>Erstellt ab</AdminLabel><AdminInput type="date" value={f.created_from ?? ""} onChange={(e) => set({ created_from: e.target.value || undefined })} /></div>
          <div><AdminLabel>Erstellt bis</AdminLabel><AdminInput type="date" value={f.created_to ?? ""} onChange={(e) => set({ created_to: e.target.value || undefined })} /></div>
          <div className="flex items-end"><Link href="/teacher/groups" className="text-sm font-semibold text-[var(--admin-primary)]">+ Neue Gruppe (Lehrer-Ansicht)</Link></div>
        </div>
      </AdminCard>

      {msg && <p role="status" className={`text-sm ${msg.ok ? "text-[var(--admin-success)]" : "text-[var(--admin-danger)]"}`}>{msg.text}</p>}

      <AdminCard className="overflow-x-auto p-0">
        {list.isLoading ? <div className="p-6"><Loader2 className="animate-spin text-[var(--admin-text-muted)]" /></div> : list.isError ? (
          <p className="p-6 text-sm text-[var(--admin-danger)]">{apiErrorMessage(list.error, "Konnte nicht geladen werden (Super-Admin nötig).")}</p>
        ) : (list.data?.items ?? []).length === 0 ? <p className="p-6 text-sm text-[var(--admin-text-muted)]">Keine Gruppen.</p> : (
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr className="border-b border-[var(--admin-border)]">{["Gruppe", "Lehrkraft", "Niveau", "Schüler", "Code", "Status", "Beginn", "Letzte Aktivität", "Aktionen"].map((h) => <th key={h} className="px-3 py-2.5">{h}</th>)}</tr>
            </thead>
            <tbody>
              {list.data!.items.map((g) => (
                <tr key={g.id} className="border-b border-[var(--admin-border)] last:border-0">
                  <td className="max-w-[220px] px-3 py-2.5"><Link href={`/teacher/groups/${g.id}`} className="font-semibold text-[var(--admin-text-primary)] hover:underline">{g.name}</Link>
                    <p className="truncate text-xs text-[var(--admin-text-muted)]">{g.courses.map((c) => c.title).join(", ") || "kein Kurs"}</p></td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{g.teacher.name}</td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{g.level}</td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{g.student_count}{g.capacity ? `/${g.capacity}` : ""}</td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{g.code ? `${g.code.usable ? "aktiv" : "nicht nutzbar"} · ${g.code.use_count}×` : "—"}</td>
                  <td className="px-3 py-2.5 text-xs font-semibold text-[var(--admin-text-primary)]">{STATUS_LABEL[g.status]}</td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{g.start_date ?? "—"}</td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{fmt(g.last_activity_at)}</td>
                  <td className="px-3 py-2.5">
                    <div className="flex flex-wrap gap-1.5">
                      {g.status === "blocked" ? (
                        <AdminButton size="sm" variant="secondary" disabled={busy === g.id} onClick={() => setStatus(g.id, "active")}>Entsperren</AdminButton>
                      ) : (
                        <AdminButton size="sm" variant="secondary" disabled={busy === g.id} onClick={() => window.confirm(`„${g.name}" sperren?`) && setStatus(g.id, "blocked")}>Sperren</AdminButton>
                      )}
                      {g.status !== "archived" && (
                        <AdminButton size="sm" variant="secondary" disabled={busy === g.id} onClick={() => window.confirm(`„${g.name}" archivieren?`) && setStatus(g.id, "archived")}>Archivieren</AdminButton>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {pages > 1 && (
          <div className="flex items-center gap-2 p-3 text-sm text-[var(--admin-text-secondary)]">
            <AdminButton size="sm" variant="secondary" disabled={f.page <= 1} onClick={() => set({ page: f.page - 1 })}>Zurück</AdminButton>
            Seite {f.page} / {pages}
            <AdminButton size="sm" variant="secondary" disabled={f.page >= pages} onClick={() => set({ page: f.page + 1 })}>Weiter</AdminButton>
          </div>
        )}
      </AdminCard>
    </div>
  );
}
