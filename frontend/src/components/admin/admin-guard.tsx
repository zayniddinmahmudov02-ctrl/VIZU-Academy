"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

/** Gate for the entire /admin route tree. Deliberately standalone — does
 * NOT import components/auth/auth-guard.tsx (the Student Dashboard's
 * guard) even though the logic is similar, so the two dashboards stay
 * fully import-independent per the "never import each other's
 * components" requirement. Only `useCurrentUser` (shared auth/identity
 * infrastructure, not a dashboard component) is reused — rebuilding the
 * session-resolution logic itself would mean two divergent sources of
 * truth for "who is logged in," which is a real risk, not just
 * duplication. */
export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading, error } = useCurrentUser();

  const unauthenticated = !loading && (error || !user);
  const notSuperAdmin = !loading && !!user && user.role !== "SUPER_ADMIN";

  useEffect(() => {
    if (unauthenticated) {
      router.replace("/login");
    } else if (notSuperAdmin) {
      router.replace("/dashboard");
    }
  }, [unauthenticated, notSuperAdmin, router]);

  if (loading || unauthenticated || notSuperAdmin) {
    return (
      <div className="admin-shell flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-[var(--admin-border-strong)] border-t-[var(--admin-primary)]" />
      </div>
    );
  }

  return <>{children}</>;
}
