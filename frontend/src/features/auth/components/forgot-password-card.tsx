import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import Logo from "@/components/common/logo";
import ForgotPasswordForm from "./forgot-password-form";

export default function ForgotPasswordCard() {
  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-8 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">
            Passwort vergessen?
          </h1>
          <p className="mt-2 text-center text-sm leading-6 text-text-secondary">
            Gib deine E-Mail-Adresse ein und wir senden dir einen Link zum Zurücksetzen.
          </p>
        </div>

        <ForgotPasswordForm />

        <Link
          href="/login"
          className="mt-6 flex items-center justify-center gap-1.5 text-sm font-medium text-text-secondary hover:text-text-primary"
        >
          <ArrowLeft size={15} />
          Zurück zur Anmeldung
        </Link>
      </div>
    </div>
  );
}
