"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import ZertifikateClient from "@/features/admin/components/certificates/zertifikate-client";

/** One student's certificates — course certificates and VIZU-Multilevel — from the unified view. */
export default function UserCertificateProfilePage() {
  const { userId } = useParams<{ userId: string }>();

  return (
    <div>
      <Link
        href="/admin/certificates"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--admin-text-muted)] hover:text-[var(--admin-text-primary)]"
      >
        <ArrowLeft size={14} />
        Zertifikate
      </Link>

      <AdminPageHeader title="Zertifikatsprofil" description="Alle Zertifikate dieses Lernenden." />

      <Suspense fallback={<p className="py-10 text-center text-sm text-[var(--admin-text-muted)]">Lädt …</p>}>
        <ZertifikateClient userId={userId} />
      </Suspense>
    </div>
  );
}
