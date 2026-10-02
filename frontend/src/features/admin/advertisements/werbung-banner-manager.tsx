"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { BarChart3, Eye, EyeOff, Loader2, Megaphone, Pencil, Plus, Trash2, X } from "lucide-react";

import {
  AdminButton,
  AdminCard,
  AdminCheckbox,
  AdminInput,
  AdminLabel,
  AdminTextarea,
} from "@/components/admin/admin-ui";
import AdminEmptySection from "@/components/admin/admin-empty-section";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FileUploadField from "@/components/admin/file-upload-field";
import AdvertisementBannerView from "@/components/dashboard/home/advertisement-banner-view";
import { resolveMediaUrl } from "@/lib/media";

import {
  createAdvertisement,
  deleteAdvertisement,
  getAdvertisementAnalytics,
  listAdvertisements,
  setAdvertisementActive,
  parseAdvertisementApiError,
  updateAdvertisement,
  type AdminAdvertisement,
  type AdvertisementFieldError,
} from "./advertisement-admin-service";
import {
  ADVERTISEMENT_FIELD_LABELS,
  EMPTY_ADVERTISEMENT_FORM,
  buildAdvertisementPayload,
  isoToLocalInput,
  type AdvertisementFormState,
} from "./advertisement-payload";

const QUERY_KEY = ["admin-advertisements"];

function formatRange(ad: AdminAdvertisement): string {
  const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("de-DE") : null);
  const start = fmt(ad.starts_at);
  const end = fmt(ad.ends_at);
  if (!start && !end) return "Unbegrenzt";
  return `${start ?? "sofort"} – ${end ?? "offen"}`;
}

/** Turns a failed save into messages for the admin. The full backend
 * response (which field failed and why) is always logged for developers. */
function saveErrors(error: unknown): AdvertisementFieldError[] {
  const parsed = parseAdvertisementApiError(error);
  console.error("[Werbung-Banner] Speichern fehlgeschlagen", {
    status: parsed.status,
    fieldErrors: parsed.fieldErrors,
    message: parsed.message,
    response: (error as { response?: { data?: unknown } }).response?.data,
  });
  if (parsed.fieldErrors.length) return parsed.fieldErrors;
  if (parsed.status === 403) return [{ field: "", message: "Keine Berechtigung, Werbung zu verwalten." }];
  if (parsed.message) return [{ field: "", message: parsed.message }];
  return [{ field: "", message: "Speichern fehlgeschlagen. Bitte später erneut versuchen." }];
}

const numberFmt = new Intl.NumberFormat("de-DE");

/** Admin → Werbung-Banner: create / edit (with live "Vorschau" of the real
 * dashboard banner), activate / deactivate / delete, and real analytics
 * (impressions, clicks, CTR, today / week, impressions vs. clicks chart). */
export default function WerbungBannerManager() {
  const queryClient = useQueryClient();
  const { data: ads, isLoading, isError } = useQuery({ queryKey: QUERY_KEY, queryFn: listAdvertisements, retry: false });

  const [editing, setEditing] = useState<AdminAdvertisement | "new" | null>(null);
  const [form, setForm] = useState<AdvertisementFormState>(EMPTY_ADVERTISEMENT_FORM);
  const [errors, setErrors] = useState<AdvertisementFieldError[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<AdminAdvertisement | null>(null);
  const [analyticsFor, setAnalyticsFor] = useState<AdminAdvertisement | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: QUERY_KEY });

  const saveMutation = useMutation({
    mutationFn: (payload: Parameters<typeof createAdvertisement>[0]) =>
      editing === "new" ? createAdvertisement(payload) : updateAdvertisement((editing as AdminAdvertisement).id, payload),
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
    onError: (e) => setErrors(saveErrors(e)),
  });

  const toggleMutation = useMutation({
    mutationFn: (ad: AdminAdvertisement) => setAdvertisementActive(ad.id, !ad.is_active),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteAdvertisement(deleteTarget!.id),
    onSuccess: () => {
      if (analyticsFor?.id === deleteTarget?.id) setAnalyticsFor(null);
      setDeleteTarget(null);
      invalidate();
    },
  });

  function save() {
    const result = buildAdvertisementPayload(form);
    if (!result.ok) {
      setErrors(result.errors);
      return;
    }
    setErrors([]);
    saveMutation.mutate(result.payload);
  }

  function openNew() {
    setErrors([]);
    setForm(EMPTY_ADVERTISEMENT_FORM);
    setEditing("new");
  }

  function openEdit(ad: AdminAdvertisement) {
    setErrors([]);
    setForm({
      title: ad.title,
      description: ad.description ?? "",
      image_url: ad.image_url,
      target_url: ad.target_url,
      cta_text: ad.cta_text,
      is_active: ad.is_active,
      priority: ad.priority,
      starts_at: isoToLocalInput(ad.starts_at),
      ends_at: isoToLocalInput(ad.ends_at),
    });
    setEditing(ad);
  }

  return (
    <div className="space-y-6">
      <AdminCard>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-2xl text-sm text-[var(--admin-text-secondary)]">
            Das Banner oben im Studenten-Dashboard. Von allen aktiven Werbungen im gültigen Zeitraum wird die mit der höchsten
            Priorität angezeigt. Aufrufe und Klicks werden real gezählt.
          </p>
          <AdminButton onClick={openNew}>
            <Plus size={15} />
            Neue Werbung
          </AdminButton>
        </div>
      </AdminCard>

      <AnimatePresence>
        {editing !== null && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <AdminCard>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">
                  {editing === "new" ? "Neue Werbung" : "Werbung bearbeiten"}
                </h3>
                <button
                  type="button"
                  onClick={() => setEditing(null)}
                  aria-label="Schließen"
                  className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="grid gap-6 xl:grid-cols-2">
                <div className="space-y-4">
                  <div>
                    <AdminLabel>Titel</AdminLabel>
                    <AdminInput value={form.title} maxLength={160} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                  </div>
                  <div>
                    <AdminLabel>Beschreibung (optional)</AdminLabel>
                    <AdminTextarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                  </div>
                  <FileUploadField
                    label="Bild"
                    value={form.image_url}
                    onChange={(url) => setForm({ ...form, image_url: url })}
                    folder="images"
                    accept="image/*"
                  />
                  {form.image_url && (
                    <button
                      type="button"
                      className="text-xs text-[var(--admin-text-secondary)] underline"
                      onClick={() => setForm({ ...form, image_url: null })}
                    >
                      Bild entfernen
                    </button>
                  )}
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <AdminLabel>Link (https://…)</AdminLabel>
                      <AdminInput
                        type="url"
                        placeholder="https://"
                        value={form.target_url}
                        onChange={(e) => setForm({ ...form, target_url: e.target.value })}
                      />
                    </div>
                    <div>
                      <AdminLabel>CTA-Text</AdminLabel>
                      <AdminInput value={form.cta_text} maxLength={60} onChange={(e) => setForm({ ...form, cta_text: e.target.value })} />
                    </div>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div>
                      <AdminLabel>Startdatum</AdminLabel>
                      <AdminInput type="datetime-local" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })} />
                    </div>
                    <div>
                      <AdminLabel>Enddatum</AdminLabel>
                      <AdminInput type="datetime-local" value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })} />
                    </div>
                    <div>
                      <AdminLabel>Priorität</AdminLabel>
                      <AdminInput
                        type="number"
                        step={1}
                        inputMode="numeric"
                        value={form.priority}
                        onChange={(e) => {
                          const value = Number.parseInt(e.target.value, 10);
                          setForm({ ...form, priority: Number.isNaN(value) ? 0 : value });
                        }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <AdminCheckbox checked={form.is_active} onCheckedChange={(c) => setForm({ ...form, is_active: c })} aria-label="Aktiv" />
                    <span className="text-sm text-[var(--admin-text-primary)]">Aktiv</span>
                  </div>
                  {errors.length > 0 && (
                    <div role="alert" data-testid="ad-form-errors" className="rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-sm text-[var(--admin-danger)]">
                      <p className="font-semibold">Werbung wurde nicht gespeichert:</p>
                      <ul className="mt-1 list-disc space-y-0.5 pl-5">
                        {errors.map((e, i) => (
                          <li key={i}>
                            {e.field ? `${ADVERTISEMENT_FIELD_LABELS[e.field] ?? e.field}: ` : ""}
                            {e.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <AdminButton
                      onClick={save}
                      disabled={saveMutation.isPending || !form.title.trim() || !form.target_url.trim()}
                    >
                      {saveMutation.isPending ? "Wird gespeichert..." : "Speichern"}
                    </AdminButton>
                    <AdminButton variant="ghost" onClick={() => setEditing(null)}>
                      Abbrechen
                    </AdminButton>
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Vorschau</p>
                  <motion.div key={`${form.image_url}|${form.title}`} initial={{ opacity: 0.6 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
                    <AdvertisementBannerView
                      title={form.title || "Werbungstitel"}
                      description={form.description || null}
                      imageUrl={form.image_url}
                      ctaText={form.cta_text || "Mehr erfahren"}
                      href={undefined}
                    />
                  </motion.div>
                  <p className="mt-2 truncate text-xs text-[var(--admin-text-muted)]">Link: {form.target_url || "—"}</p>
                </div>
              </div>
            </AdminCard>
          </motion.div>
        )}
      </AnimatePresence>

      {isLoading ? (
        <div className="flex h-40 items-center justify-center">
          <Loader2 size={22} className="animate-spin text-[var(--admin-primary)]" />
        </div>
      ) : isError ? (
        <AdminCard>
          <p className="text-sm text-[var(--admin-danger)]">
            Werbung konnte nicht geladen werden. Werbung verwalten dürfen nur Super-Admin, Admin und Content-Manager.
          </p>
        </AdminCard>
      ) : !ads || ads.length === 0 ? (
        <AdminEmptySection icon={Megaphone} title="Noch keine Werbung" description="Lege die erste Werbung an. Ohne aktive Werbung sehen Studenten ein neutrales VIZU-Banner." />
      ) : (
        <AdminCard className="overflow-x-auto p-0">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr className="border-b border-[var(--admin-border)]">
                {["Bild", "Titel", "Status", "Zeitraum", "Aufrufe", "Klicks", "CTR", "Aktionen"].map((h) => (
                  <th key={h} className="px-4 py-3 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ads.map((ad) => (
                <tr key={ad.id} className="border-b border-[var(--admin-border)] last:border-0">
                  <td className="px-4 py-3">
                    {ad.image_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={resolveMediaUrl(ad.image_url) ?? ""} alt="" className="h-10 w-16 rounded-md object-cover" />
                    ) : (
                      <div className="flex h-10 w-16 items-center justify-center rounded-md bg-white/5">
                        <Megaphone size={14} className="text-[var(--admin-text-muted)]" />
                      </div>
                    )}
                  </td>
                  <td className="max-w-[220px] px-4 py-3">
                    <p className="truncate font-semibold text-[var(--admin-text-primary)]">{ad.title}</p>
                    <p className="text-xs text-[var(--admin-text-muted)]">Priorität {ad.priority}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        ad.is_active
                          ? "rounded-full bg-[var(--admin-success,#22c55e)]/15 px-2 py-0.5 text-xs font-semibold text-[var(--admin-success,#22c55e)]"
                          : "rounded-full bg-[var(--admin-text-muted)]/15 px-2 py-0.5 text-xs font-semibold text-[var(--admin-text-muted)]"
                      }
                    >
                      {ad.is_active ? "Aktiv" : "Inaktiv"}
                    </span>
                    {ad.is_current && <p className="mt-1 text-[10px] font-semibold text-orange-400">wird angezeigt</p>}
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{formatRange(ad)}</td>
                  <td className="px-4 py-3 tabular-nums text-[var(--admin-text-primary)]">{numberFmt.format(ad.impressions)}</td>
                  <td className="px-4 py-3 tabular-nums text-[var(--admin-text-primary)]">{numberFmt.format(ad.clicks)}</td>
                  <td className="px-4 py-3 tabular-nums text-[var(--admin-text-primary)]">{ad.ctr.toFixed(2)}%</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      <AdminButton size="sm" variant="secondary" onClick={() => openEdit(ad)}>
                        <Pencil size={13} />
                        Bearbeiten
                      </AdminButton>
                      <AdminButton size="sm" variant="secondary" onClick={() => toggleMutation.mutate(ad)} disabled={toggleMutation.isPending}>
                        {ad.is_active ? <EyeOff size={13} /> : <Eye size={13} />}
                        {ad.is_active ? "Deaktivieren" : "Aktivieren"}
                      </AdminButton>
                      <AdminButton size="sm" variant="secondary" onClick={() => setAnalyticsFor(ad)}>
                        <BarChart3 size={13} />
                        Analytics
                      </AdminButton>
                      <AdminButton size="sm" variant="ghost" onClick={() => setDeleteTarget(ad)} aria-label="Löschen">
                        <Trash2 size={13} />
                        Löschen
                      </AdminButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </AdminCard>
      )}

      {analyticsFor && <AnalyticsPanel ad={analyticsFor} onClose={() => setAnalyticsFor(null)} />}

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(o) => !o && setDeleteTarget(null)}
        title="Werbung löschen"
        description={deleteTarget ? `„${deleteTarget.title}“ und ihre Statistik wirklich löschen?` : ""}
        onConfirm={() => deleteMutation.mutate()}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}

function AnalyticsPanel({ ad, onClose }: { ad: AdminAdvertisement; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-advertisement-analytics", ad.id],
    queryFn: () => getAdvertisementAnalytics(ad.id),
  });
  const max = Math.max(1, ...(data?.series ?? []).map((p) => Math.max(p.impressions, p.clicks)));

  return (
    <AdminCard>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Analytics — {ad.title}</h3>
        <button type="button" onClick={onClose} aria-label="Schließen" className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5">
          <X size={16} />
        </button>
      </div>
      {isLoading || !data ? (
        <Loader2 size={20} className="animate-spin text-[var(--admin-primary)]" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              ["Aufrufe", numberFmt.format(data.impressions)],
              ["Klicks", numberFmt.format(data.clicks)],
              ["CTR", `${data.ctr.toFixed(2)}%`],
              ["Heute", `${data.impressions_today} / ${data.clicks_today}`],
              ["Diese Woche", `${data.impressions_week} / ${data.clicks_week}`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl bg-white/5 px-4 py-3 ring-1 ring-[var(--admin-border)]">
                <p className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
                <p className="mt-1 text-lg font-bold tabular-nums text-[var(--admin-text-primary)]">{value}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-[var(--admin-text-muted)]">„Heute“ und „Diese Woche“: Aufrufe / Klicks.</p>

          <p className="mt-6 text-xs font-semibold text-[var(--admin-text-primary)]">Aufrufe vs. Klicks (letzte 14 Tage)</p>
          <div className="mt-2 flex items-center gap-4 text-[11px] text-[var(--admin-text-muted)]">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-blue-500" /> Aufrufe
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-orange-500" /> Klicks
            </span>
          </div>
          <div className="mt-3 flex h-44 items-end gap-1.5">
            {data.series.map((point) => (
              <div key={point.date} className="flex flex-1 flex-col items-center gap-1.5">
                <div className="flex h-full w-full items-end justify-center gap-0.5">
                  <div
                    className="w-1/2 rounded-t bg-blue-500 transition-all"
                    style={{ height: `${(point.impressions / max) * 100}%`, minHeight: point.impressions ? 3 : 0 }}
                    title={`${point.date}: ${point.impressions} Aufrufe`}
                  />
                  <div
                    className="w-1/2 rounded-t bg-orange-500 transition-all"
                    style={{ height: `${(point.clicks / max) * 100}%`, minHeight: point.clicks ? 3 : 0 }}
                    title={`${point.date}: ${point.clicks} Klicks`}
                  />
                </div>
                <span className="text-[9px] text-[var(--admin-text-muted)]">{point.date.slice(8, 10)}.{point.date.slice(5, 7)}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </AdminCard>
  );
}
