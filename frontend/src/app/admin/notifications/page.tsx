"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, EyeOff, Loader2, Pencil, Plus, Send, X } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import InternalRoutePicker from "@/features/admin/advertisements/internal-route-picker";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  archiveBroadcast,
  createBroadcast,
  deactivateBroadcast,
  getBroadcastMeta,
  listBroadcasts,
  publishBroadcast,
  resolveStudent,
  updateBroadcast,
  type AdminBroadcast,
  type BroadcastPayload,
} from "@/features/admin/services/notifications-admin-service";

const TYPE_LABEL: Record<string, string> = { INFO: "Info", SUCCESS: "Success", WARNING: "Warning", ANNOUNCEMENT: "Announcement" };
const AUD_LABEL: Record<string, string> = { ALL: "Alle Studenten", LEVEL: "Niveau / Kurs", LANGUAGE: "Sprache (de / uz)", USER: "Ein Student" };
const STATE_LABEL: Record<string, string> = { DRAFT: "Entwurf", PUBLISHED: "Veröffentlicht", SCHEDULED: "Geplant", INACTIVE: "Deaktiviert", ARCHIVED: "Archiviert" };

type Form = Required<Pick<BroadcastPayload, "title_de" | "title_uz" | "message_de" | "message_uz" | "type" | "audience_type" | "link_type" | "is_important">> & {
  audience_value: string; student_query: string; internal_route: string; internal_params: Record<string, string>; external_url: string;
};
const EMPTY: Form = { title_de: "", title_uz: "", message_de: "", message_uz: "", type: "INFO", audience_type: "ALL", audience_value: "", student_query: "",
  link_type: "NONE", internal_route: "", internal_params: {}, external_url: "", is_important: false };

function audienceText(b: AdminBroadcast) {
  if (b.audience_type === "USER") return b.audience_student ? `${b.audience_student.name} (${b.audience_student.email})` : "Ein Student";
  return b.audience_value ? `${AUD_LABEL[b.audience_type]}: ${b.audience_value}` : AUD_LABEL[b.audience_type];
}

/** Admin -> Notifications: create, edit (until published), publish now or
 * scheduled (with confirmation), deactivate, archive; recipients / reads. */
export default function NotificationsAdminPage() {
  const qc = useQueryClient();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const meta = useQuery({ queryKey: ["admin", "broadcast-meta"], queryFn: getBroadcastMeta });
  const list = useQuery({ queryKey: ["admin", "broadcasts", status, page], queryFn: () => listBroadcasts(status, page) });
  const [editing, setEditing] = useState<AdminBroadcast | "new" | null>(null);
  const [form, setForm] = useState<Form>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [publishing, setPublishing] = useState<{ item: AdminBroadcast; at: string } | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const set = (p: Partial<Form>) => setForm((f) => ({ ...f, ...p }));
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin", "broadcasts"] });

  function openEdit(b: AdminBroadcast | "new") {
    setMsg(null);
    if (b === "new") setForm({ ...EMPTY, audience_type: (meta.data?.audiences[0] as Form["audience_type"]) ?? "ALL" });
    else setForm({ title_de: b.title_de, title_uz: b.title_uz, message_de: b.message_de, message_uz: b.message_uz, type: b.type, audience_type: b.audience_type,
      audience_value: b.audience_value ?? "", student_query: b.audience_student?.email ?? "", link_type: b.link_type, internal_route: b.internal_route ?? "",
      internal_params: b.internal_params ?? {}, external_url: b.external_url ?? "", is_important: b.is_important });
    setEditing(b);
  }

  async function save() {
    setSaving(true);
    setMsg(null);
    try {
      let audienceValue: string | null = form.audience_value || null;
      if (form.audience_type === "USER") audienceValue = (await resolveStudent(form.student_query.trim())).id;
      const payload: BroadcastPayload = {
        title_de: form.title_de, title_uz: form.title_uz, message_de: form.message_de, message_uz: form.message_uz, type: form.type,
        audience_type: form.audience_type, audience_value: form.audience_type === "ALL" ? null : audienceValue, link_type: form.link_type,
        internal_route: form.link_type === "INTERNAL" ? form.internal_route : null, internal_params: form.link_type === "INTERNAL" ? form.internal_params : null,
        external_url: form.link_type === "EXTERNAL" ? form.external_url.trim() : null, is_important: form.is_important,
      };
      if (editing === "new") await createBroadcast(payload);
      else if (editing) await updateBroadcast(editing.id, payload);
      setMsg({ ok: true, text: "Gespeichert (Entwurf). Jetzt veröffentlichen oder planen." });
      setEditing(null);
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setSaving(false);
    }
  }

  async function run(action: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await action();
      setMsg({ ok: true, text: ok });
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Aktion fehlgeschlagen.") });
    }
  }

  const items = list.data?.items ?? [];
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  return (
    <div className="space-y-6" data-testid="admin-notifications">
      <AdminPageHeader title="Notifications" description="Benachrichtigungen an Studenten (Glocke im Studentenpanel). Text in Deutsch und Usbekisch, ohne HTML." />

      <AdminCard>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-48">
            <AdminLabel>Status</AdminLabel>
            <AdminSelect value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">Alle</option>
              {["DRAFT", "PUBLISHED", "INACTIVE", "ARCHIVED"].map((s) => <option key={s} value={s}>{STATE_LABEL[s]}</option>)}
            </AdminSelect>
          </div>
          <AdminButton onClick={() => openEdit("new")} data-testid="ntf-new"><Plus size={14} /> Neue Benachrichtigung</AdminButton>
        </div>
      </AdminCard>

      {msg && <p role="status" className={`rounded-xl px-4 py-3 text-sm ${msg.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>{msg.text}</p>}

      {editing !== null && (
        <AdminCard>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{editing === "new" ? "Neue Benachrichtigung" : "Benachrichtigung bearbeiten"}</h3>
            <button type="button" onClick={() => setEditing(null)} aria-label="Schließen" className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5"><X size={16} /></button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div><AdminLabel>Titel (de)</AdminLabel><AdminInput value={form.title_de} maxLength={160} onChange={(e) => set({ title_de: e.target.value })} /></div>
            <div><AdminLabel>Sarlavha (uz)</AdminLabel><AdminInput value={form.title_uz} maxLength={160} onChange={(e) => set({ title_uz: e.target.value })} /></div>
            <div><AdminLabel>Text (de)</AdminLabel><AdminTextarea rows={4} maxLength={2000} value={form.message_de} onChange={(e) => set({ message_de: e.target.value })} /></div>
            <div><AdminLabel>Matn (uz)</AdminLabel><AdminTextarea rows={4} maxLength={2000} value={form.message_uz} onChange={(e) => set({ message_uz: e.target.value })} /></div>
            <div>
              <AdminLabel>Typ</AdminLabel>
              <AdminSelect value={form.type} onChange={(e) => set({ type: e.target.value as Form["type"] })}>
                {(meta.data?.types ?? Object.keys(TYPE_LABEL)).map((x) => <option key={x} value={x}>{TYPE_LABEL[x] ?? x}</option>)}
              </AdminSelect>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <AdminLabel>Empfänger</AdminLabel>
                <AdminSelect value={form.audience_type} onChange={(e) => set({ audience_type: e.target.value as Form["audience_type"], audience_value: "" })} data-testid="ntf-audience">
                  {(meta.data?.audiences ?? ["USER"]).map((a) => <option key={a} value={a}>{AUD_LABEL[a]}</option>)}
                </AdminSelect>
              </div>
              {form.audience_type === "LEVEL" && (
                <div><AdminLabel>Niveau</AdminLabel>
                  <AdminSelect value={form.audience_value} onChange={(e) => set({ audience_value: e.target.value })}>
                    <option value="">—</option>{(meta.data?.levels ?? []).map((l) => <option key={l} value={l}>{l}</option>)}
                  </AdminSelect></div>
              )}
              {form.audience_type === "LANGUAGE" && (
                <div><AdminLabel>Sprache</AdminLabel>
                  <AdminSelect value={form.audience_value} onChange={(e) => set({ audience_value: e.target.value })}>
                    <option value="">—</option>{(meta.data?.languages ?? []).map((l) => <option key={l} value={l}>{l}</option>)}
                  </AdminSelect></div>
              )}
              {form.audience_type === "USER" && (
                <div><AdminLabel>E-Mail des Studenten</AdminLabel><AdminInput value={form.student_query} onChange={(e) => set({ student_query: e.target.value })} placeholder="name@example.com" /></div>
              )}
            </div>
            <div className="md:col-span-2">
              <AdminLabel>Link</AdminLabel>
              <div className="mb-3 flex flex-wrap gap-2">
                {([["NONE", "Kein Link"], ["INTERNAL", "Seite im Studentenpanel"], ["EXTERNAL", "Externer Link (http/https)"]] as const).map(([k, l]) => (
                  <button key={k} type="button" onClick={() => set({ link_type: k })}
                          className={`rounded-lg px-3 py-2 text-sm font-semibold ring-1 ${form.link_type === k ? "bg-[var(--admin-primary)] text-white ring-[var(--admin-primary)]" : "text-[var(--admin-text-secondary)] ring-[var(--admin-border-strong)]"}`}>{l}</button>
                ))}
              </div>
              {form.link_type === "INTERNAL" && (
                <InternalRoutePicker routes={meta.data?.internal_routes ?? []} value={form.internal_route} params={form.internal_params}
                                     onChange={(route, params) => set({ internal_route: route, internal_params: params })} />
              )}
              {form.link_type === "EXTERNAL" && <AdminInput type="url" placeholder="https://" value={form.external_url} onChange={(e) => set({ external_url: e.target.value })} />}
            </div>
            <label className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]">
              <AdminCheckbox checked={form.is_important} onCheckedChange={(v) => set({ is_important: Boolean(v) })} /> Wichtig (hervorgehoben)
            </label>
            <div className="flex gap-2 md:col-span-2">
              <AdminButton onClick={save} disabled={saving} data-testid="ntf-save">{saving && <Loader2 size={14} className="animate-spin" />} Als Entwurf speichern</AdminButton>
              <AdminButton variant="ghost" onClick={() => setEditing(null)}>Abbrechen</AdminButton>
            </div>
          </div>
        </AdminCard>
      )}

      {publishing && (
        <AdminCard>
          <h3 className="mb-3 text-sm font-semibold text-[var(--admin-text-primary)]">Veröffentlichen: {publishing.item.title_de}</h3>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <AdminLabel>Zeitpunkt (leer = sofort)</AdminLabel>
              <AdminInput type="datetime-local" value={publishing.at} onChange={(e) => setPublishing({ ...publishing, at: e.target.value })} />
            </div>
            <AdminButton onClick={() => setConfirmOpen(true)} data-testid="ntf-publish-confirm"><Send size={14} /> Veröffentlichen …</AdminButton>
            <AdminButton variant="ghost" onClick={() => setPublishing(null)}>Abbrechen</AdminButton>
          </div>
        </AdminCard>
      )}
      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={publishing?.item.is_important ? "Wichtige Benachrichtigung veröffentlichen?" : "Benachrichtigung veröffentlichen?"}
        description={publishing ? `Empfänger: ${audienceText(publishing.item)} (${publishing.item.recipients ?? "?"} Studenten). ${publishing.at ? `Geplant für ${new Date(publishing.at).toLocaleString("de-DE")}.` : "Sofort sichtbar."}` : ""}
        onConfirm={async () => {
          const p = publishing;
          if (!p) return;
          await run(() => publishBroadcast(p.item.id, p.at ? new Date(p.at).toISOString() : null, true), p.at ? "Geplant." : "Veröffentlicht.");
          setConfirmOpen(false);
          setPublishing(null);
        }}
      />

      <AdminCard className="overflow-x-auto p-0">
        {list.isLoading ? <div className="p-6"><Loader2 className="animate-spin text-[var(--admin-text-muted)]" /></div> : list.isError ? (
          <p className="p-6 text-sm text-[var(--admin-danger)]">{apiErrorMessage(list.error, "Konnte nicht geladen werden.")}</p>
        ) : items.length === 0 ? <p className="p-6 text-sm text-[var(--admin-text-muted)]">Noch keine Benachrichtigungen.</p> : (
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr className="border-b border-[var(--admin-border)]">{["Titel", "Typ", "Empfänger", "Status", "Gelesen", ""].map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr>
            </thead>
            <tbody>
              {items.map((b) => (
                <tr key={b.id} className="border-b border-[var(--admin-border)] last:border-0" data-testid="ntf-row">
                  <td className="max-w-[280px] px-4 py-3"><p className="truncate font-semibold text-[var(--admin-text-primary)]">{b.title_de}</p><p className="truncate text-xs text-[var(--admin-text-muted)]">{b.title_uz}</p></td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{TYPE_LABEL[b.type]}{b.is_important ? " · wichtig" : ""}</td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{audienceText(b)}</td>
                  <td className="px-4 py-3 text-xs">
                    <span className="font-semibold text-[var(--admin-text-primary)]">{STATE_LABEL[b.state] ?? b.state}</span>
                    {b.publish_at && <span className="block text-[var(--admin-text-muted)]">{new Date(b.publish_at).toLocaleString("de-DE")}</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{b.reads} / {b.recipients ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {b.editable && <AdminButton size="sm" variant="secondary" onClick={() => openEdit(b)} aria-label="Bearbeiten"><Pencil size={13} /></AdminButton>}
                      {b.status !== "ARCHIVED" && b.state !== "PUBLISHED" && (
                        <AdminButton size="sm" onClick={() => setPublishing({ item: b, at: "" })} data-testid="ntf-publish"><Send size={13} /> Veröffentlichen</AdminButton>
                      )}
                      {(b.status === "PUBLISHED") && <AdminButton size="sm" variant="secondary" onClick={() => run(() => deactivateBroadcast(b.id), "Deaktiviert.")} aria-label="Deaktivieren"><EyeOff size={13} /></AdminButton>}
                      {b.status !== "ARCHIVED" && <AdminButton size="sm" variant="ghost" onClick={() => run(() => archiveBroadcast(b.id), "Archiviert.")} aria-label="Archivieren"><Archive size={13} /></AdminButton>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </AdminCard>
      {pages > 1 && (
        <div className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
          <AdminButton size="sm" variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Zurück</AdminButton>
          Seite {page} / {pages}
          <AdminButton size="sm" variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Weiter</AdminButton>
        </div>
      )}
    </div>
  );
}
