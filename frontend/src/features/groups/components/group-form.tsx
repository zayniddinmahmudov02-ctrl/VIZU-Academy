"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, Copy, Loader2 } from "lucide-react";

import { useTranslation } from "@/lib/i18n/use-translation";
import { cn } from "@/lib/utils";
import { getGroupOptions, LEVELS, type GroupInput, type GroupSummary, type Level } from "../groups-service";
import { card, input, primaryBtn, secondaryBtn, textarea, useErrorText } from "./ui";

const label = "mb-1 block text-xs font-medium text-text-secondary";

/** Create / edit a group. The teacher select appears only for a SUPER_ADMIN
 *  (the options endpoint lists teachers only for them; the backend rejects
 *  a teacher_id from anyone else anyway). */
export default function GroupForm({ group, onSubmit, onCancel }: {
  group?: GroupSummary;
  onSubmit: (data: GroupInput) => Promise<void>;
  onCancel?: () => void;
}) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const options = useQuery({ queryKey: ["groups", "options"], queryFn: getGroupOptions, staleTime: 5 * 60_000 });
  const [form, setForm] = useState<GroupInput>({
    name: group?.name ?? "",
    description: group?.description ?? "",
    level: group?.level ?? "A1",
    mode: group?.mode ?? "online",
    status: group?.status,
    start_date: group?.start_date ?? "",
    end_date: group?.end_date ?? "",
    capacity: group?.capacity ?? null,
    course_ids: group?.courses.map((c) => c.id) ?? [],
    teacher_id: group?.teacher.id ?? "",
    chat_mode: group?.chat_mode ?? "open",
    code_expires_at: "",
    code_max_uses: null,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (p: Partial<GroupInput>) => setForm((f) => ({ ...f, ...p }));
  const courses = (options.data?.courses ?? []).filter((c) => c.level?.toUpperCase() === form.level);
  const teachers = options.data?.teachers ?? [];

  async function submit() {
    setBusy(true);
    setError(null);
    const data: GroupInput = {
      ...form,
      description: form.description || null,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      capacity: form.capacity || null,
      teacher_id: form.teacher_id || null,
      course_ids: form.course_ids.filter((id) => courses.some((c) => c.id === id)),
      code_expires_at: form.code_expires_at ? new Date(form.code_expires_at).toISOString() : null,
    };
    if (group) {
      delete data.chat_mode;
      delete data.code_expires_at;
      delete data.code_max_uses;
      if (!teachers.length) delete data.teacher_id;
      if (data.status === group.status) delete data.status;
    } else if (!teachers.length) {
      delete data.teacher_id;
    }
    try {
      await onSubmit(data);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className={cn(card, "space-y-4 p-5")} onSubmit={(e) => { e.preventDefault(); submit(); }} data-testid="group-form">
      <h2 className="text-base font-bold text-text-primary">{group ? t("groups.editGroup") : t("groups.newGroup")}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2"><label className={label}>{t("groups.name")}</label>
          <input className={input} value={form.name} minLength={2} maxLength={120} required onChange={(e) => set({ name: e.target.value })} /></div>
        <div className="sm:col-span-2"><label className={label}>{t("groups.description")}</label>
          <textarea className={textarea} rows={2} maxLength={2000} value={form.description ?? ""} onChange={(e) => set({ description: e.target.value })} /></div>
        {teachers.length > 0 && (
          <div className="sm:col-span-2"><label className={label}>{t("groups.teacher")}</label>
            <select className={input} value={form.teacher_id ?? ""} onChange={(e) => set({ teacher_id: e.target.value })}>
              <option value="">— {t("groups.teacher")} —</option>
              {teachers.map((tc) => <option key={tc.id} value={tc.id}>{tc.name} ({tc.email})</option>)}
            </select></div>
        )}
        <div><label className={label}>{t("groups.level")}</label>
          <select className={input} value={form.level} onChange={(e) => set({ level: e.target.value as Level, course_ids: [] })}>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select></div>
        <div><label className={label}>{t("groups.mode")}</label>
          <select className={input} value={form.mode} onChange={(e) => set({ mode: e.target.value as GroupInput["mode"] })}>
            {(["online", "offline", "hybrid"] as const).map((m) => <option key={m} value={m}>{t(`groups.mode_${m}`)}</option>)}
          </select></div>
        <div className="sm:col-span-2">
          <span className={label}>{t("groups.courses")}</span>
          <div className="flex flex-wrap gap-2">
            {courses.length === 0 && <span className="text-xs text-text-muted">{t("groups.noCourses")}</span>}
            {courses.map((c) => {
              const on = form.course_ids.includes(c.id);
              return (
                <label key={c.id} className={cn("flex min-h-11 cursor-pointer items-center gap-2 rounded-xl px-3 text-sm ring-1", on ? "bg-accent-blue/10 text-accent-blue ring-accent-blue/40" : "text-text-secondary ring-surface-border")}>
                  <input type="checkbox" checked={on} onChange={() => set({ course_ids: on ? form.course_ids.filter((x) => x !== c.id) : [...form.course_ids, c.id] })} />
                  {c.title}
                </label>
              );
            })}
          </div>
        </div>
        <div><label className={label}>{t("groups.startDate")}</label>
          <input type="date" className={input} value={form.start_date ?? ""} onChange={(e) => set({ start_date: e.target.value })} /></div>
        <div><label className={label}>{t("groups.endDate")}</label>
          <input type="date" className={input} value={form.end_date ?? ""} onChange={(e) => set({ end_date: e.target.value })} /></div>
        <div><label className={label}>{t("groups.capacity")}</label>
          <input type="number" min={1} max={1000} className={input} value={form.capacity ?? ""} onChange={(e) => set({ capacity: e.target.value ? Number(e.target.value) : null })} /></div>
        {group ? (
          <div><label className={label}>{t("groups.status")}</label>
            <select className={input} value={form.status} onChange={(e) => set({ status: e.target.value as GroupInput["status"] })} disabled={group.status === "blocked" && !teachers.length}>
              {(["active", "paused", "archived", ...(teachers.length || group.status === "blocked" ? ["blocked"] : [])] as const).map((s) => <option key={s} value={s}>{t(`groups.status_${s}`)}</option>)}
            </select></div>
        ) : (
          <>
            <div><label className={label}>{t("groups.chatMode")}</label>
              <select className={input} value={form.chat_mode} onChange={(e) => set({ chat_mode: e.target.value as GroupInput["chat_mode"] })}>
                {(["open", "teacher_only", "closed"] as const).map((m) => <option key={m} value={m}>{t(`groups.chat_${m}`)}</option>)}
              </select></div>
            <div><label className={label}>{t("groups.expiresAt")}</label>
              <input type="datetime-local" className={input} value={form.code_expires_at ?? ""} onChange={(e) => set({ code_expires_at: e.target.value })} /></div>
            <div><label className={label}>{t("groups.maxUses")}</label>
              <input type="number" min={1} className={input} value={form.code_max_uses ?? ""} onChange={(e) => set({ code_max_uses: e.target.value ? Number(e.target.value) : null })} /></div>
          </>
        )}
      </div>
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
      <div className="flex flex-wrap justify-end gap-2">
        {onCancel && <button type="button" className={secondaryBtn} onClick={onCancel}>{t("groups.cancel")}</button>}
        <button type="submit" className={primaryBtn} disabled={busy || form.name.trim().length < 2}>
          {busy && <Loader2 size={14} className="animate-spin" />} {group ? t("groups.save") : t("groups.createGroup")}
        </button>
      </div>
    </form>
  );
}

/** The plain join code exists only in this response — shown once. */
export function CodeReveal({ code, onClose }: { code: string; onClose?: () => void }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  return (
    <div className="space-y-3 rounded-card bg-success/10 p-5 ring-1 ring-success/30" role="status" data-testid="code-reveal">
      <p className="text-sm font-bold text-text-primary">{t("groups.code")}</p>
      <div className="flex flex-wrap items-center gap-3">
        <code className="rounded-xl bg-surface-card px-4 py-2 font-mono text-2xl font-bold tracking-[0.2em] text-text-primary ring-1 ring-surface-border">{code}</code>
        <button type="button" className={secondaryBtn} onClick={() => { navigator.clipboard?.writeText(code).then(() => setCopied(true)).catch(() => undefined); }}>
          {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? t("groups.copied") : t("groups.copy")}
        </button>
        {onClose && <button type="button" className={secondaryBtn} onClick={onClose}>OK</button>}
      </div>
      <p className="text-xs text-text-secondary">{t("groups.codeOnce")}</p>
    </div>
  );
}
