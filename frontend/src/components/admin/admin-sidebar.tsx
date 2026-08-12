"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";

import Logo from "@/components/common/logo";
import { ADMIN_NAV_GROUPS } from "@/features/admin/constants/nav";
import { cn } from "@/lib/utils";

function isActive(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function AdminSidebar({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <aside className={cn("flex h-full w-[270px] flex-col bg-[var(--admin-card)]", className)}>
      <div className="flex items-center gap-2 border-b border-[var(--admin-border)] px-5 py-6">
        <Logo size={40} showText={false} />
        <div>
          <p className="text-sm font-extrabold leading-tight tracking-tight text-[var(--admin-text-primary)]">
            VIZU <span className="text-[var(--admin-primary)]">Admin</span>
          </p>
          <p className="mt-0.5 flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-[var(--admin-text-muted)]">
            <ShieldCheck size={11} />
            Super Admin
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-5">
        {ADMIN_NAV_GROUPS.map((group, i) => (
          <div key={i} className={i > 0 ? "border-t border-[var(--admin-border)] pt-4" : ""}>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-[var(--admin-primary)]/15 text-[var(--admin-primary)]"
                        : "text-[var(--admin-text-secondary)] hover:bg-[var(--admin-hover)] hover:text-[var(--admin-text-primary)]",
                    )}
                  >
                    <item.icon size={17} className="shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
