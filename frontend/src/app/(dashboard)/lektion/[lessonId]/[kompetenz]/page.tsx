import LmsLessonClient from "../lms-lesson-client";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ lessonId: string; kompetenz: string }>;
}

export default async function LmsCompetencyPage({ params }: Props) {
  const { lessonId, kompetenz } = await params;
  return <LmsLessonClient lessonId={lessonId} kompetenz={kompetenz} />;
}
