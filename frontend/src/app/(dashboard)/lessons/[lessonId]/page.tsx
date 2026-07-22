import { redirect } from "next/navigation";

import { DEFAULT_SECTION_SLUG } from "@/constants/lesson-sections";

interface Props {
  params: Promise<{
    lessonId: string;
  }>;
}

export default async function LessonRedirectPage({ params }: Props) {
  const { lessonId } = await params;

  redirect(`/lessons/${lessonId}/${DEFAULT_SECTION_SLUG}`);
}
