import { BookOpen, GraduationCap, Users } from "lucide-react";

import BrandenburgGate from "@/components/auth/brandenburg-gate";
import Logo from "@/components/common/logo";
import LoginForm from "./login-form";
import SessionRedirect from "./session-redirect";

const FEATURES = [
  { icon: GraduationCap, label: "Zertifizierte Kurse" },
  { icon: BookOpen, label: "Interaktive Lektionen" },
  { icon: Users, label: "Tausende Lernende" },
];

export default function LoginCard() {
  return (
    <div className="mx-auto grid w-full max-w-4xl overflow-hidden rounded-dialog bg-surface-card shadow-[var(--shadow-lg)] ring-1 ring-surface-border lg:grid-cols-2">
      <SessionRedirect />

      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-brand-700 via-accent-blue to-purple-600 p-10 text-white lg:flex">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-24 left-0 h-64 w-64 rounded-full bg-purple-300/20 blur-3xl" />
        <BrandenburgGate className="pointer-events-none absolute bottom-0 left-1/2 h-[160px] w-[420px] -translate-x-1/2 text-white/10" />

        <div className="relative z-10">
          <div className="inline-flex items-center gap-2.5 rounded-full bg-white/15 px-4 py-2 backdrop-blur-md">
            <GraduationCap size={17} />
            <span className="text-sm font-semibold">Deutsch lernen, professionell</span>
          </div>

          <h2 className="mt-6 text-3xl font-bold leading-tight tracking-tight">
            Dein Weg zum
            <br />
            Deutsch-Zertifikat
          </h2>

          <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/80">
            Von A1 bis C2 — strukturierte Kurse, echte Prüfungsvorbereitung und ein
            Lernpfad, der zu dir passt.
          </p>
        </div>

        <div className="relative z-10 flex flex-col gap-3">
          {FEATURES.map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-3 rounded-2xl bg-white/10 px-4 py-3 backdrop-blur-md transition hover:bg-white/15"
            >
              <Icon size={18} />
              <span className="text-sm font-medium">{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="relative p-8 sm:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--accent-blue)_0%,transparent_60%)] opacity-[0.05]" />

        <div className="relative">
          <div className="mb-8 flex flex-col items-center lg:items-start">
            <Logo size={48} showText={false} />
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-text-primary">
              Willkommen zurück
            </h1>
            <p className="mt-2 text-center text-sm leading-6 text-text-secondary lg:text-left">
              Melde dich an, um mit deinem Deutschkurs fortzufahren.
            </p>
          </div>

          <LoginForm />
        </div>
      </div>
    </div>
  );
}
