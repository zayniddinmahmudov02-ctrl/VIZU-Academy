"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Eye } from "lucide-react";

import { getImpersonatingLabel, isImpersonating, stopImpersonation } from "@/src/lib/token";

export default function ImpersonationBanner() {
  const pathname = usePathname();
  const router = useRouter();
  const [active, setActive] = useState(false);
  const [label, setLabel] = useState<string | null>(null);

  useEffect(() => {
    setActive(isImpersonating());
    setLabel(getImpersonatingLabel());
  }, [pathname]);

  if (!active || pathname?.startsWith("/admin")) {
    return null;
  }

  function handleExit() {
    stopImpersonation();
    router.push("/admin/users");
    router.refresh();
  }

  return (
    <div className="sticky top-0 z-[100] flex items-center justify-center gap-3 bg-[#5b5bf8] px-4 py-2 text-sm font-medium text-white">
      <Eye size={16} />
      <span>Viewing as {label ?? "user"} (impersonated by Super Admin)</span>
      <button
        type="button"
        onClick={handleExit}
        className="rounded-lg bg-white/20 px-3 py-1 text-xs font-semibold transition-colors hover:bg-white/30"
      >
        Exit
      </button>
    </div>
  );
}
