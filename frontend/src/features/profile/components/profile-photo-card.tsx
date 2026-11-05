"use client";

import { ImageIcon, Trash2, Upload } from "lucide-react";

import Avatar from "@/components/ui/avatar";
import PhotoCropper from "@/features/profile/components/photo-cropper";
import type { Crop } from "@/features/profile/utils/photo-crop";
import Button from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n/use-translation";

interface Props {
  name: string;
  currentImage: string | null;
  previewUrl: string | null;
  uploading: boolean;
  removing: boolean;
  error: string | null;
  onPick: () => void;
  onConfirm: () => void;
  onCancelPreview: () => void;
  onRemove: () => void;
  onCrop: (crop: Crop) => void;
}

export default function ProfilePhotoCard({
  name,
  currentImage,
  previewUrl,
  uploading,
  removing,
  error,
  onPick,
  onConfirm,
  onCancelPreview,
  onRemove,
  onCrop,
}: Props) {
  const { t } = useTranslation();

  return (
    <section className="rounded-card bg-surface-card p-5 shadow-[var(--shadow-md)] ring-1 ring-surface-border sm:p-7" data-testid="profile-photo-card">
      <h2 className="flex items-center gap-2 text-lg font-bold text-text-primary">
        <ImageIcon size={18} className="text-accent-blue" />
        {t("profile.photo")}
      </h2>

      <div className="mt-5 flex flex-wrap items-center gap-5">
        {previewUrl ? (
          <PhotoCropper src={previewUrl} onChange={onCrop} />
        ) : (
          <Avatar src={currentImage ?? undefined} name={name} size={80} />
        )}

        <div className="flex flex-1 flex-col gap-3">
          {error && <p role="alert" className="text-sm text-danger" data-testid="profile-photo-error">{error}</p>}

          {previewUrl ? (
            <div className="flex flex-wrap gap-3">
              <Button size="sm" onClick={onConfirm} disabled={uploading} data-testid="profile-photo-save">
                <Upload size={15} />
                {uploading ? t("profile.saving") : t("profile.save")}
              </Button>
              <Button size="sm" variant="ghost" onClick={onCancelPreview} disabled={uploading}>
                {t("profile.cancel")}
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              <Button size="sm" variant="secondary" onClick={onPick} data-testid="profile-photo-pick">
                <Upload size={15} />
                {currentImage ? t("profile.replacePhoto") : t("profile.uploadPhoto")}
              </Button>
              {currentImage && (
                <Button size="sm" variant="ghost" onClick={onRemove} disabled={removing} data-testid="profile-photo-remove">
                  <Trash2 size={15} />
                  {removing ? t("profile.saving") : t("profile.removePhoto")}
                </Button>
              )}
            </div>
          )}

          <p className="text-xs text-text-muted">{t("profile.photoHint")}</p>
        </div>
      </div>
    </section>
  );
}
