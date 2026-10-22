"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import Logo from "@/components/common/logo";
import { ADMIN_NAV_GROUPS } from "@/features/admin/constants/nav";
import { getManagedPageNavigation } from "@/features/admin/services/page-management-service";
import { cn } from "@/lib/utils";

function matches(pathname: string, href: string): boolean {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

// only the most specific matching item is active (/admin/lms/loesung marks
// "Lösung", not also its parent "LMS A1–C1")
const ALL_HREFS = ADMIN_NAV_GROUPS.flatMap((g) => g.items.map((i) => i.href));

function isActive(pathname: string, href: string): boolean {
  if (!matches(pathname, href)) return false;
  return !ALL_HREFS.some((other) => other !== href && other.length > href.length && matches(pathname, other));
}

export default function AdminSidebar({ className }: { className?: string }) {
  const pathname = usePathname();
  const navigation = useQuery({
    queryKey: ["admin-managed-page-navigation"],
    queryFn: getManagedPageNavigation,
    staleTime: 30_000,
  });
  const navGroups = ADMIN_NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => navigation.data?.[item.href] !== false),
  })).filter((group) => group.items.length > 0);

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
        {navigation.isError && (
          <p role="status" className="px-3 text-xs text-[var(--admin-warning)]">
            Menüstatus konnte nicht geladen werden; Standardmenü wird angezeigt.
          </p>
        )}
        {navGroups.map((group, i) => (
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
                      item.child && "ml-6 py-2 text-[13px]",
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
