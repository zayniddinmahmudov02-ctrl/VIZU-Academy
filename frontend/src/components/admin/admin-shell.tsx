"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import AdminSidebar from "./admin-sidebar";
import AdminTopbar from "./admin-topbar";

interface Props {
  children: ReactNode;
}

const SUPER_ADMIN = "SUPER_ADMIN";

export default function AdminShell({ children }: Props) {
  const router = useRouter();
  const { user, loading, error } = useCurrentUser();

  const authorized = !loading && !error && user?.role === SUPER_ADMIN;
  const denied = !loading && (error || (user && user.role !== SUPER_ADMIN));

  useEffect(() => {
    if (denied) {
      router.replace("/dashboard");
    }
  }, [denied, router]);

  if (loading) {
    return (
      <div className="admin-shell flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
      </div>
    );
  }

  if (!authorized) {
    return <div className="admin-shell min-h-screen" />;
  }

  return (
    <div className="admin-shell flex min-h-screen">
      <AdminSidebar user={user} />
      <div className="flex min-w-0 flex-1 flex-col">
        <AdminTopbar user={user} />
        <main className="flex-1 overflow-x-hidden p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
