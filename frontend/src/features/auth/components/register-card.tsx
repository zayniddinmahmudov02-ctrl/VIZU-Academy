import Link from "next/link";

import Logo from "@/components/common/logo";
import RegisterForm from "./register-form";

export default function RegisterCard() {
  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-purple)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-8 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">
            Konto erstellen
          </h1>
          <p className="mt-2 text-center text-sm leading-6 text-text-secondary">
            Starte deine Deutschlernreise mit VIZU Academy.
          </p>
        </div>

        <RegisterForm />

        <p className="mt-6 text-center text-sm text-text-secondary">
          Bereits ein Konto?{" "}
          <Link href="/login" className="font-medium text-accent-blue hover:text-accent-blue-hover">
            Anmelden
          </Link>
        </p>
      </div>
    </div>
  );
}
