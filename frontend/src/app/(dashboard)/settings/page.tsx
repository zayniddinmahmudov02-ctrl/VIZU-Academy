"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, Bell, Globe, Settings as SettingsIcon } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import Skeleton from "@/components/ui/skeleton";
import { languages } from "@/constants/languages";
import PanelSwitcher from "@/features/auth/components/panel-switcher";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import AccountInfoCard from "@/features/profile/components/account-info-card";
import LanguageCard from "@/features/profile/components/language-card";
import PersonalInfoCard from "@/features/profile/components/personal-info-card";
import ProfileHeader from "@/features/profile/components/profile-header";
import ProfilePhotoCard from "@/features/profile/components/profile-photo-card";
import SecurityCard from "@/features/profile/components/security-card";
import { useRemoveProfilePhoto, useUploadProfilePhoto } from "@/features/profile/hooks/use-profile-photo";
import {
  ALLOWED_PHOTO_TYPES,
  MAX_PHOTO_SIZE_BYTES,
} from "@/features/profile/validation/profile.schema";
import { useTranslation } from "@/lib/i18n/use-translation";

export default function SettingsPage() {
  const { t, language } = useTranslation();
  const { user, loading, error } = useCurrentUser();
  const [emailNotif, setEmailNotif] = useState(true);
  const [reminders, setReminders] = useState(true);
  const currentLanguage = languages.find((item) => item.code === language) ?? languages[0];

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<{ file: File; url: string } | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);

  const uploadPhoto = useUploadProfilePhoto();
  const removePhoto = useRemoveProfilePhoto();

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview.url);
    };
  }, [preview]);

  function pickPhoto() {
    setPhotoError(null);
    fileInputRef.current?.click();
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!ALLOWED_PHOTO_TYPES.includes(file.type)) {
      setPhotoError(t("profile.photoInvalidType"));
      return;
    }

    if (file.size > MAX_PHOTO_SIZE_BYTES) {
      setPhotoError(t("profile.photoTooLarge"));
      return;
    }

    setPhotoError(null);
    setPreview({ file, url: URL.createObjectURL(file) });
  }

  function confirmPhotoUpload() {
    if (!preview) return;

    uploadPhoto.mutate(preview.file, {
      onSuccess: () => {
        URL.revokeObjectURL(preview.url);
        setPreview(null);
      },
      onError: () => setPhotoError(t("profile.saveError")),
    });
  }

  function cancelPreview() {
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setPhotoError(null);
  }

  function handleRemovePhoto() {
    setPhotoError(null);
    removePhoto.mutate(undefined, {
      onError: () => setPhotoError(t("profile.saveError")),
    });
  }

  return (
    <div className="space-y-8">
      <PageHeader
        icon={SettingsIcon}
        titleKey="settings.title"
        subtitleKey="settings.subtitle"
        gradient="from-accent-blue to-purple-600"
      />

      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_PHOTO_TYPES.join(",")}
        className="hidden"
        onChange={onFileChange}
      />

      <PanelSwitcher />

      {/* Profile (moved here from the former /profile page) */}
      {loading && <ProfileSkeleton />}

      {!loading && error && (
        <div className="flex items-center gap-2 rounded-card bg-danger/10 px-5 py-4 text-sm text-danger">
          <AlertCircle size={16} />
          {t("common.errorTitle")}
        </div>
      )}

      {!loading && !error && user && (
        <>
          <ProfileHeader user={user} onPickPhoto={pickPhoto} />

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-6">
              <PersonalInfoCard user={user} />
              <ProfilePhotoCard
                name={[user.firstName, user.lastName].filter(Boolean).join(" ") || user.username}
                currentImage={user.profileImage}
                previewUrl={preview?.url ?? null}
                uploading={uploadPhoto.isPending}
                removing={removePhoto.isPending}
                error={photoError}
                onPick={pickPhoto}
                onConfirm={confirmPhotoUpload}
                onCancelPreview={cancelPreview}
                onRemove={handleRemovePhoto}
              />
            </div>

            <div className="space-y-6">
              <SecurityCard />
              <LanguageCard />
              <AccountInfoCard user={user} />
            </div>
          </div>
        </>
      )}

      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("settings.notifications")}</h2>
        <div className="mt-5 space-y-2">
          <Toggle
            icon={<Bell size={18} />}
            label={t("settings.emailNotifications")}
            checked={emailNotif}
            onChange={setEmailNotif}
          />
          <Toggle
            icon={<Bell size={18} />}
            label={t("settings.dailyReminders")}
            checked={reminders}
            onChange={setReminders}
          />
        </div>
      </section>

      <section className="rounded-card bg-surface-card p-7 shadow-[var(--shadow-md)] ring-1 ring-surface-border">
        <h2 className="text-lg font-bold text-text-primary">{t("settings.appearance")}</h2>
        <p className="mt-1 text-sm text-text-secondary">
          {t("settings.appearanceBody")}
        </p>
        <div className="mt-5 space-y-2">
          <div className="flex items-center justify-between rounded-2xl bg-surface-hover p-4">
            <span className="flex items-center gap-3 text-sm font-medium text-text-primary">
              <Globe size={18} /> {t("settings.language")}
            </span>
            <span className="text-sm text-text-secondary">{currentLanguage.name}</span>
          </div>
        </div>
      </section>
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-[168px] rounded-card" />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Skeleton className="h-64 rounded-card" />
          <Skeleton className="h-40 rounded-card" />
        </div>
        <div className="space-y-6">
          <Skeleton className="h-72 rounded-card" />
          <Skeleton className="h-40 rounded-card" />
          <Skeleton className="h-32 rounded-card" />
        </div>
      </div>
    </div>
  );
}

function Toggle({
  icon,
  label,
  checked,
  onChange,
}: {
  icon: React.ReactNode;
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-surface-hover p-4">
      <span className="flex items-center gap-3 text-sm font-medium text-text-primary">
        {icon}
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${
          checked ? "bg-accent-blue" : "bg-surface-border"
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
            checked ? "left-[22px]" : "left-0.5"
          }`}
        />
      </button>
    </div>
  );
}
