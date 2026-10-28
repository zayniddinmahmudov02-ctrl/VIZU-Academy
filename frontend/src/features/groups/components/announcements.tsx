"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, ArchiveRestore, Megaphone, Pin, PinOff } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { createAnnouncement, getAnnouncements, updateAnnouncement } from "../groups-service";
import { card, ErrorBox, fmtDate, input, Loading, primaryBtn, textarea, useErrorText } from "./ui";

/** Announcements; the group's teacher also writes, pins and archives them. */
export default function Announcements({ groupId, manager }: { groupId: string; manager: boolean }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const errorText = useErrorText();
  const key = ["groups", groupId, "announcements", manager];
  const list = useQuery({ queryKey: key, queryFn: () => getAnnouncements(groupId, manager) });
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [pin, setPin] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(fn: () => Promise<unknown>, reset = false) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      if (reset) {
        setTitle("");
        setBody("");
        setPin(false);
      }
      await qc.invalidateQueries({ queryKey: ["groups", groupId, "announcements"] });
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {manager && (
        <form className={cn(card, "space-y-3 p-5")} onSubmit={(e) => { e.preventDefault(); run(() => createAnnouncement(groupId, { title, body, is_pinned: pin }), true); }}>
          <p className="flex items-center gap-2 text-sm font-bold text-text-primary"><Megaphone size={16} /> {t("groups.newAnnouncement")}</p>
          <input className={input} placeholder={t("groups.titleField")} value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} required />
          <textarea className={textarea} placeholder={t("groups.bodyField")} rows={4} value={body} maxLength={5000} onChange={(e) => setBody(e.target.value)} required />
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label className="flex items-center gap-2 text-sm text-text-secondary"><input type="checkbox" checked={pin} onChange={(e) => setPin(e.target.checked)} /> {t("groups.pinned")}</label>
            <button type="submit" className={primaryBtn} disabled={busy || !title.trim() || !body.trim()}>{t("groups.publish")}</button>
          </div>
          {error && <p role="alert" className="text-xs text-danger">{error}</p>}
        </form>
      )}

      {list.isLoading ? <Loading /> : list.isError ? <ErrorBox error={list.error} onRetry={() => list.refetch()} /> : (list.data ?? []).length === 0 ? (
        <p className={cn(card, "p-6 text-center text-sm text-text-muted")}>{t("groups.noAnnouncements")}</p>
      ) : (
        <ul className="space-y-3">
          {list.data!.map((a) => (
            <li key={a.id} className={cn(card, "p-5", a.is_pinned && "ring-accent-blue/40", a.archived && "opacity-60")}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="flex items-center gap-1.5 text-base font-bold text-text-primary">{a.is_pinned && <Pin size={14} className="text-accent-blue" />}{a.title}</h3>
                  <p className="text-xs text-text-muted">{a.author ?? "—"} · {fmtDate(a.created_at, true)}</p>
                </div>
                {manager && (
                  <div className="flex shrink-0 gap-1">
                    <button type="button" className="rounded-lg p-2 text-text-secondary hover:bg-surface-hover" disabled={busy}
                            aria-label={a.is_pinned ? t("groups.unpin") : t("groups.pin")} title={a.is_pinned ? t("groups.unpin") : t("groups.pin")}
                            onClick={() => run(() => updateAnnouncement(groupId, a.id, { is_pinned: !a.is_pinned }))}>{a.is_pinned ? <PinOff size={15} /> : <Pin size={15} />}</button>
                    <button type="button" className="rounded-lg p-2 text-text-secondary hover:bg-surface-hover" disabled={busy}
                            aria-label={a.archived ? t("groups.restore") : t("groups.archive")} title={a.archived ? t("groups.restore") : t("groups.archive")}
                            onClick={() => run(() => updateAnnouncement(groupId, a.id, { archived: !a.archived }))}>{a.archived ? <ArchiveRestore size={15} /> : <Archive size={15} />}</button>
                  </div>
                )}
              </div>
              <p className="mt-3 whitespace-pre-wrap break-words text-sm text-text-secondary">{a.body}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
