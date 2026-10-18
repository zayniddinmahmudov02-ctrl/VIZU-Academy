"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RotateCcw, Save } from "lucide-react";

import { AdminButton, AdminCheckbox, AdminInput, AdminPageHeader } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import {
  getAngeboteConfig,
  saveAngeboteConfig,
  type AngeboteConfig,
  type OfferOverride,
} from "@/features/admin/services/angebote-config-service";

const LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const card = "rounded-2xl bg-[var(--admin-card)] p-4 ring-1 ring-[var(--admin-border)] sm:p-5";

type Row = { original_price: string; sale_price: string; discount_percent: string; active: boolean; levels: string[] };

function toNum(v: string): number | null {
  const n = Number(v.replace(/\s/g, ""));
  return v.trim() === "" || !Number.isFinite(n) ? null : Math.round(n);
}

/** Admin -> Angebote & Preise: course prices, sale on / off, package
 * contents, free lessons per course and which levels are released (B2 / C1
 * "Tez orada"). Saved as overrides of the backend defaults; takes effect at
 * once for the student panel and for new orders. Orders are reviewed under
 * Payments. */
export default function AngebotePage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin", "angebote-config"], queryFn: getAngeboteConfig });
  const [rows, setRows] = useState<Record<string, Row>>({});
  const [levels, setLevels] = useState<Record<string, boolean>>({});
  const [free, setFree] = useState("1");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  function load(cfg: AngeboteConfig) {
    setRows(Object.fromEntries(cfg.offers.map((o) => [o.code, {
      original_price: o.original_price?.toString() ?? "", sale_price: o.sale_price?.toString() ?? "",
      discount_percent: o.discount_percent?.toString() ?? "", active: o.active, levels: [...o.levels],
    }])));
    setLevels({ ...cfg.levels });
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
    setSaving(true);
    setMessage(null);
    // only what differs from the code defaults is stored as an override
    const offers: Record<string, OfferOverride> = {};
    for (const o of data.offers) {
      const r = rows[o.code];
      const d = data.defaults.offers[o.code] ?? {};
      const next: OfferOverride = {
        original_price: toNum(r.original_price), sale_price: toNum(r.sale_price), discount_percent: toNum(r.discount_percent), active: r.active,
      };
      if (o.kind === "PACKAGE") next.levels = LEVELS.filter((lv) => r.levels.includes(lv));
      const diff: OfferOverride = {};
      for (const [k, v] of Object.entries(next) as [keyof OfferOverride, unknown][]) {
        if (JSON.stringify(v) !== JSON.stringify(d[k] ?? null)) (diff as Record<string, unknown>)[k] = v;
      }
      if (Object.keys(diff).length) offers[o.code] = diff;
    }
    const levelDiff = Object.fromEntries(LEVELS.filter((lv) => levels[lv] !== data.defaults.levels[lv]).map((lv) => [lv, levels[lv]]));
    try {
      const saved = await saveAngeboteConfig({ offers, levels: levelDiff, free_lessons: Number(free) });
      queryClient.setQueryData(["admin", "angebote-config"], saved);
      setMessage({ ok: true, text: "Gespeichert — gilt sofort für das Studentenpanel und neue Bestellungen." });
    } catch (err) {
      setMessage({ ok: false, text: apiErrorMessage(err, "Speichern fehlgeschlagen.") });
    } finally {
      setSaving(false);
    }
  }

  const set = (code: string, patch: Partial<Row>) => setRows((prev) => ({ ...prev, [code]: { ...prev[code], ...patch } }));

  return (
    <div className="space-y-6" data-testid="admin-angebote">
      <AdminPageHeader title="Angebote & Preise" description="Kurspreise, Verkauf an/aus, Pakete, kostenlose Lektionen und Freigabe der Niveaus. Bestellungen prüfen Sie unter Payments." />

      {isLoading && <Loader2 className="animate-spin text-[var(--admin-text-muted)]" />}
      {error && <p className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(error, "Konfiguration konnte nicht geladen werden (nur Super Admin).")}</p>}

      {data && Object.keys(rows).length > 0 && (
        <>
          <section className={card}>
            <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Niveaus</h2>
            <div className="flex flex-wrap gap-4">
              {LEVELS.map((lv) => (
                <label key={lv} className="flex items-center gap-2 text-sm text-[var(--admin-text-primary)]" data-testid={`angebote-level-${lv}`}>
                  <AdminCheckbox checked={!!levels[lv]} onCheckedChange={(v) => setLevels((p) => ({ ...p, [lv]: Boolean(v) }))} />
                  <span className="font-semibold">{lv}</span>
                  <span className="text-xs text-[var(--admin-text-muted)]">{levels[lv] ? "freigegeben" : "Tez orada (gesperrt)"}</span>
                </label>
              ))}
            </div>
            <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Ein gesperrtes Niveau ist für Studenten sichtbar, aber ohne Zugang — auch nicht mit dem A1 → C1 Paket oder Premium.</p>
            <div className="mt-4 flex items-center gap-3">
              <span className="text-sm text-[var(--admin-text-primary)]">Kostenlose Lektionen pro Kurs</span>
              <AdminInput className="w-20" type="number" min={0} max={5} value={free} onChange={(e) => setFree(e.target.value)} data-testid="angebote-free" />
            </div>
          </section>

          <section className={`${card} overflow-x-auto`}>
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-[var(--admin-text-muted)]">
                <tr>{["Angebot", "Inhalt", "Preis (UZS)", "Alter Preis", "Rabatt %", "Im Verkauf", "Status"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr>
              </thead>
              <tbody>
                {data.offers.map((o) => {
                  const r = rows[o.code];
                  return (
                    <tr key={o.code} className="border-t border-[var(--admin-border)]" data-testid={`angebote-row-${o.code}`}>
                      <td className="px-3 py-2.5 font-semibold text-[var(--admin-text-primary)]">{o.label}<span className="block text-xs font-normal text-[var(--admin-text-muted)]">{o.kind === "PACKAGE" ? "Paket" : "Einzelkurs"}</span></td>
                      <td className="px-3 py-2.5">
                        {o.kind === "PACKAGE" ? (
                          <div className="flex flex-wrap gap-2">
                            {LEVELS.map((lv) => (
                              <label key={lv} className="flex items-center gap-1 text-xs text-[var(--admin-text-secondary)]">
                                <AdminCheckbox checked={r.levels.includes(lv)} onCheckedChange={(v) => set(o.code, { levels: v ? [...r.levels, lv] : r.levels.filter((x) => x !== lv) })} /> {lv}
                              </label>
                            ))}
                          </div>
                        ) : <span className="text-xs text-[var(--admin-text-secondary)]">{o.levels.join(", ")}</span>}
                      </td>
                      <td className="px-3 py-2.5"><AdminInput className="w-32" inputMode="numeric" value={r.sale_price} onChange={(e) => set(o.code, { sale_price: e.target.value })} data-testid={`angebote-price-${o.code}`} /></td>
                      <td className="px-3 py-2.5"><AdminInput className="w-32" inputMode="numeric" value={r.original_price} onChange={(e) => set(o.code, { original_price: e.target.value })} /></td>
                      <td className="px-3 py-2.5"><AdminInput className="w-20" inputMode="numeric" value={r.discount_percent} onChange={(e) => set(o.code, { discount_percent: e.target.value })} /></td>
                      <td className="px-3 py-2.5"><AdminCheckbox checked={r.active} onCheckedChange={(v) => set(o.code, { active: Boolean(v) })} /></td>
                      <td className="px-3 py-2.5 text-xs">
                        {o.purchasable ? <span className="text-[var(--admin-success)]">verkäuflich</span> : <span className="text-[var(--admin-text-muted)]">nicht im Verkauf</span>}
                        {o.kind === "PACKAGE" && o.available_levels.length < o.levels.length && (
                          <span className="block text-[var(--admin-text-muted)]">öffnet jetzt: {o.available_levels.join(", ") || "—"}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>

          {message && (
            <p role="status" data-testid="angebote-message"
               className={`rounded-xl px-4 py-3 text-sm ${message.ok ? "bg-[var(--admin-success)]/10 text-[var(--admin-success)]" : "bg-[var(--admin-danger)]/10 text-[var(--admin-danger)]"}`}>{message.text}</p>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <AdminButton onClick={save} disabled={saving} data-testid="angebote-save">{saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />} Speichern</AdminButton>
            <AdminButton variant="secondary" onClick={() => load(data)} disabled={saving}><RotateCcw size={15} /> Zurücksetzen</AdminButton>
            <Link href="/admin/payments" className="text-sm font-semibold text-[var(--admin-primary)] hover:underline">Bestellungen & Zahlungen prüfen →</Link>
          </div>
          <p className="text-xs text-[var(--admin-text-muted)]">Bereits erstellte Bestellungen behalten ihren Betrag. Lektionen öffnen sich nur nach „Approve“ einer Bestellung unter Payments.</p>
        </>
      )}
    </div>
  );
}
