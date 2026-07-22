import AdminUserProfilePage from "@/features/admin/pages/admin-user-profile-page";

export default async function AdminUserProfileRoute({ params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  return <AdminUserProfilePage userId={userId} />;
}
