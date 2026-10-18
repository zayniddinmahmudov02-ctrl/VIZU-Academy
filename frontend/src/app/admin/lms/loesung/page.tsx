import { Suspense } from "react";

import LoesungListClient from "@/features/admin/components/loesung/loesung-list-client";

export const dynamic = "force-dynamic";

export default function LoesungPage() {
  return (
    <Suspense fallback={null}>
      <LoesungListClient />
    </Suspense>
  );
}