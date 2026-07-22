import { Laptop, Smartphone, Tablet } from "lucide-react";

import type { DeviceHistoryItem } from "../types/user";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("de-DE", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function iconFor(device: string) {
  if (device === "Mobile") return Smartphone;
  if (device === "Tablet") return Tablet;
  return Laptop;
}

export default function DeviceHistoryList({ devices }: { devices: DeviceHistoryItem[] }) {
  return (
    <div className="admin-glass rounded-2xl p-5">
      <p className="mb-4 text-xs font-bold uppercase tracking-wide text-[var(--admin-text-muted)]">Device History</p>

      <div className="space-y-2">
        {devices.length === 0 ? (
          <p className="py-6 text-center text-xs text-[var(--admin-text-muted)]">No devices recorded yet.</p>
        ) : (
          devices.map((device, index) => {
            const Icon = iconFor(device.device);
            return (
              <div key={index} className="flex items-center justify-between rounded-xl bg-white/[0.03] px-3 py-2.5">
                <div className="flex items-center gap-3">
                  <Icon size={16} className="text-[var(--admin-text-secondary)]" />
                  <div>
                    <p className="text-sm text-white">
                      {device.device} · {device.browser} · {device.os}
                    </p>
                    <p className="text-[11px] text-[var(--admin-text-muted)]">
                      {device.ipAddress ?? "Unknown IP"} · {device.loginCount} logins
                    </p>
                  </div>
                </div>
                <span className="shrink-0 text-[11px] text-[var(--admin-text-muted)]">Last seen {formatDate(device.lastSeen)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
