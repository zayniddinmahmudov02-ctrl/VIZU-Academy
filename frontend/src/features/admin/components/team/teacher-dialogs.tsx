"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, KeyRound, ShieldCheck, Trash2 } from "lucide-react";

import { AdminButton, AdminInput, AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import ConfirmDialog from "@/components/admin/confirm-dialog";
import FormDialog from "@/components/admin/form-dialog";
import {
  assignTeamCourse, assignTeamGroup, createTeamTeacher, getTeamChoices, getTeamTeacher, removeTeamCourse, removeTeamGroup, resetTeamPassword,
  setTeamControl, setTeamStatus, updateTeamTeacher, type TeamTeacherDetail,
} from "@/features/admin/services/team-service";
import { cn } from "@/lib/utils";

const ERRORS: Record<string, string> = {
  USERNAME_TAKEN: "Dieser Benutzername ist bereits vergeben.",
  USERNAME_INVALID: "Benutzername: 3–50 Zeichen, nur a–z, 0–9, _ . -",
  EMAIL_TAKEN: "Diese E-Mail-Adresse wird bereits verwendet.",
  EMAIL_INVALID: "Bitte eine gültige E-Mail-Adresse eingeben (oder leer lassen).",
  PASSWORD_TOO_WEAK: "Passwort: mindestens 10 Zeichen mit Buchstaben und Ziffern.",
  NAME_REQUIRED: "Bitte den vollständigen Namen eingeben.",
  GROUP_NOT_FOUND: "Gruppe nicht gefunden.",
  COURSE_NOT_FOUND: "Kurs nicht gefunden.",
  TEACHER_NOT_FOUND: "Lehrkraft nicht gefunden.",
};

export function teamError(err: unknown, fallback = "Die Aktion ist fehlgeschlagen."): string {
  const data = (err as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data;
  const raw = data?.message ?? data?.detail;
  if (typeof raw !== "string" || !raw) return fallback;
  const code = raw.split(":")[0].trim();
  return ERRORS[code] ?? raw;
}

export const ACTION_LABELS: Record<string, string> = {
  team_teacher_created: "Konto angelegt",
  team_teacher_updated: "Daten geändert",
  team_control_changed: "Kontroll-Berechtigung",
  team_status_changed: "Status",
  team_password_reset: "Passwort zurückgesetzt",
  team_group_assigned: "Gruppe zugewiesen",
  team_group_removed: "Gruppe entfernt",
  team_course_assigned: "Kurs zugewiesen",
  team_course_removed: "Kurs entfernt",
};

export function formatDe(iso: string | null | undefined, withTime = true): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("de-DE", withTime ? { dateStyle: "short", timeStyle: "short", timeZone: "Asia/Tashkent" } : { dateStyle: "short", timeZone: "Asia/Tashkent" });
}

function KontrollQuestion({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <fieldset className="rounded-xl border border-[var(--admin-border)] p-3" data-testid="kontroll-question">
      <legend className="px-1 text-sm font-semibold text-[var(--admin-text-primary)]">Darf dieser Lehrer auf den Bereich „Kontroll“ zugreifen?</legend>
      <div className="mt-1 grid gap-2 sm:grid-cols-2">
        {[[true, "Ja — Kontroll aktivieren"], [false, "Nein — Kein Zugriff"]].map(([v, label]) => (
          <label key={String(v)} className={cn("flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm ring-1",
            value === v ? "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)] ring-[var(--admin-primary)]/40" : "text-[var(--admin-text-secondary)] ring-[var(--admin-border)]")}>
            <input type="radio" name="kontroll" checked={value === v} onChange={() => onChange(v as boolean)} data-testid={v ? "kontroll-yes" : "kontroll-no"} />
            {label as string}
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Kontroll zeigt die Aktivität aller Schüler (nur lesen). Standard: Nein. Jede Änderung wird protokolliert.</p>
    </fieldset>
  );
}

function PasswordResult({ username, password, onClose }: { username: string; password: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  return (
    <FormDialog open onOpenChange={(o) => !o && onClose()} title="Zugangsdaten" description="Das vorläufige Passwort wird nur jetzt angezeigt. Beim ersten Login muss die Lehrkraft ein eigenes Passwort festlegen."
                footer={<AdminButton onClick={onClose} data-testid="password-result-close">Fertig</AdminButton>}>
      <div className="space-y-3" data-testid="password-result">
        <div><p className="text-xs text-[var(--admin-text-muted)]">Benutzername</p><p className="font-mono text-sm text-[var(--admin-text-primary)]" data-testid="result-username">{username}</p></div>
        <div>
          <p className="text-xs text-[var(--admin-text-muted)]">Vorläufiges Passwort</p>
          <div className="mt-1 flex items-center gap-2">
            <code className="flex-1 rounded-lg bg-[var(--admin-hover)] px-3 py-2 font-mono text-sm text-[var(--admin-text-primary)]" data-testid="result-password">{password}</code>
            <AdminButton size="sm" variant="secondary" onClick={() => { void navigator.clipboard?.writeText(`${username} / ${password}`); setCopied(true); }}>
              <Copy size={14} /> {copied ? "Kopiert" : "Kopieren"}
            </AdminButton>
          </div>
        </div>
      </div>
    </FormDialog>
  );
}

export function CreateTeacherDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const qc = useQueryClient();
  const empty = { full_name: "", username: "", email: "", password: "", own: false, control: false };
  const [form, setForm] = useState(empty);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ username: string; password: string } | null>(null);
  const close = () => { setForm(empty); setError(null); onOpenChange(false); };
  const create = useMutation({
    mutationFn: () => createTeamTeacher({ full_name: form.full_name.trim(), username: form.username.trim().toLowerCase(), email: form.email.trim() || null,
                                          password: form.own ? form.password : null, can_access_student_control: form.control }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["admin-team"] });
      close();
      setResult({ username: res.teacher.username, password: res.temporary_password });
    },
    onError: (err) => setError(teamError(err)),
  });
  const set = (patch: Partial<typeof form>) => { setForm((f) => ({ ...f, ...patch })); setError(null); };

  return (
    <>
      <FormDialog open={open} onOpenChange={(o) => (o ? onOpenChange(true) : close())} title="Lehrer hinzufügen" description="Konto, Rolle, Berechtigungen und Lehrer-Panel werden sofort angelegt." size="lg"
                  footer={<>
                    <AdminButton variant="ghost" onClick={close} disabled={create.isPending}>Abbrechen</AdminButton>
                    <AdminButton onClick={() => create.mutate()} disabled={create.isPending || form.full_name.trim().length < 2 || form.username.trim().length < 3 || (form.own && form.password.length < 10)} data-testid="create-teacher-submit">
                      {create.isPending ? "Wird angelegt..." : "Lehrer anlegen"}
                    </AdminButton>
                  </>}>
        <div className="grid gap-4 sm:grid-cols-2" data-testid="create-teacher-dialog">
          <div className="sm:col-span-2"><AdminLabel>Vollständiger Name</AdminLabel><AdminInput value={form.full_name} onChange={(e) => set({ full_name: e.target.value })} placeholder="z. B. Dilnoza Karimova" data-testid="teacher-full-name" /></div>
          <div><AdminLabel>Benutzername (Login)</AdminLabel><AdminInput value={form.username} onChange={(e) => set({ username: e.target.value })} placeholder="teacher_001" autoComplete="off" data-testid="teacher-username" />
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">3–50 Zeichen: a–z, 0–9, _ . -</p></div>
          <div><AdminLabel>E-Mail (optional)</AdminLabel><AdminInput type="email" value={form.email} onChange={(e) => set({ email: e.target.value })} placeholder="lehrer@schule.uz" data-testid="teacher-email" />
            <p className="mt-1 text-xs text-[var(--admin-text-muted)]">Ohne E-Mail meldet sich die Lehrkraft mit dem Benutzernamen an.</p></div>
          <div className="sm:col-span-2">
            <AdminLabel>Vorläufiges Passwort</AdminLabel>
            <div className="flex flex-wrap gap-2">
              {[[false, "Sicher automatisch erzeugen"], [true, "Selbst festlegen"]].map(([v, label]) => (
                <label key={String(v)} className="flex items-center gap-2 text-sm text-[var(--admin-text-secondary)]">
                  <input type="radio" name="pw" checked={form.own === v} onChange={() => set({ own: v as boolean })} data-testid={v ? "password-own" : "password-generate"} /> {label as string}
                </label>
              ))}
            </div>
            {form.own && <AdminInput type="text" value={form.password} onChange={(e) => set({ password: e.target.value })} placeholder="mindestens 10 Zeichen, Buchstaben und Ziffern" className="mt-2" autoComplete="new-password" data-testid="teacher-password" />}
          </div>
          <div className="sm:col-span-2"><KontrollQuestion value={form.control} onChange={(control) => set({ control })} /></div>
          {error && <p className="text-sm text-[var(--admin-danger)] sm:col-span-2" role="alert" data-testid="create-teacher-error">{error}</p>}
        </div>
      </FormDialog>
      {result && <PasswordResult username={result.username} password={result.password} onClose={() => setResult(null)} />}
    </>
  );
}

function Section({ title, children, icon: Icon }: { title: string; children: React.ReactNode; icon?: typeof ShieldCheck }) {
  return (
    <section className="rounded-xl border border-[var(--admin-border)] p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">{Icon && <Icon size={15} />}{title}</h3>
      {children}
    </section>
  );
}

export function TeacherDetailDialog({ teacherId, onClose }: { teacherId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const detail = useQuery({ queryKey: ["admin-team", "teacher", teacherId], queryFn: () => getTeamTeacher(teacherId) });
  const choices = useQuery({ queryKey: ["admin-team", "choices"], queryFn: getTeamChoices });
  const [edit, setEdit] = useState<{ full_name: string; username: string; email: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [groupPick, setGroupPick] = useState("");
  const [coursePick, setCoursePick] = useState("");
  const [confirm, setConfirm] = useState<null | { title: string; text: string; run: () => Promise<unknown>; danger?: boolean }>(null);
  const [ownPassword, setOwnPassword] = useState("");
  const [result, setResult] = useState<{ username: string; password: string } | null>(null);
  const d = detail.data;
  // the form starts from the loaded teacher and keeps the admin's typing afterwards
  const form = edit ?? (d ? { full_name: d.name, username: d.username, email: d.email ?? "" } : null);

  const apply = useMutation({
    mutationFn: (run: () => Promise<TeamTeacherDetail | { teacher: TeamTeacherDetail; temporary_password: string } | unknown>) => run(),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["admin-team"] });
      setError(null);
      const withPassword = res as { teacher?: TeamTeacherDetail; temporary_password?: string };
      if (withPassword?.temporary_password && withPassword.teacher) setResult({ username: withPassword.teacher.username, password: withPassword.temporary_password });
      else setNotice("Gespeichert.");
    },
    onError: (err) => { setError(teamError(err)); setNotice(null); },
  });
  const run = (fn: () => Promise<unknown>) => { setNotice(null); apply.mutate(fn); };

  const freeGroups = (choices.data?.groups ?? []).filter((g) => g.teacher_id !== teacherId);
  const freeCourses = (choices.data?.courses ?? []).filter((c) => !d?.courses.some((x) => x.course_id === c.id));

  return (
    <>
      <FormDialog open onOpenChange={(o) => !o && onClose()} title={d ? `${d.name} (${d.username})` : "Lehrkraft"} size="xl"
                  description={d ? `Angelegt ${formatDe(d.created_at)} · letzte Anmeldung ${formatDe(d.last_login_at)}${d.must_change_password ? " · muss das Passwort noch ändern" : ""}` : undefined}
                  footer={<AdminButton variant="secondary" onClick={onClose}>Schließen</AdminButton>}>
        {!d ? <p className="py-8 text-center text-sm text-[var(--admin-text-muted)]">{detail.isError ? "Konnte nicht geladen werden." : "Wird geladen..."}</p> : (
          <div className="space-y-4" data-testid="teacher-detail">
            {error && <p className="rounded-lg bg-[var(--admin-danger)]/10 px-3 py-2 text-sm text-[var(--admin-danger)]" role="alert">{error}</p>}
            {notice && <p className="rounded-lg bg-[var(--admin-accent)]/10 px-3 py-2 text-sm text-[var(--admin-accent)]" role="status" data-testid="team-notice">{notice}</p>}
            <div className="grid gap-4 lg:grid-cols-2">
              <Section title="Profil">
                {form && (
                  <div className="space-y-2">
                    <AdminInput value={form.full_name} onChange={(e) => setEdit({ ...form, full_name: e.target.value })} aria-label="Vollständiger Name" />
                    <AdminInput value={form.username} onChange={(e) => setEdit({ ...form, username: e.target.value })} aria-label="Benutzername" />
                    <AdminInput value={form.email} onChange={(e) => setEdit({ ...form, email: e.target.value })} aria-label="E-Mail" placeholder="E-Mail (optional)" />
                    <AdminButton size="sm" onClick={() => run(() => updateTeamTeacher(teacherId, { full_name: form.full_name.trim(), username: form.username.trim().toLowerCase(), email: form.email.trim() || null }))}
                                 disabled={apply.isPending}>Profil speichern</AdminButton>
                  </div>
                )}
              </Section>
              <Section title="Kontroll-Berechtigung" icon={ShieldCheck}>
                <div className="flex flex-wrap items-center gap-2" data-testid="detail-kontroll">
                  <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold", d.can_access_student_control ? "bg-[var(--admin-accent)]/15 text-[var(--admin-accent)]" : "bg-white/5 text-[var(--admin-text-muted)]")}>
                    {d.can_access_student_control ? "Ja — Kontroll aktiv" : "Nein — kein Zugriff"}
                  </span>
                  <AdminButton size="sm" variant="secondary" disabled={apply.isPending} data-testid="toggle-kontroll"
                               onClick={() => setConfirm({ title: d.can_access_student_control ? "Kontroll entziehen?" : "Kontroll freigeben?",
                                                           text: d.can_access_student_control ? "Die Lehrkraft sieht die Aktivität der Schüler danach nicht mehr." : "Die Lehrkraft darf danach die Aktivität ALLER Schüler ansehen (nur lesen).",
                                                           run: () => setTeamControl(teacherId, !d.can_access_student_control) })}>
                    {d.can_access_student_control ? "Deaktivieren" : "Aktivieren"}
                  </AdminButton>
                </div>
                {d.control_changed_at && <p className="mt-2 text-xs text-[var(--admin-text-muted)]">Zuletzt geändert {formatDe(d.control_changed_at)}</p>}
              </Section>
              <Section title="Status">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-[var(--admin-text-secondary)]">{d.status === "active" ? "Aktiv" : d.status === "blocked" ? "Gesperrt" : "Inaktiv"}</span>
                  <AdminButton size="sm" variant={d.status === "active" ? "danger" : "primary"} disabled={apply.isPending} data-testid="toggle-status"
                               onClick={() => setConfirm({ title: d.status === "active" ? "Lehrkraft deaktivieren?" : "Lehrkraft aktivieren?", danger: d.status === "active",
                                                           text: d.status === "active" ? "Die Lehrkraft wird sofort abgemeldet und kann sich nicht mehr anmelden. Daten bleiben erhalten." : "Die Lehrkraft kann sich wieder anmelden.",
                                                           run: () => setTeamStatus(teacherId, d.status !== "active") })}>
                    {d.status === "active" ? "Deaktivieren" : "Aktivieren"}
                  </AdminButton>
                </div>
              </Section>
              <Section title="Passwort zurücksetzen" icon={KeyRound}>
                <div className="flex flex-wrap gap-2">
                  <AdminInput value={ownPassword} onChange={(e) => setOwnPassword(e.target.value)} placeholder="leer = sicher erzeugen" className="min-w-0 flex-1" autoComplete="new-password" />
                  <AdminButton size="sm" variant="secondary" disabled={apply.isPending}
                               onClick={() => setConfirm({ title: "Passwort zurücksetzen?", text: "Alle Sitzungen der Lehrkraft werden beendet; beim nächsten Login muss sie ein eigenes Passwort festlegen.",
                                                           run: () => resetTeamPassword(teacherId, ownPassword || undefined) })}>Zurücksetzen</AdminButton>
                </div>
              </Section>
              <Section title={`Gruppen (${d.groups.length})`}>
                <ul className="mb-3 space-y-1">
                  {d.groups.length === 0 && <li className="text-sm text-[var(--admin-text-muted)]">Noch keine Gruppen zugewiesen.</li>}
                  {d.groups.map((g) => (
                    <li key={g.id} className="flex items-center justify-between gap-2 text-sm text-[var(--admin-text-primary)]">
                      <span>{g.name} · {g.level} <span className="text-xs text-[var(--admin-text-muted)]">{g.status}</span></span>
                      <button type="button" aria-label={`${g.name} entfernen`} className="rounded p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-danger)]"
                              onClick={() => setConfirm({ title: "Gruppe entfernen?", text: `„${g.name}“ wird dir (Super Admin) zugeordnet — eine Gruppe hat immer eine Lehrkraft.`, danger: true,
                                                          run: () => removeTeamGroup(teacherId, g.id) })}><Trash2 size={14} /></button>
                    </li>
                  ))}
                </ul>
                <div className="flex gap-2">
                  <div className="min-w-0 flex-1">
                    <AdminSelect value={groupPick} onChange={(e) => setGroupPick(e.target.value)} aria-label="Gruppe wählen" data-testid="assign-group-select">
                      <option value="">Gruppe wählen…</option>
                      {freeGroups.map((g) => <option key={g.id} value={g.id}>{g.name} ({g.level}) — jetzt: {g.teacher ?? "?"}</option>)}
                    </AdminSelect>
                  </div>
                  <AdminButton size="sm" disabled={!groupPick || apply.isPending} onClick={() => { const id = groupPick; setGroupPick(""); run(() => assignTeamGroup(teacherId, id)); }} data-testid="assign-group">Zuweisen</AdminButton>
                </div>
              </Section>
              <Section title={`Kurse (${d.courses.length})`}>
                <ul className="mb-3 space-y-1">
                  {d.courses.length === 0 && <li className="text-sm text-[var(--admin-text-muted)]">Noch keine Kurse zugewiesen.</li>}
                  {d.courses.map((c) => (
                    <li key={c.course_id} className="flex items-center justify-between gap-2 text-sm text-[var(--admin-text-primary)]">
                      <span>{c.level} · {c.title}</span>
                      <button type="button" aria-label={`${c.title} entfernen`} className="rounded p-1 text-[var(--admin-text-muted)] hover:text-[var(--admin-danger)]"
                              onClick={() => setConfirm({ title: "Kurs entfernen?", text: `Die Lehrkraft bewertet danach keine Abgaben aus „${c.title}“ mehr.`, danger: true,
                                                          run: () => removeTeamCourse(teacherId, c.course_id) })}><Trash2 size={14} /></button>
                    </li>
                  ))}
                </ul>
                <div className="flex gap-2">
                  <div className="min-w-0 flex-1">
                    <AdminSelect value={coursePick} onChange={(e) => setCoursePick(e.target.value)} aria-label="Kurs wählen" data-testid="assign-course-select">
                      <option value="">Kurs wählen…</option>
                      {freeCourses.map((c) => <option key={c.id} value={c.id}>{c.level} · {c.title}</option>)}
                    </AdminSelect>
                  </div>
                  <AdminButton size="sm" disabled={!coursePick || apply.isPending} onClick={() => { const id = coursePick; setCoursePick(""); run(() => assignTeamCourse(teacherId, id)); }} data-testid="assign-course">Zuweisen</AdminButton>
                </div>
              </Section>
            </div>
            <Section title="Änderungsverlauf">
              {d.history.length === 0 ? <p className="text-sm text-[var(--admin-text-muted)]">Noch keine Änderungen.</p> : (
                <ul className="max-h-56 space-y-1.5 overflow-y-auto text-sm" data-testid="teacher-history">
                  {d.history.map((h) => (
                    <li key={h.id} className="flex flex-wrap justify-between gap-2">
                      <span className="text-[var(--admin-text-primary)]">{ACTION_LABELS[h.action] ?? h.action}{h.details ? <span className="text-[var(--admin-text-muted)]"> — {h.details}</span> : null}</span>
                      <span className="text-xs text-[var(--admin-text-muted)]">{formatDe(h.at)}{h.actor ? ` · ${h.actor}` : ""}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          </div>
        )}
      </FormDialog>
      {confirm && (
        <ConfirmDialog open onOpenChange={(o) => !o && setConfirm(null)} title={confirm.title} description={confirm.text} variant={confirm.danger ? "danger" : "primary"}
                       confirmLabel="Bestätigen" isPending={apply.isPending}
                       onConfirm={() => { const fn = confirm.run; setConfirm(null); run(fn); }} />
      )}
      {result && <PasswordResult username={result.username} password={result.password} onClose={() => setResult(null)} />}
    </>
  );
}
