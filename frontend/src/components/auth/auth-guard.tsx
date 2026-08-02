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
        <Loading />
      </div>
    );
  }

  return <>{children}</>;
}
