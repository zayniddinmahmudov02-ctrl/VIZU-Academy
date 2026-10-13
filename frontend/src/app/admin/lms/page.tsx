import LmsPageClient from "@/features/admin/components/lms/lms-page-client";

// Client-fetched content only — dynamic rendering avoids a long-cached
// static shell.
export const dynamic = "force-dynamic";

export default function LmsPage() {
  return <LmsPageClient />;
}
