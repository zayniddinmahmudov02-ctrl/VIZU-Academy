"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, Eye, EyeOff, ShieldCheck } from "lucide-react";

import Button from "@/components/ui/button";
import Checkbox from "@/components/ui/checkbox";
import Input from "@/components/ui/input";
import { decodeJwtPayload } from "@/lib/jwt";
import { saveRefreshToken, saveToken } from "@/lib/token";

import { useLogin } from "../hooks/use-login";
import { verifyAdminPasswordService } from "../services/auth.service";
import type { JwtPayload } from "../types/auth.types";
import { getErrorMessage } from "../utils/get-error-message";

import {
  loginSchema,
  LoginFormData,
} from "../validation/login.schema";

export default function LoginForm() {
  const router = useRouter();

  const loginMutation = useLogin();

  const [step, setStep] = useState<"credentials" | "admin-verify">("credentials");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const [adminPassword, setAdminPassword] = useState("");
  const [showAdminPassword, setShowAdminPassword] = useState(false);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminVerifying, setAdminVerifying] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormData) {
    setFormError(null);

    try {
      const response = await loginMutation.mutateAsync(data);

      saveToken(response.access_token, rememberMe);
      saveRefreshToken(response.refresh_token, rememberMe);

      const payload = decodeJwtPayload<JwtPayload>(response.access_token);

      if (payload?.role === "SUPER_ADMIN") {
        setStep("admin-verify");
        return;
      }

      router.push("/dashboard");
    } catch (error) {
      setFormError(getErrorMessage(error, "Email oder Passwort ist falsch."));
    }
  }

  async function onVerifyAdminPassword() {
    setAdminError(null);
    setAdminVerifying(true);

    try {
      await verifyAdminPasswordService({ password: adminPassword });
      router.push("/admin");
    } catch (error) {
      setAdminError(getErrorMessage(error, "Incorrect administrator password."));
    } finally {
      setAdminVerifying(false);
    }
  }

  if (step === "admin-verify") {
    return (
      <div className="space-y-5">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue/10">
            <ShieldCheck size={26} className="text-accent-blue" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-text-primary">
              Zusätzliche Verifizierung
            </h2>
            <p className="mt-1 text-sm text-text-secondary">
              Für den Super-Admin-Zugang ist ein zusätzliches Admin-Passwort erforderlich.
            </p>
          </div>
        </div>

        {adminError && (
          <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{adminError}</span>
          </div>
        )}

        <div>
          <label className="mb-2 block text-sm font-medium text-text-primary">
            Admin-Passwort
          </label>
          <div className="relative">
            <Input
              type={showAdminPassword ? "text" : "password"}
              placeholder="Admin-Passwort"
              value={adminPassword}
              error={!!adminError}
              onChange={(e) => setAdminPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onVerifyAdminPassword();
                }
              }}
              className="pr-11"
              autoFocus
            />
            <button
              type="button"
              onClick={() => setShowAdminPassword((v) => !v)}
              className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
              tabIndex={-1}
              aria-label={showAdminPassword ? "Passwort verbergen" : "Passwort anzeigen"}
            >
              {showAdminPassword ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </div>

        <Button
          type="button"
          fullWidth
          disabled={adminVerifying || adminPassword.length === 0}
          onClick={onVerifyAdminPassword}
        >
          {adminVerifying ? "Wird überprüft..." : "Bestätigen"}
        </Button>

        <button
          type="button"
          onClick={() => {
            setStep("credentials");
            setAdminPassword("");
            setAdminError(null);
          }}
          className="w-full text-center text-sm font-medium text-text-secondary hover:text-text-primary"
        >
          Zurück zur Anmeldung
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {formError && (
        <div className="flex items-start gap-2 rounded-xl bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Email</label>

        <Input type="email" placeholder="deine@email.com" error={!!errors.email} {...register("email")} />

        {errors.email && (
          <p className="mt-2 text-sm text-danger">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-text-primary">Passwort</label>

        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            placeholder="Passwort"
            autoComplete="current-password"
            error={!!errors.password}
            className="pr-11"
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-text-muted hover:text-text-secondary"
            tabIndex={-1}
            aria-label={showPassword ? "Passwort verbergen" : "Passwort anzeigen"}
          >
            {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
          </button>
        </div>

        {errors.password && (
          <p className="mt-2 text-sm text-danger">{errors.password.message}</p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <label className="flex cursor-pointer items-center gap-2.5 select-none">
          <Checkbox checked={rememberMe} onCheckedChange={setRememberMe} aria-label="Angemeldet bleiben" />
          <span className="text-sm text-text-secondary">Angemeldet bleiben</span>
        </label>

        <Link href="/forgot-password" className="text-sm font-medium text-accent-blue hover:text-accent-blue-hover">
          Passwort vergessen?
        </Link>
      </div>

      <Button type="submit" fullWidth disabled={loginMutation.isPending}>
        {loginMutation.isPending ? "Wird angemeldet..." : "Anmelden"}
      </Button>

      <p className="text-center text-sm text-text-secondary">
        Noch kein Konto?{" "}
        <Link href="/register" className="font-medium text-accent-blue hover:text-accent-blue-hover">
          Jetzt registrieren
        </Link>
      </p>
    </form>
  );
}
