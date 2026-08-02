import { Suspense } from "react";

import Loading from "@/components/common/loading";
import ResetPasswordCard from "@/features/auth/components/reset-password-card";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ResetPasswordCard />
    </Suspense>
  );
}
