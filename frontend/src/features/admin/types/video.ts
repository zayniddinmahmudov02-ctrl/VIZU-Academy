export interface AdminVideoItem {
  id: string;
  lessonId: string;
  title: string;
  description: string | null;
  videoUrl: string | null;
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
  thumbnailFile?: File;
  durationSeconds?: number;
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

export interface ReplaceVideoInput {
  file: File;
  durationSeconds?: number;
}
