import MediaManagementClient from "@/features/admin/components/media-management/media-management-client";

interface Props {
  searchParams: Promise<{ level?: string | string[] }>;
}

export default async function MediaManagementPage({ searchParams }: Props) {
  const params = await searchParams;
  const initialLevel = params.level === "A2" ? "A2" : "";
  return <MediaManagementClient initialLevel={initialLevel} />;
}
