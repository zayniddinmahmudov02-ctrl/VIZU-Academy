"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import Loading from "@/components/common/loading";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { loginUrl } from "@/lib/auth-redirect";

/** Login check for the full-screen meeting route. Unlike AuthGuard it does not send a SUPER_ADMIN to /admin: a
 *  Super Admin may host any group's lesson. Who may enter which room is decided by the backend (join → 404 / 403). */
export default function MeetingGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading, error } = useCurrentUser();
  const unauthenticated = !loading && (error || !user);

  useEffect(() => {
    if (unauthenticated) router.replace(loginUrl());
  }, [unauthenticated, router]);

  if (loading || unauthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loading />
      </div>
    );
  }
  return <>{children}</>;
}
