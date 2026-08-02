"use client";

import { Info, Mail, Shield, User } from "lucide-react";

import { AdminCard, AdminPageHeader } from "@/components/admin/admin-ui";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

export default function SettingsPage() {
  const { user } = useCurrentUser();

  return (
    <div>
      <AdminPageHeader title="Settings" description="Kontoinformationen und Systemeinstellungen." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AdminCard>
          <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Mein Konto</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-2.5 text-[var(--admin-text-secondary)]">
              <User size={14} />
              {user?.username ?? "—"}
            </div>
            <div className="flex items-center gap-2.5 text-[var(--admin-text-secondary)]">
              <Mail size={14} />
              {user?.email ?? "—"}
            </div>
            <div className="flex items-center gap-2.5 text-[var(--admin-text-secondary)]">
              <Shield size={14} />
              {user?.role ?? "—"}
            </div>
          </div>
        </AdminCard>

        <AdminCard className="flex items-start gap-3">
          <Info size={18} className="mt-0.5 shrink-0 text-[var(--admin-primary)]" />
          <p className="text-sm text-[var(--admin-text-secondary)]">
            Plattformweite Einstellungen (E-Mail-Versand, Zahlungsanbieter, Feature-Flags, ...) sind noch
            nicht an ein Backend angebunden. Dieser Bereich zeigt bewusst nur echte, vorhandene Daten an,
            statt Einstellungen zu simulieren, die nirgendwo gespeichert werden.
          </p>
        </AdminCard>
      </div>
    </div>
  );
}
