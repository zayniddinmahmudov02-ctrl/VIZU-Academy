"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Pencil, Plus, RotateCcw, Save } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminLabel, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import FormDialog from "@/components/admin/form-dialog";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  createPackage,
  getAngeboteConfig,
  listPackages,
  saveAngeboteConfig,
  updatePackage,
  type AngeboteConfig,
  type CoursePackage,
  type PackageInput,
  type PackageStatus,
} from "@/features/admin/services/angebote-config-service";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const LANGS = ["uz", "de", "en", "ru"] as const;
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";
const STATUS_LABEL: Record<PackageStatus, string> = { ACTIVE: "Aktiv (im Verkauf)", COMING_SOON: "Bald verfügbar", DISABLED: "Deaktiviert" };
const STATUS_STYLE: Record<PackageStatus, string> = {
  ACTIVE: "bg-[var(--admin-success)]/15 text-[var(--admin-success)]",
  COMING_SOON: "bg-[var(--admin-warning)]/15 text-[var(--admin-warning)]",
  DISABLED: "bg-white/5 text-[var(--admin-text-muted)]",
};
const som = (v: number | null) => (v == null ? "—" : `${new Intl.NumberFormat("de-DE").format(v)} UZS`);

function toNum(v: string): number | null {
  const n = Number(v.replace(/\s/g, ""));
  return v.trim() === "" || !Number.isFinite(n) ? null : Math.round(n);
}

/** Admin -> Angebote & Preise: course packages (price, duration, contents, status, description — table
 * course_packages, nothing hard-coded in the student panel) and the level settings (release, lesson-access gate,
 * free lessons). Every change is audited and takes effect at once; orders keep their own amount, duration and levels. */
export default function AngebotePage() {
  return (
    <div className="space-y-6" data-testid="admin-angebote">
      <AdminPageHeader title="Angebote & Preise" description="Kurspakete, Preise, Laufzeiten und Status sowie die Freigabe der Niveaus. Bestellungen prüfen Sie unter Payments." />
      <PackagesSection />
      <LevelSettings />
    </div>
  );
}

// ── packages ─────────────────────────────────────────────────

type Form = {
  code: string; name: string; package_type: "LEVEL" | "PACKAGE"; included_levels: string[]; price: string; original_price: string;
  discount_percent: string; duration_days: string; status: PackageStatus; description: Record<string, string>; sort_order: string;
};

const EMPTY: Form = { code: "", name: "", package_type: "PACKAGE", included_levels: [], price: "", original_price: "", discount_percent: "",
  duration_days: "30", status: "COMING_SOON", description: {}, sort_order: "100" };

function toForm(p: CoursePackage): Form {
  return { code: p.code, name: p.name, package_type: p.package_type, included_levels: [...p.included_levels], price: p.price?.toString() ?? "",
    original_price: p.original_price?.toString() ?? "", discount_percent: p.discount_percent?.toString() ?? "",
    duration_days: String(p.duration_days), status: p.status, description: { ...p.description }, sort_order: String(p.sort_order) };
}

function PackagesSection() {
  const queryClient = useQueryClient();
  const { data: packages, isLoading, error } = useQuery({ queryKey: ["admin", "packages"], queryFn: listPackages });
  const [editing, setEditing] = useState<string | null>(null); // package code, "new" or null
  const [form, setForm] = useState<Form>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function open(p: CoursePackage | null) {
    setForm(p ? toForm(p) : EMPTY);
    setFormError(null);
    setEditing(p ? p.code : "new");
  }

  async function submit() {
    const price = toNum(form.price);
    const payload: PackageInput = {
      name: form.name.trim(), package_type: form.package_type, included_levels: LEVELS.filter((lv) => form.included_levels.includes(lv)),
      price, original_price: toNum(form.original_price), discount_percent: toNum(form.discount_percent),
      duration_days: toNum(form.duration_days) ?? 0, status: form.status, description: form.description, sort_order: toNum(form.sort_order) ?? 0,
    };
    const before = editing !== "new" ? packages?.find((p) => p.code === editing) : null;
    if (before && before.status !== "ACTIVE" && form.status === "ACTIVE"
        && !window.confirm(`${form.name} in den Verkauf nehmen (${som(price)}, ${payload.duration_days} Tage)? Studenten können es dann sofort kaufen.`)) {
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      if (editing === "new") await createPackage({ ...payload, code: form.code.trim().toUpperCase() });
      else await updatePackage(editing!, payload);
      await queryClient.invalidateQueries({ queryKey: ["admin", "packages"] });
      setEditing(null);
    } catch (err) {
      setFormError(apiErrorMessage(err, "Speichern fehlgeschlagen."));
    } finally {
      setSaving(false);
    }
  }

  const set = (patch: Partial<Form>) => setForm((prev) => ({ ...prev, ...patch }));

  return (
    <section className={card} data-testid="admin-packages">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Kurspakete</h2>
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            Aktiv = im Verkauf · Bald verfügbar = sichtbar ohne Preis und Kaufknopf · Deaktiviert = ausgeblendet. Pakete werden nie gelöscht
            (Bestellungen verweisen darauf). Ein Paket mit B2 / C1 öffnet diese Niveaus für seine Käufer automatisch, sobald sie freigegeben sind.
          </p>
        </div>
        <AdminButton size="sm" onClick={() => open(null)} data-testid="package-new"><Plus size={14} /> Neues Paket</AdminButton>
      </div>
      {isLoading && <Loader2 className="animate-spin text-[var(--admin-text-muted)]" />}
      {error && <p className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Pakete konnten nicht geladen werden (nur Super Admin).")}</p>}
      {packages && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
              <tr>{["Paket", "Inhalt", "Preis", "Laufzeit", "Status", "Bestellungen", ""].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr>
            </thead>
            <tbody>
              {packages.map((p) => (
                <tr key={p.code} className="border-t border-[var(--admin-border)]" data-testid={`package-row-${p.code}`}>
                  <td className="px-3 py-2.5 font-semibold text-[var(--admin-text-primary)]">
                    {p.name}
                    <span className="block text-xs font-normal text-[var(--admin-text-muted)]">{p.code} · {p.package_type === "PACKAGE" ? "Komplett-Paket" : "Einzelkurs"}</span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{p.included_levels.join(" + ")}</td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-primary)]">
                    {som(p.price)}
                    {p.original_price != null && <span className="block text-xs text-[var(--admin-text-muted)] line-through">{som(p.original_price)}</span>}
                  </td>
                  <td className="px-3 py-2.5 text-[var(--admin-text-primary)]">{p.duration_days} Tage</td>
                  <td className="px-3 py-2.5">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[p.status]}`}>{STATUS_LABEL[p.status]}</span>
                    {p.status === "ACTIVE" && !p.purchasable && <span className="mt-1 block text-xs text-[var(--admin-danger)]">nicht kaufbar (Niveau gesperrt)</span>}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-[var(--admin-text-secondary)]">{p.approved_orders} bezahlt · {p.pending_orders} offen</td>
                  <td className="px-3 py-2.5 text-right">
                    <AdminButton size="sm" variant="secondary" onClick={() => open(p)} data-testid={`package-edit-${p.code}`}><Pencil size={13} /> Bearbeiten</AdminButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <FormDialog
        open={editing !== null}
        onOpenChange={(o) => !o && setEditing(null)}
        title={editing === "new" ? "Neues Paket" : `Paket ${editing ?? ""} bearbeiten`}
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <AdminButton variant="secondary" onClick={() => setEditing(null)} disabled={saving}>Abbrechen</AdminButton>
            <AdminButton onClick={() => void submit()} disabled={saving} data-testid="package-save">
              {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} Speichern
            </AdminButton>
          </div>
        }
      >
        {formError && <p className="mb-3 rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-sm text-[var(--admin-danger)]" data-testid="package-error">{formError}</p>}
        <div className="grid gap-3 sm:grid-cols-2">
          {editing === "new" && (
            <div>
              <AdminLabel>Code (A–Z, 0–9, _)</AdminLabel>
              <AdminInput value={form.code} maxLength={20} onChange={(e) => set({ code: e.target.value.toUpperCase() })} data-testid="package-code" />
            </div>
          )}
          <div>
            <AdminLabel>Name</AdminLabel>
            <AdminInput value={form.name} maxLength={120} onChange={(e) => set({ name: e.target.value })} data-testid="package-name" />
          </div>
          <div>
            <AdminLabel>Typ</AdminLabel>
            <AdminSelect value={form.package_type} onChange={(e) => set({ package_type: e.target.value as Form["package_type"] })} disabled={editing !== "new"}>
              <option value="LEVEL">Einzelkurs</option>
              <option value="PACKAGE">Komplett-Paket</option>
            </AdminSelect>
          </div>
          <div>
            <AdminLabel>Status</AdminLabel>
            <AdminSelect value={form.status} onChange={(e) => set({ status: e.target.value as PackageStatus })} data-testid="package-status">
              {(Object.keys(STATUS_LABEL) as PackageStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </AdminSelect>
          </div>
          <div className="sm:col-span-2">
            <AdminLabel>Enthaltene Niveaus</AdminLabel>
            <div className="flex flex-wrap gap-3">
              {LEVELS.map((lv) => (
                <label key={lv} className="flex items-center gap-1.5 text-sm text-[var(--admin-text-primary)]">
                  <AdminCheckbox
                    checked={form.included_levels.includes(lv)}
                    disabled={editing !== "new" && form.package_type === "LEVEL"}
                    onCheckedChange={(v) => set({ included_levels: v ? [...form.included_levels, lv] : form.included_levels.filter((x) => x !== lv) })}
                  />
                  {lv}
                </label>
              ))}
            </div>
            {editing !== "new" && <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Gilt nur für neue Bestellungen — bisherige Käufer behalten ihre Niveaus.</p>}
          </div>
          <div>
            <AdminLabel>Preis (UZS)</AdminLabel>
            <AdminInput inputMode="numeric" value={form.price} onChange={(e) => set({ price: e.target.value })} data-testid="package-price" />
          </div>
          <div>
            <AdminLabel>Alter Preis (optional, durchgestrichen)</AdminLabel>
            <AdminInput inputMode="numeric" value={form.original_price} onChange={(e) => set({ original_price: e.target.value })} />
          </div>
          <div>
            <AdminLabel>Rabatt-Badge % (optional)</AdminLabel>
            <AdminInput inputMode="numeric" value={form.discount_percent} onChange={(e) => set({ discount_percent: e.target.value })} />
          </div>
          <div>
            <AdminLabel>Laufzeit (Tage, ab Zahlungsfreigabe)</AdminLabel>
            <AdminInput inputMode="numeric" value={form.duration_days} onChange={(e) => set({ duration_days: e.target.value })} data-testid="package-days" />
          </div>
          <div>
            <AdminLabel>Reihenfolge</AdminLabel>
            <AdminInput inputMode="numeric" value={form.sort_order} onChange={(e) => set({ sort_order: e.target.value })} />
          </div>
          {LANGS.map((lang) => (
            <div key={lang} className="sm:col-span-2">
              <AdminLabel>Beschreibung ({lang.toUpperCase()})</AdminLabel>
              <AdminTextarea rows={2} maxLength={1000} value={form.description[lang] ?? ""}
                onChange={(e) => set({ description: { ...form.description, [lang]: e.target.value } })} />
            </div>
          ))}
        </div>
      </FormDialog>
    </section>
  );
}

// ── level settings ───────────────────────────────────────────

function LevelSettings() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["admin", "angebote-config"], queryFn: getAngeboteConfig });
  const [levels, setLevels] = useState<Record<string, boolean>>({});
  const [sales, setSales] = useState<Record<string, boolean>>({});
  const [free, setFree] = useState("1");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  function load(cfg: AngeboteConfig) {
    setLevels({ ...cfg.levels });
    setSales({ ...(cfg.sales ?? {}) });
    setFree(String(cfg.free_lessons));
  }
  // adopt freshly loaded / saved config (state adjusted during render, not in an effect)
  const [loadedFrom, setLoadedFrom] = useState<AngeboteConfig | null>(null);
  if (data && data !== loadedFrom) {
    setLoadedFrom(data);
    load(data);
  }

  async function save() {
    if (!data) return;
    const released = LEVELS.filter((lv) => levels[lv] && !data.levels[lv]);
    if (released.length && !window.confirm(`${released.join(", ")} freigeben? Käufer eines Pakets mit ${released.join(", ")} (z. B. A1–C1) erhalten sofort Zugang — ohne neue Zahlung.`)) return;
    setSaving(true);
    setMessage(null);
    const levelDiff = Object.fromEntries(LEVELS.filter((lv) => levels[lv] !== data.defaults.levels[lv]).map((lv) => [lv, levels[lv]]));
    const salesDiff = Object.fromEntries(LEVELS.filter((lv) => !!sales[lv] !== !!data.defaults.sales?.[lv]).map((lv) => [lv, !!sales[lv]]));
    try {
      const saved = await saveAngeboteConfig({ levels: levelDiff, sales: salesDiff, free_lessons: Number(free) });
      queryClient.setQueryData(["admin", "angebote-config"], saved);
      await queryClient.invalidateQueries({ queryKey: ["admin", "packages"] });
      setMessage({ ok: true, text: "Gespeichert — gilt sofort." });
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setSaving(false);
    }
  }

  if (!data) return null;
  return (
    <section className={card}>
      <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Niveaus freigeben</h2>
      <div className="flex flex-wrap gap-4">
        {LEVELS.map((lv) => (
          <label key={lv} className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]" data-testid={`angebote-level-${lv}`}>
            <AdminCheckbox checked={!!levels[lv]} onCheckedChange={(v) => setLevels((p) => ({ ...p, [lv]: Boolean(v) }))} />
            <span className="font-semibold">{lv}</span>
            <span className="text-xs text-[var(--admin-text-muted)]">{levels[lv] ? "freigegeben" : "Tez orada (gesperrt)"}</span>
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Ein gesperrtes Niveau ist sichtbar, aber ohne Zugang — auch nicht für Paketkäufer. Nach der Freigabe öffnet es sich für alle Käufer eines Pakets, das es enthält.</p>

      <h2 className="mb-3 mt-5 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Bezahlte Lektionen auch mit altem Premium</h2>
      <div className="flex flex-wrap gap-4">
        {LEVELS.map((lv) => (
          <label key={lv} className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]" data-testid={`angebote-sales-${lv}`}>
            <AdminCheckbox checked={!!sales[lv]} onCheckedChange={(v) => setSales((p) => ({ ...p, [lv]: Boolean(v) }))} />
            <span className="font-semibold">{lv}</span>
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Aus: bezahlte Lektionen nur für Käufer dieses Niveaus (nicht für das frühere zeitbasierte Premium). Der Verkauf selbst wird über den Paketstatus gesteuert.</p>
      <div className="mt-4 flex items-center gap-3">
        <span className="text-sm text-[var(--admin-text-primary)]">Kostenlose Lektionen pro Kurs</span>
        <AdminInput className="w-20" type="number" min={0} max={5} value={free} onChange={(e) => setFree(e.target.value)} data-testid="angebote-free" />
      </div>
      {message && (
        <p role="status" data-testid="angebote-message"
           className={`mt-4 rounded-xl px-4 py-3 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>{message.text}</p>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <AdminButton onClick={save} disabled={saving} data-testid="angebote-save">{saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} Speichern</AdminButton>
        <AdminButton variant="secondary" onClick={() => load(data)} disabled={saving}><RotateCcw size={15} /> Zurücksetzen</AdminButton>
        <Link href="/admin/payments" className="text-sm font-semibold text-[var(--admin-primary)] hover:underline">Bestellungen & Zahlungen prüfen →</Link>
      </div>
    </section>
  );
}
