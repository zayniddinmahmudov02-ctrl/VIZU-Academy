"use client";

import Link from "next/link";
import { Award, BookOpen, ClipboardCheck, Layers3, type LucideIcon, Megaphone, UserPlus, Video } from "lucide-react";

import { AdminCard } from "@/components/admin/admin-ui";

interface QuickAction {
  label: string;
  href?: string;
  icon: LucideIcon;
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: "New Course", href: "/admin/levels", icon: BookOpen },
  { label: "New Lesson", href: "/admin/lessons", icon: Video },
  { label: "New Module", href: "/admin/modules", icon: Layers3 },
  { label: "New Mock Test", href: "/admin/mock-exams", icon: ClipboardCheck },
  { label: "New User", href: "/admin/users", icon: UserPlus },
  { label: "New Certificate", href: "/admin/certificates", icon: Award },
  { label: "Broadcast Message", icon: Megaphone },
];

export default function DashboardQuickActions() {
  return (
    <AdminCard>
      <h3 className="mb-4 text-sm font-semibold text-[var(--admin-text-primary)]">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          const content = (
            <>
              <Icon size={17} />
              <span>{action.label}</span>
            </>
          );
          if (!action.href) {
            return (
              <div
                key={action.label}
                title="Coming soon"
                className="flex cursor-not-allowed items-center gap-2 rounded-lg bg-white/[0.02] px-3.5 py-2.5 text-sm font-medium text-[var(--admin-text-muted)] opacity-50"
              >
                {content}
              </div>
            );
          }
          return (
            <Link
              key={action.label}
              href={action.href}
              className="flex items-center gap-2 rounded-lg bg-[var(--admin-card)] px-3.5 py-2.5 text-sm font-medium text-[var(--admin-text-primary)] ring-1 ring-[var(--admin-border-strong)] transition hover:bg-[var(--admin-card-hover)] hover:text-[var(--admin-primary)]"
            >
              {content}
            </Link>
          );
        })}
      </div>
    </AdminCard>
  );
}
