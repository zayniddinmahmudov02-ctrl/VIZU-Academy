"use client";

import { AdminLabel, AdminSelect } from "@/components/admin/admin-ui";
import { useCrudList } from "@/features/admin/hooks/use-crud";
import { lessonsApi } from "@/features/admin/services/lessons-service";

interface Props {
  value: string;
  onChange: (lessonId: string) => void;
  label?: string;
}

export default function LessonPicker({ value, onChange, label = "Lektion" }: Props) {
  const { data: lessons } = useCrudList("lessons", lessonsApi);

  return (
    <div>
      <AdminLabel>{label}</AdminLabel>
      <AdminSelect value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Lektion wählen...</option>
        {(lessons ?? []).map((lesson) => (
          <option key={lesson.id} value={lesson.id}>
            {lesson.number}. {lesson.title}
          </option>
        ))}
      </AdminSelect>
    </div>
  );
}
