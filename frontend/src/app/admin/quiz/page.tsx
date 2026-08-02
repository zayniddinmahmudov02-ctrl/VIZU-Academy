"use client";

import { AdminPageHeader } from "@/components/admin/admin-ui";
import QuizManager from "@/features/admin/components/managers/quiz-manager";

export default function QuizPage() {
  return (
    <div>
      <AdminPageHeader title="Quiz" description="Alle Quizze, plattformweit." />
      <QuizManager />
    </div>
  );
}
