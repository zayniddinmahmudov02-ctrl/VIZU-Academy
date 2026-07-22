export interface AdminVideoItem {
  id: string;
  lessonId: string;
  title: string;
  description: string | null;
  thumbnailUrl: string | null;
  durationSeconds: number;
  orderIndex: number;
  isPreview: boolean;
  isPublished: boolean;
  hasStorageKey: boolean;
}

export interface UploadVideoInput {
  lessonId: string;
  title: string;
  description?: string;
  thumbnailUrl?: string;
  orderIndex?: number;
  isPreview?: boolean;
  isPublished?: boolean;
  file: File;
}

export interface UpdateVideoInput {
  title?: string;
  description?: string;
  thumbnailUrl?: string;
  orderIndex?: number;
  isPreview?: boolean;
  isPublished?: boolean;
}
