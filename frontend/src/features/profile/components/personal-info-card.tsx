"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Lock, Pencil, User } from "lucide-react";

import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import type { CurrentUser } from "@/features/auth/types/user";
import { useTranslation } from "@/lib/i18n/use-translation";

import { useUpdateProfile } from "../hooks/use-update-profile";
import { getErrorMessage } from "@/features/auth/utils/get-error-message";
import { profileSchema, type ProfileFormData } from "../validation/profile.schema";

interface Props {
  user: CurrentUser;
}

export default function PersonalInfoCard({ user }: Props) {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const updateProfile = useUpdateProfile();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    values: {
      firstName: user.firstName ?? "",
      lastName: user.lastName ?? "",
      phoneNumber: user.phoneNumber ?? "",
      country: user.country ?? "",
    },
  });

  useEffect(() => {
    if (!savedAt) return;
    const timeout = setTimeout(() => setSavedAt(null), 3000);
    return () => clearTimeout(timeout);
  }, [savedAt]);

  function onCancel() {
    reset();
    setEditing(false);
    updateProfile.reset();
  }

  function onSubmit(data: ProfileFormData) {
    updateProfile.mutate(
      {
        firstName: data.firstName || undefined,
        lastName: data.lastName || undefined,
        phoneNumber: data.phoneNumber || undefined,
        country: data.country || undefined,
      },
      {
        onSuccess: () => {
          setEditing(false);
          setSavedAt(Date.now());
        },
      },
    );
  }

  return (
    <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
          <User size={18} className="text-accent-blue" />
          {t("profile.personalInfo")}
        </h2>

        {!editing && (
          <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
            <Pencil size={14} />
            {t("profile.edit")}
          </Button>
        )}
      </div>

      {savedAt && !editing && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-success/10 px-4 py-2.5 text-sm text-success">
          <CheckCircle2 size={16} />
          {t("profile.saveSuccess")}
        </div>
      )}

      {updateProfile.isError && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger/10 px-4 py-2.5 text-sm text-danger">
          <AlertCircle size={16} />
          {getErrorMessage(updateProfile.error, t("profile.saveError"))}
        </div>
      )}

      {editing ? (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-5 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("profile.firstName")} error={errors.firstName?.message}>
              <Input {...register("firstName")} error={!!errors.firstName} />
            </Field>
            <Field label={t("profile.lastName")} error={errors.lastName?.message}>
              <Input {...register("lastName")} error={!!errors.lastName} />
            </Field>
            <Field label={t("profile.phoneNumber")} error={errors.phoneNumber?.message}>
              <Input {...register("phoneNumber")} error={!!errors.phoneNumber} />
            </Field>
            <Field label={t("profile.country")} error={errors.country?.message}>
              <Input {...register("country")} error={!!errors.country} />
            </Field>
          </div>

          <EmailRow email={user.email} />

          <div className="flex gap-3 pt-2">
            <Button type="submit" size="sm" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? t("profile.saving") : t("profile.save")}
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={onCancel} disabled={updateProfile.isPending}>
              {t("profile.cancel")}
            </Button>
          </div>
        </form>
      ) : (
        <dl className="mt-5 space-y-4 text-sm">
          <Row label={t("profile.fullName")} value={fullName(user) || t("profile.notProvided")} />
          <Row label={t("profile.phoneNumber")} value={user.phoneNumber || t("profile.notProvided")} />
          <Row label={t("profile.country")} value={user.country || t("profile.notProvided")} />
          <EmailRow email={user.email} readOnlyRow />
        </dl>
      )}
    </section>
  );
}

function fullName(user: CurrentUser): string {
  return [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-text-secondary">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-surface-border pb-3 last:border-0 last:pb-0">
      <dt className="text-text-secondary">{label}</dt>
      <dd className="font-medium text-text-primary">{value}</dd>
    </div>
  );
}

function EmailRow({ email, readOnlyRow }: { email: string; readOnlyRow?: boolean }) {
  const { t } = useTranslation();

  if (readOnlyRow) {
    return (
      <div className="flex items-center justify-between border-b border-surface-border pb-3">
        <dt className="text-text-secondary">{t("profile.email")}</dt>
        <dd className="flex items-center gap-1.5 font-medium text-text-primary">
          <Lock size={12} className="text-text-muted" />
          {email}
        </dd>
      </div>
    );
  }

  return (
    <div>
      <label className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-text-secondary">
        <Lock size={12} />
        {t("profile.email")}
      </label>
      <Input value={email} disabled readOnly />
      <p className="mt-1.5 text-xs text-text-muted">{t("profile.emailReadOnlyNote")}</p>
    </div>
  );
}
