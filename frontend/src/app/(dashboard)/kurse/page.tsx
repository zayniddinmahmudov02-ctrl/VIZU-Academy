import KursePageClient from "./kurse-page-client";

// client-fetched per student — never a cached static shell
export const dynamic = "force-dynamic";

export default function KursePage() {
  return <KursePageClient />;
}
