"use client";

import { useMemo } from "react";
import { Wrench } from "lucide-react";

import { sidebarItems } from "@/constants/sidebar";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

/** The static sidebar list, plus "Admin Panel" appended for SUPER_ADMIN
 *  only — computed fresh on every render from the live user role (no
 *  stale cache), so it never needs a page refresh to appear or disappear. */
export function useSidebarItems() {
  const { user } = useCurrentUser();

  return useMemo(() => {
    if (user?.role !== "SUPER_ADMIN") {
      return sidebarItems;
    }

    return [
      ...sidebarItems,
      {
        titleKey: "sidebar.adminPanel",
        href: "/admin",
        icon: Wrench,
      },
    ];
  }, [user?.role]);
}
