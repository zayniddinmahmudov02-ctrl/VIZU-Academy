export interface AdminCourseItem {
  id: string;
  languageId: string;
  level: string;
  title: string;
  description: string | null;
  orderIndex: number;
  isActive: boolean;
}

export interface CreateCourseInput {
  languageId: string;
  level: string;
  title: string;
  description?: string;
  orderIndex?: number;
  isActive?: boolean;
}

export interface UpdateCourseInput {
  languageId?: string;
  level?: string;
  title?: string;
  description?: string;
  orderIndex?: number;
  isActive?: boolean;
}
