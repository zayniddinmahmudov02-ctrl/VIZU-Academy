"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Pencil, Trash2 } from "lucide-react";

import { ErrorState, Loading, Panel, TeacherPageTitle } from "@/components/teacher/teacher-ui";
import { useTranslation } from "@/lib/i18n/use-translation";

import { deleteCertificate, deletePhoto, getOwnProfile, updateOwnProfile, uploadCertificate, uploadPhoto } from "../services/market-service";
import type { OwnProfile } from "../types";
import RatioCropper from "./ratio-cropper";
import TeacherProfileView from "./teacher-profile-view";
import { Pill, Stars, TeacherPhoto, buttonPrimary, buttonSecondary, formatDate, inputClass, useErrorText } from "./ui";

function Checks({ values, options, onChange, testId }: { values: string[]; options: string[]; onChange: (v: string[]) => void; testId: string }) {
  return (
    <div className="flex flex-wrap gap-2" data-testid={testId}>
      {options.map((o) => {
        const on = values.includes(o);
        return (
          <button key={o} type="button" aria-pressed={on} onClick={() => onChange(on ? values.filter((v) => v !== o) : [...values, o])}
                  className={`rounded-full px-3 py-1.5 text-sm font-medium ring-1 transition ${on ? "bg-accent-blue text-white ring-accent-blue" : "bg-surface-bg text-text-secondary ring-surface-border"}`}>
            {o}
          </button>
        );
      })}
    </div>
  );
}

function ProfileForm({ profile }: { profile: OwnProfile }) {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const [form, setForm] = useState({
    first_name: profile.first_name ?? "", last_name: profile.last_name ?? "", headline: profile.headline ?? "", bio: profile.experience.bio ?? "",
    specialization: profile.experience.specialization ?? "", methodology: profile.experience.methodology ?? "",
    experience_years: profile.experience.years?.toString() ?? "", teaching_since: profile.experience.teaching_since?.toString() ?? "",
    languages: profile.languages, levels: profile.levels, exam_prep: profile.experience.exam_prep,
  });
  const [saved, setSaved] = useState(false);
  const save = useMutation({
    mutationFn: () => updateOwnProfile({
      ...form, experience_years: form.experience_years ? Number(form.experience_years) : null,
      teaching_since: form.teaching_since ? Number(form.teaching_since) : null,
    }),
    onSuccess: (data) => { qc.setQueryData(["teacher-own-profile"], data); setSaved(true); },
  });
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => { setSaved(false); setForm((f) => ({ ...f, [k]: e.target.value })); };
  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); save.mutate(); }} data-testid="profile-form">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-text-secondary">{t("market.firstName")}<input className={inputClass} value={form.first_name} onChange={set("first_name")} required maxLength={100} data-testid="pf-first" /></label>
        <label className="text-xs text-text-secondary">{t("market.lastName")}<input className={inputClass} value={form.last_name} onChange={set("last_name")} maxLength={100} data-testid="pf-last" /></label>
      </div>
      <label className="block text-xs text-text-secondary">{t("market.headline")}<input className={inputClass} value={form.headline} onChange={set("headline")} maxLength={160} data-testid="pf-headline" /></label>
      <label className="block text-xs text-text-secondary">{t("market.bio")}<textarea className={inputClass} rows={4} value={form.bio} onChange={set("bio")} maxLength={4000} data-testid="pf-bio" /></label>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-xs text-text-secondary">{t("market.experienceYears")}<input type="number" min={0} max={70} className={inputClass} value={form.experience_years} onChange={set("experience_years")} data-testid="pf-years" /></label>
        <label className="text-xs text-text-secondary">{t("market.teachingSince")}<input type="number" min={1950} max={2100} className={inputClass} value={form.teaching_since} onChange={set("teaching_since")} data-testid="pf-since" /></label>
      </div>
      <label className="block text-xs text-text-secondary">{t("market.specialization")}<input className={inputClass} value={form.specialization} onChange={set("specialization")} maxLength={300} data-testid="pf-spec" /></label>
      <label className="block text-xs text-text-secondary">{t("market.methodology")}<textarea className={inputClass} rows={3} value={form.methodology} onChange={set("methodology")} maxLength={4000} data-testid="pf-method" /></label>
      <div className="space-y-1"><p className="text-xs text-text-secondary">{t("market.languages")}</p>
        <Checks values={form.languages} options={profile.choices.languages} onChange={(v) => setForm((f) => ({ ...f, languages: v }))} testId="pf-languages" /></div>
      <div className="space-y-1"><p className="text-xs text-text-secondary">{t("market.levels")}</p>
        <Checks values={form.levels} options={profile.choices.levels} onChange={(v) => setForm((f) => ({ ...f, levels: v }))} testId="pf-levels" /></div>
      <div className="space-y-1"><p className="text-xs text-text-secondary">{t("market.examPrep")}</p>
        <Checks values={form.exam_prep} options={profile.choices.exams} onChange={(v) => setForm((f) => ({ ...f, exam_prep: v }))} testId="pf-exams" /></div>
      {save.isError && <p className="text-sm text-danger" role="alert">{errorText(save.error)}</p>}
      <div className="flex items-center gap-3">
        <button type="submit" className={buttonPrimary} disabled={save.isPending} data-testid="pf-save">{t("market.save")}</button>
        {saved && <span className="text-sm text-emerald-600" role="status" data-testid="pf-saved">{t("market.saved")}</span>}
      </div>
    </form>
  );
}

function Certificates({ profile }: { profile: OwnProfile }) {
  const { t, language } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const [form, setForm] = useState({ title: "", issuer: "", issued_on: "", level: "" });
  const [file, setFile] = useState<File | null>(null);
  const refresh = () => void qc.invalidateQueries({ queryKey: ["teacher-own-profile"] });
  const add = useMutation({ mutationFn: () => uploadCertificate({ ...form, file: file! }), onSuccess: () => { setForm({ title: "", issuer: "", issued_on: "", level: "" }); setFile(null); refresh(); } });
  const remove = useMutation({ mutationFn: (id: string) => deleteCertificate(id), onSuccess: refresh });
  return (
    <div className="space-y-4">
      <ul className="space-y-2">
        {profile.certificates.map((c) => (
          <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-bg p-3 ring-1 ring-surface-border" data-testid="own-certificate">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-text-primary">{c.title}</p>
              <p className="text-xs text-text-secondary">{c.issuer}{c.issued_on ? ` · ${formatDate(c.issued_on, language)}` : ""}</p>
              {c.status === "rejected" && c.reject_reason && <p className="text-xs text-danger">{c.reject_reason}</p>}
            </div>
            <div className="flex items-center gap-2">
              <Pill tone={c.status === "verified" ? "APPROVED" : c.status === "rejected" ? "REJECTED" : "PENDING"} testId="own-certificate-status">{t(`market.cert_${c.status}`)}</Pill>
              {c.status !== "verified" && (
                <button type="button" className="rounded-lg p-2 text-text-muted hover:text-danger" aria-label={t("market.delete")} onClick={() => remove.mutate(c.id)}>
                  <Trash2 size={16} />
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
      <form className="grid gap-2 rounded-xl bg-surface-bg p-3 ring-1 ring-surface-border sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); add.mutate(); }}
            data-testid="certificate-form">
        <p className="text-sm font-semibold text-text-primary sm:col-span-2">{t("market.addCertificate")}</p>
        <input className={inputClass} placeholder={t("market.certTitle")} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required minLength={2} maxLength={200} data-testid="cert-title" />
        <input className={inputClass} placeholder={t("market.certIssuer")} value={form.issuer} onChange={(e) => setForm({ ...form, issuer: e.target.value })} required minLength={2} maxLength={200} data-testid="cert-issuer" />
        <label className="text-xs text-text-secondary">{t("market.certDate")}<input type="date" className={inputClass} value={form.issued_on} onChange={(e) => setForm({ ...form, issued_on: e.target.value })} /></label>
        <label className="text-xs text-text-secondary">{t("market.certLevel")}<input className={inputClass} value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} maxLength={40} /></label>
        <label className="text-xs text-text-secondary sm:col-span-2">{t("market.certFile")}
          <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" className={inputClass} onChange={(e) => setFile(e.target.files?.[0] ?? null)} required data-testid="cert-file" /></label>
        {add.isError && <p className="text-sm text-danger sm:col-span-2" role="alert">{errorText(add.error)}</p>}
        <button type="submit" className={`${buttonPrimary} sm:col-span-2`} disabled={add.isPending || !file} data-testid="cert-submit">{t("market.addCertificate")}</button>
      </form>
    </div>
  );
}

export default function TeacherProfileEditor() {
  const { t } = useTranslation();
  const errorText = useErrorText();
  const qc = useQueryClient();
  const [preview, setPreview] = useState(false);
  const q = useQuery({ queryKey: ["teacher-own-profile"], queryFn: getOwnProfile });
  const refresh = () => void qc.invalidateQueries({ queryKey: ["teacher-own-profile"] });
  const photo = useMutation({ mutationFn: ({ file, crop }: { file: File; crop: { x: number; y: number; w: number } }) => uploadPhoto(file, crop), onSuccess: refresh });
  const removePhoto = useMutation({ mutationFn: deletePhoto, onSuccess: refresh });
  if (q.isLoading) return <Loading />;
  if (q.isError || !q.data) return <ErrorState onRetry={() => q.refetch()} />;
  const p = q.data;
  const state = p.admin.profile_disabled ? "statusDisabled" : p.admin.catalog_hidden ? "statusHidden" : "statusListed";

  return (
    <div data-testid="teacher-profile-editor">
      <TeacherPageTitle title={t("market.profileTitle")} subtitle={t("market.profileSubtitle")} actions={
        <button type="button" className={buttonSecondary} onClick={() => setPreview((v) => !v)} data-testid="profile-preview-toggle">
          {preview ? <><Pencil size={16} /> {t("market.editMode")}</> : <><Eye size={16} /> {t("market.preview")}</>}
        </button>
      } />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Pill tone={state === "statusListed" ? "APPROVED" : "REJECTED"} testId="profile-state">{t(`market.${state}`)}</Pill>
        {p.verified && <Pill tone="APPROVED">{t("market.verified")}</Pill>}
      </div>
      {preview ? <TeacherProfileView profile={p} preview /> : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <div className="space-y-6">
            <Panel title={t("market.photo")} testId="photo-panel">
              <div className="flex flex-wrap items-start gap-4">
                <div className="w-32 shrink-0"><TeacherPhoto url={p.photo_url} name={p.name} /></div>
                <div className="min-w-0 flex-1 space-y-3">
                  <p className="text-xs text-text-secondary">{t("market.photoHint")}</p>
                  <RatioCropper ratio={9 / 16} busy={photo.isPending} onSave={(file, crop) => photo.mutate({ file, crop })} testId="photo-cropper" />
                  {photo.isError && <p className="text-sm text-danger" role="alert">{errorText(photo.error)}</p>}
                  {p.photo_url && <button type="button" className="text-xs text-danger" onClick={() => removePhoto.mutate()}>{t("market.removePhoto")}</button>}
                </div>
              </div>
            </Panel>
            <Panel title={t("market.ratingTitle")} testId="own-rating">
              <div className="flex items-center gap-3">
                <Stars value={p.rating.avg} size={20} />
                <span className="font-bold text-text-primary">{p.rating.count ? `${p.rating.avg.toFixed(1)}/5` : "—"}</span>
                <span className="text-sm text-text-muted">{t("market.ratingCount", { n: p.rating.count })}</span>
              </div>
              <p className="mt-2 text-xs text-text-muted">{t("market.ratingReadOnly")}</p>
            </Panel>
            <Panel title={t("market.certificatesTitle")} testId="own-certificates"><Certificates profile={p} /></Panel>
          </div>
          <Panel title={t("market.experienceTitle")}><ProfileForm key={p.id} profile={p} /></Panel>
        </div>
      )}
    </div>
  );
}
