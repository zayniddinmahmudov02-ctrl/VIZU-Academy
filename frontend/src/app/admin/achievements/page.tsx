"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff, Loader2, Pencil, Plus, Users, X } from "lucide-react";

import { AdminButton, AdminCard, AdminCheckbox, AdminInput, AdminLabel, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FileUploadField from "@/components/admin/file-upload-field";
import MedalIcon from "@/components/achievements/medal-icon";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  createAchievement,
  createAchievementCategory,
  getAchievementMeta,
  listAchievementAwards,
  listAchievementCategories,
  listAchievements,
  updateAchievement,
  type AchievementPayload,
  type AdminAchievement,
} from "@/features/admin/services/achievements-admin-service";

const fmt = new Intl.NumberFormat("de-DE");
const STATUS_LABEL: Record<string, string> = { AVAILABLE: "verfügbar", RESERVED: "reserviert (offene Bestellung)", USED: "eingelöst", NONE: "—" };

type Form = {
  key: string; category_id: string; name_de: string; name_uz: string; description_de: string; description_uz: string;
  icon_preset: string; icon_color: string; image_url: string | null; condition_type: string; level: string; lesson_number: string; count: string;
  reward_type: "NONE" | "ORDER_DISCOUNT"; reward_value: string; reward_offers: string[]; reward_combine_with_promo: boolean; is_active: boolean; order_index: string;
};

const EMPTY: Form = {
  key: "", category_id: "", name_de: "", name_uz: "", description_de: "", description_uz: "", icon_preset: "rocket", icon_color: "green", image_url: null,
  condition_type: "LESSON_COMPLETED", level: "A1", lesson_number: "1", count: "1", reward_type: "NONE", reward_value: "", reward_offers: ["A1"],
  reward_combine_with_promo: false, is_active: false, order_index: "0",
};

function toForm(a: AdminAchievement): Form {
  const p = a.condition_params ?? {};
  return {
    key: a.key, category_id: a.category_id, name_de: a.name_de, name_uz: a.name_uz, description_de: a.description_de ?? "", description_uz: a.description_uz ?? "",
    icon_preset: a.icon_preset, icon_color: a.icon_color, image_url: a.image_url, condition_type: a.condition_type, level: String(p.level ?? "A1"),
    lesson_number: String(p.lesson_number ?? "1"), count: String(p.count ?? "1"), reward_type: a.reward_type, reward_value: a.reward_value ? String(a.reward_value) : "",
    reward_offers: a.reward_offers ?? [], reward_combine_with_promo: a.reward_combine_with_promo, is_active: a.is_active, order_index: String(a.order_index),
  };
}

function toPayload(f: Form, creating: boolean): AchievementPayload {
  const params: Record<string, string | number> = { level: f.level };
  if (f.condition_type === "LESSON_COMPLETED") params.lesson_number = Number(f.lesson_number);
  else params.count = Number(f.count);
  const payload: AchievementPayload = {
    category_id: f.category_id, name_de: f.name_de, name_uz: f.name_uz, description_de: f.description_de || null, description_uz: f.description_uz || null,
    icon_preset: f.icon_preset, icon_color: f.icon_color, image_url: f.image_url, condition_type: f.condition_type, condition_params: params,
    reward_type: f.reward_type, reward_value: f.reward_type === "ORDER_DISCOUNT" ? Number(f.reward_value) : 0,
    reward_offers: f.reward_type === "ORDER_DISCOUNT" ? f.reward_offers : [], reward_combine_with_promo: f.reward_combine_with_promo,
    is_active: f.is_active, order_index: Number(f.order_index) || 0,
  };
  if (creating) payload.key = f.key;
  return payload;
}

/** Admin -> Achievements / Medals: categories, medals (texts uz/de, icon,
 * server-checked condition, reward), activation and who received them.
 * Awarding itself only ever happens on the server. */
export default function AchievementsAdminPage() {
  const qc = useQueryClient();
  const [category, setCategory] = useState("");
  const meta = useQuery({ queryKey: ["admin", "achievements", "meta"], queryFn: getAchievementMeta });
  const cats = useQuery({ queryKey: ["admin", "achievements", "categories"], queryFn: listAchievementCategories });
  const list = useQuery({ queryKey: ["admin", "achievements", category], queryFn: () => listAchievements(category || undefined) });
  const [editing, setEditing] = useState<AdminAchievement | "new" | null>(null);
  const [form, setForm] = useState<Form>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [awardsFor, setAwardsFor] = useState<AdminAchievement | null>(null);
  const [newCat, setNewCat] = useState<{ key: string; name_de: string; name_uz: string } | null>(null);
  const awards = useQuery({ queryKey: ["admin", "achievements", "awards", awardsFor?.id], queryFn: () => listAchievementAwards(awardsFor!.id), enabled: !!awardsFor });

  const refresh = () => qc.invalidateQueries({ queryKey: ["admin", "achievements"] });
  const set = (patch: Partial<Form>) => setForm((f) => ({ ...f, ...patch }));

  async function save() {
    setSaving(true);
    setMsg(null);
    try {
      if (editing === "new") await createAchievement(toPayload(form, true));
      else if (editing) await updateAchievement(editing.id, toPayload(form, false));
      setMsg({ ok: true, text: "Gespeichert." });
      setEditing(null);
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setSaving(false);
    }
  }

  async function toggle(a: AdminAchievement) {
    try {
      await updateAchievement(a.id, { is_active: !a.is_active });
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Ändern fehlgeschlagen.") });
    }
  }

  async function saveCategory() {
    if (!newCat) return;
    try {
      await createAchievementCategory(newCat);
      setNewCat(null);
      await refresh();
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Kategorie konnte nicht angelegt werden.") });
    }
  }

  const condition = meta.data?.conditions.find((c) => c.type === form.condition_type);

  return (
    <div className="space-y-6" data-testid="admin-achievements">
      <AdminPageHeader title="Achievements / Medals" description="Medaillen, Bedingungen und Belohnungen. Vergeben werden Medaillen ausschließlich vom Server — einmal pro Student." />

      <AdminCard>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-60">
            <AdminLabel>Kategorie</AdminLabel>
            <AdminSelect value={category} onChange={(e) => setCategory(e.target.value)} data-testid="ach-filter">
              <option value="">Alle Kategorien</option>
              {(cats.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name_de} / {c.name_uz} ({c.achievement_count})</option>)}
            </AdminSelect>
          </div>
          <AdminButton variant="secondary" onClick={() => setNewCat({ key: "", name_de: "", name_uz: "" })}><Plus size={14} /> Kategorie</AdminButton>
          <AdminButton onClick={() => { setForm({ ...EMPTY, category_id: category || cats.data?.[0]?.id || "" }); setEditing("new"); setMsg(null); }} data-testid="ach-new">
            <Plus size={14} /> Neue Medaille
          </AdminButton>
        </div>
        {newCat && (
          <div className="mt-4 flex flex-wrap items-end gap-2">
            <div><AdminLabel>Schlüssel</AdminLabel><AdminInput className="w-40" value={newCat.key} placeholder="z. B. streak_medals" onChange={(e) => setNewCat({ ...newCat, key: e.target.value })} /></div>
            <div><AdminLabel>Name (de)</AdminLabel><AdminInput className="w-48" value={newCat.name_de} onChange={(e) => setNewCat({ ...newCat, name_de: e.target.value })} /></div>
            <div><AdminLabel>Name (uz)</AdminLabel><AdminInput className="w-48" value={newCat.name_uz} onChange={(e) => setNewCat({ ...newCat, name_uz: e.target.value })} /></div>
            <AdminButton onClick={saveCategory}>Anlegen</AdminButton>
            <AdminButton variant="ghost" onClick={() => setNewCat(null)}>Abbrechen</AdminButton>
          </div>
        )}
      </AdminCard>

      {msg && <p role="status" className={`rounded-xl px-4 py-3 text-sm ${msg.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>{msg.text}</p>}

      {editing !== null && (
        <AdminCard>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">{editing === "new" ? "Neue Medaille" : `Medaille bearbeiten: ${editing.key}`}</h3>
            <button type="button" onClick={() => setEditing(null)} aria-label="Schließen" className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5"><X size={16} /></button>
          </div>
          <div className="grid gap-6 xl:grid-cols-[1fr_240px]">
            <div className="grid gap-4 md:grid-cols-2">
              {editing === "new" && <div><AdminLabel>Schlüssel (eindeutig)</AdminLabel><AdminInput value={form.key} placeholder="z. B. a1_finisher" onChange={(e) => set({ key: e.target.value })} /></div>}
              <div>
                <AdminLabel>Kategorie</AdminLabel>
                <AdminSelect value={form.category_id} onChange={(e) => set({ category_id: e.target.value })}>
                  {(cats.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name_de} / {c.name_uz}</option>)}
                </AdminSelect>
              </div>
              <div><AdminLabel>Name (de)</AdminLabel><AdminInput value={form.name_de} maxLength={120} onChange={(e) => set({ name_de: e.target.value })} /></div>
              <div><AdminLabel>Name (uz)</AdminLabel><AdminInput value={form.name_uz} maxLength={120} onChange={(e) => set({ name_uz: e.target.value })} /></div>
              <div><AdminLabel>Beschreibung (de)</AdminLabel><AdminTextarea rows={2} value={form.description_de} onChange={(e) => set({ description_de: e.target.value })} /></div>
              <div><AdminLabel>Beschreibung (uz)</AdminLabel><AdminTextarea rows={2} value={form.description_uz} onChange={(e) => set({ description_uz: e.target.value })} /></div>
              <div>
                <AdminLabel>Symbol</AdminLabel>
                <AdminSelect value={form.icon_preset} onChange={(e) => set({ icon_preset: e.target.value })}>
                  {(meta.data?.icon_presets ?? []).map((p) => <option key={p} value={p}>{p}</option>)}
                </AdminSelect>
              </div>
              <div>
                <AdminLabel>Farbe</AdminLabel>
                <AdminSelect value={form.icon_color} onChange={(e) => set({ icon_color: e.target.value })}>
                  {(meta.data?.icon_colors ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
                </AdminSelect>
              </div>
              <div className="md:col-span-2">
                <FileUploadField label="Eigenes Bild (optional, ersetzt das Symbol)" value={form.image_url} onChange={(url) => set({ image_url: url })} folder="images" accept="image/*" />
              </div>

              <div>
                <AdminLabel>Bedingung (vom Server geprüft)</AdminLabel>
                <AdminSelect value={form.condition_type} onChange={(e) => set({ condition_type: e.target.value })} data-testid="ach-condition">
                  {(meta.data?.conditions ?? []).map((c) => <option key={c.type} value={c.type}>{c.label_de} / {c.label_uz}</option>)}
                </AdminSelect>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <AdminLabel>Niveau</AdminLabel>
                  <AdminSelect value={form.level} onChange={(e) => set({ level: e.target.value })}>
                    {(condition?.levels ?? ["A1"]).map((l) => <option key={l} value={l}>{l}</option>)}
                  </AdminSelect>
                </div>
                {form.condition_type === "LESSON_COMPLETED" ? (
                  <div><AdminLabel>Lektion Nr.</AdminLabel><AdminInput type="number" min={1} max={100} value={form.lesson_number} onChange={(e) => set({ lesson_number: e.target.value })} /></div>
                ) : (
                  <div><AdminLabel>Anzahl Lektionen</AdminLabel><AdminInput type="number" min={1} max={100} value={form.count} onChange={(e) => set({ count: e.target.value })} /></div>
                )}
              </div>

              <div>
                <AdminLabel>Belohnung</AdminLabel>
                <AdminSelect value={form.reward_type} onChange={(e) => set({ reward_type: e.target.value as Form["reward_type"] })} data-testid="ach-reward-type">
                  <option value="NONE">keine</option>
                  <option value="ORDER_DISCOUNT">Rabatt (UZS) auf eine Bestellung</option>
                </AdminSelect>
              </div>
              {form.reward_type === "ORDER_DISCOUNT" && (
                <div className="grid gap-3">
                  <div><AdminLabel>Betrag (UZS)</AdminLabel><AdminInput inputMode="numeric" value={form.reward_value} onChange={(e) => set({ reward_value: e.target.value.replace(/\D/g, "") })} data-testid="ach-reward-value" /></div>
                  <div className="flex flex-wrap gap-3">
                    {(meta.data?.offers ?? []).map((o) => (
                      <label key={o.code} className="flex items-center gap-1.5 text-xs text-[var(--admin-text-secondary)]">
                        <AdminCheckbox checked={form.reward_offers.includes(o.code)}
                                       onCheckedChange={(v) => set({ reward_offers: v ? [...form.reward_offers, o.code] : form.reward_offers.filter((x) => x !== o.code) })} />
                        {o.label}
                      </label>
                    ))}
                  </div>
                  <label className="flex items-center gap-2 text-xs text-[var(--admin-text-secondary)]">
                    <AdminCheckbox checked={form.reward_combine_with_promo} onCheckedChange={(v) => set({ reward_combine_with_promo: Boolean(v) })} />
                    Mit Promo-Code kombinierbar (der Aktionspreis gilt immer)
                  </label>
                  <p className="text-xs text-[var(--admin-text-muted)]">Gilt nur für die gewählten Angebote, einmal pro Student. Eine Änderung gilt auch für bereits vergebene, noch nicht eingelöste Belohnungen.</p>
                </div>
              )}
              <div><AdminLabel>Reihenfolge</AdminLabel><AdminInput type="number" min={0} value={form.order_index} onChange={(e) => set({ order_index: e.target.value })} /></div>
              <label className="flex items-center gap-2 self-end text-sm text-[var(--admin-text-primary)]">
                <AdminCheckbox checked={form.is_active} onCheckedChange={(v) => set({ is_active: Boolean(v) })} /> Aktiv (für Studenten sichtbar und vergebbar)
              </label>
              <div className="flex gap-2 md:col-span-2">
                <AdminButton onClick={save} disabled={saving} data-testid="ach-save">{saving ? <Loader2 size={14} className="animate-spin" /> : null} Speichern</AdminButton>
                <AdminButton variant="ghost" onClick={() => setEditing(null)}>Abbrechen</AdminButton>
              </div>
            </div>
            <div className="flex flex-col items-center gap-3 rounded-xl bg-white/5 p-4 text-center">
              <p className="text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Vorschau</p>
              <MedalIcon preset={form.icon_preset} color={form.icon_color} imageUrl={form.image_url} earned size={96} />
              <MedalIcon preset={form.icon_preset} color={form.icon_color} imageUrl={form.image_url} earned={false} size={48} />
              <p className="text-sm font-semibold text-[var(--admin-text-primary)]">{form.name_de || "Name"}</p>
            </div>
          </div>
        </AdminCard>
      )}

      <AdminCard className="overflow-x-auto p-0">
        {list.isLoading ? (
          <div className="p-6"><Loader2 className="animate-spin text-[var(--admin-text-muted)]" /></div>
        ) : list.isError ? (
          <p className="p-6 text-sm text-[var(--admin-danger)]">{apiErrorMessage(list.error, "Konnte nicht geladen werden (nur Super Admin).")}</p>
        ) : (
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr className="border-b border-[var(--admin-border)]">{["", "Medaille", "Kategorie", "Bedingung", "Belohnung", "Vergeben", "Status", ""].map((h, i) => <th key={i} className="px-4 py-3">{h}</th>)}</tr>
            </thead>
            <tbody>
              {(list.data ?? []).map((a) => (
                <tr key={a.id} className="border-b border-[var(--admin-border)] last:border-0" data-testid="ach-row">
                  <td className="px-4 py-3"><MedalIcon preset={a.icon_preset} color={a.icon_color} imageUrl={a.image_url} earned size={36} /></td>
                  <td className="px-4 py-3"><p className="font-semibold text-[var(--admin-text-primary)]">{a.name_de}</p><p className="text-xs text-[var(--admin-text-muted)]">{a.name_uz} · {a.key}</p></td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{a.category?.name_de} / {a.category?.name_uz}</td>
                  <td className="max-w-[240px] px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{a.condition_de}</td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{a.reward_type === "ORDER_DISCOUNT" ? `-${fmt.format(a.reward_value)} UZS · ${a.reward_offers.join(", ")}` : "—"}</td>
                  <td className="px-4 py-3 text-xs text-[var(--admin-text-secondary)]">{a.awarded_count}{a.reward_counts.USED ? ` · ${a.reward_counts.USED} eingelöst` : ""}</td>
                  <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${a.is_active ? "bg-[var(--admin-success)]/15 text-[var(--admin-success)]" : "bg-white/10 text-[var(--admin-text-muted)]"}`}>{a.is_active ? "Aktiv" : "Inaktiv"}</span></td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1.5">
                      <AdminButton size="sm" variant="secondary" onClick={() => { setForm(toForm(a)); setEditing(a); setMsg(null); }} aria-label="Bearbeiten"><Pencil size={13} /></AdminButton>
                      <AdminButton size="sm" variant="secondary" onClick={() => toggle(a)} aria-label={a.is_active ? "Deaktivieren" : "Aktivieren"}>{a.is_active ? <EyeOff size={13} /> : <Eye size={13} />}</AdminButton>
                      <AdminButton size="sm" variant="secondary" onClick={() => setAwardsFor(a)} aria-label="Empfänger"><Users size={13} /></AdminButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </AdminCard>

      {awardsFor && (
        <AdminCard>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--admin-text-primary)]">Empfänger — {awardsFor.name_de}</h3>
            <button type="button" onClick={() => setAwardsFor(null)} aria-label="Schließen" className="rounded-lg p-1.5 text-[var(--admin-text-secondary)] hover:bg-white/5"><X size={16} /></button>
          </div>
          {awards.isLoading ? <Loader2 className="animate-spin text-[var(--admin-text-muted)]" /> : (awards.data ?? []).length === 0 ? (
            <p className="text-sm text-[var(--admin-text-muted)]">Noch an niemanden vergeben.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]"><tr>{["Student", "Vergeben am", "Belohnung", "Status", "Bestellung"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr></thead>
                <tbody>
                  {(awards.data ?? []).map((w) => (
                    <tr key={w.id} className="border-t border-[var(--admin-border)]">
                      <td className="px-3 py-2"><p className="text-[var(--admin-text-primary)]">{w.name}</p><p className="text-xs text-[var(--admin-text-muted)]">{w.email}</p></td>
                      <td className="px-3 py-2 text-xs text-[var(--admin-text-secondary)]">{new Date(w.awarded_at).toLocaleString("de-DE")}</td>
                      <td className="px-3 py-2 text-xs text-[var(--admin-text-secondary)]">{w.reward_type === "ORDER_DISCOUNT" ? `-${fmt.format(w.reward_value)} UZS` : "—"}</td>
                      <td className="px-3 py-2 text-xs text-[var(--admin-text-secondary)]">{STATUS_LABEL[w.reward_status] ?? w.reward_status}{w.reward_used_at ? ` (${new Date(w.reward_used_at).toLocaleDateString("de-DE")})` : ""}</td>
                      <td className="px-3 py-2 text-xs text-[var(--admin-text-secondary)]">{w.order ? `${w.order.plan} · ${w.order.status} · ${fmt.format(w.order.final_amount)} UZS` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </AdminCard>
      )}
    </div>
  );
}
