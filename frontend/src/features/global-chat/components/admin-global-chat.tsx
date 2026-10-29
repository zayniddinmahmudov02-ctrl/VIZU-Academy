"use client";

import { useEffect, useState } from "react";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Check, Eye, EyeOff, History, Loader2, Pin, PinOff, RotateCcw, Search, ShieldAlert, VolumeX, X } from "lucide-react";

import { AdminButton, AdminCard, AdminInput, AdminPageHeader, AdminSelect, AdminTextarea } from "@/components/admin/admin-ui";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { cn } from "@/lib/utils";
import {
  addYears,
  fmtDateTime,
  getActions,
  getAdminMessages,
  getMessageEdits,
  getRestrictions,
  getStats,
  getUserHistory,
  getWordFilter,
  moderateMessage,
  resetWordFilter,
  revokeRestriction,
  saveWordFilter,
  searchUsers,
  updateRestriction,
  type ChatMessage,
  type ModerationAction,
  type Restriction,
  type RestrictionKind,
} from "../global-chat-service";
import RestrictDialog, { fieldClass, restrictionErrorText, toLocalInput } from "./restrict-dialog";

type Tab = "review" | "messages" | "restrictions" | "log" | "filter";
type Target = { user: { id: string; name: string }; messageId?: string; kind: RestrictionKind };

const ACTION_LABELS: Record<string, string> = {
  "message.pin": "Angeheftet",
  "message.unpin": "Gelöst",
  "message.hide": "Ausgeblendet",
  "message.unhide": "Wieder eingeblendet",
  "message.approve": "Freigegeben",
  "message.flag": "Vom Wortfilter zurückgehalten",
  "message.delete": "Vom Autor gelöscht",
  "mute.create": "Stummgeschaltet",
  "mute.update": "Stummschaltung geändert",
  "mute.revoke": "Stummschaltung aufgehoben",
  "ban.create": "Gesperrt",
  "ban.update": "Sperre geändert",
  "ban.revoke": "Sperre aufgehoben",
  "filter.update": "Wortfilter geändert",
  "filter.reset": "Wortfilter zurückgesetzt",
};

const STATE_TONE: Record<Restriction["state"], string> = {
  active: "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]",
  expired: "bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]",
  revoked: "bg-[var(--admin-hover)] text-[var(--admin-text-muted)] line-through",
};

function Pill({ className, children }: { className?: string; children: React.ReactNode }) {
  return <span className={cn("inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[11px] font-semibold", className)}>{children}</span>;
}

function Pager({ page, total, pageSize, onPage }: { page: number; total: number; pageSize: number; onPage: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-end gap-2 text-sm text-[var(--admin-text-secondary)]">
      <AdminButton variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>Zurück</AdminButton>
      <span>{page} / {pages}</span>
      <AdminButton variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>Weiter</AdminButton>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">{children}</p>;
}

export default function AdminGlobalChat() {
  const { user } = useCurrentUser();
  const isSuper = user?.role === "SUPER_ADMIN";
  const qc = useQueryClient();
  const stats = useQuery({ queryKey: ["gc-stats"], queryFn: getStats, refetchInterval: 30_000 });
  const [tab, setTab] = useState<Tab>("review");
  const [target, setTarget] = useState<Target | null>(null);
  const [historyUser, setHistoryUser] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const refreshAll = () => qc.invalidateQueries({ predicate: (q) => String(q.queryKey[0]).startsWith("gc-") });

  const tabs: { id: Tab; label: string; badge?: number }[] = [
    { id: "review", label: "Prüfen", badge: stats.data?.pending },
    { id: "messages", label: "Nachrichten" },
    { id: "restrictions", label: "Mutes & Sperren", badge: (stats.data?.active_mutes ?? 0) + (stats.data?.active_bans ?? 0) },
    { id: "log", label: "Protokoll" },
    { id: "filter", label: "Wortfilter" },
  ];

  const actions = {
    restrict: (t: Target) => setTarget(t),
    history: (id: string) => setHistoryUser(id),
    done: (text: string) => {
      setFlash(text);
      refreshAll();
    },
  };

  return (
    <div>
      <AdminPageHeader title="Global Chat" description="Moderation des gemeinsamen Chats aller Benutzer: anheften, ausblenden, stummschalten, sperren." />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {([
          ["Nachrichten 24 h", stats.data?.messages_24h],
          ["Zu prüfen", stats.data?.pending],
          ["Ausgeblendet 7 T.", stats.data?.hidden_7d],
          ["Angeheftet", stats.data?.pinned],
          ["Aktive Mutes", stats.data?.active_mutes],
          ["Aktive Sperren", stats.data?.active_bans],
        ] as const).map(([label, value]) => (
          <AdminCard key={label} className="p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--admin-text-muted)]">{label}</p>
            <p className="mt-1 text-2xl font-bold text-[var(--admin-text-primary)]">{value ?? "–"}</p>
          </AdminCard>
        ))}
      </div>

      <div role="tablist" className="mb-4 flex gap-1 overflow-x-auto rounded-xl bg-[var(--admin-hover)] p-1">
        {tabs.map((t) => (
          <button key={t.id} type="button" role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
                  className={cn("inline-flex min-h-10 shrink-0 items-center gap-1.5 rounded-lg px-3 text-sm font-semibold",
                    tab === t.id ? "bg-[var(--admin-primary)] text-white" : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-card)]")}>
            {t.label}
            {!!t.badge && <span className={cn("rounded-full px-1.5 text-[10px]", tab === t.id ? "bg-white/25" : "bg-[var(--admin-primary)] text-white")}>{t.badge}</span>}
          </button>
        ))}
      </div>

      {flash && (
        <p role="status" className="mb-4 flex items-center justify-between gap-2 rounded-lg bg-success/15 px-3 py-2 text-sm text-success">
          {flash}<button type="button" onClick={() => setFlash(null)} aria-label="Schließen"><X size={14} /></button>
        </p>
      )}

      {tab === "review" && <MessagesTab fixedFilter="pending" actions={actions} />}
      {tab === "messages" && <MessagesTab actions={actions} />}
      {tab === "restrictions" && <RestrictionsTab isSuper={isSuper} actions={actions} />}
      {tab === "log" && <LogTab actions={actions} />}
      {tab === "filter" && <FilterTab onSaved={actions.done} />}

      {target && (
        <RestrictDialog target={target.user} messageId={target.messageId} initialKind={target.kind} canBanPermanently={isSuper}
                        onClose={() => setTarget(null)}
                        onDone={(r) => {
                          setTarget(null);
                          actions.done(`${r.user.name}: ${r.kind === "ban" ? "gesperrt" : "stummgeschaltet"} bis ${r.permanent ? "dauerhaft" : fmtDateTime(r.ends_at)}`);
                        }} />
      )}
      {historyUser && <UserHistoryDrawer userId={historyUser} onClose={() => setHistoryUser(null)} actions={actions} />}
    </div>
  );
}

type Actions = { restrict: (t: Target) => void; history: (id: string) => void; done: (text: string) => void };

// ---------- messages / review queue ----------

function MessagesTab({ fixedFilter, actions }: { fixedFilter?: "pending"; actions: Actions }) {
  const [filter, setFilter] = useState(fixedFilter ?? "all");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const list = useQuery({
    queryKey: ["gc-messages", filter, search, page],
    queryFn: () => getAdminMessages({ filter, q: search, page }),
    placeholderData: keepPreviousData,
    refetchInterval: fixedFilter ? 15_000 : false,
  });

  return (
    <AdminCard>
      {!fixedFilter && (
        <form className="mb-4 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); setSearch(q.trim()); setPage(1); }}>
          <div className="w-44">
            <AdminSelect value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1); }} aria-label="Filter">
              <option value="all">Alle Nachrichten</option>
              <option value="pinned">Angeheftet</option>
              <option value="hidden">Ausgeblendet</option>
              <option value="flagged">Vom Filter markiert</option>
              <option value="pending">Zu prüfen</option>
              <option value="edited">Bearbeitet</option>
              <option value="deleted">Vom Autor gelöscht</option>
            </AdminSelect>
          </div>
          <div className="min-w-48 flex-1"><AdminInput value={q} onChange={(e) => setQ(e.target.value)} placeholder="Text suchen…" /></div>
          <AdminButton type="submit" variant="secondary"><Search size={15} /> Suchen</AdminButton>
        </form>
      )}
      {fixedFilter && <p className="mb-4 text-sm text-[var(--admin-text-secondary)]">Nachrichten, die der Wortfilter zurückgehalten hat. Nur der Absender sieht sie, bis du sie freigibst oder ausblendest. Der Filter sperrt niemanden automatisch.</p>}

      {list.isLoading ? <Empty><Loader2 className="mx-auto animate-spin" /></Empty>
        : list.isError ? <Empty>Nachrichten konnten nicht geladen werden.</Empty>
        : !list.data?.items.length ? <Empty>{fixedFilter ? "Nichts zu prüfen." : "Keine Nachrichten."}</Empty>
        : (
          <ul className="divide-y divide-[var(--admin-border)]">
            {list.data.items.map((m) => <MessageRow key={m.id} m={m} actions={actions} />)}
          </ul>
        )}
      {list.data && <Pager page={page} total={list.data.total} pageSize={list.data.page_size} onPage={setPage} />}
    </AdminCard>
  );
}

function MessageVersions({ messageId }: { messageId: string }) {
  const versions = useQuery({ queryKey: ["gc-edits", messageId], queryFn: () => getMessageEdits(messageId) });
  if (versions.isLoading) return <Loader2 size={14} className="mt-2 animate-spin" />;
  if (versions.isError) return <p className="mt-2 text-xs text-[var(--admin-danger)]">Versionen konnten nicht geladen werden.</p>;
  return (
    <ol className="mt-2 space-y-1.5 border-l-2 border-[var(--admin-border)] pl-3 text-xs" data-testid="gc-admin-versions">
      {versions.data?.map((v) => (
        <li key={v.id}>
          <p className="text-[var(--admin-text-muted)]">bis {fmtDateTime(v.edited_at)}{v.previous_status !== "visible" ? ` · ${v.previous_status}` : ""}</p>
          <p className="whitespace-pre-wrap break-words text-[var(--admin-text-secondary)]">{v.previous_body}</p>
        </li>
      ))}
    </ol>
  );
}

function MessageRow({ m, actions }: { m: ChatMessage; actions: Actions }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const deleted = m.status === "deleted";

  async function run(action: "pin" | "unpin" | "hide" | "unhide" | "approve") {
    let reason: string | undefined;
    if (action === "hide") {
      const answer = window.prompt("Grund für das Ausblenden (optional):");
      if (answer === null) return;
      reason = answer.trim() || undefined;
    }
    setBusy(true);
    setError(null);
    try {
      await moderateMessage(m.id, action, reason);
      actions.done(`Nachricht: ${ACTION_LABELS[`message.${action}`]}`);
    } catch (err) {
      const code = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(code === "too_many_pins" ? "Schon 5 Nachrichten angeheftet – bitte erst eine lösen." : "Aktion fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="py-3" data-testid="gc-admin-message">
      <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--admin-text-muted)]">
        {m.sender ? (
          <button type="button" onClick={() => actions.history(m.sender!.id)} className="font-semibold text-[var(--admin-text-primary)] hover:underline">{m.sender.name}</button>
        ) : <span>Gelöschtes Konto</span>}
        {m.sender?.email && <span>{m.sender.email}</span>}
        {m.sender?.role && <Pill className="bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]">{m.sender.role}</Pill>}
        <span>· {fmtDateTime(m.created_at)}</span>
        {m.status === "pending" && <Pill className="bg-amber-500/15 text-amber-600"><ShieldAlert size={11} className="mr-1" />zu prüfen</Pill>}
        {m.status === "hidden" && <Pill className="bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]">ausgeblendet{m.hidden_reason ? `: ${m.hidden_reason}` : ""}</Pill>}
        {m.is_pinned && <Pill className="bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"><Pin size={11} className="mr-1" />angeheftet</Pill>}
        {!!m.flagged_words?.length && <Pill className="bg-amber-500/15 text-amber-600">Filter: {m.flagged_words.join(", ")}</Pill>}
        {deleted && <Pill className="bg-[var(--admin-hover)] text-[var(--admin-text-secondary)]">vom Autor gelöscht {fmtDateTime(m.deleted_at)}</Pill>}
        {m.edited_at && (
          <button type="button" onClick={() => setShowVersions((v) => !v)} aria-expanded={showVersions}
                  className="rounded-full bg-[var(--admin-hover)] px-2 py-0.5 text-[11px] font-semibold text-[var(--admin-text-secondary)] hover:underline">
            bearbeitet {fmtDateTime(m.edited_at)} – {showVersions ? "Versionen ausblenden" : "frühere Versionen"}
          </button>
        )}
      </div>
      <p className={cn("mt-1 whitespace-pre-wrap break-words text-sm text-[var(--admin-text-primary)]", deleted && "opacity-70")}>{m.body}</p>
      {showVersions && <MessageVersions messageId={m.id} />}
      <div className="mt-2 flex flex-wrap gap-1.5">
        {m.status === "pending" && <AdminButton size="sm" disabled={busy} onClick={() => run("approve")}><Check size={13} /> Freigeben</AdminButton>}
        {m.status === "visible" && (m.is_pinned
          ? <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => run("unpin")}><PinOff size={13} /> Lösen</AdminButton>
          : <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => run("pin")}><Pin size={13} /> Anheften</AdminButton>)}
        {!deleted && (m.status === "hidden"
          ? <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => run("unhide")}><Eye size={13} /> Einblenden</AdminButton>
          : <AdminButton size="sm" variant="secondary" disabled={busy} onClick={() => run("hide")}><EyeOff size={13} /> Ausblenden</AdminButton>)}
        {m.can_restrict && m.sender && (
          <>
            <AdminButton size="sm" variant="secondary" onClick={() => actions.restrict({ user: m.sender!, messageId: m.id, kind: "mute" })}><VolumeX size={13} /> Stummschalten</AdminButton>
            <AdminButton size="sm" variant="danger" onClick={() => actions.restrict({ user: m.sender!, messageId: m.id, kind: "ban" })}><Ban size={13} /> Sperren</AdminButton>
          </>
        )}
        {m.sender && <AdminButton size="sm" variant="ghost" onClick={() => actions.history(m.sender!.id)}><History size={13} /> Verlauf</AdminButton>}
      </div>
      {error && <p role="alert" className="mt-1 text-xs text-[var(--admin-danger)]">{error}</p>}
    </li>
  );
}

// ---------- restrictions ----------

function RestrictionsTab({ isSuper, actions }: { isSuper: boolean; actions: Actions }) {
  const [state, setState] = useState("active");
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<{ r: Restriction; mode: "edit" | "revoke" } | null>(null);
  const [picking, setPicking] = useState(false);
  const list = useQuery({
    queryKey: ["gc-restrictions", state, kind, search, page],
    queryFn: () => getRestrictions({ state, kind, q: search, page }),
    placeholderData: keepPreviousData,
  });

  return (
    <AdminCard>
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); setSearch(q.trim()); setPage(1); }}>
        <div className="w-36">
          <AdminSelect value={state} onChange={(e) => { setState(e.target.value); setPage(1); }} aria-label="Status">
            <option value="active">Aktiv</option>
            <option value="expired">Abgelaufen</option>
            <option value="revoked">Aufgehoben</option>
            <option value="all">Alle</option>
          </AdminSelect>
        </div>
        <div className="w-36">
          <AdminSelect value={kind} onChange={(e) => { setKind(e.target.value); setPage(1); }} aria-label="Art">
            <option value="">Mute + Sperre</option>
            <option value="mute">Nur Mutes</option>
            <option value="ban">Nur Sperren</option>
          </AdminSelect>
        </div>
        <div className="min-w-48 flex-1"><AdminInput value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name oder E-Mail…" /></div>
        <AdminButton type="submit" variant="secondary"><Search size={15} /> Suchen</AdminButton>
        <AdminButton type="button" onClick={() => setPicking(true)}><Ban size={15} /> Benutzer sperren / stummschalten</AdminButton>
      </form>

      {list.isLoading ? <Empty><Loader2 className="mx-auto animate-spin" /></Empty>
        : list.isError ? <Empty>Liste konnte nicht geladen werden.</Empty>
        : !list.data?.items.length ? <Empty>Keine Einträge.</Empty>
        : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-wide text-[var(--admin-text-muted)]">
                <tr><th className="py-2 pr-3">Benutzer</th><th className="pr-3">Art</th><th className="pr-3">Zeitraum</th><th className="pr-3">Grund</th><th className="pr-3">Von</th><th /></tr>
              </thead>
              <tbody className="divide-y divide-[var(--admin-border)] text-[var(--admin-text-primary)]">
                {list.data.items.map((r) => (
                  <tr key={r.id} data-testid="gc-restriction-row" className="align-top">
                    <td className="py-3 pr-3">
                      <button type="button" onClick={() => actions.history(r.user.id)} className="font-semibold hover:underline">{r.user.name}</button>
                      <p className="text-xs text-[var(--admin-text-muted)]">{r.user.email}</p>
                    </td>
                    <td className="pr-3 py-3">
                      <div className="flex flex-col items-start gap-1">
                        <Pill className={r.kind === "ban" ? "bg-[var(--admin-danger)]/15 text-[var(--admin-danger)]" : "bg-amber-500/15 text-amber-600"}>{r.kind === "ban" ? "Sperre" : "Mute"}</Pill>
                        <Pill className={STATE_TONE[r.state]}>{r.state === "active" ? "aktiv" : r.state === "expired" ? "abgelaufen" : "aufgehoben"}</Pill>
                      </div>
                    </td>
                    <td className="py-3 pr-3 text-xs">
                      <p>ab {fmtDateTime(r.starts_at)}</p>
                      <p className="font-semibold">bis {r.permanent ? "dauerhaft" : fmtDateTime(r.ends_at)}</p>
                      {r.revoked_at && <p className="text-[var(--admin-text-muted)]">aufgehoben {fmtDateTime(r.revoked_at)}{r.revoke_reason ? ` (${r.revoke_reason})` : ""}</p>}
                    </td>
                    <td className="max-w-xs py-3 pr-3 text-xs">
                      <p className="break-words">{r.reason}</p>
                      {r.public_note && <p className="mt-1 text-[var(--admin-text-muted)]">Hinweis: {r.public_note}</p>}
                    </td>
                    <td className="py-3 pr-3 text-xs">{r.created_by ?? "—"}<p className="text-[var(--admin-text-muted)]">{fmtDateTime(r.created_at)}</p></td>
                    <td className="py-3 text-right">
                      {r.state !== "revoked" && (isSuper || !r.permanent) && (
                        <div className="flex justify-end gap-1.5">
                          <AdminButton size="sm" variant="secondary" onClick={() => setEditing({ r, mode: "edit" })}>Dauer ändern</AdminButton>
                          {r.state === "active" && <AdminButton size="sm" variant="ghost" onClick={() => setEditing({ r, mode: "revoke" })}><RotateCcw size={13} /> Aufheben</AdminButton>}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      {list.data && <Pager page={page} total={list.data.total} pageSize={list.data.page_size} onPage={setPage} />}

      {editing && <EditRestrictionDialog r={editing.r} mode={editing.mode} isSuper={isSuper} onClose={() => setEditing(null)}
                                         onDone={(text) => { setEditing(null); actions.done(text); }} />}
      {picking && <UserPicker onClose={() => setPicking(false)} onPick={(u, kind) => { setPicking(false); actions.restrict({ user: u, kind }); }} />}
    </AdminCard>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-[70] flex items-end justify-center bg-black/50 sm:items-center sm:p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div role="dialog" aria-modal="true" aria-label={title} className="max-h-[100dvh] w-full overflow-y-auto rounded-t-2xl bg-surface-card p-5 text-text-primary shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:max-w-md sm:rounded-2xl">
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 className="text-base font-bold">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Schließen" className="rounded-full p-1.5 text-text-muted hover:bg-surface-hover"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function EditRestrictionDialog({ r, mode, isSuper, onClose, onDone }: { r: Restriction; mode: "edit" | "revoke"; isSuper: boolean; onClose: () => void; onDone: (text: string) => void }) {
  const [choice, setChoice] = useState<string>(r.kind === "ban" ? (r.permanent ? "permanent" : "date") : "date");
  const [end, setEnd] = useState(() => toLocalInput(r.ends_at ? new Date(r.ends_at) : addYears(new Date(), 1)));
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const label = r.kind === "ban" ? "Sperre" : "Mute";
  const start = new Date(r.starts_at);

  async function submit() {
    setSaving(true);
    setError(null);
    try {
      if (mode === "revoke") {
        await revokeRestriction(r.id, reason.trim() || undefined);
        onDone(`${r.user.name}: ${label} aufgehoben – darf wieder schreiben.`);
        return;
      }
      const data = choice === "permanent" ? { permanent: true }
        : choice.startsWith("y") ? { ban_years: Number(choice.slice(1)) }
        : { ends_at: new Date(end).toISOString() };
      const updated = await updateRestriction(r.id, { ...data, reason: reason.trim() || undefined });
      onDone(`${r.user.name}: ${label} jetzt bis ${updated.permanent ? "dauerhaft" : fmtDateTime(updated.ends_at)}`);
    } catch (err) {
      setError(restrictionErrorText(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={`${label} ${mode === "revoke" ? "aufheben" : "ändern"}: ${r.user.name}`} onClose={onClose}>
      <p className="mb-3 text-sm text-text-secondary">Aktuell: ab {fmtDateTime(r.starts_at)} bis {r.permanent ? "dauerhaft" : fmtDateTime(r.ends_at)}</p>
      {mode === "edit" && (
        <fieldset className="mb-3 space-y-2 text-sm">
          <legend className="mb-1 font-medium">Neues Ende</legend>
          {r.kind === "ban" && [1, 2, 3, 5].map((y) => (
            <label key={y} className="flex items-center gap-2">
              <input type="radio" name="gc-edit" checked={choice === `y${y}`} onChange={() => setChoice(`y${y}`)} />
              {y} {y === 1 ? "Jahr" : "Jahre"} ab Beginn ({fmtDateTime(addYears(start, y).toISOString())})
            </label>
          ))}
          <label className="flex items-center gap-2">
            <input type="radio" name="gc-edit" checked={choice === "date"} onChange={() => setChoice("date")} /> Datum:
            <input type="datetime-local" value={end} min={toLocalInput(new Date())} onChange={(e) => { setEnd(e.target.value); setChoice("date"); }} className={cn(fieldClass, "w-auto py-1.5")} />
          </label>
          {r.kind === "ban" && isSuper && (
            <label className="flex items-center gap-2">
              <input type="radio" name="gc-edit" checked={choice === "permanent"} onChange={() => setChoice("permanent")} /> Dauerhaft
            </label>
          )}
        </fieldset>
      )}
      <label className="mb-4 block text-sm">
        <span className="mb-1 block font-medium">{mode === "revoke" ? "Grund für die Aufhebung (optional)" : "Grund der Änderung (optional)"}</span>
        <AdminTextarea value={reason} onChange={(e) => setReason(e.target.value)} rows={2} maxLength={500} />
      </label>
      {error && <p role="alert" className="mb-3 rounded-lg bg-danger/10 p-2.5 text-sm text-danger">{error}</p>}
      <div className="flex justify-end gap-2">
        <AdminButton variant="secondary" onClick={onClose}>Abbrechen</AdminButton>
        <AdminButton disabled={saving} onClick={submit}>
          {saving && <Loader2 size={15} className="animate-spin" />}{mode === "revoke" ? "Aufheben" : "Speichern"}
        </AdminButton>
      </div>
    </Modal>
  );
}

function UserPicker({ onClose, onPick }: { onClose: () => void; onPick: (u: { id: string; name: string }, kind: RestrictionKind) => void }) {
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  useEffect(() => {
    const id = setTimeout(() => setTerm(q.trim()), 300);
    return () => clearTimeout(id);
  }, [q]);
  const users = useQuery({ queryKey: ["gc-user-search", term], queryFn: () => searchUsers(term), enabled: term.length >= 2 });

  return (
    <Modal title="Benutzer suchen" onClose={onClose}>
      <AdminInput autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, Benutzername oder E-Mail (mind. 2 Zeichen)" />
      <ul className="mt-3 max-h-80 divide-y divide-[var(--admin-border)] overflow-y-auto">
        {users.isFetching && <li className="py-3 text-center"><Loader2 size={16} className="mx-auto animate-spin" /></li>}
        {users.data?.length === 0 && <li className="py-3 text-sm text-text-muted">Niemand gefunden.</li>}
        {users.data?.map((u) => (
          <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{u.name}</p>
              <p className="truncate text-xs text-text-muted">{u.email} · {u.role}{u.status.restriction ? ` · bereits ${u.status.restriction.kind === "ban" ? "gesperrt" : "stumm"}` : ""}</p>
            </div>
            {u.is_moderator ? <span className="text-xs text-text-muted">Admin – nicht möglich</span> : (
              <div className="flex gap-1.5">
                <AdminButton size="sm" variant="secondary" onClick={() => onPick(u, "mute")}><VolumeX size={13} /> Mute</AdminButton>
                <AdminButton size="sm" variant="danger" onClick={() => onPick(u, "ban")}><Ban size={13} /> Sperre</AdminButton>
              </div>
            )}
          </li>
        ))}
      </ul>
    </Modal>
  );
}

// ---------- log ----------

function ActionText({ a }: { a: ModerationAction }) {
  const meta = a.meta ?? {};
  const detail = a.action.endsWith(".update") ? `${meta.from ? fmtDateTime(String(meta.from)) : "dauerhaft"} → ${meta.to ? fmtDateTime(String(meta.to)) : "dauerhaft"}`
    : a.action.endsWith(".create") && "ends_at" in meta ? `bis ${meta.ends_at ? fmtDateTime(String(meta.ends_at)) : "dauerhaft"}`
    : a.action === "message.flag" ? `Wörter: ${((meta.words as string[]) ?? []).join(", ")}`
    : typeof meta.excerpt === "string" ? `„${meta.excerpt}“`
    : "";
  return (
    <>
      <span className="font-semibold">{ACTION_LABELS[a.action] ?? a.action}</span>
      {detail && <span className="ml-1 break-words text-[var(--admin-text-secondary)]">{detail}</span>}
      {a.reason && <span className="block text-xs text-[var(--admin-text-muted)]">Grund: {a.reason}</span>}
    </>
  );
}

function LogTab({ actions }: { actions: Actions }) {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const log = useQuery({ queryKey: ["gc-actions", action, page], queryFn: () => getActions({ action, page }), placeholderData: keepPreviousData });
  return (
    <AdminCard>
      <div className="mb-4 w-48">
        <AdminSelect value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }} aria-label="Aktion">
          <option value="">Alle Aktionen</option>
          <option value="ban">Sperren</option>
          <option value="mute">Mutes</option>
          <option value="message">Nachrichten</option>
          <option value="filter">Wortfilter</option>
        </AdminSelect>
      </div>
      {log.isLoading ? <Empty><Loader2 className="mx-auto animate-spin" /></Empty>
        : !log.data?.items.length ? <Empty>Noch keine Einträge.</Empty>
        : (
          <ul className="divide-y divide-[var(--admin-border)] text-sm text-[var(--admin-text-primary)]">
            {log.data.items.map((a) => (
              <li key={a.id} className="grid gap-1 py-2.5 sm:grid-cols-[150px_1fr_180px]">
                <span className="text-xs text-[var(--admin-text-muted)]">{fmtDateTime(a.created_at)}</span>
                <span><ActionText a={a} /></span>
                <span className="text-xs sm:text-right">
                  {a.actor ?? "Wortfilter"}
                  {a.target_user && <> → <button type="button" onClick={() => actions.history(a.target_user!.id)} className="font-semibold hover:underline">{a.target_user.name}</button></>}
                </span>
              </li>
            ))}
          </ul>
        )}
      {log.data && <Pager page={page} total={log.data.total} pageSize={log.data.page_size} onPage={setPage} />}
    </AdminCard>
  );
}

// ---------- word filter ----------

function FilterTab({ onSaved }: { onSaved: (text: string) => void }) {
  const config = useQuery({ queryKey: ["gc-filter"], queryFn: getWordFilter });
  const [text, setText] = useState<string | null>(null);
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const words = text ?? config.data?.words.join("\n") ?? "";
  const on = enabled ?? config.data?.enabled ?? true;

  async function save(reset = false) {
    setSaving(true);
    setError(null);
    try {
      if (reset) {
        if (!window.confirm("Wortliste auf die Standardliste zurücksetzen?")) return;
        await resetWordFilter();
      } else {
        await saveWordFilter({ enabled: on, words: words.split(/[\n,]/).map((w) => w.trim()).filter(Boolean) });
      }
      setText(null);
      setEnabled(null);
      onSaved(reset ? "Wortfilter zurückgesetzt" : "Wortfilter gespeichert");
    } catch {
      setError("Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AdminCard>
      <p className="mb-3 text-sm text-[var(--admin-text-secondary)]">
        Ein Treffer hält die Nachricht nur zur Prüfung zurück (Tab „Prüfen“) – niemand wird automatisch gesperrt. Es werden nur ganze Wörter verglichen
        (Groß/Klein, Zahlen statt Buchstaben und gedehnte Buchstaben werden erkannt). <code>wort*</code> trifft alle Wörter, die so beginnen. Eine Zeile pro Eintrag.
      </p>
      {config.isLoading ? <Empty><Loader2 className="mx-auto animate-spin" /></Empty> : (
        <>
          <label className="mb-3 flex items-center gap-2 text-sm text-[var(--admin-text-primary)]">
            <input type="checkbox" checked={on} onChange={(e) => setEnabled(e.target.checked)} /> Wortfilter aktiv
          </label>
          <AdminTextarea value={words} onChange={(e) => setText(e.target.value)} rows={14} className="font-mono text-xs" aria-label="Wortliste" />
          <p className="mt-1 text-xs text-[var(--admin-text-muted)]">
            {config.data?.is_default ? "Standardliste (Usbekisch, Russisch, Deutsch, Englisch)" : `Angepasst ${fmtDateTime(config.data?.updated_at)}`}
          </p>
          {error && <p role="alert" className="mt-2 text-sm text-[var(--admin-danger)]">{error}</p>}
          <div className="mt-4 flex flex-wrap justify-end gap-2">
            {!config.data?.is_default && <AdminButton variant="secondary" disabled={saving} onClick={() => save(true)}>Standard wiederherstellen</AdminButton>}
            <AdminButton disabled={saving} onClick={() => save()}>{saving && <Loader2 size={15} className="animate-spin" />}Speichern</AdminButton>
          </div>
        </>
      )}
    </AdminCard>
  );
}

// ---------- one user's history ----------

function UserHistoryDrawer({ userId, onClose, actions }: { userId: string; onClose: () => void; actions: Actions }) {
  const history = useQuery({ queryKey: ["gc-user", userId], queryFn: () => getUserHistory(userId) });
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const h = history.data;

  return (
    <div className="fixed inset-0 z-[60] flex justify-end bg-black/40" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside role="dialog" aria-modal="true" aria-label="Moderationsverlauf" data-testid="gc-user-history"
             className="h-full w-full max-w-lg overflow-y-auto bg-surface-card p-5 text-text-primary shadow-[var(--shadow-lg)]">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold">{h?.user.name ?? "…"}</h2>
            {h && <p className="text-sm text-text-muted">{h.user.email} · {h.user.role}</p>}
          </div>
          <button type="button" onClick={onClose} aria-label="Schließen" className="rounded-full p-1.5 text-text-muted hover:bg-surface-hover"><X size={18} /></button>
        </div>
        {history.isLoading && <Loader2 className="mx-auto animate-spin" />}
        {history.isError && <p className="text-sm text-danger">Verlauf konnte nicht geladen werden.</p>}
        {h && (
          <>
            <div className={cn("mb-4 rounded-xl p-3 text-sm", h.status.restriction ? "bg-danger/10 text-danger" : "bg-success/10 text-success")}>
              {h.status.restriction
                ? `${h.status.restriction.kind === "ban" ? "Gesperrt" : "Stummgeschaltet"} bis ${h.status.restriction.permanent ? "dauerhaft" : fmtDateTime(h.status.restriction.ends_at)}`
                : "Darf im Global Chat schreiben."}
            </div>
            <div className="mb-4 grid grid-cols-4 gap-2 text-center text-xs">
              {([["Nachrichten", h.messages.total], ["Ausgeblendet", h.messages.hidden], ["Zu prüfen", h.messages.pending], ["Filter-Treffer", h.messages.flagged],
                 ["Bearbeitet", h.messages.edited], ["Selbst gelöscht", h.messages.deleted]] as const).map(([l, v]) => (
                <div key={l} className="rounded-lg bg-surface-hover p-2"><p className="text-lg font-bold text-text-primary">{v}</p><p className="text-text-muted">{l}</p></div>
              ))}
            </div>
            {!h.user.is_moderator && (
              <div className="mb-5 flex gap-2">
                <AdminButton size="sm" variant="secondary" onClick={() => actions.restrict({ user: h.user, kind: "mute" })}><VolumeX size={13} /> Stummschalten</AdminButton>
                <AdminButton size="sm" variant="danger" onClick={() => actions.restrict({ user: h.user, kind: "ban" })}><Ban size={13} /> Sperren</AdminButton>
              </div>
            )}
            <h3 className="mb-2 text-sm font-bold">Mutes & Sperren ({h.restrictions.length})</h3>
            {h.restrictions.length === 0 ? <p className="mb-4 text-sm text-text-muted">Keine.</p> : (
              <ul className="mb-5 space-y-2">
                {h.restrictions.map((r) => (
                  <li key={r.id} className="rounded-lg bg-surface-hover p-2.5 text-xs">
                    <p className="font-semibold">{r.kind === "ban" ? "Sperre" : "Mute"} · {r.state} · {fmtDateTime(r.starts_at)} → {r.permanent ? "dauerhaft" : fmtDateTime(r.ends_at)}</p>
                    <p className="mt-0.5 break-words text-text-secondary">{r.reason}</p>
                    <p className="text-text-muted">von {r.created_by ?? "—"}{r.revoked_at ? ` · aufgehoben ${fmtDateTime(r.revoked_at)}` : ""}</p>
                  </li>
                ))}
              </ul>
            )}
            <h3 className="mb-2 text-sm font-bold">Verlauf ({h.actions.length})</h3>
            {h.actions.length === 0 ? <p className="text-sm text-text-muted">Keine Moderation bisher.</p> : (
              <ul className="space-y-2 text-sm">
                {h.actions.map((a) => (
                  <li key={a.id} className="border-l-2 border-surface-border pl-3">
                    <p className="text-xs text-text-muted">{fmtDateTime(a.created_at)} · {a.actor ?? "Wortfilter"}</p>
                    <ActionText a={a} />
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
