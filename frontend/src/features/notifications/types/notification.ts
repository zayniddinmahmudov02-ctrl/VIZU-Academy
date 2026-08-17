export type NotificationType = "information" | "update" | "exam" | "course" | "system";

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  createdAt: string;
  isRead: boolean;
  audioUrl?: string;
}

export interface NotificationInput {
  title: string;
  message: string;
  type: NotificationType;
}
