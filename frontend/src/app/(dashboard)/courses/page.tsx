import CoursesPageClient from "./courses-page-client";

// This page's content is 100% client-fetched (React Query) — forcing
// dynamic rendering just drops the default 1-year static-shell cache
// (`s-maxage=31536000`) that Next.js otherwise applies, so a deploy is
// never at risk of a stale cached shell outliving its own JS bundle.
export const dynamic = "force-dynamic";

export default function CoursesPage() {
  return <CoursesPageClient />;
}
