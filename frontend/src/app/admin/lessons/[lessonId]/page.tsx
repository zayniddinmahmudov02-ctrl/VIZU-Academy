import AdminLessonDetailPage from "@/features/admin/pages/admin-lesson-detail-page";

export default async function AdminLessonDetailRoute({ params }: { params: Promise<{ lessonId: string }> }) {
  const { lessonId } = await params;
  return <AdminLessonDetailPage lessonId={lessonId} />;
}
