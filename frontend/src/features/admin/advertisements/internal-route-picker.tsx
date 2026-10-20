"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";

import { AdminInput, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";

import type { InternalRoute } from "./advertisement-admin-service";

const PARAM_LABELS: Record<string, string> = { level: "Niveau", offer: "Angebot" };

/** Picks a student page for an internal Werbung link: only pages of the
 * server's whitelist (GET /admin/advertisements/internal-routes), grouped and
 * searchable; parameters only from their allowed values. */
export default function InternalRoutePicker({
  routes,
  value,
  params,
  onChange,
}: {
  routes: InternalRoute[];
  value: string;
  params: Record<string, string>;
  onChange: (route: string, params: Record<string, string>) => void;
}) {
  const [query, setQuery] = useState("");
  const selected = routes.find((r) => r.key === value);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const map = new Map<string, InternalRoute[]>();
    for (const r of routes) {
      // the selected page always stays in the list, even when filtered out
      if (q && r.key !== value && !`${r.group} ${r.label} ${r.path}`.toLowerCase().includes(q)) continue;
      map.set(r.group, [...(map.get(r.group) ?? []), r]);
    }
    return [...map.entries()];
  }, [routes, query, value]);

  return (
    <div className="space-y-3" data-testid="ad-internal-route">
      <div>
        <AdminLabel>Studentenseite</AdminLabel>
        <div className="relative mb-2">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--admin-text-muted)]" />
          <AdminInput className="pl-8" placeholder="Seite suchen…" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Seite suchen" />
        </div>
        <AdminSelect
          value={value}
          onChange={(e) => {
            const route = routes.find((r) => r.key === e.target.value);
            // keep still-valid params, reset the rest
            const next = Object.fromEntries((route?.params ?? []).map((p) => [p.name, p.choices.includes(params[p.name]) ? params[p.name] : ""]));
            onChange(e.target.value, next);
          }}
          data-testid="ad-internal-route-select"
        >
          <option value="">— Seite wählen —</option>
          {value && !selected && <option value={value}>{value} (nicht mehr verfügbar)</option>}
          {groups.map(([group, items]) => (
            <optgroup key={group} label={group}>
              {items.map((r) => (
                <option key={r.key} value={r.key}>
                  {r.label} — {r.path}
                </option>
              ))}
            </optgroup>
          ))}
        </AdminSelect>
        {groups.length === 0 && <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Keine Seite gefunden.</p>}
      </div>

      {selected && selected.params.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {selected.params.map((p) => (
            <div key={p.name}>
              <AdminLabel>{PARAM_LABELS[p.name] ?? p.name}</AdminLabel>
              <AdminSelect value={params[p.name] ?? ""} onChange={(e) => onChange(value, { ...params, [p.name]: e.target.value })}
                           data-testid={`ad-internal-param-${p.name}`}>
                <option value="">— wählen —</option>
                {p.choices.map((c) => (
                  <option key={c} value={c}>
                    {c.toUpperCase()}
                  </option>
                ))}
              </AdminSelect>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-[var(--admin-text-muted)]">
        Nur echte Seiten des Studentenpanels. Der Link öffnet die Seite — Zugangsregeln (bezahlte Lektionen, Kurse nicht im Verkauf) gelten weiter.
      </p>
    </div>
  );
}
