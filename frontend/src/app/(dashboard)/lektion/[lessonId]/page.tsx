import LmsLessonClient from "./lms-lesson-client";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ lessonId: string }>;
}

export default async function LmsLessonPage({ params }: Props) {
  const { lessonId } = await params;
  return <LmsLessonClient lessonId={lessonId} />;
}
