export interface AdminLessonItem {
  id: string;
  moduleId: string;
  number: number;
  title: string;
  duration: number;
  isFree: boolean;
  videoUrl: string | null;
}

export interface CreateLessonInput {
  moduleId: string;
  number: number;
  title: string;
  duration: number;
  isFree?: boolean;
  videoUrl?: string | null;
}

export interface UpdateLessonInput {
  moduleId?: string;
  number?: number;
  title?: string;
  duration?: number;
  isFree?: boolean;
  videoUrl?: string | null;
}

export interface AdminModuleOption {
  id: string;
  title: string;
  courseId: string;
}
