"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import Loading from "@/components/common/loading";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

interface Props {
  children: React.ReactNode;
  /** If set, only this role may view the children — anyone else (including
   * an otherwise-valid session) is redirected to /dashboard instead. */
  requiredRole?: string;
}

export default function AuthGuard({ children, requiredRole }: Props) {
  const router = useRouter();
  const { user, loading, error } = useCurrentUser();

  const unauthenticated = !loading && (error || !user);
  const forbidden = !loading && !!user && !!requiredRole && user.role !== requiredRole;
  // The Super Admin account must always land on /admin, never /dashboard —
  // even if they navigate here directly instead of via the login flow.
  const isSuperAdminOnStudentSurface = !loading && !!user && user.role === "SUPER_ADMIN";

  useEffect(() => {
    if (unauthenticated) {
      router.replace("/login");
    } else if (isSuperAdminOnStudentSurface) {
      router.replace("/admin");
    } else if (forbidden) {
      router.replace("/dashboard");
    }
  }, [unauthenticated, isSuperAdminOnStudentSurface, forbidden, router]);

  if (loading || unauthenticated || isSuperAdminOnStudentSurface || forbidden) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-bg">
        <Loading />
      </div>
    );
  }

  return <>{children}</>;
}
