"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { AdminButton, AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import { apiErrorMessage } from "@/features/admin/services/lesson-skills-admin-service";
import { adminEndRoom, adminOverview, type AdminRoom } from "@/features/video-rooms/video-rooms-service";

const LIVEKIT_LABEL = { available: "Erreichbar", unconfigured: "Nicht konfiguriert", unavailable: "Nicht erreichbar" } as const;
const STATUS_LABEL: Record<string, string> = { live: "Live", scheduled: "Geplant", ended: "Beendet", cancelled: "Abgesagt" };
const REASON_LABEL: Record<string, string> = { host: "Lehrkraft", admin: "Administrator", empty: "Leer (LiveKit)", expired: "Abgelaufen", cancelled: "Abgesagt" };
const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" }) : "—");

function RoomTable({ rooms, onEnd, busy, kind }: { rooms: AdminRoom[]; onEnd?: (r: AdminRoom) => void; busy: string | null; kind: "live" | "scheduled" | "recent" }) {
  if (!rooms.length) return <p className="text-sm text-[var(--admin-text-muted)]">Keine Einträge.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="text-xs text-[var(--admin-text-muted)]">
          <tr>
            <th className="py-2 pr-3">Gruppe</th><th className="py-2 pr-3">Lehrkraft</th><th className="py-2 pr-3">Titel</th>
            <th className="py-2 pr-3">{kind === "scheduled" ? "Geplant für" : kind === "live" ? "Begonnen" : "Beendet"}</th>
            {kind === "live" && <th className="py-2 pr-3">Online (DB / LiveKit)</th>}
            {kind === "recent" && <th className="py-2 pr-3">Status / Grund</th>}
            {onEnd && <th className="py-2" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--admin-border)]">
          {rooms.map((r) => (
            <tr key={r.id} data-testid="admin-video-room">
              <td className="py-2 pr-3 font-medium text-[var(--admin-text-primary)]">
                <Link href={r.group.id ? `/teacher/groups/${r.group.id}?tab=video` : "/admin/lehrer-marktplatz?tab=spezialstunden"} className="hover:underline">{r.group.name}</Link> <span className="text-xs text-[var(--admin-text-muted)]">{r.group.level}</span>
              </td>
              <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{r.group.teacher}</td>
              <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{r.title}</td>
              <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{fmt(kind === "scheduled" ? r.scheduled_at : kind === "live" ? r.started_at : r.ended_at)}</td>
              {kind === "live" && (
                <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">
                  {r.online_count} / {r.server_participants ?? "—"}{r.server_room_active === false && <span className="ml-2 text-xs text-[var(--admin-danger)]">LiveKit-Raum fehlt</span>}
                </td>
              )}
              {kind === "recent" && <td className="py-2 pr-3 text-[var(--admin-text-secondary)]">{STATUS_LABEL[r.status]} · {REASON_LABEL[r.end_reason ?? ""] ?? r.end_reason ?? "—"}</td>}
              {onEnd && (
                <td className="py-2 text-right">
                  <AdminButton size="sm" variant="danger" disabled={busy === r.id} onClick={() => onEnd(r)} data-testid="admin-video-end">Beenden</AdminButton>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Admin -> Videounterricht: live and scheduled group video lessons from the database and the LiveKit server
 *  (SUPER_ADMIN; the backend enforces it). Ending a lesson here removes everyone from the LiveKit room. */
export default function AdminVideoRoomsPage() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin", "video-rooms"], queryFn: adminOverview, refetchInterval: 15_000 });
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function end(r: AdminRoom) {
    if (!window.confirm(`„${r.title}" (${r.group.name}) für alle beenden?`)) return;
    setBusy(r.id);
    setMsg(null);
    try {
      await adminEndRoom(r.id);
      await qc.invalidateQueries({ queryKey: ["admin", "video-rooms"] });
      setMsg({ ok: true, text: "Stunde beendet." });
    } catch (err) {
      setMsg({ ok: false, text: apiErrorMessage(err, "Aktion fehlgeschlagen.") });
    } finally {
      setBusy(null);
    }
  }

  const d = q.data;
  return (
    <div className="space-y-6" data-testid="admin-video-rooms">
      <AdminPageHeader title="Videounterricht" description="Gruppen-Videostunden (LiveKit SFU): Status aus Datenbank und Videoserver, Aktualisierung alle 15 Sekunden." />
      {q.isLoading ? <Loader2 className="animate-spin text-[var(--admin-text-muted)]" /> : q.isError || !d ? (
        <p role="alert" className="text-sm text-[var(--admin-danger)]">{apiErrorMessage(q.error, "Status konnte nicht geladen werden.")}</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {[["LiveKit", LIVEKIT_LABEL[d.livekit_status]], ["Live", d.totals.live], ["Online", d.totals.online], ["Geplant", d.totals.scheduled],
              ["Plätze / Token", `${d.limits.max_participants} / ${Math.round(d.limits.token_ttl_seconds / 60)} min`]].map(([label, value]) => (
              <AdminCard key={label as string}>
                <p className="text-xs text-[var(--admin-text-muted)]">{label}</p>
                <p data-testid={label === "LiveKit" ? "admin-livekit-status" : undefined} className="text-xl font-bold text-[var(--admin-text-primary)]">{value}</p>
              </AdminCard>
            ))}
          </div>
          {msg && <p role="status" className={msg.ok ? "text-sm text-[var(--admin-success,#16a34a)]" : "text-sm text-[var(--admin-danger)]"}>{msg.text}</p>}
          <AdminCard><h2 className="mb-3 font-semibold text-[var(--admin-text-primary)]">Live</h2><RoomTable rooms={d.live} kind="live" onEnd={end} busy={busy} /></AdminCard>
          <AdminCard><h2 className="mb-3 font-semibold text-[var(--admin-text-primary)]">Geplant</h2><RoomTable rooms={d.scheduled} kind="scheduled" busy={busy} /></AdminCard>
          <AdminCard><h2 className="mb-3 font-semibold text-[var(--admin-text-primary)]">Zuletzt</h2><RoomTable rooms={d.recent} kind="recent" busy={busy} /></AdminCard>
        </>
      )}
    </div>
  );
}
