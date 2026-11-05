"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, CircleAlert } from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import { getBattleOverview } from "@/features/admin/services/battle-admin-service";
import ThemesPanel from "@/features/battle/admin/themes-panel";
import WordsPanel from "@/features/battle/admin/words-panel";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "overview", label: "Übersicht" },
  { key: "words", label: "Wörter & Bilder" },
  { key: "themes", label: "Design & Themes" },
] as const;

/** Game Management → Battle. */
export default function BattleAdmin() {
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("overview");
  return (
    <div data-testid="admin-battle">
      <AdminPageHeader title="Game Management · Battle" description="VIZU DEUTSCH BATTLE — Bildwörter, Bildbibliothek mit Lizenzen, Arena-Themes je CEFR-Stufe." />
      <div className="mb-5 flex gap-1 overflow-x-auto rounded-xl bg-[var(--admin-card)] p-1 ring-1 ring-[var(--admin-border)]" role="tablist">
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)} data-testid={`admin-battle-tab-${t.key}`}
                  className={cn("shrink-0 rounded-lg px-4 py-2 text-sm font-semibold transition", tab === t.key ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)]")}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === "overview" && <Overview />}
      {tab === "words" && <WordsPanel />}
      {tab === "themes" && <ThemesPanel />}
    </div>
  );
}

function Overview() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["admin-battle-overview"], queryFn: getBattleOverview });
  if (isLoading) return <AdminCard><p className="text-sm text-[var(--admin-text-secondary)]">Lädt…</p></AdminCard>;
  if (isError || !data) return <AdminCard><p className="text-sm text-[var(--admin-danger)]">Übersicht konnte nicht geladen werden.</p></AdminCard>;
  return (
    <div className="space-y-5" data-testid="admin-battle-overview">
      <AdminCard>
        <h2 className="mb-3 text-sm font-bold text-[var(--admin-text-primary)]">Spielbereit je Stufe (mind. {data.min_pool} veröffentlichte Bildwörter)</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Object.entries(data.stages).map(([stage, s]) => (
            <div key={stage} className="rounded-xl p-3 ring-1 ring-[var(--admin-border)]">
              <p className="flex items-center gap-1.5 text-lg font-bold text-[var(--admin-text-primary)]">
                {s.ready ? <CheckCircle2 size={16} className="text-emerald-400" /> : <CircleAlert size={16} className="text-amber-400" />} {stage}
              </p>
              <p className="text-xs text-[var(--admin-text-secondary)]">{s.pool} Wörter im Pool</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-[var(--admin-text-muted)]">Höhere Stufen spielen mit den Wörtern der Stufen darunter, bis eigene Wörter veröffentlicht sind. C1+ hat keine eigene Wortquelle.</p>
      </AdminCard>
      <div className="grid gap-5 lg:grid-cols-3">
        <AdminCard>
          <h2 className="mb-3 text-sm font-bold text-[var(--admin-text-primary)]">Wörter je Level</h2>
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-[var(--admin-text-muted)]"><tr><th>Level</th><th>Gesamt</th><th>Spielbar</th><th>Ohne Bild</th></tr></thead>
            <tbody className="text-[var(--admin-text-primary)]">
              {Object.entries(data.levels).map(([lv, r]) => <tr key={lv}><td className="py-1 font-semibold">{lv}</td><td>{r.words}</td><td>{r.playable}</td><td>{r.without_image}</td></tr>)}
            </tbody>
          </table>
        </AdminCard>
        <AdminCard>
          <h2 className="mb-3 text-sm font-bold text-[var(--admin-text-primary)]">Bilder nach Status</h2>
          <ul className="space-y-1 text-sm text-[var(--admin-text-primary)]">
            {Object.entries(data.images).map(([s, n]) => <li key={s} className="flex justify-between"><span>{s}</span><b>{n}</b></li>)}
          </ul>
        </AdminCard>
        <AdminCard>
          <h2 className="mb-3 text-sm font-bold text-[var(--admin-text-primary)]">Kämpfe (7 Tage) · {data.players} Spieler</h2>
          {data.matches_7d.length === 0 ? <p className="text-sm text-[var(--admin-text-secondary)]">Noch keine Kämpfe.</p> : (
            <ul className="space-y-1 text-sm text-[var(--admin-text-primary)]">
              {data.matches_7d.map((m) => <li key={`${m.mode}-${m.status}`} className="flex justify-between"><span>{m.mode} · {m.status}</span><b>{m.count}</b></li>)}
            </ul>
          )}
        </AdminCard>
      </div>
    </div>
  );
}
