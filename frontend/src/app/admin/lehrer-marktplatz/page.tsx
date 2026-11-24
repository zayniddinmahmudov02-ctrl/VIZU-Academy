"use client";

import AdminMarket from "@/features/teacher-market/components/admin-market";

/** Admin -> Lehrer-Marktplatz (My Teacher): staff read, SUPER_ADMIN decides (the backend enforces both). */
export default function AdminTeacherMarketPage() {
  return <AdminMarket />;
}
