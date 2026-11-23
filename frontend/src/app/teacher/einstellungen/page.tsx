"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, ShieldOff } from "lucide-react";

import { fieldClass, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { CURRENT_USER_QUERY_KEY, useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { changePassword } from "@/features/profile/services/profile-service";
import { TEACHER_ME_KEY, useTeacherMe } from "@/features/teacher/hooks/use-teacher-me";
import { changeTeacherUsername } from "@/features/teacher/services/teacher-panel.service";
import { useTranslation } from "@/lib/i18n/use-translation";
import { removeRefreshToken, removeToken } from "@/lib/token";
import { cn } from "@/lib/utils";

const USERNAME = /^[a-z0-9_.-]{3,50}$/;

export default function TeacherSettingsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const qc = useQueryClient();
  const { user } = useCurrentUser();
  const me = useTeacherMe();
  const [username, setUsername] = useState<string | null>(null);
  const [nameNote, setNameNote] = useState<{ ok: boolean; text: string } | null>(null);
  const [pw, setPw] = useState({ current: "", next: "", repeat: "" });
  const [pwNote, setPwNote] = useState<{ ok: boolean; text: string } | null>(null);
  const value = username ?? user?.username ?? "";

  const saveName = useMutation({
    mutationFn: () => changeTeacherUsername(value.trim().toLowerCase()),
    onSuccess: () => { setNameNote({ ok: true, text: t("tpanel.saved") }); qc.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY }); qc.invalidateQueries({ queryKey: TEACHER_ME_KEY }); },
    onError: (err) => {
      const status = (err as { response?: { status?: number } }).response?.status;
      setNameNote({ ok: false, text: status === 409 ? t("tpanel.usernameTaken") : status === 422 ? t("tpanel.usernameInvalid") : t("tpanel.saveError") });
    },
  });
  const savePw = useMutation({
    mutationFn: () => changePassword({ currentPassword: pw.current, newPassword: pw.next }),
    onSuccess: () => {
      setPwNote({ ok: true, text: t("tpanel.passwordChanged") });
      removeToken();
      removeRefreshToken();
      window.setTimeout(() => { qc.clear(); router.replace("/login"); }, 1800);
    },
    onError: () => setPwNote({ ok: false, text: t("pwgate.wrong") }),
  });

  function submitPw(e: React.FormEvent) {
    e.preventDefault();
    if (pw.next.length < 8) return setPwNote({ ok: false, text: t("tpanel.passwordShort") });
    if (pw.next !== pw.repeat) return setPwNote({ ok: false, text: t("tpanel.passwordMismatch") });
    savePw.mutate();
  }

  return (
    <div data-testid="teacher-einstellungen">
      <TeacherPageTitle title={t("tpanel.settingsTitle")} subtitle={t("tpanel.settingsSubtitle")} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title={t("tpanel.changeUsername")}>
          <form onSubmit={(e) => { e.preventDefault(); if (!USERNAME.test(value.trim().toLowerCase())) return setNameNote({ ok: false, text: t("tpanel.usernameInvalid") }); saveName.mutate(); }} className="space-y-3">
            <input value={value} onChange={(e) => { setUsername(e.target.value); setNameNote(null); }} className={`${fieldClass} w-full`} aria-label={t("tpanel.username")} data-testid="settings-username" autoComplete="username" />
            <p className="text-xs text-text-muted">{t("tpanel.usernameHint")}</p>
            {nameNote && <p className={cn("text-sm", nameNote.ok ? "text-success" : "text-danger")} role="status">{nameNote.text}</p>}
            <button type="submit" disabled={saveName.isPending} className="rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" data-testid="settings-username-save">{t("tpanel.saveUsername")}</button>
          </form>
        </Panel>
        <Panel title={t("tpanel.changePassword")}>
          <form onSubmit={submitPw} className="space-y-3">
            {(["current", "next", "repeat"] as const).map((k) => (
              <label key={k} className="block text-sm font-medium text-text-primary">{t(k === "current" ? "tpanel.currentPassword" : k === "next" ? "tpanel.newPassword" : "tpanel.repeatPassword")}
                <input type="password" value={pw[k]} onChange={(e) => setPw((p) => ({ ...p, [k]: e.target.value }))} className={`${fieldClass} mt-1 w-full`}
                       autoComplete={k === "current" ? "current-password" : "new-password"} />
              </label>
            ))}
            {pwNote && <p className={cn("text-sm", pwNote.ok ? "text-success" : "text-danger")} role="status">{pwNote.text}</p>}
            <button type="submit" disabled={savePw.isPending} className="rounded-xl bg-accent-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{t("tpanel.savePassword")}</button>
          </form>
        </Panel>
        <Panel title={t("tpanel.kontrollAccess")} testId="settings-kontroll">
          <p className="flex items-center gap-2 text-sm text-text-secondary">
            {me.data?.can_access_student_control ? <><ShieldCheck size={18} className="text-success" /> {t("tpanel.kontrollYes")}</> : <><ShieldOff size={18} className="text-text-muted" /> {t("tpanel.kontrollNo")}</>}
          </p>
        </Panel>
      </div>
    </div>
  );
}
