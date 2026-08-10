"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  Camera,
  CheckCircle2,
  Eye,
  EyeOff,
  IdCard,
  Moon,
  ShieldCheck,
  Sun,
  Trash2,
  Upload,
} from "lucide-react";
import { useTheme } from "next-themes";

import { AdminButton, AdminCard, AdminInput, AdminLabel, AdminPageHeader } from "@/components/admin/admin-ui";
import Avatar from "@/components/ui/avatar";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getErrorMessage } from "@/features/auth/utils/get-error-message";
import { useChangePassword } from "@/features/profile/hooks/use-change-password";
import { useRemoveProfilePhoto, useUploadProfilePhoto } from "@/features/profile/hooks/use-profile-photo";
import { useUpdateProfile } from "@/features/profile/hooks/use-update-profile";
import {
  ALLOWED_PHOTO_TYPES,
  MAX_PHOTO_SIZE_BYTES,
  changePasswordSchema,
  profileSchema,
  type ChangePasswordFormData,
  type ProfileFormData,
} from "@/features/profile/validation/profile.schema";
import { useHasMounted } from "@/hooks/use-mounted";
import { removeRefreshToken, removeToken } from "@/lib/token";

export default function AdminSettingsPage() {
  const { user } = useCurrentUser();

  return (
    <div>
      <AdminPageHeader title="Settings" description="Admin-Profil, Passwort und Erscheinungsbild." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AvatarCard user={user} />
        <ProfileInfoCard user={user} />
        <ThemeCard />
        <PasswordCard />
      </div>
    </div>
  );
}

function AvatarCard({ user }: { user: ReturnType<typeof useCurrentUser>["user"] }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<{ file: File; url: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadPhoto = useUploadProfilePhoto();
  const removePhoto = useRemoveProfilePhoto();

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview.url);
    };
  }, [preview]);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    if (!ALLOWED_PHOTO_TYPES.includes(file.type)) {
      setError("Bitte wähle ein JPG-, PNG- oder WEBP-Bild.");
      return;
    }
    if (file.size > MAX_PHOTO_SIZE_BYTES) {
      setError("Das Bild darf maximal 5 MB groß sein.");
      return;
    }

    setError(null);
    setPreview({ file, url: URL.createObjectURL(file) });
  }

  function confirmUpload() {
    if (!preview) return;
    uploadPhoto.mutate(preview.file, {
      onSuccess: () => {
        URL.revokeObjectURL(preview.url);
        setPreview(null);
      },
      onError: () => setError("Hochladen fehlgeschlagen."),
    });
  }

  function cancelPreview() {
    if (preview) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setError(null);
  }

  const name = user ? [user.firstName, user.lastName].filter(Boolean).join(" ") || user.username : "";

  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Admin-Avatar</h3>

      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_PHOTO_TYPES.join(",")}
        className="hidden"
        onChange={onFileChange}
      />

      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="group relative rounded-full outline-none"
          aria-label="Profilbild ändern"
        >
          {preview ? (
            <img src={preview.url} alt={name} className="h-16 w-16 rounded-full object-cover" />
          ) : (
            <Avatar src={user?.profileImage ?? undefined} name={name || "Admin"} size={64} />
          )}
          <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/0 text-white opacity-0 transition group-hover:bg-black/40 group-hover:opacity-100">
            <Camera size={18} />
          </span>
        </button>

        <div className="flex-1 space-y-2">
          {error && (
            <p className="flex items-center gap-1.5 text-xs text-[var(--admin-danger)]">
              <AlertCircle size={13} />
              {error}
            </p>
          )}

          {preview ? (
            <div className="flex gap-2">
              <AdminButton size="sm" onClick={confirmUpload} disabled={uploadPhoto.isPending}>
                <Upload size={13} />
                {uploadPhoto.isPending ? "Wird gespeichert..." : "Speichern"}
              </AdminButton>
              <AdminButton size="sm" variant="ghost" onClick={cancelPreview} disabled={uploadPhoto.isPending}>
                Abbrechen
              </AdminButton>
            </div>
          ) : (
            <div className="flex gap-2">
              <AdminButton size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()}>
                <Upload size={13} />
                {user?.profileImage ? "Ersetzen" : "Hochladen"}
              </AdminButton>
              {user?.profileImage && (
                <AdminButton
                  size="sm"
                  variant="ghost"
                  onClick={() => removePhoto.mutate()}
                  disabled={removePhoto.isPending}
                >
                  <Trash2 size={13} />
                  Entfernen
                </AdminButton>
              )}
            </div>
          )}

          <p className="text-xs text-[var(--admin-text-muted)]">JPG, PNG oder WEBP, maximal 5 MB.</p>
        </div>
      </div>
    </AdminCard>
  );
}

function ProfileInfoCard({ user }: { user: ReturnType<typeof useCurrentUser>["user"] }) {
  const updateProfile = useUpdateProfile();
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    values: {
      firstName: user?.firstName ?? "",
      lastName: user?.lastName ?? "",
      phoneNumber: user?.phoneNumber ?? "",
      country: user?.country ?? "",
    },
  });

  function onSubmit(data: ProfileFormData) {
    updateProfile.mutate(data, {
      onSuccess: (updated) => {
        setSuccess(true);
        reset({
          firstName: updated.firstName ?? "",
          lastName: updated.lastName ?? "",
          phoneNumber: updated.phoneNumber ?? "",
          country: updated.country ?? "",
        });
        setTimeout(() => setSuccess(false), 2500);
      },
    });
  }

  return (
    <AdminCard>
      <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">
        <IdCard size={15} />
        Profilinformationen
      </h3>

      <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 sm:grid-cols-2">
        {updateProfile.isError && (
          <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-danger)]/10 px-4 py-2.5 text-sm text-[var(--admin-danger)] sm:col-span-2">
            <AlertCircle size={15} />
            {getErrorMessage(updateProfile.error, "Speichern fehlgeschlagen.")}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-accent)]/10 px-4 py-2.5 text-sm text-[var(--admin-accent)] sm:col-span-2">
            <CheckCircle2 size={15} />
            Profil aktualisiert.
          </div>
        )}

        <div>
          <AdminLabel>Vorname</AdminLabel>
          <AdminInput {...register("firstName")} />
          {errors.firstName && <p className="mt-1 text-xs text-[var(--admin-danger)]">{errors.firstName.message}</p>}
        </div>
        <div>
          <AdminLabel>Nachname</AdminLabel>
          <AdminInput {...register("lastName")} />
          {errors.lastName && <p className="mt-1 text-xs text-[var(--admin-danger)]">{errors.lastName.message}</p>}
        </div>
        <div>
          <AdminLabel>Telefonnummer</AdminLabel>
          <AdminInput {...register("phoneNumber")} />
          {errors.phoneNumber && (
            <p className="mt-1 text-xs text-[var(--admin-danger)]">{errors.phoneNumber.message}</p>
          )}
        </div>
        <div>
          <AdminLabel>Land</AdminLabel>
          <AdminInput {...register("country")} />
          {errors.country && <p className="mt-1 text-xs text-[var(--admin-danger)]">{errors.country.message}</p>}
        </div>

        <div className="sm:col-span-2">
          <AdminButton type="submit" size="sm" disabled={updateProfile.isPending || !isDirty}>
            {updateProfile.isPending ? "Wird gespeichert..." : "Speichern"}
          </AdminButton>
        </div>
      </form>
    </AdminCard>
  );
}

function ThemeCard() {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useHasMounted();
  const isDark = mounted && resolvedTheme === "dark";

  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Erscheinungsbild</h3>
      <div className="flex items-center justify-between rounded-lg bg-white/5 px-4 py-3">
        <span className="flex items-center gap-2.5 text-sm text-[var(--admin-text-secondary)]">
          {isDark ? <Moon size={15} /> : <Sun size={15} />}
          {isDark ? "Dunkel" : "Hell"}
        </span>
        <button
          type="button"
          role="switch"
          aria-checked={isDark}
          onClick={() => setTheme(isDark ? "light" : "dark")}
          className={`relative h-6 w-11 rounded-full transition-colors ${
            isDark ? "bg-[var(--admin-primary)]" : "bg-white/10"
          }`}
        >
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
              isDark ? "left-[22px]" : "left-0.5"
            }`}
          />
        </button>
      </div>
      <p className="mt-2.5 text-xs text-[var(--admin-text-muted)]">
        Die Einstellung wird gespeichert und angewendet, sobald diese Ansicht ein helles Farbschema
        unterstützt.
      </p>
    </AdminCard>
  );
}

function PasswordCard() {
  const router = useRouter();
  const changePassword = useChangePassword();
  const [success, setSuccess] = useState(false);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({ resolver: zodResolver(changePasswordSchema) });

  function onSubmit(data: ChangePasswordFormData) {
    changePassword.mutate(
      { currentPassword: data.currentPassword, newPassword: data.newPassword },
      {
        onSuccess: () => {
          reset();
          setSuccess(true);
          setTimeout(() => {
            removeToken();
            removeRefreshToken();
            router.push("/login");
          }, 2500);
        },
      },
    );
  }

  return (
    <AdminCard className="lg:col-span-2">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold text-[var(--admin-text-primary)]">
        <ShieldCheck size={15} />
        Passwort ändern
      </h3>

      {success ? (
        <div className="mt-4 flex items-center gap-2 rounded-lg bg-[var(--admin-accent)]/10 px-4 py-3 text-sm text-[var(--admin-accent)]">
          <CheckCircle2 size={16} />
          Passwort geändert. Andere angemeldete Geräte wurden abgemeldet.
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 grid gap-4 sm:grid-cols-3">
          {changePassword.isError && (
            <div className="flex items-center gap-2 rounded-lg bg-[var(--admin-danger)]/10 px-4 py-2.5 text-sm text-[var(--admin-danger)] sm:col-span-3">
              <AlertCircle size={15} />
              {getErrorMessage(changePassword.error, "Das aktuelle Passwort ist falsch.")}
            </div>
          )}

          <PasswordField
            label="Aktuelles Passwort"
            show={showCurrent}
            onToggle={() => setShowCurrent((v) => !v)}
            error={errors.currentPassword?.message}
            autoComplete="current-password"
            inputProps={register("currentPassword")}
          />
          <PasswordField
            label="Neues Passwort"
            show={showNew}
            onToggle={() => setShowNew((v) => !v)}
            error={errors.newPassword?.message}
            autoComplete="new-password"
            inputProps={register("newPassword")}
          />
          <PasswordField
            label="Bestätigen"
            show={showConfirm}
            onToggle={() => setShowConfirm((v) => !v)}
            error={errors.confirmPassword?.message}
            autoComplete="new-password"
            inputProps={register("confirmPassword")}
          />

          <div className="sm:col-span-3">
            <AdminButton type="submit" size="sm" disabled={changePassword.isPending}>
              {changePassword.isPending ? "Wird gespeichert..." : "Passwort ändern"}
            </AdminButton>
          </div>
        </form>
      )}
    </AdminCard>
  );
}

function PasswordField({
  label,
  show,
  onToggle,
  error,
  autoComplete,
  inputProps,
}: {
  label: string;
  show: boolean;
  onToggle: () => void;
  error?: string;
  autoComplete: string;
  inputProps: ReturnType<ReturnType<typeof useForm<ChangePasswordFormData>>["register"]>;
}) {
  return (
    <div>
      <AdminLabel>{label}</AdminLabel>
      <div className="relative">
        <AdminInput type={show ? "text" : "password"} autoComplete={autoComplete} className="pr-10" {...inputProps} />
        <button
          type="button"
          tabIndex={-1}
          onClick={onToggle}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-[var(--admin-text-muted)] hover:text-[var(--admin-text-secondary)]"
        >
          {show ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-[var(--admin-danger)]">{error}</p>}
    </div>
  );
}
