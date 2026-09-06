"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

/** Gate for the entire /teacher route tree — TEACHER or SUPER_ADMIN only
 * (mirrors components/admin/admin-guard.tsx's independent-guard pattern:
 * deliberately standalone, not importing AuthGuard/AdminGuard, so none of
 * the three dashboards depend on each other's components). The actual,
 * unbypassable check is server-side (require_teacher_panel_access,
 * backend/app/api/dependencies/auth.py) — this is UX only. */
export default function TeacherGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading, error } = useCurrentUser();

  const unauthenticated = !loading && (error || !user);
  const forbidden = !loading && !!user && user.role !== "TEACHER" && user.role !== "SUPER_ADMIN";

  useEffect(() => {
    if (unauthenticated) {
      router.replace("/login");
    } else if (forbidden) {
      router.replace("/dashboard");
    }
  }, [unauthenticated, forbidden, router]);

  if (loading || unauthenticated || forbidden) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-bg">
        <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-surface-border border-t-accent-blue" />
      </div>
    );
  }

  return <>{children}</>;
}
