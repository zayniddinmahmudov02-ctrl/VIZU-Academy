"use client";

import { useEffect, useRef, useState } from "react";
import { AlertCircle, User } from "lucide-react";

import PageHeader from "@/components/dashboard/page-header";
import Skeleton from "@/components/ui/skeleton";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useTranslation } from "@/lib/i18n/use-translation";

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

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, loading, error } = useCurrentUser();

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
        icon={User}
        titleKey="sidebar.profile"
        subtitleKey="profile.pageSubtitle"
        gradient="from-brand-900 to-accent-blue"
      />

      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_PHOTO_TYPES.join(",")}
        className="hidden"
        onChange={onFileChange}
      />

      {loading && <ProfilePageSkeleton />}

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
    </div>
  );
}

function ProfilePageSkeleton() {
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
