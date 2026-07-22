import Link from "next/link";

import Logo from "@/components/common/logo";
import LoginForm from "./login-form";

export default function LoginCard() {
  return (
    <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-dialog bg-surface-card p-8 shadow-[var(--shadow-lg)] ring-1 ring-surface-border sm:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />

      <div className="relative">
        <div className="mb-8 flex flex-col items-center">
          <Logo size={48} showText={false} />
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">
            VIZU Academy
          </h1>
          <p className="mt-2 text-center text-sm leading-6 text-text-secondary">
            Professional Language Learning Platform
          </p>
        </div>

        <LoginForm />

        <div className="mt-6 flex items-center justify-between text-sm">
          <Link href="/forgot-password" className="font-medium text-accent-blue hover:text-accent-blue-hover">
            Passwort vergessen?
          </Link>
          <Link href="/register" className="font-medium text-text-secondary hover:text-text-primary">
            Konto erstellen
          </Link>
        </div>
      </div>
    </div>
  );
}
